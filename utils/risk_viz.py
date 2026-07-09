"""Visual explanations for *why* a clause is risky.

Two jobs:
  1. Locate a risky clause inside the source contract and highlight it in context,
     so the reader sees where the risk actually lives.
  2. Show the drivers behind the score — likelihood x impact per clause — as
     charts and per-clause meters.

Severity is a *status* encoding (Critical/High/Medium/Low), so it never travels as
colour alone: every severity mark carries a text label, and the risk matrix also
varies marker shape. Critical/High/Medium sit close together under deuteranopia,
which makes the secondary encoding mandatory rather than decorative.
"""

from __future__ import annotations

import html
import re
from difflib import SequenceMatcher

import plotly.graph_objects as go

from utils import theme

SEVERITY_ORDER = ["Critical", "High", "Medium", "Low"]

# Fallbacks for analyses saved before the agent returned likelihood/impact.
_SEVERITY_DEFAULTS = {
    "critical": (5, 4),
    "high": (4, 3),
    "medium": (3, 3),
    "low": (2, 2),
}

# Distinct shapes so severity survives colour-vision deficiency.
_SEVERITY_SYMBOL = {
    "Critical": "diamond",
    "High": "square",
    "Medium": "triangle-up",
    "Low": "circle",
}

_LIKELIHOOD_TICKS = ["Rare", "Unlikely", "Possible", "Likely", "Almost certain"]
_IMPACT_TICKS = ["Minor", "Moderate", "Serious", "Major", "Severe"]


def severity_color(severity: str) -> str:
    return theme.RISK_COLORS.get(str(severity).lower(), theme.MUTED)


def _clamp(value, lo: int = 1, hi: int = 5) -> int:
    try:
        return max(lo, min(hi, int(round(float(value)))))
    except (TypeError, ValueError):
        return lo


def normalize_clause(clause: dict) -> dict:
    """Fill in likelihood/impact, derived from severity when the agent omitted them."""
    severity = str(clause.get("severity", "Medium")).title()
    if severity not in SEVERITY_ORDER:
        severity = "Medium"
    d_impact, d_likelihood = _SEVERITY_DEFAULTS[severity.lower()]

    impact = _clamp(clause.get("impact", d_impact))
    likelihood = _clamp(clause.get("likelihood", d_likelihood))
    return {
        **clause,
        "severity": severity,
        "impact": impact,
        "likelihood": likelihood,
        "exposure": impact * likelihood,
    }


def normalize_clauses(clauses: list[dict]) -> list[dict]:
    return [normalize_clause(c) for c in clauses or []]


# ---------------------------------------------------------------------------
# Locating the clause inside the contract
# ---------------------------------------------------------------------------
def _text_to_html(text: str) -> str:
    """Escape untrusted text and preserve its line breaks as markup."""
    return html.escape(text).replace("\n", "<br>")


def _split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.;:])\s+|\n+", text)
    return [p for p in (s.strip() for s in parts) if p]


def _ratio(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


# Legal boilerplate carries no signal about *which* clause we are looking at.
_STOPWORDS = frozenset("""
a an the and or of to in on at by for with from as is are be been shall will may
this that these those any all such other no not it its their his her party parties
agreement section clause herein hereof thereof pursuant which who whom whose
""".split())


def _content_tokens(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {w for w in words if w not in _STOPWORDS and len(w) > 2}


def _containment(needle_tokens: set[str], window: str) -> float:
    """Share of the clause's meaningful words that appear in the candidate window.

    A pure character ratio produces confident nonsense on legal prose — every
    sentence shares the same boilerplate — so a clause absent from the contract
    can still score ~0.4 against an unrelated sentence. Requiring the clause's
    *content words* to actually be present is what rejects those.
    """
    if not needle_tokens:
        return 0.0
    return len(needle_tokens & _content_tokens(window)) / len(needle_tokens)


def locate_clause(contract_text: str, clause_text: str,
                  min_score: float = 0.30, min_containment: float = 0.5):
    """Best-effort locate `clause_text` in `contract_text`.

    The agent may paraphrase, so this scores sliding windows of sentences rather
    than looking for an exact substring. A window must clear BOTH a character
    similarity floor and a content-word containment floor. Returns
    (start, end, score) character offsets, or None when nothing matches well enough.
    """
    if not contract_text or not clause_text:
        return None

    needle = " ".join(clause_text.split())
    if not needle:
        return None

    # Exact hit is the common case for verbatim quotes — take it directly.
    idx = contract_text.lower().find(needle.lower())
    if idx != -1:
        return idx, idx + len(needle), 1.0

    sentences = _split_sentences(contract_text)
    if not sentences:
        return None

    # Locate each sentence's offset so we can map a window back to the source.
    offsets, cursor = [], 0
    for s in sentences:
        found = contract_text.find(s, cursor)
        if found == -1:
            found = cursor
        offsets.append(found)
        cursor = found + len(s)

    needle_tokens = _content_tokens(needle)
    span = max(1, min(len(sentences), len(_split_sentences(needle))))
    best = None
    for width in {span, span + 1}:
        for i in range(len(sentences) - width + 1):
            window = " ".join(sentences[i:i + width])
            if _containment(needle_tokens, window) < min_containment:
                continue
            score = _ratio(window, needle)
            if best is None or score > best[2]:
                start = offsets[i]
                end = offsets[i + width - 1] + len(sentences[i + width - 1])
                best = (start, end, score)

    if best and best[2] >= min_score:
        return best
    return None


def highlight_clause_html(contract_text: str, clause_text: str, severity: str,
                          context_chars: int = 320) -> str | None:
    """Render the located clause highlighted inside its surrounding contract text."""
    hit = locate_clause(contract_text, clause_text)
    if not hit:
        return None
    start, end, score = hit

    lead_start = max(0, start - context_chars)
    tail_end = min(len(contract_text), end + context_chars)

    lead = contract_text[lead_start:start]
    body = contract_text[start:end]
    tail = contract_text[end:tail_end]

    color = severity_color(severity)
    prefix = "…" if lead_start > 0 else ""
    suffix = "…" if tail_end < len(contract_text) else ""
    exact = "verbatim match" if score >= 0.999 else f"closest match · {score:.0%} similar"

    # Escape first, then turn newlines into <br>. Collapsing the markup instead
    # (as theme._compact does) would glue words across the contract's line breaks.
    lead_html = _text_to_html(prefix + lead)
    body_html = _text_to_html(body)
    tail_html = _text_to_html(tail + suffix)

    return (
        '<div class="risk-excerpt">'
        '<div class="risk-excerpt-head">📍 Where this appears in the contract'
        f'<span class="risk-excerpt-meta">{html.escape(exact)}</span></div>'
        f'<div class="risk-excerpt-body">{lead_html}'
        f'<mark class="risk-mark" style="--mark:{color};">{body_html}</mark>'
        f'{tail_html}</div></div>'
    )


# ---------------------------------------------------------------------------
# Per-clause "why it's a risk" panel
# ---------------------------------------------------------------------------
def _meter(label: str, value: int, caption: str, color: str) -> str:
    pct = int(value / 5 * 100)
    return (
        '<div class="risk-meter"><div class="risk-meter-top">'
        f'<span class="risk-meter-label">{html.escape(label)}</span>'
        f'<span class="risk-meter-val">{value}<span class="risk-meter-max">/5</span></span></div>'
        '<div class="risk-meter-track">'
        f'<div class="risk-meter-fill" style="width:{pct}%; background:{color};"></div></div>'
        f'<div class="risk-meter-cap">{html.escape(caption)}</div></div>'
    )


def why_panel_html(clause: dict) -> str:
    """A compact visual answer to 'why is this a risk?'."""
    c = normalize_clause(clause)
    color = severity_color(c["severity"])
    likelihood, impact, exposure = c["likelihood"], c["impact"], c["exposure"]

    business_impact = c.get("business_impact") or c.get("explanation") or ""
    trigger = c.get("trigger_scenario") or ""

    trigger_html = ""
    if trigger:
        trigger_html = (f'<div class="risk-trigger"><b>What triggers it:</b> '
                        f'{_text_to_html(str(trigger))}</div>')

    meters = (_meter("Likelihood", likelihood, _LIKELIHOOD_TICKS[likelihood - 1], color)
              + _meter("Impact", impact, _IMPACT_TICKS[impact - 1], color))

    return (
        f'<div class="risk-why" style="--sev:{color};">'
        '<div class="risk-why-head"><span class="risk-why-title">Why this is a risk</span>'
        f'<span class="risk-why-score">Exposure <b>{exposure}</b>'
        '<span class="risk-meter-max">/25</span></span></div>'
        f'<div class="risk-why-body">{_text_to_html(str(business_impact))}</div>'
        f'{trigger_html}'
        f'<div class="risk-meters">{meters}</div></div>'
    )


# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------
def _label(clause: dict, limit: int = 42) -> str:
    text = str(clause.get("risk_type") or "Risk")
    return text if len(text) <= limit else text[: limit - 1] + "…"


def risk_driver_chart(clauses: list[dict]) -> go.Figure:
    """What is pushing the score up — one bar per clause, ranked by exposure."""
    items = sorted(normalize_clauses(clauses), key=lambda c: c["exposure"])
    if not items:
        return _empty("No risky clauses identified")

    fig = go.Figure(go.Bar(
        x=[c["exposure"] for c in items],
        y=[_label(c) for c in items],
        orientation="h",
        marker=dict(color=[severity_color(c["severity"]) for c in items],
                    line=dict(width=0)),
        width=0.46,
        text=[c["severity"] for c in items],
        textposition="outside",
        textfont=dict(size=11, color=theme.SLATE),
        customdata=[[c["severity"], c["likelihood"], c["impact"]] for c in items],
        hovertemplate=("<b>%{y}</b><br>Severity: %{customdata[0]}"
                       "<br>Likelihood: %{customdata[1]}/5 · Impact: %{customdata[2]}/5"
                       "<br>Exposure: %{x}/25<extra></extra>"),
    ))
    top = max(c["exposure"] for c in items)
    fig.update_xaxes(title="Exposure  (likelihood × impact)", range=[0, top * 1.22])
    fig.update_yaxes(title=None, ticksuffix="  ")
    fig = theme.style_fig(fig, "What's driving the risk score",
                          height=max(240, 58 * len(items) + 90))
    fig.update_layout(bargap=0.32, showlegend=False)
    return fig


def risk_matrix_chart(clauses: list[dict]) -> go.Figure:
    """Likelihood × impact matrix. Background is a single-hue exposure ramp;
    clauses are plotted as severity-shaped, severity-coloured, direct-labelled marks."""
    items = normalize_clauses(clauses)
    if not items:
        return _empty("No risky clauses identified")

    axis = [1, 2, 3, 4, 5]
    fig = go.Figure()

    # Sequential single-hue backdrop: more exposure = darker. Recessive on purpose.
    fig.add_trace(go.Heatmap(
        x=axis, y=axis,
        z=[[likelihood * impact for likelihood in axis] for impact in axis],
        colorscale=[[0.0, "#FFFFFF"], [0.35, "#FEE2E2"], [0.7, "#FCA5A5"], [1.0, "#EF4444"]],
        opacity=0.42, showscale=True, hoverinfo="skip", xgap=2, ygap=2,
        colorbar=dict(title=dict(text="Exposure", side="right"), thickness=10,
                      len=0.72, outlinewidth=0, tickfont=dict(size=10)),
    ))

    # One trace per severity present -> legend entries, in severity order.
    for severity in SEVERITY_ORDER:
        group = [c for c in items if c["severity"] == severity]
        if not group:
            continue
        fig.add_trace(go.Scatter(
            x=[c["likelihood"] for c in group],
            y=[c["impact"] for c in group],
            mode="markers+text",
            name=severity,
            marker=dict(size=15, symbol=_SEVERITY_SYMBOL[severity],
                        color=severity_color(severity),
                        line=dict(color="#FFFFFF", width=2)),
            text=[_label(c, 26) for c in group],
            textposition="top center",
            textfont=dict(size=10, color=theme.SLATE),
            customdata=[[c["severity"], c["exposure"]] for c in group],
            hovertemplate=("<b>%{text}</b><br>Severity: %{customdata[0]}"
                           "<br>Likelihood: %{x}/5 · Impact: %{y}/5"
                           "<br>Exposure: %{customdata[1]}/25<extra></extra>"),
        ))

    fig.update_xaxes(title="Likelihood →", tickvals=axis, ticktext=_LIKELIHOOD_TICKS,
                     range=[0.5, 5.5], tickfont=dict(size=10), showgrid=False)
    fig.update_yaxes(title="Impact →", tickvals=axis, ticktext=_IMPACT_TICKS,
                     range=[0.5, 5.7], tickfont=dict(size=10), showgrid=False)
    fig = theme.style_fig(fig, "Risk matrix — likelihood vs impact", height=430)
    fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.0,
                                  xanchor="right", x=1, title=None))
    return fig


def _empty(message: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(text=message, xref="paper", yref="paper", x=0.5, y=0.5,
                       showarrow=False, font=dict(size=14, color=theme.MUTED))
    fig.update_layout(xaxis=dict(visible=False), yaxis=dict(visible=False))
    return theme.style_fig(fig, None, height=260)


# ---------------------------------------------------------------------------
# CSS for the highlight + why panel
# ---------------------------------------------------------------------------
RISK_CSS = """
<style>
.risk-excerpt { background:#FFFFFF; border:1px solid #E2E8F0; border-radius:12px;
  padding:.85rem 1rem; margin:.5rem 0 .75rem; }
.risk-excerpt-head { font-size:.78rem; font-weight:700; color:#475569;
  text-transform:uppercase; letter-spacing:.04em; margin-bottom:.5rem;
  display:flex; align-items:center; justify-content:space-between; gap:.5rem; }
.risk-excerpt-meta { font-weight:600; text-transform:none; letter-spacing:0;
  color:#94A3B8; font-size:.74rem; }
.risk-excerpt-body { font-family:'Inter',sans-serif; font-size:.86rem; line-height:1.65;
  color:#475569; white-space:pre-wrap; max-height:260px; overflow-y:auto; }
.risk-mark { background:color-mix(in srgb, var(--mark) 16%, transparent);
  border-bottom:2px solid var(--mark); color:#0F172A; font-weight:600;
  padding:1px 2px; border-radius:3px; }

.risk-why { background:#FFFFFF; border:1px solid #E2E8F0; border-left:4px solid var(--sev);
  border-radius:12px; padding:.9rem 1.05rem; margin:.5rem 0 .75rem; }
.risk-why-head { display:flex; align-items:center; justify-content:space-between;
  gap:.75rem; margin-bottom:.4rem; }
.risk-why-title { font-family:'Plus Jakarta Sans',sans-serif; font-weight:700;
  font-size:.98rem; color:#0F172A; }
.risk-why-score { font-size:.8rem; font-weight:600; color:#475569; white-space:nowrap; }
.risk-why-body { font-size:.88rem; line-height:1.6; color:#475569; }
.risk-trigger { font-size:.84rem; line-height:1.55; color:#475569; margin-top:.5rem;
  background:#F8FAFC; border:1px solid #EDF1F6; border-radius:8px; padding:.5rem .65rem; }
.risk-meters { display:grid; grid-template-columns:1fr 1fr; gap:.9rem; margin-top:.85rem; }
.risk-meter-top { display:flex; align-items:baseline; justify-content:space-between; }
.risk-meter-label { font-size:.74rem; font-weight:700; text-transform:uppercase;
  letter-spacing:.04em; color:#94A3B8; }
.risk-meter-val { font-family:'Plus Jakarta Sans',sans-serif; font-weight:800;
  font-size:1.05rem; color:#0F172A; }
.risk-meter-max { font-size:.72rem; font-weight:600; color:#94A3B8; }
.risk-meter-track { height:7px; border-radius:999px; background:#EDF1F6; margin-top:.3rem;
  overflow:hidden; }
.risk-meter-fill { height:100%; border-radius:999px; }
.risk-meter-cap { font-size:.74rem; color:#94A3B8; margin-top:.28rem; }
@media (max-width: 640px) { .risk-meters { grid-template-columns:1fr; } }
</style>
"""

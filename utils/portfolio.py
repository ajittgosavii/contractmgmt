"""Portfolio-level risk: roll every contract's risk analysis into one view.

Per-contract analysis answers "is this contract risky?". This module answers the
question a GC or CFO actually asks: "where is the risk concentrated across
everything we've signed?"
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from utils import theme
from utils.risk_viz import SEVERITY_ORDER, normalize_clauses, severity_color

# Free-text risk_type values from the LLM get folded into these buckets so the
# heatmap has stable columns instead of one column per phrasing.
_CANONICAL_RISKS = {
    "Liability": ("liabilit", "indemnif", "damages", "hold harmless"),
    "Termination": ("terminat", "exit", "cancel"),
    "Auto-Renewal": ("renew", "evergreen", "rollover"),
    "IP & Ownership": ("intellectual", " ip ", "ownership", "work product", "licence", "license"),
    "Payment": ("payment", "fee", "invoice", "price", "late charge"),
    "Data & Privacy": ("data", "privacy", "gdpr", "ccpa", "personal information"),
    "Confidentiality": ("confidential", "nda", "non-disclosure", "trade secret"),
    "Compliance": ("complian", "regulat", "sanction", "anti-bribery", "sox"),
    "Dispute & Jurisdiction": ("dispute", "arbitrat", "jurisdiction", "governing law", "venue"),
    "Service Levels": ("sla", "service level", "uptime", "performance credit"),
}


def canonical_risk_type(risk_type: str) -> str:
    """Map a free-text risk type onto a stable bucket."""
    probe = f" {str(risk_type).lower()} "
    for bucket, needles in _CANONICAL_RISKS.items():
        if any(n in probe for n in needles):
            return bucket
    return "Other"


def build_exposure_frame(contracts: pd.DataFrame, analyses: dict[str, dict]) -> pd.DataFrame:
    """One row per (contract, risk bucket) with the summed exposure."""
    rows: list[dict] = []
    if contracts is None or contracts.empty:
        return pd.DataFrame(columns=["contract", "risk_type", "exposure", "severity", "count"])

    names = dict(zip(contracts["id"], contracts["filename"]))
    for contract_id, analysis in analyses.items():
        name = names.get(contract_id)
        if not name:
            continue  # analysis for a deleted contract
        for clause in normalize_clauses(analysis.get("risky_clauses", [])):
            rows.append({
                "contract": name,
                "risk_type": canonical_risk_type(clause.get("risk_type", "")),
                "exposure": clause["exposure"],
                "severity": clause["severity"],
                "count": 1,
            })

    if not rows:
        return pd.DataFrame(columns=["contract", "risk_type", "exposure", "severity", "count"])

    df = pd.DataFrame(rows)
    agg = (df.groupby(["contract", "risk_type"], as_index=False)
             .agg(exposure=("exposure", "sum"), count=("count", "sum")))
    # Worst severity in each cell, for the tooltip.
    rank = {s: i for i, s in enumerate(SEVERITY_ORDER)}
    worst = (df.assign(_r=df["severity"].map(rank))
               .sort_values("_r")
               .groupby(["contract", "risk_type"], as_index=False)
               .first()[["contract", "risk_type", "severity"]])
    return agg.merge(worst, on=["contract", "risk_type"], how="left")


def live_analyses(contracts: pd.DataFrame, analyses: dict[str, dict]) -> dict[str, dict]:
    """Drop analyses whose contract has since been deleted.

    Without this, a removed contract keeps inflating the KPIs and the average
    score even though it no longer appears anywhere in the portfolio view.
    """
    if contracts is None or contracts.empty:
        return {}
    known = set(contracts["id"])
    return {cid: a for cid, a in analyses.items() if cid in known}


def portfolio_stats(contracts: pd.DataFrame, analyses: dict[str, dict]) -> dict:
    analyses = live_analyses(contracts, analyses)
    exposure = build_exposure_frame(contracts, analyses)
    clauses = [c for a in analyses.values() for c in normalize_clauses(a.get("risky_clauses", []))]
    severities = [c["severity"] for c in clauses]

    total = 0 if contracts is None or contracts.empty else len(contracts)
    analysed = len(analyses)

    scores = [a.get("overall_risk_score") for a in analyses.values()
              if isinstance(a.get("overall_risk_score"), (int, float))]

    top_type, top_exposure = "—", 0
    if not exposure.empty:
        by_type = exposure.groupby("risk_type")["exposure"].sum().sort_values(ascending=False)
        top_type, top_exposure = by_type.index[0], int(by_type.iloc[0])

    return {
        "contracts_total": total,
        "contracts_analysed": analysed,
        "coverage_pct": round(analysed / total * 100) if total else 0,
        "critical": severities.count("Critical"),
        "high": severities.count("High"),
        "clauses_total": len(clauses),
        "avg_score": round(sum(scores) / len(scores)) if scores else 0,
        "top_risk_type": top_type,
        "top_risk_exposure": top_exposure,
    }


def _empty(message: str, height: int = 300) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(text=message, xref="paper", yref="paper", x=0.5, y=0.5,
                       showarrow=False, font=dict(size=14, color=theme.MUTED))
    fig.update_layout(xaxis=dict(visible=False), yaxis=dict(visible=False))
    return theme.style_fig(fig, None, height=height)


def exposure_heatmap(exposure: pd.DataFrame, max_contracts: int = 18) -> go.Figure:
    """Contract × risk-type grid. Magnitude on a grid → one hue, more-is-darker."""
    if exposure.empty:
        return _empty("No analysed contracts yet — run Risk Analysis on a contract first.")

    order = (exposure.groupby("contract")["exposure"].sum()
             .sort_values(ascending=False).index.tolist())
    hidden = max(0, len(order) - max_contracts)
    order = order[:max_contracts]
    frame = exposure[exposure["contract"].isin(order)]

    grid = frame.pivot_table(index="contract", columns="risk_type", values="exposure",
                             aggfunc="sum", fill_value=0).reindex(order[::-1])
    counts = frame.pivot_table(index="contract", columns="risk_type", values="count",
                               aggfunc="sum", fill_value=0).reindex(order[::-1])
    sev = frame.pivot_table(index="contract", columns="risk_type", values="severity",
                            aggfunc="first").reindex(order[::-1]).fillna("—")

    customdata = [[[counts.iloc[r, c], sev.iloc[r, c]] for c in range(grid.shape[1])]
                  for r in range(grid.shape[0])]

    fig = go.Figure(go.Heatmap(
        z=grid.values, x=grid.columns.tolist(), y=[_short(n) for n in grid.index],
        customdata=customdata,
        colorscale=[[0.0, "#FFFFFF"], [0.25, "#E1F0FA"], [0.55, "#7FBDE3"], [1.0, theme.COBALT_DEEP]],
        xgap=2, ygap=2,
        colorbar=dict(title=dict(text="Exposure", side="right"), thickness=10,
                      len=0.8, outlinewidth=0, tickfont=dict(size=10)),
        hovertemplate=("<b>%{y}</b><br>%{x}<br>Exposure: %{z}"
                       "<br>Clauses: %{customdata[0]} · Worst: %{customdata[1]}<extra></extra>"),
    ))
    title = "Risk concentration — contract × risk type"
    if hidden:
        title += f"  (top {max_contracts} of {max_contracts + hidden})"
    fig = theme.style_fig(fig, title, height=max(320, 30 * len(grid.index) + 190))
    fig.update_xaxes(side="bottom", tickangle=-30, tickfont=dict(size=10), showgrid=False)
    fig.update_yaxes(tickfont=dict(size=10), showgrid=False)
    return fig


def top_exposures_chart(exposure: pd.DataFrame, limit: int = 8) -> go.Figure:
    """Which risk categories carry the most exposure across the whole portfolio."""
    if exposure.empty:
        return _empty("Nothing to rank yet.")
    by_type = (exposure.groupby("risk_type")["exposure"].sum()
               .sort_values(ascending=False).head(limit).sort_values())

    fig = go.Figure(go.Bar(
        x=by_type.values, y=by_type.index.tolist(), orientation="h",
        marker=dict(color=theme.COBALT, line=dict(width=0)), width=0.46,
        hovertemplate="<b>%{y}</b><br>Total exposure: %{x}<extra></extra>",
    ))
    fig.update_xaxes(title="Total exposure across portfolio",
                     range=[0, by_type.max() * 1.12])
    fig.update_yaxes(title=None, ticksuffix="  ")
    fig = theme.style_fig(fig, "Where the risk is concentrated",
                          height=max(260, 44 * len(by_type) + 110))
    fig.update_layout(bargap=0.34, showlegend=False)
    return fig


def severity_mix_chart(analyses: dict[str, dict]) -> go.Figure:
    """Severity is a status scale — stacked bar with labels, never colour alone.

    Callers pass already-filtered analyses (see live_analyses).
    """
    clauses = [c for a in analyses.values() for c in normalize_clauses(a.get("risky_clauses", []))]
    if not clauses:
        return _empty("No risky clauses found yet.")
    counts = {s: sum(1 for c in clauses if c["severity"] == s) for s in SEVERITY_ORDER}

    fig = go.Figure()
    for severity in SEVERITY_ORDER:
        value = counts[severity]
        if not value:
            continue
        fig.add_trace(go.Bar(
            x=[value], y=["All contracts"], orientation="h", name=severity,
            marker=dict(color=severity_color(severity), line=dict(color="#FFFFFF", width=2)),
            text=[f"{severity} · {value}"], textposition="inside",
            insidetextanchor="middle", textfont=dict(size=11, color="#FFFFFF"),
            hovertemplate=f"<b>{severity}</b>: {value} clause(s)<extra></extra>",
        ))
    fig = theme.style_fig(fig, "Severity mix across the portfolio", height=190)
    fig.update_layout(barmode="stack", bargap=0.5,
                      legend=dict(orientation="h", yanchor="bottom", y=1.0, x=0, title=None))
    fig.update_xaxes(title="Risky clauses", showgrid=False)
    fig.update_yaxes(visible=False)
    return fig


def _short(name: str, limit: int = 34) -> str:
    return name if len(name) <= limit else name[: limit - 1] + "…"

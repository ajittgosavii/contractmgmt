"""
Enterprise design system for Infosys Cobalt AI CLM.

Centralizes the visual language: color tokens, typography, and reusable
HTML/CSS components (KPI cards, page hero, section titles, pills, empty
states) plus a shared Plotly theme so every chart looks consistent.

Usage:
    from utils import theme
    theme.inject()                       # once, right after set_page_config
    st.markdown(theme.page_hero(...), unsafe_allow_html=True)
    st.markdown(theme.kpi_row([...]), unsafe_allow_html=True)
    fig = theme.style_fig(fig, "Title")
"""

from __future__ import annotations

import html

import plotly.graph_objects as go

# ---------------------------------------------------------------------------
# Design tokens
# ---------------------------------------------------------------------------
COBALT = "#007CC3"
COBALT_DARK = "#005A9C"
COBALT_DEEP = "#0B2E63"
VIOLET = "#5B2D8E"
CYAN = "#00AEEF"

INK = "#0F172A"          # primary text
SLATE = "#475569"        # secondary text
MUTED = "#94A3B8"        # tertiary / captions
LINE = "#E2E8F0"         # borders
SURFACE = "#FFFFFF"
CANVAS = "#F5F7FB"       # app background
SOFT = "#F8FAFC"

SUCCESS = "#16A34A"
WARNING = "#D97706"
DANGER = "#DC2626"
INFO = "#0EA5E9"

# Categorical palette for charts (cobalt-anchored, colorblind-considerate)
CHART_COLORWAY = ["#007CC3", "#5B2D8E", "#00AEEF", "#0EA5E9",
                  "#14B8A6", "#F59E0B", "#EF4444", "#8B5CF6"]

RISK_COLORS = {
    "critical": DANGER,
    "high": "#EA580C",
    "medium": WARNING,
    "low": SUCCESS,
}

STATUS_COLORS = {
    "Draft": MUTED,
    "Under Review": WARNING,
    "Active": SUCCESS,
    "Expired": DANGER,
    "Terminated": VIOLET,
    "Open": INFO,
    "In Progress": WARNING,
    "Completed": SUCCESS,
}


# ---------------------------------------------------------------------------
# Global CSS
# ---------------------------------------------------------------------------
def inject() -> None:
    import streamlit as st

    st.markdown(_CSS, unsafe_allow_html=True)


_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@600;700;800&display=swap');

:root {{
  --cobalt: {COBALT}; --cobalt-dark: {COBALT_DARK}; --violet: {VIOLET};
  --ink: {INK}; --slate: {SLATE}; --muted: {MUTED}; --line: {LINE};
  --surface: {SURFACE}; --canvas: {CANVAS}; --soft: {SOFT};
  --success: {SUCCESS}; --warning: {WARNING}; --danger: {DANGER};
  --radius: 14px; --shadow: 0 1px 2px rgba(15,23,42,.04), 0 6px 20px rgba(15,23,42,.06);
}}

html, body, [class*="css"], .stMarkdown, p, span, div, label, input, textarea, button, select {{
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}}
h1, h2, h3, .hero-title, .kpi-value {{
  font-family: 'Plus Jakarta Sans', 'Inter', sans-serif;
  letter-spacing: -0.01em;
}}

/* App canvas */
.stApp {{ background: var(--canvas); }}
.main .block-container {{ padding-top: 1.4rem; padding-bottom: 3rem; max-width: 1400px; }}
[data-testid="stHeader"] {{ background: transparent; }}

/* ---- Page headers (used app-wide) ---- */
.main-header {{
  font-family:'Plus Jakarta Sans', sans-serif; font-size:1.85rem; font-weight:800;
  color:var(--ink); line-height:1.15; display:flex; align-items:center; gap:.5rem; margin-bottom:.15rem;
}}
.sub-header {{ font-size:.95rem; color:var(--slate); margin:0 0 1.1rem; }}

/* ---- Page hero ---- */
.page-hero {{
  background: linear-gradient(120deg, #ffffff 0%, #f2f7fd 100%);
  border: 1px solid var(--line); border-left: 5px solid var(--cobalt);
  border-radius: var(--radius); padding: 1.15rem 1.4rem; margin-bottom: 1.25rem;
  box-shadow: var(--shadow);
}}
.hero-row {{ display: flex; align-items: center; gap: .85rem; }}
.hero-ico {{
  width: 46px; height: 46px; border-radius: 12px; flex: 0 0 46px;
  display: flex; align-items: center; justify-content: center; font-size: 1.5rem;
  background: linear-gradient(135deg, #e8f2fc 0%, #efe8fb 100%); border: 1px solid var(--line);
}}
.hero-title {{ font-size: 1.6rem; font-weight: 800; color: var(--ink); line-height: 1.1; margin: 0; }}
.hero-sub {{ font-size: .92rem; color: var(--slate); margin-top: .15rem; }}

/* ---- KPI cards ---- */
.kpi-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: .9rem; margin-bottom: .4rem; }}
.kpi-card {{
  background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius);
  padding: 1rem 1.1rem; box-shadow: var(--shadow); position: relative; overflow: hidden;
  transition: transform .12s ease, box-shadow .12s ease;
}}
.kpi-card:hover {{ transform: translateY(-2px); box-shadow: 0 10px 28px rgba(15,23,42,.10); }}
.kpi-card::before {{ content:""; position:absolute; top:0; left:0; width:100%; height:3px; background: var(--accent, var(--cobalt)); opacity:.9; }}
.kpi-top {{ display: flex; align-items: center; justify-content: space-between; }}
.kpi-ico {{ font-size: 1.15rem; width: 34px; height: 34px; border-radius: 9px; display:flex; align-items:center; justify-content:center;
  background: var(--accent-soft, #e8f2fc); }}
.kpi-label {{ font-size: .74rem; font-weight: 600; text-transform: uppercase; letter-spacing: .04em; color: var(--muted); }}
.kpi-value {{ font-size: 2rem; font-weight: 800; color: var(--ink); line-height: 1.05; margin-top: .35rem; }}
.kpi-trend {{ font-size: .74rem; font-weight: 600; padding: 2px 8px; border-radius: 999px; }}
.trend-up {{ color: var(--success); background: #dcfce7; }}
.trend-down {{ color: var(--danger); background: #fee2e2; }}
.trend-flat {{ color: var(--slate); background: #eef2f7; }}
.kpi-foot {{ font-size: .76rem; color: var(--slate); margin-top: .5rem; }}

/* ---- Generic card / section ---- */
.eo-card {{ background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius); padding: 1.2rem 1.3rem; box-shadow: var(--shadow); margin-bottom: 1rem; }}
.section-title {{ display:flex; align-items:center; gap:.55rem; font-family:'Plus Jakarta Sans',sans-serif; font-weight:700; font-size:1.15rem; color:var(--ink); margin: 1.1rem 0 .6rem; }}
.section-title::before {{ content:""; width:4px; height:20px; border-radius:3px; background: linear-gradient(180deg,var(--cobalt),var(--violet)); }}

/* ---- Pills ---- */
.pill {{ display:inline-block; padding:3px 11px; border-radius:999px; font-size:.75rem; font-weight:600; border:1px solid transparent; }}
.pill-soft {{ background:#eef2f7; color:var(--slate); }}

/* ---- Agent card ---- */
.agent-card {{
  background: linear-gradient(135deg,#EFF6FF 0%, #F5EEFC 100%);
  border:1px solid var(--line); border-left:4px solid var(--cobalt);
  border-radius:12px; padding:1rem 1.15rem; margin-bottom:1rem;
}}
.agent-name {{ font-size:1.02rem; font-weight:700; color:var(--cobalt-dark); }}
.agent-desc {{ font-size:.85rem; color:var(--slate); margin-top:.25rem; line-height:1.45; }}

/* ---- Empty state ---- */
.empty-state {{ text-align:center; padding:2.4rem 1rem; background:var(--surface); border:1px dashed var(--line); border-radius:var(--radius); }}
.empty-ico {{ font-size:2.4rem; }}
.empty-title {{ font-weight:700; color:var(--ink); margin-top:.5rem; font-size:1.05rem; }}
.empty-msg {{ color:var(--slate); font-size:.9rem; margin-top:.25rem; }}

/* ---- Buttons ---- */
.stButton > button {{ border-radius: 10px; font-weight: 600; }}
div[data-testid="stForm"] button[kind="primaryFormSubmit"],
button[kind="primary"] {{
  background: linear-gradient(135deg, var(--cobalt) 0%, var(--cobalt-dark) 100%) !important;
  border: none !important; box-shadow: 0 2px 8px rgba(0,124,195,.28) !important;
}}
button[kind="primary"]:hover {{ filter: brightness(1.05); }}

/* ---- Sidebar ---- */
[data-testid="stSidebar"] {{ background: linear-gradient(180deg,#ffffff 0%, #f3f7fc 100%); border-right:1px solid var(--line); }}
[data-testid="stSidebar"] .block-container {{ padding-top: 1rem; }}
.nav-section {{ font-size:.68rem; font-weight:700; color:var(--muted); text-transform:uppercase; letter-spacing:.07em; margin:1rem .2rem .35rem; }}
div[data-testid="stSidebar"] .stButton > button {{
  text-align:left; justify-content:flex-start; font-size:.88rem; font-weight:500;
  padding:.45rem .7rem; border:none; background:transparent; color:var(--ink); border-radius:9px;
}}
div[data-testid="stSidebar"] .stButton > button:hover {{ background:#e8f2fc; color:var(--cobalt-dark); }}
div[data-testid="stSidebar"] .stButton > button[kind="primary"] {{
  background: linear-gradient(135deg,#e8f2fc,#eee7fb) !important; color:var(--cobalt-dark) !important;
  box-shadow:none !important; border-left:3px solid var(--cobalt) !important; font-weight:700;
}}

/* ---- Tabs ---- */
.stTabs [data-baseweb="tab-list"] {{ gap:6px; border-bottom:1px solid var(--line); }}
.stTabs [data-baseweb="tab"] {{ padding:8px 18px; border-radius:9px 9px 0 0; font-weight:600; font-size:.9rem; }}
.stTabs [aria-selected="true"] {{ background:#e8f2fc; color:var(--cobalt-dark); }}

/* ---- Misc ---- */
.stDataFrame {{ border:1px solid var(--line); border-radius:12px; overflow:hidden; }}
[data-testid="stMetricValue"] {{ font-family:'Plus Jakarta Sans',sans-serif; }}
.role-badge {{ display:inline-block; padding:2px 9px; border-radius:6px; font-size:.7rem; font-weight:700; }}
.role-admin {{ background:var(--danger); color:#fff; }}
.role-analyst {{ background:var(--cobalt); color:#fff; }}
.role-viewer {{ background:var(--muted); color:#fff; }}
.ocr-badge {{ background:#FEF3C7; color:#92400E; padding:2px 9px; border-radius:6px; font-size:.72rem; font-weight:700; border:1px solid #FDE68A; }}
.cobalt-footer {{ text-align:center; font-size:.72rem; color:var(--muted); margin-top:1.2rem; line-height:1.5; }}
.app-tag {{ font-size:.7rem; color:var(--muted); }}
</style>
"""


# ---------------------------------------------------------------------------
# Component builders (return HTML strings)
# ---------------------------------------------------------------------------
def _compact(markup: str) -> str:
    """Collapse indentation so Streamlit's Markdown doesn't treat the HTML as a
    code block (any line indented 4+ spaces would render as literal text)."""
    return "".join(line.strip() for line in markup.strip().splitlines())


def page_hero(title: str, subtitle: str = "", icon: str = "📄") -> str:
    return _compact(f"""
    <div class="page-hero"><div class="hero-row">
      <div class="hero-ico">{icon}</div>
      <div>
        <div class="hero-title">{html.escape(title)}</div>
        {f'<div class="hero-sub">{html.escape(subtitle)}</div>' if subtitle else ''}
      </div>
    </div></div>
    """)


_TONES = {
    "cobalt": ("#007CC3", "#e8f2fc"),
    "violet": ("#5B2D8E", "#efe6fb"),
    "success": (SUCCESS, "#dcfce7"),
    "warning": (WARNING, "#fef3c7"),
    "danger": (DANGER, "#fee2e2"),
    "info": (INFO, "#e0f2fe"),
}


def kpi_card(label: str, value, icon: str = "📊", tone: str = "cobalt",
             trend: str | None = None, trend_dir: str = "flat", foot: str = "") -> str:
    accent, soft = _TONES.get(tone, _TONES["cobalt"])
    trend_html = ""
    if trend:
        cls = {"up": "trend-up", "down": "trend-down"}.get(trend_dir, "trend-flat")
        arrow = {"up": "▲", "down": "▼"}.get(trend_dir, "•")
        trend_html = f'<span class="kpi-trend {cls}">{arrow} {html.escape(str(trend))}</span>'
    foot_html = f'<div class="kpi-foot">{html.escape(foot)}</div>' if foot else ""
    return _compact(f"""
    <div class="kpi-card" style="--accent:{accent}; --accent-soft:{soft};">
      <div class="kpi-top">
        <span class="kpi-ico" style="background:{soft};">{icon}</span>
        {trend_html}
      </div>
      <div class="kpi-label">{html.escape(label)}</div>
      <div class="kpi-value">{html.escape(str(value))}</div>
      {foot_html}
    </div>
    """)


def kpi_row(cards: list[str]) -> str:
    return _compact(f'<div class="kpi-grid">{"".join(cards)}</div>')


def section_title(text: str, icon: str = "") -> str:
    return f'<div class="section-title">{icon + " " if icon else ""}{html.escape(text)}</div>'


def status_pill(status: str) -> str:
    color = STATUS_COLORS.get(status, MUTED)
    return f'<span class="pill" style="background:{color}1a; color:{color}; border-color:{color}40;">{html.escape(str(status))}</span>'


def risk_pill(level: str) -> str:
    color = RISK_COLORS.get(str(level).lower(), MUTED)
    return f'<span class="pill" style="background:{color}1a; color:{color}; border-color:{color}40;">{html.escape(str(level))}</span>'


def empty_state(title: str, message: str = "", icon: str = "📭") -> str:
    return _compact(f"""
    <div class="empty-state">
      <div class="empty-ico">{icon}</div>
      <div class="empty-title">{html.escape(title)}</div>
      {f'<div class="empty-msg">{html.escape(message)}</div>' if message else ''}
    </div>
    """)


# ---------------------------------------------------------------------------
# Plotly enterprise theme
# ---------------------------------------------------------------------------
def style_fig(fig: go.Figure, title: str | None = None, height: int | None = None) -> go.Figure:
    """Apply the shared enterprise chart styling to a Plotly figure."""
    fig.update_layout(
        colorway=CHART_COLORWAY,
        font=dict(family="Inter, sans-serif", color=INK, size=13),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=54 if title else 24, b=28, l=28, r=24),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=12)),
        hoverlabel=dict(font=dict(family="Inter, sans-serif", size=12), bgcolor="white"),
    )
    if title:
        fig.update_layout(title=dict(
            text=title, x=0.01, xanchor="left",
            font=dict(family="Plus Jakarta Sans, sans-serif", size=16, color=INK),
        ))
    if height:
        fig.update_layout(height=height)
    fig.update_xaxes(gridcolor="#EDF1F6", zerolinecolor="#E2E8F0", linecolor="#E2E8F0")
    fig.update_yaxes(gridcolor="#EDF1F6", zerolinecolor="#E2E8F0", linecolor="#E2E8F0")
    return fig

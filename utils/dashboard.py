"""Plotly dashboard chart helpers — styled with the enterprise theme."""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from utils import theme


def contracts_by_status_chart(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return _empty_chart("No contracts yet")
    counts = df["status"].value_counts()
    fig = go.Figure(go.Pie(
        labels=counts.index.tolist(),
        values=counts.values.tolist(),
        hole=0.62,
        marker=dict(colors=[theme.STATUS_COLORS.get(s, theme.MUTED) for s in counts.index],
                    line=dict(color="#ffffff", width=2)),
        textinfo="label+percent", textfont=dict(size=12),
    ))
    fig.add_annotation(text=f"<b>{int(counts.sum())}</b><br>total", showarrow=False,
                       font=dict(size=16, color=theme.INK), x=0.5, y=0.5)
    return theme.style_fig(fig, "Contracts by Status", height=350)


def risk_score_distribution_chart(df: pd.DataFrame) -> go.Figure:
    scored = df[df["risk_score"].notna() & (df["risk_score"] > 0)]
    if scored.empty:
        return _empty_chart("No risk scores yet")
    fig = px.histogram(scored, x="risk_score", nbins=10, color_discrete_sequence=[theme.COBALT])
    fig.update_traces(marker_line_color="#ffffff", marker_line_width=1)
    fig.update_layout(xaxis_title="Risk Score", yaxis_title="Contracts", bargap=0.08)
    return theme.style_fig(fig, "Risk Score Distribution", height=350)


def contracts_by_type_chart(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return _empty_chart("No contracts yet")
    counts = df["contract_type"].value_counts().sort_values()
    labels = [c.split(" (")[0] for c in counts.index.tolist()]
    fig = go.Figure(go.Bar(
        x=counts.values.tolist(), y=labels, orientation="h",
        marker=dict(color=theme.COBALT, line=dict(color="#fff", width=1)),
        text=counts.values.tolist(), textposition="outside",
    ))
    fig.update_layout(xaxis_title="Count", yaxis_title="")
    return theme.style_fig(fig, "Contracts by Type", height=350)


def risk_by_type_chart(df: pd.DataFrame) -> go.Figure:
    """Average risk score per contract type — surfaces where exposure concentrates."""
    scored = df[df["risk_score"].notna() & (df["risk_score"] > 0)]
    if scored.empty:
        return _empty_chart("No risk scores yet")
    grp = scored.groupby("contract_type")["risk_score"].mean().sort_values()
    labels = [c.split(" (")[0] for c in grp.index.tolist()]

    def _c(v):
        if v >= 80: return theme.RISK_COLORS["critical"]
        if v >= 60: return theme.RISK_COLORS["high"]
        if v >= 40: return theme.RISK_COLORS["medium"]
        return theme.RISK_COLORS["low"]

    fig = go.Figure(go.Bar(
        x=grp.values.round(1).tolist(), y=labels, orientation="h",
        marker=dict(color=[_c(v) for v in grp.values]),
        text=[f"{v:.0f}" for v in grp.values], textposition="outside",
    ))
    fig.update_layout(xaxis_title="Avg Risk Score", yaxis_title="", xaxis=dict(range=[0, 100]))
    return theme.style_fig(fig, "Average Risk by Contract Type", height=350)


def expiring_contracts_timeline(df: pd.DataFrame) -> go.Figure:
    active = df[(df["status"] == "Active") & (df["expiration_date"].notna()) & (df["expiration_date"] != "")]
    if active.empty:
        return _empty_chart("No active contracts with expiration dates")
    active = active.copy()
    active["expiration_date"] = pd.to_datetime(active["expiration_date"], errors="coerce")
    active = active.dropna(subset=["expiration_date"]).sort_values("expiration_date").head(15)
    fig = go.Figure(go.Bar(
        x=active["expiration_date"], y=active["filename"], orientation="h",
        marker=dict(color=theme.WARNING),
    ))
    fig.update_layout(margin=dict(l=160))
    return theme.style_fig(fig, "Upcoming Expirations", height=400)


def risk_gauge_chart(score: int) -> go.Figure:
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number=dict(font=dict(family="Plus Jakarta Sans, sans-serif", size=40, color=theme.INK)),
        gauge=dict(
            axis=dict(range=[0, 100], tickcolor=theme.MUTED),
            bar=dict(color=theme.COBALT, thickness=0.28),
            bgcolor="rgba(0,0,0,0)", borderwidth=0,
            steps=[
                dict(range=[0, 20], color="#D1FAE5"),
                dict(range=[20, 40], color="#FEF3C7"),
                dict(range=[40, 60], color="#FED7AA"),
                dict(range=[60, 80], color="#FECACA"),
                dict(range=[80, 100], color="#FCA5A5"),
            ],
            threshold=dict(line=dict(color=theme.DANGER, width=4), thickness=0.78, value=score),
        ),
    ))
    return theme.style_fig(fig, "Overall Risk Score", height=300)


def _empty_chart(message: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(text=message, xref="paper", yref="paper", x=0.5, y=0.5,
                       showarrow=False, font=dict(size=15, color=theme.MUTED))
    fig.update_layout(height=300, margin=dict(t=20, b=20, l=20, r=20),
                      xaxis=dict(visible=False), yaxis=dict(visible=False))
    return theme.style_fig(fig, None, height=300)

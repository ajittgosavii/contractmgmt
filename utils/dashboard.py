"""Plotly dashboard chart helpers."""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd


def contracts_by_status_chart(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return _empty_chart("No contracts yet")
    counts = df["status"].value_counts()
    colors = {"Draft": "#94A3B8", "Under Review": "#FBBF24", "Active": "#34D399", "Expired": "#F87171", "Terminated": "#A78BFA"}
    fig = go.Figure(go.Pie(
        labels=counts.index.tolist(),
        values=counts.values.tolist(),
        hole=0.5,
        marker=dict(colors=[colors.get(s, "#64748B") for s in counts.index]),
    ))
    fig.update_layout(title="Contracts by Status", height=350, margin=dict(t=40, b=20, l=20, r=20))
    return fig


def risk_score_distribution_chart(df: pd.DataFrame) -> go.Figure:
    scored = df[df["risk_score"].notna() & (df["risk_score"] > 0)]
    if scored.empty:
        return _empty_chart("No risk scores yet")
    fig = px.histogram(scored, x="risk_score", nbins=10, color_discrete_sequence=["#007CC3"])
    fig.update_layout(title="Risk Score Distribution", xaxis_title="Risk Score", yaxis_title="Count", height=350, margin=dict(t=40, b=20, l=20, r=20))
    return fig


def contracts_by_type_chart(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return _empty_chart("No contracts yet")
    counts = df["contract_type"].value_counts()
    fig = px.bar(x=counts.index.tolist(), y=counts.values.tolist(), color_discrete_sequence=["#007CC3"])
    fig.update_layout(title="Contracts by Type", xaxis_title="Type", yaxis_title="Count", height=350, margin=dict(t=40, b=20, l=20, r=20))
    return fig


def expiring_contracts_timeline(df: pd.DataFrame) -> go.Figure:
    active = df[(df["status"] == "Active") & (df["expiration_date"].notna()) & (df["expiration_date"] != "")]
    if active.empty:
        return _empty_chart("No active contracts with expiration dates")
    active = active.copy()
    active["expiration_date"] = pd.to_datetime(active["expiration_date"], errors="coerce")
    active = active.dropna(subset=["expiration_date"]).sort_values("expiration_date").head(15)
    fig = go.Figure(go.Bar(
        x=active["expiration_date"],
        y=active["filename"],
        orientation="h",
        marker_color="#F87171",
    ))
    fig.update_layout(title="Upcoming Expirations", height=400, margin=dict(t=40, b=20, l=150, r=20))
    return fig


def risk_gauge_chart(score: int) -> go.Figure:
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        gauge=dict(
            axis=dict(range=[0, 100]),
            bar=dict(color="#007CC3"),
            steps=[
                dict(range=[0, 20], color="#D1FAE5"),
                dict(range=[20, 40], color="#FEF3C7"),
                dict(range=[40, 60], color="#FED7AA"),
                dict(range=[60, 80], color="#FECACA"),
                dict(range=[80, 100], color="#FCA5A5"),
            ],
            threshold=dict(line=dict(color="red", width=4), thickness=0.75, value=score),
        ),
        title=dict(text="Overall Risk Score"),
    ))
    fig.update_layout(height=300, margin=dict(t=60, b=20, l=30, r=30))
    return fig


def _empty_chart(message: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(text=message, xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False, font=dict(size=16, color="#94A3B8"))
    fig.update_layout(height=300, margin=dict(t=20, b=20, l=20, r=20), xaxis=dict(visible=False), yaxis=dict(visible=False))
    return fig

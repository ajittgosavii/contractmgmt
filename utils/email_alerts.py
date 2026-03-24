"""Email alerts for expiring contracts and risk notifications."""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

import pandas as pd


# Email configuration — set via environment variables or Streamlit secrets
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
ALERT_FROM_EMAIL = os.getenv("ALERT_FROM_EMAIL", "")


def send_email(to_email: str, subject: str, html_body: str) -> bool:
    """Send an email alert. Returns True on success."""
    if not all([SMTP_USERNAME, SMTP_PASSWORD, ALERT_FROM_EMAIL]):
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = ALERT_FROM_EMAIL
    msg["To"] = to_email
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Email send failed: {e}")
        return False


def get_expiring_contracts(contracts_df: pd.DataFrame, days_ahead: int = 30) -> pd.DataFrame:
    """Get contracts expiring within the specified number of days."""
    if contracts_df.empty:
        return pd.DataFrame()

    df = contracts_df.copy()
    df = df[(df["status"] == "Active") & (df["expiration_date"].notna()) & (df["expiration_date"] != "")]
    if df.empty:
        return pd.DataFrame()

    df["expiration_date_parsed"] = pd.to_datetime(df["expiration_date"], errors="coerce")
    df = df.dropna(subset=["expiration_date_parsed"])

    cutoff = datetime.now() + timedelta(days=days_ahead)
    expiring = df[df["expiration_date_parsed"] <= cutoff].sort_values("expiration_date_parsed")
    return expiring


def build_expiry_alert_html(expiring_df: pd.DataFrame, days_ahead: int = 30) -> str:
    """Build HTML email body for expiring contract alerts."""
    rows = ""
    for _, row in expiring_df.iterrows():
        exp_date = row.get("expiration_date", "N/A")
        risk_color = "#DC2626" if row.get("risk_score", 0) and row["risk_score"] >= 60 else "#16A34A"
        rows += f"""
        <tr>
            <td style="padding: 8px; border-bottom: 1px solid #E2E8F0;">{row.get('filename', 'N/A')}</td>
            <td style="padding: 8px; border-bottom: 1px solid #E2E8F0;">{row.get('contract_type', 'N/A')}</td>
            <td style="padding: 8px; border-bottom: 1px solid #E2E8F0; font-weight: bold; color: #DC2626;">{exp_date}</td>
            <td style="padding: 8px; border-bottom: 1px solid #E2E8F0; color: {risk_color};">{row.get('risk_score', 'N/A')}</td>
        </tr>
        """

    return f"""
    <div style="font-family: Arial, sans-serif; max-width: 700px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #007CC3, #5B2D8E); padding: 20px; border-radius: 10px 10px 0 0;">
            <h2 style="color: white; margin: 0;">Infosys Cobalt - Contract Expiry Alert</h2>
            <p style="color: #E0E7FF; margin: 5px 0 0;">AI Contract Lifecycle Management</p>
        </div>
        <div style="background: #F8FAFC; padding: 20px; border: 1px solid #E2E8F0;">
            <p style="color: #1E293B; font-size: 14px;">
                The following <strong>{len(expiring_df)}</strong> contract(s) are expiring within the next <strong>{days_ahead} days</strong>:
            </p>
            <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
                <thead>
                    <tr style="background: #007CC3; color: white;">
                        <th style="padding: 10px; text-align: left;">Contract</th>
                        <th style="padding: 10px; text-align: left;">Type</th>
                        <th style="padding: 10px; text-align: left;">Expires</th>
                        <th style="padding: 10px; text-align: left;">Risk Score</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
            <p style="color: #64748B; font-size: 12px; margin-top: 20px;">
                Action required: Review these contracts and initiate renewal or termination as appropriate.
            </p>
        </div>
        <div style="background: #1E293B; padding: 10px 20px; border-radius: 0 0 10px 10px; text-align: center;">
            <p style="color: #94A3B8; font-size: 11px; margin: 0;">Infosys Cobalt Powered AI Contract Lifecycle Management</p>
        </div>
    </div>
    """


def build_risk_alert_html(contract_name: str, risk_score: int, risk_level: str, top_risks: list) -> str:
    """Build HTML email body for high-risk contract alerts."""
    risk_items = "".join(f"<li style='margin: 5px 0;'>{r}</li>" for r in top_risks[:5])
    score_color = "#DC2626" if risk_score >= 60 else "#D97706" if risk_score >= 40 else "#16A34A"

    return f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #DC2626, #991B1B); padding: 20px; border-radius: 10px 10px 0 0;">
            <h2 style="color: white; margin: 0;">High Risk Contract Alert</h2>
        </div>
        <div style="background: #FEF2F2; padding: 20px; border: 1px solid #FECACA;">
            <h3 style="color: #1E293B;">{contract_name}</h3>
            <p style="font-size: 32px; font-weight: bold; color: {score_color}; margin: 10px 0;">
                Risk Score: {risk_score}/100 ({risk_level})
            </p>
            <h4 style="color: #1E293B;">Top Risks:</h4>
            <ul style="color: #475569;">{risk_items}</ul>
            <p style="color: #64748B; font-size: 12px; margin-top: 15px;">
                Immediate review recommended. Log in to the Contract Management portal for full analysis.
            </p>
        </div>
        <div style="background: #1E293B; padding: 10px 20px; border-radius: 0 0 10px 10px; text-align: center;">
            <p style="color: #94A3B8; font-size: 11px; margin: 0;">Infosys Cobalt Powered AI Contract Lifecycle Management</p>
        </div>
    </div>
    """


def send_expiry_alerts(contracts_df: pd.DataFrame, recipient_email: str, days_ahead: int = 30) -> dict:
    """Check for expiring contracts and send alert email. Returns result dict."""
    expiring = get_expiring_contracts(contracts_df, days_ahead)
    if expiring.empty:
        return {"sent": False, "reason": "No contracts expiring soon", "count": 0}

    html = build_expiry_alert_html(expiring, days_ahead)
    subject = f"[Cobalt CLM] {len(expiring)} Contract(s) Expiring Within {days_ahead} Days"
    success = send_email(recipient_email, subject, html)
    return {"sent": success, "count": len(expiring), "contracts": expiring["filename"].tolist()}


def send_risk_alert(contract_name: str, risk_score: int, risk_level: str, top_risks: list, recipient_email: str) -> bool:
    """Send high-risk alert for a specific contract."""
    if risk_score < 60:
        return False
    html = build_risk_alert_html(contract_name, risk_score, risk_level, top_risks)
    subject = f"[Cobalt CLM] HIGH RISK: {contract_name} scored {risk_score}/100"
    return send_email(recipient_email, subject, html)

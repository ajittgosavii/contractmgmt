"""
Infosys Cobalt Powered AI Contract Lifecycle Management
Powered by OpenAI GPT-4o
"""

import json
import streamlit as st
import pandas as pd
from datetime import datetime, date

# ---------------------------------------------------------------------------
# Page config (must be first Streamlit call)
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Infosys Cobalt - AI Contract Lifecycle Management",
    page_icon="🔷",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------
from agents.agent_extractor import ContractExtractorAgent
from agents.agent_drafter import ContractDrafterAgent
from agents.agent_risk import ContractRiskAgent
from agents.agent_comparator import ContractComparatorAgent
from agents.agent_qa import ContractQAAgent, SUGGESTED_QUESTIONS
from utils import theme
from utils.file_parser import extract_text, save_uploaded_file
from utils.ocr import extract_text_with_ocr
from utils.config import CONTRACT_TYPES, CONTRACT_STATUSES, UPLOAD_DIR
from utils.contract_templates import get_template_parameters, list_templates
from utils.dashboard import (
    contracts_by_status_chart,
    risk_score_distribution_chart,
    contracts_by_type_chart,
    risk_by_type_chart,
    expiring_contracts_timeline,
    risk_gauge_chart,
)
from utils.export import (
    export_contract_pdf,
    export_contract_docx,
    export_risk_report_pdf,
    export_contracts_excel,
)
from utils.auth import setup_authentication, check_permission, get_user_role, render_user_management
from utils.audit import log_action, get_audit_log, get_user_activity_summary, get_contract_history
from utils.audit import (
    ACTION_UPLOAD, ACTION_EXTRACT, ACTION_SAVE, ACTION_DELETE, ACTION_GENERATE_DRAFT,
    ACTION_REFINE_DRAFT, ACTION_RISK_ANALYSIS, ACTION_COMPARE, ACTION_EXPORT,
    ACTION_BULK_UPLOAD, ACTION_EMAIL_ALERT, ACTION_LOGIN, ACTION_LOGOUT,
    ACTION_CLAUSE_SAVE, ACTION_CLAUSE_DELETE,
)
from utils.email_alerts import send_expiry_alerts, send_risk_alert, get_expiring_contracts
from utils.clause_library import (
    save_clause, load_clauses, search_clauses, delete_clause, increment_usage,
    get_popular_clauses, CLAUSE_CATEGORIES,
)
import utils.data_store as db

# ---------------------------------------------------------------------------
# Named AI Agents
# ---------------------------------------------------------------------------
AGENT_PROFILES = {
    "ClauseScout": {
        "class": ContractExtractorAgent,
        "icon": "🔍",
        "description": "Intelligent contract element extractor — scans documents to identify parties, dates, obligations, penalties, and all key terms.",
    },
    "DraftCraft": {
        "class": ContractDrafterAgent,
        "icon": "✍️",
        "description": "Expert contract drafter — generates legally sound, professionally structured contract documents from templates and custom requirements.",
    },
    "RiskRadar": {
        "class": ContractRiskAgent,
        "icon": "🛡️",
        "description": "Risk analysis specialist — evaluates contracts for risky clauses, compliance gaps, missing protections, and provides actionable recommendations.",
    },
    "DiffLens": {
        "class": ContractComparatorAgent,
        "icon": "⚖️",
        "description": "Contract comparison analyst — performs side-by-side analysis of two contracts, highlights differences, and identifies which terms are more favorable.",
    },
    "ContractCopilot": {
        "class": ContractQAAgent,
        "icon": "💬",
        "description": "Conversational contract assistant — answer plain-English questions grounded in a specific contract, with citations to the exact clause it relied on.",
    },
}

# ---------------------------------------------------------------------------
# Dynamic Animated Logo (SVG)
# ---------------------------------------------------------------------------
COBALT_LOGO_SVG = """
<svg width="220" height="60" viewBox="0 0 220 60" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="cobaltGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#007CC3;stop-opacity:1">
        <animate attributeName="stop-color" values="#007CC3;#00AEEF;#5B2D8E;#007CC3" dur="4s" repeatCount="indefinite"/>
      </stop>
      <stop offset="100%" style="stop-color:#5B2D8E;stop-opacity:1">
        <animate attributeName="stop-color" values="#5B2D8E;#007CC3;#00AEEF;#5B2D8E" dur="4s" repeatCount="indefinite"/>
      </stop>
    </linearGradient>
    <linearGradient id="nodeGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" style="stop-color:#00AEEF"/>
      <stop offset="100%" style="stop-color:#5B2D8E"/>
    </linearGradient>
  </defs>
  <circle cx="20" cy="30" r="6" fill="url(#nodeGrad)" opacity="0.9">
    <animate attributeName="r" values="5;7;5" dur="2s" repeatCount="indefinite"/>
  </circle>
  <circle cx="44" cy="16" r="4" fill="#00AEEF" opacity="0.7">
    <animate attributeName="cy" values="16;20;16" dur="3s" repeatCount="indefinite"/>
  </circle>
  <circle cx="44" cy="44" r="4" fill="#5B2D8E" opacity="0.7">
    <animate attributeName="cy" values="44;40;44" dur="3s" repeatCount="indefinite"/>
  </circle>
  <line x1="26" y1="28" x2="40" y2="18" stroke="#00AEEF" stroke-width="1.5" opacity="0.5">
    <animate attributeName="opacity" values="0.3;0.8;0.3" dur="2s" repeatCount="indefinite"/>
  </line>
  <line x1="26" y1="32" x2="40" y2="42" stroke="#5B2D8E" stroke-width="1.5" opacity="0.5">
    <animate attributeName="opacity" values="0.3;0.8;0.3" dur="2.5s" repeatCount="indefinite"/>
  </line>
  <line x1="44" y1="20" x2="44" y2="40" stroke="url(#cobaltGrad)" stroke-width="1" opacity="0.4">
    <animate attributeName="opacity" values="0.2;0.6;0.2" dur="3s" repeatCount="indefinite"/>
  </line>
  <text x="58" y="28" font-family="Arial, sans-serif" font-size="18" font-weight="700" fill="url(#cobaltGrad)">Infosys</text>
  <rect x="58" y="34" rx="3" ry="3" width="56" height="16" fill="url(#cobaltGrad)" opacity="0.9">
    <animate attributeName="opacity" values="0.85;1;0.85" dur="3s" repeatCount="indefinite"/>
  </rect>
  <text x="65" y="46" font-family="Arial, sans-serif" font-size="10" font-weight="600" fill="white">COBALT</text>
  <text x="122" y="28" font-family="Arial, sans-serif" font-size="11" font-weight="400" fill="#475569">AI Contract</text>
  <text x="122" y="46" font-family="Arial, sans-serif" font-size="11" font-weight="400" fill="#475569">Lifecycle Mgmt</text>
</svg>
"""

# ---------------------------------------------------------------------------
# CSS — Enterprise design system (utils/theme.py)
# ---------------------------------------------------------------------------
theme.inject()
st.markdown("""
<style>
    .risk-critical { color: #DC2626; font-weight: 700; }
    .risk-high { color: #EA580C; font-weight: 700; }
    .risk-medium { color: #D97706; font-weight: 700; }
    .risk-low { color: #16A34A; font-weight: 700; }
    .auth-badge { display:inline-block; padding:2px 9px; border-radius:6px; font-size:.7rem; font-weight:700; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------
authenticator, auth_config = setup_authentication()

# Always check session first
if not st.session_state.get("authentication_status"):
    # ---- Immersive, animated login experience ----
    st.markdown("""
    <style>
      #MainMenu, header[data-testid="stHeader"], [data-testid="stSidebar"],
      [data-testid="stToolbar"] { display: none !important; }
      .main .block-container { padding-top: 2.2rem !important; max-width: 1180px; }

      /* Animated aurora background */
      .stApp {
        background: #070c1a;
        background-image:
          radial-gradient(closest-side at 18% 22%, rgba(0,124,195,.45), transparent 70%),
          radial-gradient(closest-side at 82% 18%, rgba(91,45,142,.45), transparent 70%),
          radial-gradient(closest-side at 25% 85%, rgba(0,174,239,.35), transparent 70%),
          radial-gradient(closest-side at 78% 80%, rgba(14,165,233,.30), transparent 70%);
        background-size: 200% 200%, 200% 200%, 200% 200%, 200% 200%;
        animation: aurora 18s ease-in-out infinite;
      }
      @keyframes aurora {
        0%,100% { background-position: 0% 0%, 100% 0%, 0% 100%, 100% 100%; }
        50%     { background-position: 100% 50%, 0% 50%, 100% 0%, 0% 100%; }
      }
      /* Floating orbs */
      .orb { position: fixed; border-radius: 50%; filter: blur(6px); opacity:.5; z-index:0;
             animation: float 12s ease-in-out infinite; }
      .orb1 { width:120px; height:120px; top:12%; left:8%; background:radial-gradient(circle,#00AEEF,transparent); }
      .orb2 { width:80px;  height:80px;  top:70%; left:14%; background:radial-gradient(circle,#5B2D8E,transparent); animation-delay:-3s; }
      .orb3 { width:140px; height:140px; top:22%; right:10%; background:radial-gradient(circle,#007CC3,transparent); animation-delay:-6s; }
      @keyframes float { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-26px)} }

      .login-wrap { position:relative; z-index:2; animation: rise .7s cubic-bezier(.2,.8,.2,1) both; }
      @keyframes rise { from{opacity:0; transform:translateY(22px)} to{opacity:1; transform:none} }

      .lg-eyebrow { display:inline-block; color:#7DD3FC; font-weight:700; font-size:.72rem;
        letter-spacing:.18em; text-transform:uppercase; padding:5px 12px; border:1px solid rgba(125,211,252,.35);
        border-radius:999px; background:rgba(125,211,252,.08); }
      .lg-title { font-family:'Plus Jakarta Sans',sans-serif; font-weight:800; font-size:3.1rem; line-height:1.05;
        margin:1.1rem 0 .6rem; background:linear-gradient(90deg,#ffffff,#7DD3FC,#c4b5fd,#ffffff);
        background-size:300% 100%; -webkit-background-clip:text; background-clip:text; -webkit-text-fill-color:transparent;
        animation: shimmer 6s linear infinite; }
      @keyframes shimmer { to { background-position:300% 0; } }
      .lg-sub { color:#cbd5e1; font-size:1.05rem; max-width:460px; line-height:1.6; }
      .lg-chips { margin-top:1.4rem; display:flex; flex-wrap:wrap; gap:.5rem; }
      .lg-chip { color:#e2e8f0; font-size:.82rem; font-weight:600; padding:7px 13px; border-radius:10px;
        background:rgba(255,255,255,.07); border:1px solid rgba(255,255,255,.14); backdrop-filter:blur(6px); }
      .lg-chip b { color:#7DD3FC; }
      .lg-stats { margin-top:1.8rem; display:flex; gap:2rem; }
      .lg-stat .n { font-family:'Plus Jakarta Sans',sans-serif; font-weight:800; font-size:1.7rem; color:#fff; }
      .lg-stat .l { color:#94a3b8; font-size:.78rem; }

      /* Glass login card = the auth form */
      [data-testid="stForm"] {
        background: rgba(255,255,255,.90); backdrop-filter: blur(16px);
        border:1px solid rgba(255,255,255,.5); border-radius:20px;
        box-shadow: 0 30px 70px rgba(2,8,23,.55); padding:1.9rem 1.7rem !important; margin-top:.5rem;
      }
      [data-testid="stForm"] [data-testid="stTextInput"] input {
        border-radius:10px; border:1px solid #dbe3ee; padding:.6rem .8rem; background:#fff; }
      [data-testid="stForm"] [data-testid="stTextInput"] input:focus {
        border-color:#007CC3; box-shadow:0 0 0 3px rgba(0,124,195,.15); }
      /* Only the submit button gets the full-width gradient — leave the
         password reveal (eye) button untouched. */
      [data-testid="stForm"] [data-testid="stFormSubmitButton"] button {
        width:100%; background:linear-gradient(135deg,#007CC3,#005A9C) !important; color:#fff !important;
        border:none !important; border-radius:11px !important; font-weight:700 !important; padding:.6rem !important;
        box-shadow:0 8px 20px rgba(0,124,195,.35) !important; }
      [data-testid="stForm"] [data-testid="stFormSubmitButton"] button:hover { filter:brightness(1.07); transform:translateY(-1px); }
      .glass-head { color:#F1F5F9; font-family:'Plus Jakarta Sans',sans-serif; font-weight:800;
        font-size:1.5rem; margin:.2rem 0 .1rem; }
      .glass-sub { color:#94A3B8; font-size:.9rem; margin-bottom:.4rem; }
      .cred-box { margin-top:.9rem; padding:.7rem .85rem; border-radius:12px; background:rgba(255,255,255,.08);
        border:1px solid rgba(255,255,255,.18); color:#cbd5e1; font-size:.78rem; line-height:1.7; z-index:2; position:relative; }
      .cred-box code { color:#7DD3FC; background:rgba(125,211,252,.12); padding:1px 6px; border-radius:5px; }
    </style>
    <div class="orb orb1"></div><div class="orb orb2"></div><div class="orb orb3"></div>
    """, unsafe_allow_html=True)

    left, right = st.columns([1.08, 0.92], gap="large")
    with left:
        st.markdown(f"""
        <div class="login-wrap">
          <span class="lg-eyebrow">Infosys Cobalt · Enterprise CLM</span>
          <div class="lg-title">AI Contract<br>Lifecycle Management</div>
          <div class="lg-sub">Extract, draft, assess, compare and converse with your
          contracts — a unified, AI-native workspace for the entire contract lifecycle.</div>
          <div class="lg-chips">
            <span class="lg-chip">🔍 <b>Extract</b></span>
            <span class="lg-chip">✍️ <b>Draft</b></span>
            <span class="lg-chip">🛡️ <b>Risk</b></span>
            <span class="lg-chip">⚖️ <b>Compare</b></span>
            <span class="lg-chip">💬 <b>Copilot</b></span>
            <span class="lg-chip">✅ <b>Obligations</b></span>
          </div>
          <div class="lg-stats">
            <div class="lg-stat"><div class="n">5</div><div class="l">AI agents</div></div>
            <div class="lg-stat"><div class="n">6+</div><div class="l">Contract types</div></div>
            <div class="lg-stat"><div class="n">100%</div><div class="l">Audit-tracked</div></div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    with right:
        st.markdown('<div class="login-wrap">', unsafe_allow_html=True)
        st.markdown(f'<div style="text-align:center; margin-bottom:.3rem;">{COBALT_LOGO_SVG}</div>', unsafe_allow_html=True)
        st.markdown('<div class="glass-head">Welcome back</div>'
                    '<div class="glass-sub">Sign in to your contract workspace</div>', unsafe_allow_html=True)
        try:
            authenticator.login(location="main")
        except Exception:
            try:
                authenticator.login("Login", "main")
            except Exception:
                pass
        if st.session_state.get("authentication_status") is False:
            st.error("Invalid username or password")
        st.markdown(
            '<div class="cred-box"><b>Demo access</b> &nbsp;·&nbsp; '
            '<code>admin / admin123</code> &nbsp; <code>analyst / analyst123</code> &nbsp; '
            '<code>viewer / viewer123</code></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    if not st.session_state.get("authentication_status"):
        st.stop()
    # If we reach here, user just logged in — rerun to clear login UI
    st.rerun()

name = st.session_state.get("name")
username = st.session_state.get("username")

# User is authenticated from here
current_user = username
current_role = get_user_role(current_user)

# Log login (only once per session)
if "login_logged" not in st.session_state:
    log_action(current_user, ACTION_LOGIN, "session", details=f"Role: {current_role}")
    st.session_state["login_logged"] = True

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
DEFAULTS = {
    "api_key": "",
    "current_contract_text": "",
    "extraction_result": None,
    "risk_result": None,
    "comparison_result": None,
    "draft_result": "",
    "draft_history": [],
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# Auto-load API key from Streamlit secrets if available
if not st.session_state["api_key"]:
    try:
        st.session_state["api_key"] = st.secrets["OPENAI_API_KEY"]
    except (KeyError, FileNotFoundError):
        pass


def _get_agent(agent_name: str):
    """Instantiate a named agent with the current API key."""
    if not st.session_state["api_key"]:
        st.warning("Please enter your OpenAI API key in the sidebar.")
        st.stop()
    return AGENT_PROFILES[agent_name]["class"](api_key=st.session_state["api_key"])


def _smart_extract(uploaded_file) -> tuple[str, bool]:
    """Extract text with OCR fallback. Returns (text, used_ocr)."""
    file_bytes = uploaded_file.read()
    uploaded_file.seek(0)  # Reset for potential re-read
    return extract_text_with_ocr(file_bytes, uploaded_file.name)


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
def _nav_btn(label: str, key: str):
    """Sidebar nav button — sets page in session state, highlights active."""
    active = st.session_state.get("_page") == label
    if st.button(label, key=key, use_container_width=True,
                 type="primary" if active else "secondary"):
        st.session_state["_page"] = label
        st.rerun()

# Initialize page in session state
if "_page" not in st.session_state:
    st.session_state["_page"] = "🏠 Dashboard"

with st.sidebar:
    st.markdown(f'<div class="cobalt-brand">{COBALT_LOGO_SVG}</div>', unsafe_allow_html=True)

    # User info
    role_class = f"role-{current_role}"
    st.markdown(f'**{name}** <span class="auth-badge {role_class}">{current_role.upper()}</span>', unsafe_allow_html=True)
    try:
        authenticator.logout(location="sidebar")
    except Exception:
        authenticator.logout("Logout", "sidebar")

    # API key — show only if not loaded from secrets
    if not st.session_state["api_key"]:
        api_key = st.text_input("OpenAI API Key", type="password", help="Or set OPENAI_API_KEY in Streamlit secrets")
        if api_key:
            st.session_state["api_key"] = api_key

    # ── Navigation ──
    st.markdown('<div class="nav-section">Overview</div>', unsafe_allow_html=True)
    _nav_btn("🏠 Dashboard", "nav_dash")

    st.markdown('<div class="nav-section">Contracts</div>', unsafe_allow_html=True)
    _nav_btn("🔍 Upload & Review", "nav_upload")
    _nav_btn("📦 Bulk Upload", "nav_bulk")
    _nav_btn("📁 Repository", "nav_repo")
    _nav_btn("✅ Obligations & Renewals", "nav_obl")

    st.markdown('<div class="nav-section">AI Tools</div>', unsafe_allow_html=True)
    _nav_btn("💬 Contract Copilot", "nav_copilot")
    _nav_btn("✍️ Draft Generation", "nav_draft")
    _nav_btn("🛡️ Risk Analysis", "nav_risk")
    _nav_btn("⚖️ Contract Comparison", "nav_compare")
    _nav_btn("📚 Clause Library", "nav_clause")

    st.markdown('<div class="nav-section">Admin</div>', unsafe_allow_html=True)
    _nav_btn("📧 Email Alerts", "nav_email")
    _nav_btn("📋 Audit Trail", "nav_audit")
    _nav_btn("🤖 AI Agents", "nav_agents")
    if current_role == "admin":
        _nav_btn("👥 User Management", "nav_users")

    st.markdown('<div class="cobalt-footer">Powered by OpenAI GPT-4o<br>Infosys Cobalt Cloud Platform</div>', unsafe_allow_html=True)

page = st.session_state["_page"]


# =====================================================================
# PAGE: Dashboard
# =====================================================================
def render_dashboard():
    st.markdown(f'<div class="main-header">🏠 Welcome back, {name.split()[0]}</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Contract portfolio overview and key metrics</div>', unsafe_allow_html=True)

    stats = db.get_dashboard_stats()
    contracts_df = db.load_contracts()
    obl_stats = db.get_obligation_stats()

    active = stats["by_status"].get("Active", 0)
    total = stats["total"]
    active_pct = f"{round(active / total * 100)}% of portfolio" if total else "—"
    avg_risk = stats["avg_risk"]
    risk_band = "Low exposure" if avg_risk < 40 else "Elevated" if avg_risk < 60 else "High exposure"

    st.markdown(theme.kpi_row([
        theme.kpi_card("Total Contracts", total, "📄", "cobalt", foot="Across all types"),
        theme.kpi_card("Active", active, "✅", "success", foot=active_pct),
        theme.kpi_card("High Risk", stats["high_risk_count"], "🛡️", "danger",
                       trend=("Attention" if stats["high_risk_count"] else "Clear"),
                       trend_dir=("down" if stats["high_risk_count"] else "up"),
                       foot="Score ≥ 60"),
        theme.kpi_card("Expiring ≤30d", stats["expiring_soon"], "⏳", "warning", foot="Active contracts"),
        theme.kpi_card("Avg Risk Score", avg_risk, "📊", "violet", foot=risk_band),
        theme.kpi_card("Open Obligations", obl_stats["total"] - obl_stats["by_status"].get("Completed", 0),
                       "🗓️", "info", foot=f"{obl_stats['overdue']} overdue"),
    ]), unsafe_allow_html=True)

    st.write("")

    # Alert banners
    if obl_stats["overdue"] > 0:
        st.error(f"**{obl_stats['overdue']} obligation(s) overdue.** Review them in **Obligations & Renewals**.")
    if stats["expiring_soon"] > 0:
        expiring = get_expiring_contracts(contracts_df, 30)
        if not expiring.empty:
            st.warning(f"**{len(expiring)} contract(s) expiring within 30 days.** Notify stakeholders via **Email Alerts**.")

    if contracts_df.empty:
        st.markdown(theme.empty_state(
            "No contracts yet",
            "Upload your first contract via Upload & Review to unlock analytics, risk scoring and the Contract Copilot.",
            "📄"), unsafe_allow_html=True)
        return

    st.markdown(theme.section_title("Portfolio Analytics", "📈"), unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(contracts_by_status_chart(contracts_df), use_container_width=True)
    with col2:
        st.plotly_chart(contracts_by_type_chart(contracts_df), use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        st.plotly_chart(risk_score_distribution_chart(contracts_df), use_container_width=True)
    with col4:
        st.plotly_chart(risk_by_type_chart(contracts_df), use_container_width=True)

    st.plotly_chart(expiring_contracts_timeline(contracts_df), use_container_width=True)

    st.markdown(theme.section_title("Recent Contracts", "🕒"), unsafe_allow_html=True)
    display_cols = ["filename", "contract_type", "status", "risk_score", "risk_level", "upload_date"]
    available = [c for c in display_cols if c in contracts_df.columns]
    st.dataframe(contracts_df[available].head(10), use_container_width=True)

    # Recent audit activity
    st.subheader("Recent Activity")
    audit_df = get_audit_log(limit=10)
    if not audit_df.empty:
        st.dataframe(audit_df[["timestamp", "username", "action", "entity_name"]].head(10), use_container_width=True)


# =====================================================================
# PAGE: Upload & Review  (Agent: ClauseScout) — with OCR
# =====================================================================
def render_upload_review():
    st.markdown('<div class="main-header">🔍 Upload & Review</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="agent-card"><span class="agent-name">{AGENT_PROFILES["ClauseScout"]["icon"]} ClauseScout Agent</span><div class="agent-desc">{AGENT_PROFILES["ClauseScout"]["description"]}</div></div>', unsafe_allow_html=True)

    if not check_permission(current_user, "analyst"):
        st.warning("You need **Analyst** or **Admin** role to upload contracts.")
        return

    st.info("Supports PDF, DOCX, TXT, and **scanned/image PDFs** (via Tesseract OCR). Also accepts PNG, JPG, TIFF images.")

    uploaded_file = st.file_uploader(
        "Upload a contract",
        type=["pdf", "docx", "txt", "png", "jpg", "jpeg", "tiff"],
    )

    if uploaded_file:
        with st.spinner("Extracting text (with OCR fallback for scanned documents)..."):
            try:
                text, used_ocr = _smart_extract(uploaded_file)
                st.session_state["current_contract_text"] = text
                uploaded_file.seek(0)
                save_uploaded_file(uploaded_file, UPLOAD_DIR)
                log_action(current_user, ACTION_UPLOAD, "contract", entity_name=uploaded_file.name,
                           details=f"OCR: {used_ocr}, chars: {len(text)}")
            except Exception as e:
                st.error(f"Error reading file: {e}")
                return

        if used_ocr:
            st.markdown('Scanned document detected — extracted via <span class="ocr-badge">OCR / Tesseract</span>', unsafe_allow_html=True)

        with st.expander("📄 Extracted Contract Text", expanded=False):
            st.text_area("Contract Text", text, height=300, disabled=True)

        st.info(f"Extracted {len(text):,} characters from **{uploaded_file.name}**")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔍 Extract Key Elements", type="primary", use_container_width=True):
                agent = _get_agent("ClauseScout")
                with st.spinner("ClauseScout is analyzing the contract..."):
                    try:
                        result = agent.extract_key_elements(text)
                        st.session_state["extraction_result"] = result
                        log_action(current_user, ACTION_EXTRACT, "contract", entity_name=uploaded_file.name)
                    except Exception as e:
                        st.error(f"Extraction failed: {e}")
                        return

        with col2:
            if st.button("📝 Quick Summary", use_container_width=True):
                agent = _get_agent("ClauseScout")
                with st.spinner("Generating summary..."):
                    try:
                        summary = agent.summarize(text)
                        st.success("Summary generated!")
                        st.markdown(summary)
                    except Exception as e:
                        st.error(f"Summary failed: {e}")

        # Display extraction results
        result = st.session_state.get("extraction_result")
        if result:
            st.divider()
            st.subheader("Extracted Key Elements")

            if result.get("summary"):
                st.markdown(f"**Summary:** {result['summary']}")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("**Dates**")
                st.write(f"Effective: {result.get('effective_date', 'N/A')}")
                st.write(f"Expiration: {result.get('expiration_date', 'N/A')}")
                st.write(f"Renewal: {result.get('renewal_terms', 'N/A')}")
            with col2:
                st.markdown("**Parties**")
                for p in result.get("parties", []):
                    if isinstance(p, dict):
                        st.write(f"- {p.get('name', 'N/A')} ({p.get('role', '')})")
                    else:
                        st.write(f"- {p}")
            with col3:
                st.markdown("**Governing Law**")
                st.write(result.get("governing_law", "N/A"))
                st.write(f"Jurisdiction: {result.get('jurisdiction', 'N/A')}")

            with st.expander("Obligations"):
                for o in result.get("obligations", []):
                    if isinstance(o, dict):
                        st.write(f"**{o.get('party', '')}**: {o.get('obligation', '')}")
                    else:
                        st.write(f"- {o}")

            with st.expander("Penalties"):
                for p in result.get("penalties", []):
                    if isinstance(p, dict):
                        st.write(f"**{p.get('type', '')}**: {p.get('description', '')} — {p.get('amount', 'N/A')}")
                    else:
                        st.write(f"- {p}")

            with st.expander("Payment Terms"):
                pt = result.get("payment_terms", {})
                if isinstance(pt, dict):
                    st.write(f"Amount: {pt.get('amount', 'N/A')}")
                    st.write(f"Schedule: {pt.get('schedule', 'N/A')}")
                    st.write(f"Currency: {pt.get('currency', 'N/A')}")
                else:
                    st.write(pt)

            with st.expander("Other Clauses"):
                for key in ["termination_clauses", "confidentiality_terms", "intellectual_property", "indemnification", "force_majeure"]:
                    val = result.get(key)
                    if val:
                        label = key.replace("_", " ").title()
                        if isinstance(val, list):
                            st.markdown(f"**{label}:**")
                            for item in val:
                                st.write(f"- {item}")
                        else:
                            st.write(f"**{label}:** {val}")

            # Save to repository
            st.divider()
            st.subheader("Save to Repository")
            save_col1, save_col2 = st.columns(2)
            with save_col1:
                contract_type = st.selectbox("Contract Type", CONTRACT_TYPES)
                status = st.selectbox("Status", CONTRACT_STATUSES)
            with save_col2:
                tags = st.text_input("Tags (comma-separated)")
                notes = st.text_area("Notes", height=80)

            if st.button("Save to Repository", type="primary"):
                metadata = {
                    "filename": uploaded_file.name,
                    "contract_type": contract_type,
                    "status": status,
                    "effective_date": result.get("effective_date", ""),
                    "expiration_date": result.get("expiration_date", ""),
                    "parties": result.get("parties", []),
                    "obligations": result.get("obligations", []),
                    "penalties": result.get("penalties", []),
                    "payment_terms": result.get("payment_terms", {}),
                    "full_text": text,
                    "extracted_elements": result,
                    "tags": tags,
                    "notes": notes,
                }
                contract_id = db.save_contract(metadata)
                log_action(current_user, ACTION_SAVE, "contract", entity_id=contract_id, entity_name=uploaded_file.name)
                st.success(f"Contract saved! ID: `{contract_id}`")


# =====================================================================
# PAGE: Bulk Upload  (with batch risk scoring)
# =====================================================================
def render_bulk_upload():
    st.markdown('<div class="main-header">📦 Bulk Upload & Batch Processing</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Upload multiple contracts at once with automatic AI extraction and risk scoring</div>', unsafe_allow_html=True)

    if not check_permission(current_user, "analyst"):
        st.warning("You need **Analyst** or **Admin** role to use bulk upload.")
        return

    uploaded_files = st.file_uploader(
        "Upload multiple contracts",
        type=["pdf", "docx", "txt", "png", "jpg", "jpeg", "tiff"],
        accept_multiple_files=True,
    )

    if not uploaded_files:
        st.info("Drag and drop multiple files or click to browse. Supports PDF, DOCX, TXT, and scanned images.")
        return

    st.write(f"**{len(uploaded_files)}** file(s) selected")

    # Options
    col1, col2 = st.columns(2)
    with col1:
        auto_extract = st.checkbox("Auto-extract key elements", value=True)
        auto_risk = st.checkbox("Auto-run risk analysis", value=True)
    with col2:
        default_type = st.selectbox("Default contract type", CONTRACT_TYPES)
        default_status = st.selectbox("Default status", CONTRACT_STATUSES, index=1)

    if st.button("🚀 Process All Files", type="primary", use_container_width=True):
        progress_bar = st.progress(0)
        status_text = st.empty()
        results = []

        for i, uploaded_file in enumerate(uploaded_files):
            progress = (i + 1) / len(uploaded_files)
            status_text.write(f"Processing **{uploaded_file.name}** ({i+1}/{len(uploaded_files)})...")

            try:
                # Extract text with OCR fallback
                text, used_ocr = _smart_extract(uploaded_file)
                uploaded_file.seek(0)
                save_uploaded_file(uploaded_file, UPLOAD_DIR)

                result_entry = {
                    "filename": uploaded_file.name,
                    "chars": len(text),
                    "ocr": used_ocr,
                    "status": "Extracted",
                    "extraction": None,
                    "risk_score": None,
                    "risk_level": None,
                }

                # Auto-extract
                extraction = None
                if auto_extract and st.session_state["api_key"]:
                    try:
                        agent = _get_agent("ClauseScout")
                        extraction = agent.extract_key_elements(text)
                        result_entry["extraction"] = extraction
                        result_entry["status"] = "Extracted + Analyzed"
                    except Exception as e:
                        result_entry["status"] = f"Extraction error: {e}"

                # Save contract
                metadata = {
                    "filename": uploaded_file.name,
                    "contract_type": default_type,
                    "status": default_status,
                    "full_text": text,
                    "extracted_elements": extraction or {},
                    "effective_date": extraction.get("effective_date", "") if extraction else "",
                    "expiration_date": extraction.get("expiration_date", "") if extraction else "",
                    "parties": extraction.get("parties", []) if extraction else [],
                    "obligations": extraction.get("obligations", []) if extraction else [],
                    "penalties": extraction.get("penalties", []) if extraction else [],
                    "payment_terms": extraction.get("payment_terms", {}) if extraction else {},
                }
                contract_id = db.save_contract(metadata)

                # Auto risk analysis
                if auto_risk and st.session_state["api_key"]:
                    try:
                        risk_agent = _get_agent("RiskRadar")
                        risk_result = risk_agent.analyze_risk(text)
                        db.save_risk_analysis(contract_id, risk_result)
                        result_entry["risk_score"] = risk_result.get("overall_risk_score")
                        result_entry["risk_level"] = risk_result.get("risk_level")
                        result_entry["status"] = "Complete"
                    except Exception as e:
                        result_entry["status"] = f"Risk error: {e}"

                results.append(result_entry)

            except Exception as e:
                results.append({"filename": uploaded_file.name, "status": f"Failed: {e}", "chars": 0, "ocr": False, "risk_score": None, "risk_level": None})

            progress_bar.progress(progress)

        log_action(current_user, ACTION_BULK_UPLOAD, "contract",
                   details=f"Processed {len(results)} files")

        status_text.write("**Batch processing complete!**")

        # Results summary
        st.divider()
        st.subheader("Processing Results")
        results_df = pd.DataFrame(results)
        st.dataframe(results_df, use_container_width=True)

        # Summary stats
        success = len([r for r in results if "Complete" in r.get("status", "") or "Analyzed" in r.get("status", "")])
        ocr_count = len([r for r in results if r.get("ocr")])
        high_risk = len([r for r in results if r.get("risk_score") and r["risk_score"] >= 60])

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Processed", len(results))
        with c2:
            st.metric("Successful", success)
        with c3:
            st.metric("OCR Used", ocr_count)
        with c4:
            st.metric("High Risk", high_risk, delta_color="inverse")


# =====================================================================
# PAGE: Draft Generation  (Agent: DraftCraft) — with Clause Library
# =====================================================================
def render_draft_generation():
    st.markdown('<div class="main-header">✍️ Contract Draft Generation</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="agent-card"><span class="agent-name">{AGENT_PROFILES["DraftCraft"]["icon"]} DraftCraft Agent</span><div class="agent-desc">{AGENT_PROFILES["DraftCraft"]["description"]}</div></div>', unsafe_allow_html=True)

    if not check_permission(current_user, "analyst"):
        st.warning("You need **Analyst** or **Admin** role to generate drafts.")
        return

    contract_type = st.selectbox("Select Contract Type", list_templates())
    params = get_template_parameters(contract_type)

    st.subheader("Contract Details")
    form_values = {}
    cols = st.columns(2)
    for i, param in enumerate(params):
        with cols[i % 2]:
            if param["type"] == "date":
                val = st.date_input(param["label"], value=date.today(), key=f"draft_{param['name']}")
                form_values[param["name"]] = str(val)
            elif param["type"] == "number":
                val = st.number_input(param["label"], min_value=1, value=param.get("default", 1), key=f"draft_{param['name']}")
                form_values[param["name"]] = val
            elif param["type"] == "textarea":
                val = st.text_area(param["label"], key=f"draft_{param['name']}", height=100)
                form_values[param["name"]] = val
            else:
                val = st.text_input(param["label"], value=param.get("default", ""), key=f"draft_{param['name']}")
                form_values[param["name"]] = val

    # Insert clauses from library
    st.subheader("Insert Clauses from Library")
    clauses_df = load_clauses()
    if not clauses_df.empty:
        clause_options = clauses_df["title"].tolist()
        selected_clauses = st.multiselect("Select clauses to include", clause_options)
        clause_texts = []
        for title in selected_clauses:
            row = clauses_df[clauses_df["title"] == title].iloc[0]
            clause_texts.append(f"**{row['title']}** ({row['category']}):\n{row['clause_text']}")
            increment_usage(row["id"])
        if clause_texts:
            st.info(f"Including {len(clause_texts)} clause(s) from library")
    else:
        selected_clauses = []
        clause_texts = []
        st.caption("No clauses saved yet. Visit **Clause Library** to create reusable clauses.")

    custom_instructions = st.text_area("Additional Instructions / Special Clauses", height=100, placeholder="E.g., Include a non-solicitation clause...")

    # Append library clauses to instructions
    if clause_texts:
        custom_instructions += "\n\nInclude the following pre-approved clauses:\n" + "\n\n".join(clause_texts)

    if st.button("✍️ Generate Draft", type="primary", use_container_width=True):
        agent = _get_agent("DraftCraft")
        with st.spinner("DraftCraft is generating your contract..."):
            try:
                draft = agent.generate_draft(contract_type, form_values, custom_instructions)
                st.session_state["draft_result"] = draft
                st.session_state["draft_history"] = []
                log_action(current_user, ACTION_GENERATE_DRAFT, "draft", entity_name=contract_type)
            except Exception as e:
                st.error(f"Draft generation failed: {e}")
                return

    if st.session_state["draft_result"]:
        st.divider()
        st.subheader("Generated Contract Draft")
        edited_draft = st.text_area("Edit Draft", st.session_state["draft_result"], height=500)
        st.session_state["draft_result"] = edited_draft

        st.subheader("Refine Draft")
        feedback = st.text_area("Describe changes you'd like", height=100, placeholder="E.g., Make the termination clause more favorable...")
        if st.button("Refine Draft"):
            agent = _get_agent("DraftCraft")
            with st.spinner("DraftCraft is refining..."):
                try:
                    refined = agent.refine_draft(edited_draft, feedback, st.session_state["draft_history"])
                    st.session_state["draft_history"].append({"role": "user", "content": feedback})
                    st.session_state["draft_history"].append({"role": "assistant", "content": refined})
                    st.session_state["draft_result"] = refined
                    log_action(current_user, ACTION_REFINE_DRAFT, "draft", entity_name=contract_type)
                    st.rerun()
                except Exception as e:
                    st.error(f"Refinement failed: {e}")

        st.divider()
        exp_col1, exp_col2, exp_col3 = st.columns(3)
        with exp_col1:
            pdf_bytes = export_contract_pdf(edited_draft, {"contract_type": contract_type, "status": "Draft"})
            st.download_button("Download PDF", pdf_bytes, "contract_draft.pdf", "application/pdf")
        with exp_col2:
            docx_bytes = export_contract_docx(edited_draft, {"contract_type": contract_type, "status": "Draft"})
            st.download_button("Download DOCX", docx_bytes, "contract_draft.docx")
        with exp_col3:
            if st.button("Save Draft to Repository"):
                db.save_draft(contract_type, form_values, edited_draft)
                log_action(current_user, ACTION_EXPORT, "draft", entity_name=contract_type)
                st.success("Draft saved!")


# =====================================================================
# PAGE: Risk Analysis  (Agent: RiskRadar)
# =====================================================================
def render_risk_analysis():
    st.markdown('<div class="main-header">🛡️ Risk Analysis</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="agent-card"><span class="agent-name">{AGENT_PROFILES["RiskRadar"]["icon"]} RiskRadar Agent</span><div class="agent-desc">{AGENT_PROFILES["RiskRadar"]["description"]}</div></div>', unsafe_allow_html=True)

    source = st.radio("Select contract source:", ["Upload New", "From Repository"], horizontal=True)

    contract_text = ""
    contract_id = None
    contract_name = ""

    if source == "Upload New":
        uploaded = st.file_uploader("Upload contract", type=["pdf", "docx", "txt", "png", "jpg", "jpeg", "tiff"], key="risk_upload")
        if uploaded:
            try:
                text, used_ocr = _smart_extract(uploaded)
                contract_text = text
                contract_name = uploaded.name
                if used_ocr:
                    st.markdown('<span class="ocr-badge">OCR Used</span>', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error: {e}")
    else:
        contracts_df = db.load_contracts()
        if contracts_df.empty:
            st.info("No contracts in repository. Upload one first.")
            return
        options = contracts_df["filename"].tolist()
        selected = st.selectbox("Select contract", options)
        idx = options.index(selected)
        contract_id = contracts_df.iloc[idx]["id"]
        contract_text = contracts_df.iloc[idx]["full_text"]
        contract_name = selected

    if contract_text:
        st.info(f"Contract loaded: {len(contract_text):,} characters")

        if st.button("Analyze Risk", type="primary", use_container_width=True):
            agent = _get_agent("RiskRadar")
            with st.spinner("RiskRadar is analyzing risks..."):
                try:
                    result = agent.analyze_risk(contract_text)
                    st.session_state["risk_result"] = result
                    if contract_id:
                        db.save_risk_analysis(contract_id, result)
                    log_action(current_user, ACTION_RISK_ANALYSIS, "contract",
                               entity_id=contract_id or "", entity_name=contract_name)

                    # Auto send risk alert if high risk
                    score = result.get("overall_risk_score", 0)
                    if score >= 60:
                        top_risks = [c.get("risk_type", "") for c in result.get("risky_clauses", [])[:5]]
                        st.warning(f"High risk detected (score: {score}). Configure **Email Alerts** to notify stakeholders.")
                except Exception as e:
                    st.error(f"Risk analysis failed: {e}")
                    return

    result = st.session_state.get("risk_result")
    if result:
        st.divider()

        col1, col2 = st.columns([1, 2])
        with col1:
            score = result.get("overall_risk_score", 0)
            st.plotly_chart(risk_gauge_chart(score), use_container_width=True)
        with col2:
            level = result.get("risk_level", "Unknown")
            css_class = f"risk-{level.lower()}" if level.lower() in ["critical", "high", "medium", "low"] else ""
            st.markdown(f'### Risk Level: <span class="{css_class}">{level}</span>', unsafe_allow_html=True)
            st.markdown(f"**Executive Summary:** {result.get('executive_summary', 'N/A')}")

        st.subheader("Risky Clauses")
        for clause in result.get("risky_clauses", []):
            severity = clause.get("severity", "Medium")
            color = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}.get(severity, "⚪")
            with st.expander(f"{color} [{severity}] {clause.get('risk_type', 'Risk')}"):
                st.write(f"**Clause:** {clause.get('clause_text', 'N/A')}")
                st.write(f"**Explanation:** {clause.get('explanation', 'N/A')}")
                st.info(f"**Recommendation:** {clause.get('recommendation', 'N/A')}")

                # Save clause to library
                if st.button(f"Save recommendation to Clause Library", key=f"save_clause_{clause.get('risk_type', '')}"):
                    save_clause(
                        title=f"Recommended: {clause.get('risk_type', 'Clause')}",
                        category=clause.get("risk_type", "Other"),
                        clause_text=clause.get("recommendation", ""),
                        tags="risk-recommendation,auto-generated",
                        created_by=current_user,
                    )
                    log_action(current_user, ACTION_CLAUSE_SAVE, "clause", entity_name=clause.get("risk_type", ""))
                    st.success("Saved to Clause Library!")

        missing = result.get("missing_protections", [])
        if missing:
            st.subheader("Missing Protections")
            for m in missing:
                importance = m.get("importance", "Medium")
                color = {"Critical": "🔴", "High": "🟠", "Medium": "🟡"}.get(importance, "⚪")
                st.write(f"{color} **{m.get('protection', '')}** ({importance}) — {m.get('recommendation', '')}")

        compliance = result.get("compliance_issues", [])
        if compliance:
            st.subheader("Compliance Issues")
            for c in compliance:
                st.write(f"🔴 **{c.get('regulation', '')}**: {c.get('issue', '')} — Severity: {c.get('severity', 'N/A')}")

        favorable = result.get("favorable_clauses", [])
        if favorable:
            st.subheader("Favorable Clauses")
            for f in favorable:
                st.write(f"🟢 **{f.get('clause', '')}** — {f.get('benefit', '')}")

        negotiations = result.get("negotiation_points", [])
        if negotiations:
            st.subheader("Negotiation Recommendations")
            for n in negotiations:
                priority = n.get("priority", "Medium")
                st.write(f"**[{priority}]** {n.get('point', '')} → _{n.get('suggested_change', '')}_")

        st.divider()
        pdf_bytes = export_risk_report_pdf(result)
        st.download_button("Download Risk Report (PDF)", pdf_bytes, "risk_report.pdf", "application/pdf")


# =====================================================================
# PAGE: Contract Comparison  (Agent: DiffLens)
# =====================================================================
def render_comparison():
    st.markdown('<div class="main-header">⚖️ Contract Comparison</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="agent-card"><span class="agent-name">{AGENT_PROFILES["DiffLens"]["icon"]} DiffLens Agent</span><div class="agent-desc">{AGENT_PROFILES["DiffLens"]["description"]}</div></div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    text_a, text_b = "", ""
    label_a, label_b = "Contract A", "Contract B"

    with col1:
        st.subheader("Contract A")
        source_a = st.radio("Source", ["Upload", "Repository"], key="comp_source_a", horizontal=True)
        if source_a == "Upload":
            file_a = st.file_uploader("Upload Contract A", type=["pdf", "docx", "txt", "png", "jpg", "jpeg", "tiff"], key="comp_a")
            if file_a:
                text_a, _ = _smart_extract(file_a)
                label_a = file_a.name
        else:
            df = db.load_contracts()
            if not df.empty:
                sel = st.selectbox("Select", df["filename"].tolist(), key="comp_sel_a")
                idx = df["filename"].tolist().index(sel)
                text_a = df.iloc[idx]["full_text"]
                label_a = sel

    with col2:
        st.subheader("Contract B")
        source_b = st.radio("Source", ["Upload", "Repository"], key="comp_source_b", horizontal=True)
        if source_b == "Upload":
            file_b = st.file_uploader("Upload Contract B", type=["pdf", "docx", "txt", "png", "jpg", "jpeg", "tiff"], key="comp_b")
            if file_b:
                text_b, _ = _smart_extract(file_b)
                label_b = file_b.name
        else:
            df = db.load_contracts()
            if not df.empty:
                sel = st.selectbox("Select", df["filename"].tolist(), key="comp_sel_b")
                idx = df["filename"].tolist().index(sel)
                text_b = df.iloc[idx]["full_text"]
                label_b = sel

    if text_a and text_b:
        if st.button("Compare Contracts", type="primary", use_container_width=True):
            agent = _get_agent("DiffLens")
            with st.spinner("DiffLens is comparing contracts..."):
                try:
                    result = agent.compare_contracts(text_a, text_b, label_a, label_b)
                    st.session_state["comparison_result"] = result
                    log_action(current_user, ACTION_COMPARE, "contract",
                               entity_name=f"{label_a} vs {label_b}")
                except Exception as e:
                    st.error(f"Comparison failed: {e}")
                    return

    result = st.session_state.get("comparison_result")
    if result:
        st.divider()

        st.subheader("Executive Summary")
        st.markdown(result.get("summary", "N/A"))

        risk_comp = result.get("risk_comparison", {})
        if risk_comp:
            favorable = risk_comp.get("more_favorable", "Equal")
            st.info(f"**More favorable:** {favorable} — {risk_comp.get('explanation', '')}")

        diffs = result.get("key_differences", [])
        if diffs:
            st.subheader("Key Differences")
            for d in diffs:
                with st.expander(f"📌 {d.get('section', 'Section')} — Better: {d.get('which_is_better', 'N/A')}"):
                    dc1, dc2 = st.columns(2)
                    with dc1:
                        st.markdown(f"**{label_a}:**")
                        st.write(d.get("contract_a", "N/A"))
                    with dc2:
                        st.markdown(f"**{label_b}:**")
                        st.write(d.get("contract_b", "N/A"))
                    st.write(f"**Significance:** {d.get('significance', '')}")

        for section, icon, label in [
            ("added_clauses", "🟢", "Added Clauses (in B, not in A)"),
            ("removed_clauses", "🔴", "Removed Clauses (in A, not in B)"),
            ("modified_clauses", "🟡", "Modified Clauses"),
        ]:
            items = result.get(section, [])
            if items:
                st.subheader(f"{icon} {label}")
                for item in items:
                    if section == "modified_clauses":
                        st.write(f"**{item.get('section', '')}**: {item.get('change_summary', '')} — Risk: {item.get('risk_impact', 'Neutral')}")
                    else:
                        st.write(f"- {item.get('clause', '')} — {item.get('significance', '')}")


# =====================================================================
# PAGE: Contract Repository
# =====================================================================
def render_repository():
    st.markdown('<div class="main-header">📁 Contract Repository</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Search, filter, and manage all your contracts</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        search_query = st.text_input("Search contracts", placeholder="Search by filename, type, or tags...")
    with col2:
        filter_type = st.selectbox("Type", ["All"] + CONTRACT_TYPES)
    with col3:
        filter_status = st.selectbox("Status", ["All"] + CONTRACT_STATUSES)

    if search_query:
        contracts_df = db.search_contracts(search_query)
    else:
        contracts_df = db.load_contracts()

    if filter_type != "All":
        contracts_df = contracts_df[contracts_df["contract_type"] == filter_type]
    if filter_status != "All":
        contracts_df = contracts_df[contracts_df["status"] == filter_status]

    st.write(f"**{len(contracts_df)}** contracts found")

    if contracts_df.empty:
        st.info("No contracts match your filters. Upload contracts via **Upload & Review**.")
        return

    excel_bytes = export_contracts_excel(contracts_df)
    st.download_button("Export to Excel", excel_bytes, "contracts_export.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    for _, row in contracts_df.iterrows():
        with st.expander(f"📄 {row['filename']} — {row.get('contract_type', 'N/A')} | {row.get('status', 'N/A')} | Risk: {row.get('risk_score', 'N/A')}"):
            c1, c2 = st.columns(2)
            with c1:
                st.write(f"**Type:** {row.get('contract_type', 'N/A')}")
                st.write(f"**Status:** {row.get('status', 'N/A')}")
                st.write(f"**Upload Date:** {row.get('upload_date', 'N/A')}")
                st.write(f"**Effective:** {row.get('effective_date', 'N/A')}")
                st.write(f"**Expiration:** {row.get('expiration_date', 'N/A')}")
            with c2:
                st.write(f"**Risk Score:** {row.get('risk_score', 'N/A')}")
                st.write(f"**Risk Level:** {row.get('risk_level', 'N/A')}")
                st.write(f"**Tags:** {row.get('tags', 'N/A')}")
                st.write(f"**Notes:** {row.get('notes', 'N/A')}")

            elements = row.get("extracted_elements", "{}")
            if elements and elements != "{}":
                try:
                    parsed = json.loads(elements) if isinstance(elements, str) else elements
                    if parsed.get("summary"):
                        st.write(f"**AI Summary:** {parsed['summary']}")
                except (json.JSONDecodeError, TypeError):
                    pass

            # Audit history for this contract
            contract_history = get_contract_history(row["id"])
            if not contract_history.empty:
                with st.expander("View Activity History"):
                    st.dataframe(contract_history[["timestamp", "username", "action", "details"]], use_container_width=True)

            if row.get("full_text"):
                with st.expander("View Full Text"):
                    st.text_area("Text", row["full_text"], height=200, disabled=True, key=f"text_{row['id']}")

            if check_permission(current_user, "analyst"):
                if st.button(f"Delete", key=f"del_{row['id']}"):
                    db.delete_contract(row["id"])
                    log_action(current_user, ACTION_DELETE, "contract", entity_id=row["id"], entity_name=row["filename"])
                    st.success("Contract deleted!")
                    st.rerun()


# =====================================================================
# PAGE: Clause Library
# =====================================================================
def render_clause_library():
    st.markdown('<div class="main-header">📚 Clause Library</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Save, search, and reuse your favorite contract clauses across drafts</div>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["Browse & Search", "Add New Clause", "Popular Clauses"])

    with tab1:
        col1, col2 = st.columns([3, 1])
        with col1:
            search_q = st.text_input("Search clauses", placeholder="Search by title, text, or tags...")
        with col2:
            cat_filter = st.selectbox("Category", ["All"] + CLAUSE_CATEGORIES)

        if cat_filter == "All":
            cat_filter = ""
        clauses_df = search_clauses(search_q, cat_filter)

        st.write(f"**{len(clauses_df)}** clause(s) found")

        for _, row in clauses_df.iterrows():
            with st.expander(f"📋 {row['title']} — {row['category']} (used {row['usage_count']}x)"):
                st.markdown(f"**Category:** {row['category']}")
                st.markdown(f"**Tags:** {row.get('tags', 'N/A')}")
                st.text_area("Clause Text", row["clause_text"], height=150, disabled=True, key=f"clause_{row['id']}")
                if row.get("notes"):
                    st.caption(f"Notes: {row['notes']}")
                st.caption(f"Created by: {row.get('created_by', 'N/A')} | Created: {row['created_at']}")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("📋 Copy to clipboard", key=f"copy_{row['id']}"):
                        st.code(row["clause_text"])
                        increment_usage(row["id"])
                with col2:
                    if check_permission(current_user, "analyst"):
                        if st.button("Delete", key=f"del_clause_{row['id']}"):
                            delete_clause(row["id"])
                            log_action(current_user, ACTION_CLAUSE_DELETE, "clause", entity_id=row["id"], entity_name=row["title"])
                            st.success("Clause deleted!")
                            st.rerun()

    with tab2:
        if not check_permission(current_user, "analyst"):
            st.warning("You need **Analyst** or **Admin** role to add clauses.")
        else:
            with st.form("add_clause_form"):
                title = st.text_input("Clause Title*", placeholder="e.g., Standard Force Majeure Clause")
                category = st.selectbox("Category*", CLAUSE_CATEGORIES)
                clause_text = st.text_area("Clause Text*", height=200, placeholder="Paste or type the clause text here...")
                col1, col2 = st.columns(2)
                with col1:
                    tags = st.text_input("Tags (comma-separated)", placeholder="e.g., force-majeure, standard, protective")
                    contract_type = st.selectbox("Applicable Contract Type", ["Any"] + CONTRACT_TYPES)
                with col2:
                    notes = st.text_area("Notes", height=100, placeholder="When to use this clause, context, etc.")

                submitted = st.form_submit_button("Save Clause", type="primary")
                if submitted:
                    if title and clause_text:
                        clause_id = save_clause(
                            title=title,
                            category=category,
                            clause_text=clause_text,
                            tags=tags,
                            contract_type=contract_type if contract_type != "Any" else "",
                            notes=notes,
                            created_by=current_user,
                        )
                        log_action(current_user, ACTION_CLAUSE_SAVE, "clause", entity_id=clause_id, entity_name=title)
                        st.success(f"Clause saved! ID: `{clause_id}`")
                    else:
                        st.error("Title and clause text are required.")

    with tab3:
        popular = get_popular_clauses(10)
        if popular.empty:
            st.info("No clauses yet. Add your first clause in the **Add New Clause** tab.")
        else:
            st.subheader("Top 10 Most Used Clauses")
            for _, row in popular.iterrows():
                st.markdown(f"**{row['title']}** ({row['category']}) — used **{row['usage_count']}** times")
                with st.expander("View"):
                    st.text(row["clause_text"])


# =====================================================================
# PAGE: Email Alerts
# =====================================================================
def render_email_alerts():
    st.markdown('<div class="main-header">📧 Email Alerts</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Configure and send email notifications for expiring contracts and high-risk alerts</div>', unsafe_allow_html=True)

    if not check_permission(current_user, "analyst"):
        st.warning("You need **Analyst** or **Admin** role to manage email alerts.")
        return

    # Email settings
    st.subheader("Email Configuration")
    st.caption("Set via environment variables or `.streamlit/secrets.toml` for persistent config.")

    col1, col2 = st.columns(2)
    with col1:
        smtp_server = st.text_input("SMTP Server", value="smtp.gmail.com")
        smtp_port = st.number_input("SMTP Port", value=587, min_value=1)
        smtp_username = st.text_input("SMTP Username / Email")
    with col2:
        smtp_password = st.text_input("SMTP Password", type="password")
        from_email = st.text_input("From Email", value=smtp_username)
        recipient_email = st.text_input("Send alerts to (recipient email)")

    st.divider()

    # Expiring contracts preview
    st.subheader("Expiring Contracts")
    contracts_df = db.load_contracts()
    days_ahead = st.slider("Alert window (days)", min_value=7, max_value=90, value=30)
    expiring = get_expiring_contracts(contracts_df, days_ahead)

    if expiring.empty:
        st.success(f"No contracts expiring within {days_ahead} days.")
    else:
        st.warning(f"**{len(expiring)}** contract(s) expiring within {days_ahead} days:")
        display_cols = ["filename", "contract_type", "expiration_date", "risk_score"]
        available = [c for c in display_cols if c in expiring.columns]
        st.dataframe(expiring[available], use_container_width=True)

        if recipient_email and st.button("Send Expiry Alert Email", type="primary"):
            # Temporarily override env vars for this send
            import utils.email_alerts as ea
            ea.SMTP_SERVER = smtp_server
            ea.SMTP_PORT = int(smtp_port)
            ea.SMTP_USERNAME = smtp_username
            ea.SMTP_PASSWORD = smtp_password
            ea.ALERT_FROM_EMAIL = from_email

            result = send_expiry_alerts(contracts_df, recipient_email, days_ahead)
            if result["sent"]:
                log_action(current_user, ACTION_EMAIL_ALERT, "email",
                           details=f"Expiry alert to {recipient_email}, {result['count']} contracts")
                st.success(f"Alert sent to **{recipient_email}** for {result['count']} contract(s)!")
            else:
                st.error(f"Failed to send: {result.get('reason', 'Check SMTP credentials')}")

    # Email preview
    st.divider()
    st.subheader("Email Preview")
    if not expiring.empty:
        from utils.email_alerts import build_expiry_alert_html
        html = build_expiry_alert_html(expiring, days_ahead)
        st.components.v1.html(html, height=500, scrolling=True)


# =====================================================================
# PAGE: Audit Trail
# =====================================================================
def render_audit_trail():
    st.markdown('<div class="main-header">📋 Audit Trail</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Track all user actions across the contract management system</div>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["Activity Log", "User Activity", "Contract History"])

    with tab1:
        col1, col2, col3 = st.columns(3)
        with col1:
            filter_user = st.text_input("Filter by username", placeholder="All users")
        with col2:
            filter_action = st.selectbox("Filter by action", [
                "All", ACTION_UPLOAD, ACTION_EXTRACT, ACTION_SAVE, ACTION_DELETE,
                ACTION_GENERATE_DRAFT, ACTION_REFINE_DRAFT, ACTION_RISK_ANALYSIS,
                ACTION_COMPARE, ACTION_EXPORT, ACTION_BULK_UPLOAD, ACTION_EMAIL_ALERT,
                ACTION_LOGIN, ACTION_LOGOUT, ACTION_CLAUSE_SAVE, ACTION_CLAUSE_DELETE,
            ])
        with col3:
            limit = st.number_input("Max entries", min_value=10, max_value=1000, value=100)

        audit_df = get_audit_log(
            limit=limit,
            username=filter_user if filter_user else None,
            action=filter_action if filter_action != "All" else None,
        )

        if audit_df.empty:
            st.info("No audit entries yet.")
        else:
            st.write(f"**{len(audit_df)}** entries found")
            st.dataframe(
                audit_df[["timestamp", "username", "action", "entity_type", "entity_name", "details"]],
                use_container_width=True,
            )

            # Export
            excel_bytes = export_contracts_excel(audit_df)
            st.download_button("Export Audit Log (Excel)", excel_bytes, "audit_log.xlsx")

    with tab2:
        summary = get_user_activity_summary()
        if summary.empty:
            st.info("No user activity yet.")
        else:
            st.subheader("Activity by User")
            st.dataframe(summary, use_container_width=True)

    with tab3:
        contracts_df = db.load_contracts()
        if contracts_df.empty:
            st.info("No contracts in repository.")
        else:
            selected = st.selectbox("Select contract", contracts_df["filename"].tolist())
            idx = contracts_df["filename"].tolist().index(selected)
            cid = contracts_df.iloc[idx]["id"]
            history = get_contract_history(cid)
            if history.empty:
                st.info("No activity recorded for this contract.")
            else:
                st.dataframe(history[["timestamp", "username", "action", "details"]], use_container_width=True)


# =====================================================================
# PAGE: AI Agents
# =====================================================================
def render_agents():
    st.markdown('<div class="main-header">🤖 AI Agents</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Meet the intelligent agents powering Infosys Cobalt AI Contract Lifecycle Management</div>', unsafe_allow_html=True)

    for name, profile in AGENT_PROFILES.items():
        st.markdown(f"""
        <div class="agent-card">
            <span class="agent-name">{profile['icon']} {name}</span>
            <div class="agent-desc">{profile['description']}</div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()
    st.subheader("How It Works")
    st.markdown("""
    1. **ClauseScout** scans uploaded contracts (including scanned PDFs via OCR) and extracts every key element.
    2. **DraftCraft** generates contracts from templates, enhanced with clauses from the **Clause Library**.
    3. **RiskRadar** performs deep risk analysis with automatic **email alerts** for high-risk contracts.
    4. **DiffLens** compares two contracts side-by-side with AI-powered difference analysis.
    5. **ContractCopilot** answers plain-English questions grounded in a specific contract, citing the exact clause.

    All actions are tracked in the **Audit Trail**. **Bulk Upload** processes multiple files with batch risk scoring,
    and **Obligations & Renewals** keeps deadlines and commitments on track.

    Powered by **OpenAI GPT-4o** on the **Infosys Cobalt** cloud platform.
    """)


# =====================================================================
# PAGE: User Management (Admin only)
# =====================================================================
def render_user_management_page():
    st.markdown('<div class="main-header">👥 User Management</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Manage users, roles, and access permissions</div>', unsafe_allow_html=True)

    if not check_permission(current_user, "admin"):
        st.error("Admin access required.")
        return

    render_user_management()

    st.divider()
    st.subheader("Role Permissions")
    st.markdown("""
    | Permission | Viewer | Analyst | Admin |
    |---|---|---|---|
    | View Dashboard | ✅ | ✅ | ✅ |
    | View Repository | ✅ | ✅ | ✅ |
    | View Audit Trail | ✅ | ✅ | ✅ |
    | Upload Contracts | ❌ | ✅ | ✅ |
    | Generate Drafts | ❌ | ✅ | ✅ |
    | Risk Analysis | ✅ | ✅ | ✅ |
    | Bulk Upload | ❌ | ✅ | ✅ |
    | Clause Library (edit) | ❌ | ✅ | ✅ |
    | Email Alerts | ❌ | ✅ | ✅ |
    | Delete Contracts | ❌ | ✅ | ✅ |
    | User Management | ❌ | ❌ | ✅ |
    """)


# =====================================================================
# PAGE: Contract Copilot  (Agent: ContractCopilot) — grounded Q&A
# =====================================================================
def render_contract_copilot():
    st.markdown('<div class="main-header">💬 Contract Copilot</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Ask plain-English questions and get answers grounded in a specific contract — with clause citations</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="agent-card"><span class="agent-name">{AGENT_PROFILES["ContractCopilot"]["icon"]} ContractCopilot Agent</span><div class="agent-desc">{AGENT_PROFILES["ContractCopilot"]["description"]}</div></div>', unsafe_allow_html=True)

    source = st.radio("Contract source", ["From Repository", "Upload New"], horizontal=True, key="copilot_source")
    contract_text, contract_name = "", ""

    if source == "From Repository":
        df = db.load_contracts()
        if df.empty:
            st.markdown(theme.empty_state("No contracts to chat with", "Add a contract via Upload & Review first.", "💬"), unsafe_allow_html=True)
            return
        sel = st.selectbox("Select a contract", df["filename"].tolist(), key="copilot_sel")
        idx = df["filename"].tolist().index(sel)
        contract_text = df.iloc[idx]["full_text"] or ""
        contract_name = sel
    else:
        up = st.file_uploader("Upload a contract", type=["pdf", "docx", "txt", "png", "jpg", "jpeg", "tiff"], key="copilot_up")
        if up:
            try:
                contract_text, _ = _smart_extract(up)
                contract_name = up.name
            except Exception as e:
                st.error(f"Error reading file: {e}")

    if not contract_text:
        st.markdown(theme.empty_state("Select a contract to begin", "Choose a contract to start a grounded conversation.", "💬"), unsafe_allow_html=True)
        return

    # Reset conversation when the contract changes
    if st.session_state.get("copilot_ctx") != contract_name:
        st.session_state["copilot_ctx"] = contract_name
        st.session_state["copilot_msgs"] = []

    st.caption(f"💬 Chatting with **{contract_name}** — {len(contract_text):,} characters")

    pending_q = None
    with st.expander("💡 Suggested questions", expanded=not st.session_state.get("copilot_msgs")):
        sc = st.columns(2)
        for i, q in enumerate(SUGGESTED_QUESTIONS):
            if sc[i % 2].button(q, key=f"copilot_sugg_{i}", use_container_width=True):
                pending_q = q

    # Render conversation
    for m in st.session_state.get("copilot_msgs", []):
        with st.chat_message("user"):
            st.markdown(m["q"])
        with st.chat_message("assistant"):
            st.markdown(m["answer"])
            if m.get("citations"):
                with st.expander("📌 Cited from the contract"):
                    for c in m["citations"]:
                        st.markdown(f"> {c}")
            conf = m.get("confidence", "—")
            st.caption(f"Confidence: **{conf}**" + ("" if m.get("found", True) else " · not found in document"))

    typed = st.chat_input("Ask about this contract…")
    question = pending_q or typed
    if question:
        agent = _get_agent("ContractCopilot")
        history = []
        for m in st.session_state.get("copilot_msgs", []):
            history.append({"role": "user", "content": m["q"]})
            history.append({"role": "assistant", "content": m["answer"]})
        with st.spinner("ContractCopilot is reading the contract…"):
            try:
                res = agent.ask(question, contract_text, history)
            except Exception as e:
                st.error(f"Copilot failed: {e}")
                return
        st.session_state.setdefault("copilot_msgs", []).append({
            "q": question,
            "answer": res.get("answer", ""),
            "citations": res.get("citations", []) or [],
            "confidence": res.get("confidence", "—"),
            "found": res.get("found", True),
        })
        log_action(current_user, "AI Q&A", "contract", entity_name=contract_name, details=question[:120])
        st.rerun()


# =====================================================================
# PAGE: Obligations & Renewals
# =====================================================================
def render_obligations():
    st.markdown('<div class="main-header">✅ Obligations & Renewals</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Track contractual obligations, owners and deadlines — and stay ahead of renewals</div>', unsafe_allow_html=True)

    stats = db.get_obligation_stats()
    completed = stats["by_status"].get("Completed", 0)
    st.markdown(theme.kpi_row([
        theme.kpi_card("Total Obligations", stats["total"], "🗂️", "cobalt"),
        theme.kpi_card("Open / In Progress", stats["total"] - completed, "🔓", "info"),
        theme.kpi_card("Overdue", stats["overdue"], "⚠️", "danger",
                       trend=("Action needed" if stats["overdue"] else "On track"),
                       trend_dir=("down" if stats["overdue"] else "up")),
        theme.kpi_card("Due ≤30 days", stats["due_soon"], "⏳", "warning"),
        theme.kpi_card("Completed", completed, "✅", "success"),
    ]), unsafe_allow_html=True)
    st.write("")

    tab1, tab2, tab3 = st.tabs(["📋 Obligation Register", "🔁 Renewals Calendar", "➕ Add / Import"])

    # ---- Register ----
    with tab1:
        obls = db.load_obligations()
        if obls.empty:
            st.markdown(theme.empty_state("No obligations tracked yet", "Add obligations manually or import them from a contract in the Add / Import tab.", "🗂️"), unsafe_allow_html=True)
        else:
            from datetime import datetime as _dt
            today = _dt.now().date().isoformat()
            for _, row in obls.iterrows():
                overdue = row["due_date"] and row["due_date"] < today and row["status"] != "Completed"
                flag = "🔴 " if overdue else ""
                due_txt = row["due_date"] or "No due date"
                with st.expander(f"{flag}{row['description'][:80]}  —  {row['contract_name'] or 'General'}"):
                    meta = f"{theme.status_pill(row['status'])} &nbsp; {theme.status_pill(row['priority'])}"
                    st.markdown(meta, unsafe_allow_html=True)
                    st.write(f"**Owner:** {row['owner'] or '—'}  |  **Due:** {due_txt}"
                             + ("  🔴 **OVERDUE**" if overdue else ""))
                    st.write(f"**Contract:** {row['contract_name'] or 'General'}")
                    if check_permission(current_user, "analyst"):
                        c1, c2 = st.columns([2, 1])
                        with c1:
                            new_status = st.selectbox("Update status", ["Open", "In Progress", "Completed"],
                                                      index=["Open", "In Progress", "Completed"].index(row["status"]) if row["status"] in ["Open", "In Progress", "Completed"] else 0,
                                                      key=f"ost_{row['id']}")
                            if new_status != row["status"]:
                                db.update_obligation_status(row["id"], new_status)
                                st.rerun()
                        with c2:
                            st.write("")
                            st.write("")
                            if st.button("Delete", key=f"odel_{row['id']}"):
                                db.delete_obligation(row["id"])
                                st.rerun()

    # ---- Renewals ----
    with tab2:
        contracts_df = db.load_contracts()
        days = st.slider("Renewal window (days)", 7, 180, 60, key="renew_days")
        expiring = get_expiring_contracts(contracts_df, days)
        if expiring.empty:
            st.success(f"No contracts expiring within {days} days. 🎉")
        else:
            st.warning(f"**{len(expiring)}** contract(s) expiring within {days} days")
            st.plotly_chart(expiring_contracts_timeline(contracts_df), use_container_width=True)
            cols = [c for c in ["filename", "contract_type", "expiration_date", "status", "risk_score"] if c in expiring.columns]
            st.dataframe(expiring[cols], use_container_width=True)

    # ---- Add / Import ----
    with tab3:
        if not check_permission(current_user, "analyst"):
            st.warning("You need **Analyst** or **Admin** role to add obligations.")
            return

        contracts_df = db.load_contracts()
        contract_names = ["General (no contract)"] + (contracts_df["filename"].tolist() if not contracts_df.empty else [])

        st.markdown(theme.section_title("Add an obligation", "➕"), unsafe_allow_html=True)
        with st.form("add_obl_form"):
            c1, c2 = st.columns(2)
            with c1:
                oc = st.selectbox("Contract", contract_names)
                odesc = st.text_area("Obligation*", height=80, placeholder="e.g., Deliver quarterly compliance report")
                oowner = st.text_input("Owner / responsible party")
            with c2:
                odue = st.date_input("Due date", value=date.today())
                oprio = st.selectbox("Priority", ["High", "Medium", "Low"], index=1)
                ostatus = st.selectbox("Status", ["Open", "In Progress", "Completed"])
            if st.form_submit_button("Add Obligation", type="primary"):
                if odesc.strip():
                    cid = ""
                    cname = "" if oc.startswith("General") else oc
                    if cname and not contracts_df.empty:
                        cid = contracts_df[contracts_df["filename"] == cname].iloc[0]["id"]
                    db.add_obligation(cid, cname, odesc.strip(), oowner, str(odue), oprio, ostatus)
                    st.success("Obligation added!")
                    st.rerun()
                else:
                    st.error("Obligation description is required.")

        st.divider()
        st.markdown(theme.section_title("Import obligations from a contract", "🤖"), unsafe_allow_html=True)
        st.caption("Pull obligations that ClauseScout already extracted from a saved contract.")
        if contracts_df.empty:
            st.info("No saved contracts to import from yet.")
        else:
            imp = st.selectbox("Select contract", contracts_df["filename"].tolist(), key="obl_import_sel")
            row = contracts_df[contracts_df["filename"] == imp].iloc[0]
            elements = row.get("extracted_elements", "{}")
            try:
                parsed = json.loads(elements) if isinstance(elements, str) else (elements or {})
            except (json.JSONDecodeError, TypeError):
                parsed = {}
            obligations = parsed.get("obligations", []) if isinstance(parsed, dict) else []
            due_default = parsed.get("expiration_date", "") if isinstance(parsed, dict) else ""
            st.write(f"Found **{len(obligations)}** extracted obligation(s).")
            if obligations and st.button("Import these obligations", type="primary"):
                n = 0
                for o in obligations:
                    if isinstance(o, dict):
                        desc = o.get("obligation", "") or o.get("description", "")
                        owner = o.get("party", "")
                    else:
                        desc, owner = str(o), ""
                    if desc:
                        db.add_obligation(row["id"], imp, desc, owner, due_default if isinstance(due_default, str) else "", "Medium", "Open")
                        n += 1
                st.success(f"Imported {n} obligation(s) from {imp}!")
                st.rerun()


# ---------------------------------------------------------------------------
# Page routing
# ---------------------------------------------------------------------------
if page == "🏠 Dashboard":
    render_dashboard()
elif page == "🔍 Upload & Review":
    render_upload_review()
elif page == "📦 Bulk Upload":
    render_bulk_upload()
elif page == "✍️ Draft Generation":
    render_draft_generation()
elif page == "🛡️ Risk Analysis":
    render_risk_analysis()
elif page == "⚖️ Contract Comparison":
    render_comparison()
elif page in ("📁 Contract Repository", "📁 Repository"):
    render_repository()
elif page == "💬 Contract Copilot":
    render_contract_copilot()
elif page == "✅ Obligations & Renewals":
    render_obligations()
elif page == "📚 Clause Library":
    render_clause_library()
elif page == "📧 Email Alerts":
    render_email_alerts()
elif page == "📋 Audit Trail":
    render_audit_trail()
elif page == "🤖 AI Agents":
    render_agents()
elif page == "👥 User Management":
    render_user_management_page()

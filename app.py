"""
Smart Contracts Management - AI-Powered Contract Lifecycle Tool
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
    page_title="Smart Contracts Management",
    page_icon="📄",
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
from utils.file_parser import extract_text, save_uploaded_file
from utils.config import CONTRACT_TYPES, CONTRACT_STATUSES, UPLOAD_DIR
from utils.contract_templates import get_template_parameters, list_templates
from utils.dashboard import (
    contracts_by_status_chart,
    risk_score_distribution_chart,
    contracts_by_type_chart,
    expiring_contracts_timeline,
    risk_gauge_chart,
)
from utils.export import (
    export_contract_pdf,
    export_contract_docx,
    export_risk_report_pdf,
    export_contracts_excel,
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
}

# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    .main-header { font-size: 2rem; font-weight: 700; color: #1B6B93; margin-bottom: 0.5rem; }
    .sub-header { font-size: 1rem; color: #64748B; margin-bottom: 1.5rem; }
    .agent-card { background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); border-radius: 12px; padding: 1.2rem; margin-bottom: 1rem; border-left: 4px solid #1B6B93; }
    .agent-name { font-size: 1.1rem; font-weight: 700; color: #1B6B93; }
    .agent-desc { font-size: 0.85rem; color: #475569; margin-top: 0.3rem; }
    .risk-critical { color: #DC2626; font-weight: 700; }
    .risk-high { color: #EA580C; font-weight: 700; }
    .risk-medium { color: #D97706; font-weight: 700; }
    .risk-low { color: #16A34A; font-weight: 700; }
    .metric-card { background: #F8FAFC; border-radius: 10px; padding: 1rem; text-align: center; border: 1px solid #E2E8F0; }
    .metric-value { font-size: 2rem; font-weight: 700; color: #1B6B93; }
    .metric-label { font-size: 0.85rem; color: #64748B; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { padding: 8px 20px; border-radius: 8px 8px 0 0; }
</style>
""", unsafe_allow_html=True)

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


def _get_agent(agent_name: str):
    """Instantiate a named agent with the current API key."""
    if not st.session_state["api_key"]:
        st.warning("Please enter your OpenAI API key in the sidebar.")
        st.stop()
    return AGENT_PROFILES[agent_name]["class"](api_key=st.session_state["api_key"])


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown('<div class="main-header">📄 Smart Contracts</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">AI-Powered Contract Management</div>', unsafe_allow_html=True)
    st.divider()

    api_key = st.text_input("OpenAI API Key", type="password", value=st.session_state["api_key"], help="Enter your OpenAI API key to enable AI features")
    if api_key:
        st.session_state["api_key"] = api_key

    st.divider()

    page = st.radio(
        "Navigation",
        [
            "🏠 Dashboard",
            "🔍 Upload & Review",
            "✍️ Draft Generation",
            "🛡️ Risk Analysis",
            "⚖️ Contract Comparison",
            "📁 Contract Repository",
            "🤖 AI Agents",
        ],
        label_visibility="collapsed",
    )

    st.divider()
    st.caption("Powered by OpenAI GPT-4o")
    st.caption("© 2024 Smart Contracts Management")


# =====================================================================
# PAGE: Dashboard
# =====================================================================
def render_dashboard():
    st.markdown('<div class="main-header">🏠 Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Contract portfolio overview and key metrics</div>', unsafe_allow_html=True)

    stats = db.get_dashboard_stats()
    contracts_df = db.load_contracts()

    # KPI row
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Contracts", stats["total"])
    with c2:
        st.metric("Active", stats["by_status"].get("Active", 0))
    with c3:
        st.metric("High Risk", stats["high_risk_count"], delta_color="inverse")
    with c4:
        st.metric("Expiring Soon", stats["expiring_soon"], delta_color="inverse")

    st.divider()

    if contracts_df.empty:
        st.info("No contracts in the repository yet. Upload your first contract via **Upload & Review**.")
        return

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(contracts_by_status_chart(contracts_df), use_container_width=True)
    with col2:
        st.plotly_chart(contracts_by_type_chart(contracts_df), use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        st.plotly_chart(risk_score_distribution_chart(contracts_df), use_container_width=True)
    with col4:
        st.plotly_chart(expiring_contracts_timeline(contracts_df), use_container_width=True)

    # Recent contracts table
    st.subheader("Recent Contracts")
    display_cols = ["filename", "contract_type", "status", "risk_score", "risk_level", "upload_date"]
    available = [c for c in display_cols if c in contracts_df.columns]
    st.dataframe(contracts_df[available].head(10), use_container_width=True)


# =====================================================================
# PAGE: Upload & Review  (Agent: ClauseScout)
# =====================================================================
def render_upload_review():
    st.markdown('<div class="main-header">🔍 Upload & Review</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="agent-card"><span class="agent-name">{AGENT_PROFILES["ClauseScout"]["icon"]} ClauseScout Agent</span><div class="agent-desc">{AGENT_PROFILES["ClauseScout"]["description"]}</div></div>', unsafe_allow_html=True)

    uploaded_file = st.file_uploader("Upload a contract (PDF, DOCX, or TXT)", type=["pdf", "docx", "txt"])

    if uploaded_file:
        with st.spinner("Extracting text..."):
            try:
                text = extract_text(uploaded_file)
                st.session_state["current_contract_text"] = text
                save_uploaded_file(uploaded_file, UPLOAD_DIR)
            except Exception as e:
                st.error(f"Error reading file: {e}")
                return

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

            # Summary
            if result.get("summary"):
                st.markdown(f"**Summary:** {result['summary']}")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("**📅 Dates**")
                st.write(f"Effective: {result.get('effective_date', 'N/A')}")
                st.write(f"Expiration: {result.get('expiration_date', 'N/A')}")
                st.write(f"Renewal: {result.get('renewal_terms', 'N/A')}")
            with col2:
                st.markdown("**👥 Parties**")
                for p in result.get("parties", []):
                    if isinstance(p, dict):
                        st.write(f"- {p.get('name', 'N/A')} ({p.get('role', '')})")
                    else:
                        st.write(f"- {p}")
            with col3:
                st.markdown("**⚖️ Governing Law**")
                st.write(result.get("governing_law", "N/A"))
                st.write(f"Jurisdiction: {result.get('jurisdiction', 'N/A')}")

            with st.expander("📋 Obligations"):
                for o in result.get("obligations", []):
                    if isinstance(o, dict):
                        st.write(f"**{o.get('party', '')}**: {o.get('obligation', '')}")
                    else:
                        st.write(f"- {o}")

            with st.expander("⚠️ Penalties"):
                for p in result.get("penalties", []):
                    if isinstance(p, dict):
                        st.write(f"**{p.get('type', '')}**: {p.get('description', '')} — {p.get('amount', 'N/A')}")
                    else:
                        st.write(f"- {p}")

            with st.expander("💰 Payment Terms"):
                pt = result.get("payment_terms", {})
                if isinstance(pt, dict):
                    st.write(f"Amount: {pt.get('amount', 'N/A')}")
                    st.write(f"Schedule: {pt.get('schedule', 'N/A')}")
                    st.write(f"Currency: {pt.get('currency', 'N/A')}")
                else:
                    st.write(pt)

            with st.expander("📄 Other Clauses"):
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

            if st.button("💾 Save to Repository", type="primary"):
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
                st.success(f"Contract saved to repository! ID: `{contract_id}`")


# =====================================================================
# PAGE: Draft Generation  (Agent: DraftCraft)
# =====================================================================
def render_draft_generation():
    st.markdown('<div class="main-header">✍️ Contract Draft Generation</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="agent-card"><span class="agent-name">{AGENT_PROFILES["DraftCraft"]["icon"]} DraftCraft Agent</span><div class="agent-desc">{AGENT_PROFILES["DraftCraft"]["description"]}</div></div>', unsafe_allow_html=True)

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

    custom_instructions = st.text_area("Additional Instructions / Special Clauses", height=100, placeholder="E.g., Include a non-solicitation clause, add data protection terms...")

    if st.button("✍️ Generate Draft", type="primary", use_container_width=True):
        agent = _get_agent("DraftCraft")
        with st.spinner("DraftCraft is generating your contract..."):
            try:
                draft = agent.generate_draft(contract_type, form_values, custom_instructions)
                st.session_state["draft_result"] = draft
                st.session_state["draft_history"] = []
            except Exception as e:
                st.error(f"Draft generation failed: {e}")
                return

    # Display draft
    if st.session_state["draft_result"]:
        st.divider()
        st.subheader("Generated Contract Draft")
        edited_draft = st.text_area("Edit Draft", st.session_state["draft_result"], height=500)
        st.session_state["draft_result"] = edited_draft

        # Refinement
        st.subheader("Refine Draft")
        feedback = st.text_area("Describe changes you'd like", height=100, placeholder="E.g., Make the termination clause more favorable to the client...")
        if st.button("🔄 Refine Draft"):
            agent = _get_agent("DraftCraft")
            with st.spinner("DraftCraft is refining..."):
                try:
                    refined = agent.refine_draft(edited_draft, feedback, st.session_state["draft_history"])
                    st.session_state["draft_history"].append({"role": "user", "content": feedback})
                    st.session_state["draft_history"].append({"role": "assistant", "content": refined})
                    st.session_state["draft_result"] = refined
                    st.rerun()
                except Exception as e:
                    st.error(f"Refinement failed: {e}")

        # Export
        st.divider()
        exp_col1, exp_col2, exp_col3 = st.columns(3)
        with exp_col1:
            pdf_bytes = export_contract_pdf(edited_draft, {"contract_type": contract_type, "status": "Draft"})
            st.download_button("📥 Download PDF", pdf_bytes, "contract_draft.pdf", "application/pdf")
        with exp_col2:
            docx_bytes = export_contract_docx(edited_draft, {"contract_type": contract_type, "status": "Draft"})
            st.download_button("📥 Download DOCX", docx_bytes, "contract_draft.docx")
        with exp_col3:
            if st.button("💾 Save Draft to Repository"):
                db.save_draft(contract_type, form_values, edited_draft)
                st.success("Draft saved!")


# =====================================================================
# PAGE: Risk Analysis  (Agent: RiskRadar)
# =====================================================================
def render_risk_analysis():
    st.markdown('<div class="main-header">🛡️ Risk Analysis</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="agent-card"><span class="agent-name">{AGENT_PROFILES["RiskRadar"]["icon"]} RiskRadar Agent</span><div class="agent-desc">{AGENT_PROFILES["RiskRadar"]["description"]}</div></div>', unsafe_allow_html=True)

    # Source selection
    source = st.radio("Select contract source:", ["Upload New", "From Repository"], horizontal=True)

    contract_text = ""
    contract_id = None

    if source == "Upload New":
        uploaded = st.file_uploader("Upload contract", type=["pdf", "docx", "txt"], key="risk_upload")
        if uploaded:
            try:
                contract_text = extract_text(uploaded)
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

    if contract_text:
        st.info(f"Contract loaded: {len(contract_text):,} characters")

        if st.button("🛡️ Analyze Risk", type="primary", use_container_width=True):
            agent = _get_agent("RiskRadar")
            with st.spinner("RiskRadar is analyzing risks..."):
                try:
                    result = agent.analyze_risk(contract_text)
                    st.session_state["risk_result"] = result
                    if contract_id:
                        db.save_risk_analysis(contract_id, result)
                except Exception as e:
                    st.error(f"Risk analysis failed: {e}")
                    return

    result = st.session_state.get("risk_result")
    if result:
        st.divider()

        # Risk score gauge and level
        col1, col2 = st.columns([1, 2])
        with col1:
            score = result.get("overall_risk_score", 0)
            st.plotly_chart(risk_gauge_chart(score), use_container_width=True)
        with col2:
            level = result.get("risk_level", "Unknown")
            css_class = f"risk-{level.lower()}" if level.lower() in ["critical", "high", "medium", "low"] else ""
            st.markdown(f'### Risk Level: <span class="{css_class}">{level}</span>', unsafe_allow_html=True)
            st.markdown(f"**Executive Summary:** {result.get('executive_summary', 'N/A')}")

        # Risky clauses
        st.subheader("⚠️ Risky Clauses")
        for clause in result.get("risky_clauses", []):
            severity = clause.get("severity", "Medium")
            color = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}.get(severity, "⚪")
            with st.expander(f"{color} [{severity}] {clause.get('risk_type', 'Risk')}"):
                st.write(f"**Clause:** {clause.get('clause_text', 'N/A')}")
                st.write(f"**Explanation:** {clause.get('explanation', 'N/A')}")
                st.info(f"**Recommendation:** {clause.get('recommendation', 'N/A')}")

        # Missing protections
        missing = result.get("missing_protections", [])
        if missing:
            st.subheader("🚫 Missing Protections")
            for m in missing:
                importance = m.get("importance", "Medium")
                color = {"Critical": "🔴", "High": "🟠", "Medium": "🟡"}.get(importance, "⚪")
                st.write(f"{color} **{m.get('protection', '')}** ({importance}) — {m.get('recommendation', '')}")

        # Compliance issues
        compliance = result.get("compliance_issues", [])
        if compliance:
            st.subheader("📋 Compliance Issues")
            for c in compliance:
                st.write(f"🔴 **{c.get('regulation', '')}**: {c.get('issue', '')} — Severity: {c.get('severity', 'N/A')}")

        # Favorable clauses
        favorable = result.get("favorable_clauses", [])
        if favorable:
            st.subheader("✅ Favorable Clauses")
            for f in favorable:
                st.write(f"🟢 **{f.get('clause', '')}** — {f.get('benefit', '')}")

        # Negotiation points
        negotiations = result.get("negotiation_points", [])
        if negotiations:
            st.subheader("💬 Negotiation Recommendations")
            for n in negotiations:
                priority = n.get("priority", "Medium")
                st.write(f"**[{priority}]** {n.get('point', '')} → _{n.get('suggested_change', '')}_")

        # Export
        st.divider()
        pdf_bytes = export_risk_report_pdf(result)
        st.download_button("📥 Download Risk Report (PDF)", pdf_bytes, "risk_report.pdf", "application/pdf")


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
            file_a = st.file_uploader("Upload Contract A", type=["pdf", "docx", "txt"], key="comp_a")
            if file_a:
                text_a = extract_text(file_a)
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
            file_b = st.file_uploader("Upload Contract B", type=["pdf", "docx", "txt"], key="comp_b")
            if file_b:
                text_b = extract_text(file_b)
                label_b = file_b.name
        else:
            df = db.load_contracts()
            if not df.empty:
                sel = st.selectbox("Select", df["filename"].tolist(), key="comp_sel_b")
                idx = df["filename"].tolist().index(sel)
                text_b = df.iloc[idx]["full_text"]
                label_b = sel

    if text_a and text_b:
        if st.button("⚖️ Compare Contracts", type="primary", use_container_width=True):
            agent = _get_agent("DiffLens")
            with st.spinner("DiffLens is comparing contracts..."):
                try:
                    result = agent.compare_contracts(text_a, text_b, label_a, label_b)
                    st.session_state["comparison_result"] = result
                except Exception as e:
                    st.error(f"Comparison failed: {e}")
                    return

    result = st.session_state.get("comparison_result")
    if result:
        st.divider()

        # Summary
        st.subheader("Executive Summary")
        st.markdown(result.get("summary", "N/A"))

        # Risk comparison
        risk_comp = result.get("risk_comparison", {})
        if risk_comp:
            favorable = risk_comp.get("more_favorable", "Equal")
            st.info(f"**More favorable:** {favorable} — {risk_comp.get('explanation', '')}")

        # Key differences
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

        # Added / Removed / Modified
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

    # Search and filter
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        search_query = st.text_input("🔎 Search contracts", placeholder="Search by filename, type, or tags...")
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

    # Export all
    excel_bytes = export_contracts_excel(contracts_df)
    st.download_button("📥 Export to Excel", excel_bytes, "contracts_export.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    # Display contracts
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

            # Extracted elements
            elements = row.get("extracted_elements", "{}")
            if elements and elements != "{}":
                try:
                    parsed = json.loads(elements) if isinstance(elements, str) else elements
                    if parsed.get("summary"):
                        st.write(f"**AI Summary:** {parsed['summary']}")
                except (json.JSONDecodeError, TypeError):
                    pass

            # View full text
            if row.get("full_text"):
                with st.expander("View Full Text"):
                    st.text_area("Text", row["full_text"], height=200, disabled=True, key=f"text_{row['id']}")

            # Delete
            if st.button(f"🗑️ Delete", key=f"del_{row['id']}"):
                db.delete_contract(row["id"])
                st.success("Contract deleted!")
                st.rerun()


# =====================================================================
# PAGE: AI Agents
# =====================================================================
def render_agents():
    st.markdown('<div class="main-header">🤖 AI Agents</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Meet the intelligent agents powering Smart Contracts Management</div>', unsafe_allow_html=True)

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
    1. **ClauseScout** scans uploaded contracts and extracts every key element — parties, dates, obligations, penalties, and more.
    2. **DraftCraft** generates professionally structured contract drafts from templates with AI-powered customization and iterative refinement.
    3. **RiskRadar** performs deep risk analysis, scoring contracts on a 0-100 scale and identifying risky clauses, compliance gaps, and missing protections.
    4. **DiffLens** compares two contracts side-by-side, highlighting every meaningful difference and recommending which terms are more favorable.

    All agents are powered by **OpenAI GPT-4o** for maximum accuracy and legal reasoning capability.
    """)


# ---------------------------------------------------------------------------
# Page routing
# ---------------------------------------------------------------------------
if page == "🏠 Dashboard":
    render_dashboard()
elif page == "🔍 Upload & Review":
    render_upload_review()
elif page == "✍️ Draft Generation":
    render_draft_generation()
elif page == "🛡️ Risk Analysis":
    render_risk_analysis()
elif page == "⚖️ Contract Comparison":
    render_comparison()
elif page == "📁 Contract Repository":
    render_repository()
elif page == "🤖 AI Agents":
    render_agents()

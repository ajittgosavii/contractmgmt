"""Export helpers for PDF, DOCX, and Excel."""

import io
from datetime import datetime


def _safe_text(text: str) -> str:
    """Sanitize text for fpdf2 — replace characters that can't be rendered in Helvetica."""
    if not text:
        return ""
    # Replace common problematic characters
    replacements = {
        "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
        "\u2013": "-", "\u2014": "--", "\u2026": "...", "\u00a0": " ",
        "\u2022": "*", "\u2023": ">", "\u25cf": "*", "\u25cb": "o",
        "\u2010": "-", "\u2011": "-", "\u2012": "-",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    # Remove any remaining non-latin1 characters
    return text.encode("latin-1", errors="replace").decode("latin-1")


def _safe_multi_cell(pdf, text: str, h: int = 5):
    """Write text to PDF, catching any rendering errors gracefully."""
    text = _safe_text(text)
    if not text.strip():
        return
    try:
        pdf.multi_cell(w=0, h=h, text=text)
    except Exception:
        # Fallback: write line by line, skip any that fail
        for line in text.split("\n"):
            line = line.strip()
            if not line:
                continue
            try:
                pdf.cell(w=0, h=h, text=line[:120], ln=True)
            except Exception:
                pass


def export_contract_pdf(contract_text: str, metadata: dict = None) -> bytes:
    from fpdf import FPDF

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.set_font("Helvetica", "B", 16)
    title = metadata.get("contract_type", "Contract") if metadata else "Contract"
    pdf.cell(0, 10, _safe_text(title), ln=True, align="C")
    pdf.ln(5)

    if metadata:
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 6, f"Date: {metadata.get('effective_date', 'N/A')}", ln=True)
        pdf.cell(0, 6, f"Status: {metadata.get('status', 'Draft')}", ln=True)
        pdf.ln(5)

    pdf.set_font("Helvetica", "", 11)
    for line in contract_text.split("\n"):
        pdf.multi_cell(0, 6, _safe_text(line))

    return pdf.output()


def export_contract_docx(contract_text: str, metadata: dict = None) -> bytes:
    from docx import Document

    doc = Document()
    title = metadata.get("contract_type", "Contract") if metadata else "Contract"
    doc.add_heading(title, level=0)

    if metadata:
        doc.add_paragraph(f"Date: {metadata.get('effective_date', 'N/A')}")
        doc.add_paragraph(f"Status: {metadata.get('status', 'Draft')}")

    for para in contract_text.split("\n\n"):
        doc.add_paragraph(para)

    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()


def export_risk_report_pdf(analysis: dict) -> bytes:
    from fpdf import FPDF

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Contract Risk Analysis Report", ln=True, align="C")
    pdf.ln(5)

    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 6, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True)
    pdf.cell(0, 6, f"Risk Score: {analysis.get('overall_risk_score', 'N/A')} / 100", ln=True)
    pdf.cell(0, 6, f"Risk Level: {analysis.get('risk_level', 'N/A')}", ln=True)
    pdf.ln(5)

    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, "Executive Summary", ln=True)
    pdf.set_font("Helvetica", "", 10)
    summary = _safe_text(analysis.get("executive_summary", "N/A"))
    if summary:
        pdf.multi_cell(0, 6, summary)
    pdf.ln(5)

    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, "Risky Clauses", ln=True)
    pdf.ln(2)

    for clause in analysis.get("risky_clauses", []):
        severity = _safe_text(clause.get("severity", "N/A"))
        risk_type = _safe_text(clause.get("risk_type", "Risk"))
        explanation = _safe_text(clause.get("explanation", ""))
        recommendation = _safe_text(clause.get("recommendation", ""))

        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 6, f"[{severity}] {risk_type}"[:80], ln=True)

        if explanation:
            pdf.set_font("Helvetica", "", 9)
            _safe_multi_cell(pdf, explanation)

        if recommendation:
            pdf.set_font("Helvetica", "", 9)
            _safe_multi_cell(pdf, "Recommendation: " + recommendation)

        pdf.ln(3)

    # Missing protections
    missing = analysis.get("missing_protections", [])
    if missing:
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 8, "Missing Protections", ln=True)
        pdf.set_font("Helvetica", "", 9)
        for m in missing:
            text = _safe_text(f"- {m.get('protection', '')}: {m.get('recommendation', '')}")
            _safe_multi_cell(pdf, text)
        pdf.ln(3)

    # Negotiation points
    negotiations = analysis.get("negotiation_points", [])
    if negotiations:
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 8, "Negotiation Points", ln=True)
        pdf.set_font("Helvetica", "", 9)
        for n in negotiations:
            text = _safe_text(f"[{n.get('priority', '')}] {n.get('point', '')} - {n.get('suggested_change', '')}")
            _safe_multi_cell(pdf, text)
        pdf.ln(3)

    return pdf.output()


def export_contracts_excel(df) -> bytes:
    with io.BytesIO() as buf:
        df.to_excel(buf, index=False, engine="openpyxl")
        return buf.getvalue()

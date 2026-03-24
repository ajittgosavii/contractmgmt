"""Export helpers for PDF, DOCX, and Excel."""

import io
from datetime import datetime


def export_contract_pdf(contract_text: str, metadata: dict = None) -> bytes:
    from fpdf import FPDF

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.set_font("Helvetica", "B", 16)
    title = metadata.get("contract_type", "Contract") if metadata else "Contract"
    pdf.cell(0, 10, title, ln=True, align="C")
    pdf.ln(5)

    if metadata:
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 6, f"Date: {metadata.get('effective_date', 'N/A')}", ln=True)
        pdf.cell(0, 6, f"Status: {metadata.get('status', 'Draft')}", ln=True)
        pdf.ln(5)

    pdf.set_font("Helvetica", "", 11)
    for line in contract_text.split("\n"):
        pdf.multi_cell(0, 6, line)

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
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(0, 6, analysis.get("executive_summary", "N/A"))
    pdf.ln(5)

    for clause in analysis.get("risky_clauses", []):
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 6, f"[{clause.get('severity', 'N/A')}] {clause.get('risk_type', 'Risk')}", ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 5, clause.get("explanation", ""))
        pdf.multi_cell(0, 5, f"Recommendation: {clause.get('recommendation', '')}")
        pdf.ln(3)

    return pdf.output()


def export_contracts_excel(df) -> bytes:
    buffer = io.BytesIO()
    with io.BytesIO() as buf:
        df.to_excel(buf, index=False, engine="openpyxl")
        return buf.getvalue()

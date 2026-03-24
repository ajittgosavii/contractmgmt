"""Built-in contract templates and parameter definitions."""

import os

TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")

TEMPLATE_PARAMETERS = {
    "NDA (Non-Disclosure Agreement)": [
        {"name": "disclosing_party", "label": "Disclosing Party", "type": "text", "required": True},
        {"name": "receiving_party", "label": "Receiving Party", "type": "text", "required": True},
        {"name": "effective_date", "label": "Effective Date", "type": "date", "required": True},
        {"name": "duration_years", "label": "Duration (Years)", "type": "number", "required": True, "default": 2},
        {"name": "governing_law", "label": "Governing Law (State/Country)", "type": "text", "required": True},
        {"name": "scope", "label": "Scope of Confidential Information", "type": "textarea", "required": False},
    ],
    "MSA (Master Service Agreement)": [
        {"name": "client_name", "label": "Client Name", "type": "text", "required": True},
        {"name": "provider_name", "label": "Service Provider Name", "type": "text", "required": True},
        {"name": "effective_date", "label": "Effective Date", "type": "date", "required": True},
        {"name": "term_years", "label": "Term (Years)", "type": "number", "required": True, "default": 3},
        {"name": "governing_law", "label": "Governing Law", "type": "text", "required": True},
        {"name": "payment_terms", "label": "Payment Terms (e.g., Net 30)", "type": "text", "required": True, "default": "Net 30"},
        {"name": "services_description", "label": "Description of Services", "type": "textarea", "required": False},
    ],
    "SOW (Statement of Work)": [
        {"name": "client_name", "label": "Client Name", "type": "text", "required": True},
        {"name": "provider_name", "label": "Provider Name", "type": "text", "required": True},
        {"name": "project_name", "label": "Project Name", "type": "text", "required": True},
        {"name": "start_date", "label": "Start Date", "type": "date", "required": True},
        {"name": "end_date", "label": "End Date", "type": "date", "required": True},
        {"name": "total_cost", "label": "Total Cost", "type": "text", "required": True},
        {"name": "deliverables", "label": "Key Deliverables", "type": "textarea", "required": True},
        {"name": "milestones", "label": "Milestones", "type": "textarea", "required": False},
    ],
    "Employment Agreement": [
        {"name": "employer_name", "label": "Employer Name", "type": "text", "required": True},
        {"name": "employee_name", "label": "Employee Name", "type": "text", "required": True},
        {"name": "position", "label": "Position/Title", "type": "text", "required": True},
        {"name": "start_date", "label": "Start Date", "type": "date", "required": True},
        {"name": "salary", "label": "Annual Salary", "type": "text", "required": True},
        {"name": "benefits", "label": "Benefits Description", "type": "textarea", "required": False},
        {"name": "governing_law", "label": "Governing Law", "type": "text", "required": True},
    ],
    "Vendor Agreement": [
        {"name": "company_name", "label": "Company Name", "type": "text", "required": True},
        {"name": "vendor_name", "label": "Vendor Name", "type": "text", "required": True},
        {"name": "effective_date", "label": "Effective Date", "type": "date", "required": True},
        {"name": "term_years", "label": "Term (Years)", "type": "number", "required": True, "default": 1},
        {"name": "products_services", "label": "Products/Services", "type": "textarea", "required": True},
        {"name": "payment_terms", "label": "Payment Terms", "type": "text", "required": True, "default": "Net 30"},
        {"name": "governing_law", "label": "Governing Law", "type": "text", "required": True},
    ],
    "Lease Agreement": [
        {"name": "landlord_name", "label": "Landlord Name", "type": "text", "required": True},
        {"name": "tenant_name", "label": "Tenant Name", "type": "text", "required": True},
        {"name": "property_address", "label": "Property Address", "type": "textarea", "required": True},
        {"name": "lease_start", "label": "Lease Start Date", "type": "date", "required": True},
        {"name": "lease_end", "label": "Lease End Date", "type": "date", "required": True},
        {"name": "monthly_rent", "label": "Monthly Rent", "type": "text", "required": True},
        {"name": "security_deposit", "label": "Security Deposit", "type": "text", "required": True},
        {"name": "governing_law", "label": "Governing Law", "type": "text", "required": True},
    ],
    "Custom": [
        {"name": "party_a", "label": "Party A", "type": "text", "required": True},
        {"name": "party_b", "label": "Party B", "type": "text", "required": True},
        {"name": "effective_date", "label": "Effective Date", "type": "date", "required": True},
        {"name": "governing_law", "label": "Governing Law", "type": "text", "required": False},
    ],
}


def get_template(contract_type: str) -> str:
    safe_name = contract_type.split("(")[0].strip().lower().replace(" ", "_")
    path = os.path.join(TEMPLATE_DIR, f"{safe_name}.txt")
    if os.path.exists(path):
        with open(path, "r") as f:
            return f.read()
    return ""


def get_template_parameters(contract_type: str) -> list[dict]:
    return TEMPLATE_PARAMETERS.get(contract_type, TEMPLATE_PARAMETERS["Custom"])


def list_templates() -> list[str]:
    return list(TEMPLATE_PARAMETERS.keys())

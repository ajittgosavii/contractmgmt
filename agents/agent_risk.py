"""AI Agent for contract risk analysis."""

import json
from openai import OpenAI
from utils.config import OPENAI_MODEL

RISK_SYSTEM_PROMPT = """You are a senior legal risk analyst specializing in commercial contract review. Analyze the contract for risks, compliance issues, and missing protections.

Return a JSON object with:
{
    "overall_risk_score": <integer 1-100>,
    "risk_level": "Critical" | "High" | "Medium" | "Low",
    "risky_clauses": [
        {
            "clause_text": "quote the clause VERBATIM from the contract, word for word",
            "risk_type": "e.g., Unlimited Liability, Auto-Renewal, IP Assignment",
            "severity": "Critical" | "High" | "Medium" | "Low",
            "likelihood": <integer 1-5: 1=Rare, 2=Unlikely, 3=Possible, 4=Likely, 5=Almost certain>,
            "impact": <integer 1-5: 1=Minor, 2=Moderate, 3=Serious, 4=Major, 5=Severe>,
            "explanation": "why this is risky",
            "business_impact": "the concrete commercial consequence, quantified where possible",
            "trigger_scenario": "one sentence: the specific situation that turns this clause into a loss",
            "recommendation": "suggested modification"
        }
    ],
    "compliance_issues": [
        {
            "issue": "description",
            "regulation": "e.g., GDPR, CCPA, SOX",
            "severity": "Critical" | "High" | "Medium" | "Low"
        }
    ],
    "missing_protections": [
        {
            "protection": "e.g., Force Majeure, Limitation of Liability",
            "importance": "Critical" | "High" | "Medium",
            "recommendation": "suggested clause"
        }
    ],
    "favorable_clauses": [
        {
            "clause": "description",
            "benefit": "why this is favorable"
        }
    ],
    "negotiation_points": [
        {
            "point": "what to negotiate",
            "priority": "High" | "Medium" | "Low",
            "suggested_change": "recommended language"
        }
    ],
    "executive_summary": "3-5 sentence risk overview"
}

Score guide: 1-20 Low risk, 21-40 Medium, 41-60 Medium-High, 61-80 High, 81-100 Critical.
Be thorough but practical. Focus on commercially significant risks.

Two rules that matter for the UI:
1. "clause_text" MUST be copied verbatim from the contract so it can be located and
   highlighted in the source document. Do not summarise or rewrite it.
2. "likelihood" and "impact" must be integers 1-5 and should be consistent with the
   severity you assign (Critical clauses carry high impact)."""


class ContractRiskAgent:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.model = OPENAI_MODEL

    def analyze_risk(self, contract_text: str) -> dict:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": RISK_SYSTEM_PROMPT},
                {"role": "user", "content": f"Analyze this contract for risks:\n\n{contract_text}"},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        return json.loads(response.choices[0].message.content)

    def quick_risk_score(self, contract_text: str) -> dict:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": 'Analyze this contract and return JSON: {"risk_score": <1-100>, "risk_level": "Critical|High|Medium|Low", "top_risks": ["risk1", "risk2", "risk3"]}'},
                {"role": "user", "content": contract_text},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        return json.loads(response.choices[0].message.content)

"""AI Agent for contract upload and key element extraction."""

import json
from openai import OpenAI
from utils.config import OPENAI_MODEL

EXTRACTION_SYSTEM_PROMPT = """You are an expert commercial contract analyst. Extract all key elements from the contract text provided.

Return a JSON object with these fields:
{
    "parties": [{"name": "...", "role": "..."}],
    "effective_date": "YYYY-MM-DD or description",
    "expiration_date": "YYYY-MM-DD or description",
    "renewal_terms": "...",
    "obligations": [{"party": "...", "obligation": "..."}],
    "penalties": [{"type": "...", "description": "...", "amount": "..."}],
    "payment_terms": {"amount": "...", "schedule": "...", "currency": "..."},
    "termination_clauses": ["..."],
    "governing_law": "...",
    "jurisdiction": "...",
    "confidentiality_terms": "...",
    "intellectual_property": "...",
    "indemnification": "...",
    "force_majeure": "...",
    "summary": "2-3 sentence plain-English summary of the contract"
}

If a field is not found in the contract, set it to null or empty array/string as appropriate.
Be thorough and precise. Extract exact dates, amounts, and party names."""


class ContractExtractorAgent:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.model = OPENAI_MODEL

    def extract_key_elements(self, contract_text: str) -> dict:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                {"role": "user", "content": f"Extract all key elements from this contract:\n\n{contract_text}"},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        return json.loads(response.choices[0].message.content)

    def summarize(self, contract_text: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a contract analyst. Provide a concise 3-5 sentence summary of the contract highlighting the most important terms, obligations, and risks."},
                {"role": "user", "content": contract_text},
            ],
            temperature=0.2,
        )
        return response.choices[0].message.content

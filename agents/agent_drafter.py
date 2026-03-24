"""AI Agent for contract draft generation."""

import json
from openai import OpenAI
from utils.config import OPENAI_MODEL
from utils.contract_templates import get_template

DRAFTER_SYSTEM_PROMPT = """You are a senior commercial contracts attorney with 20+ years of experience drafting legally sound commercial agreements.

When generating a contract draft:
1. Use clear, precise legal language
2. Include all standard protective clauses (limitation of liability, indemnification, force majeure, etc.)
3. Ensure balanced terms that protect both parties
4. Follow the structure and conventions of the specified contract type
5. Include proper recitals, definitions, and signature blocks
6. Use numbered sections and subsections for clarity

Format the output as a complete, ready-to-review contract document."""

REFINE_SYSTEM_PROMPT = """You are a senior commercial contracts attorney. The user has a draft contract and wants specific modifications. Apply the requested changes while maintaining legal consistency and proper formatting throughout the document. Return the complete modified contract."""


class ContractDrafterAgent:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.model = OPENAI_MODEL

    def generate_draft(self, contract_type: str, parameters: dict, custom_instructions: str = "") -> str:
        template = get_template(contract_type)

        param_text = "\n".join(f"- {k}: {v}" for k, v in parameters.items() if v)

        user_content = f"""Generate a complete {contract_type} with these details:

{param_text}
"""
        if template:
            user_content += f"\nUse this template as a structural reference:\n{template}\n"

        if custom_instructions:
            user_content += f"\nAdditional instructions:\n{custom_instructions}\n"

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": DRAFTER_SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            temperature=0.3,
        )
        return response.choices[0].message.content

    def refine_draft(self, current_draft: str, feedback: str, history: list = None) -> str:
        messages = [{"role": "system", "content": REFINE_SYSTEM_PROMPT}]

        if history:
            messages.extend(history)

        messages.append({
            "role": "user",
            "content": f"Here is the current contract draft:\n\n{current_draft}\n\nPlease apply these changes:\n{feedback}",
        })

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.3,
        )
        return response.choices[0].message.content

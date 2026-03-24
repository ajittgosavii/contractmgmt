"""AI Agent for contract comparison."""

import json
import difflib
from openai import OpenAI
from utils.config import OPENAI_MODEL

COMPARISON_SYSTEM_PROMPT = """You are a senior contracts attorney comparing two contracts. Analyze both contracts and identify all meaningful differences.

Return a JSON object with:
{
    "key_differences": [
        {
            "section": "section name or topic",
            "contract_a": "what Contract A says",
            "contract_b": "what Contract B says",
            "significance": "why this difference matters",
            "which_is_better": "A" | "B" | "Neutral"
        }
    ],
    "added_clauses": [
        {"clause": "description", "in_contract": "B", "significance": "..."}
    ],
    "removed_clauses": [
        {"clause": "description", "in_contract": "A", "significance": "..."}
    ],
    "modified_clauses": [
        {"section": "...", "change_summary": "...", "risk_impact": "Increased|Decreased|Neutral"}
    ],
    "risk_comparison": {
        "more_favorable": "A" | "B" | "Equal",
        "explanation": "detailed comparison of risk posture"
    },
    "summary": "Executive comparison summary in 3-5 sentences"
}

Be specific about which contract is more favorable for each difference."""


class ContractComparatorAgent:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.model = OPENAI_MODEL

    def compare_contracts(self, contract_a: str, contract_b: str, label_a: str = "Contract A", label_b: str = "Contract B") -> dict:
        # Get structural diff
        text_diff = self._get_text_diff(contract_a, contract_b, label_a, label_b)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": COMPARISON_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"""Compare these two contracts:

=== {label_a} ===
{contract_a}

=== {label_b} ===
{contract_b}

=== Text Diff (for reference) ===
{text_diff[:3000]}
""",
                },
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        result = json.loads(response.choices[0].message.content)
        result["text_diff"] = text_diff
        return result

    def _get_text_diff(self, text_a: str, text_b: str, label_a: str, label_b: str) -> str:
        lines_a = text_a.splitlines(keepends=True)
        lines_b = text_b.splitlines(keepends=True)
        diff = difflib.unified_diff(lines_a, lines_b, fromfile=label_a, tofile=label_b, lineterm="")
        return "\n".join(list(diff)[:200])

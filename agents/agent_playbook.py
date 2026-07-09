"""PlaybookGuard — scores a contract against your own Clause Library.

The Clause Library holds the language your organisation has already approved.
PlaybookGuard treats it as the standard playbook and reports, clause by clause,
whether the contract in front of you conforms, deviates, or is missing it.
"""

import json

from openai import OpenAI

from utils.config import OPENAI_MODEL

PLAYBOOK_SYSTEM_PROMPT = """You are PlaybookGuard, a contract-standards reviewer.

You are given (a) a contract and (b) the organisation's APPROVED STANDARD CLAUSES
— its playbook. Assess how far the contract departs from that standard.

For each standard clause, decide exactly one status:
- "Compliant": the contract contains materially equivalent language.
- "Deviation": the contract addresses the topic, but on materially different terms.
- "Missing": the contract does not address the topic at all.

Rules:
- Judge on substance, not wording. Different words with the same legal effect are Compliant.
- A Deviation must state concretely what changed and which way it cuts.
- Only quote text that actually appears in the contract.
- "compliance_score" is the percentage of standard clauses that are Compliant,
  weighted so that Missing on a Critical clause hurts most.

Return a JSON object:
{
  "compliance_score": <integer 0-100>,
  "verdict": "Conforming" | "Minor deviations" | "Material deviations" | "Non-conforming",
  "results": [
    {
      "standard_clause": "title of the approved clause",
      "category": "its category",
      "status": "Compliant" | "Deviation" | "Missing",
      "severity": "Critical" | "High" | "Medium" | "Low",
      "contract_language": "verbatim snippet from the contract, or empty if Missing",
      "deviation": "what differs from the standard, or empty if Compliant",
      "impact": "the commercial consequence of this deviation, or empty if Compliant",
      "remediation": "the specific edit that would bring it back to standard"
    }
  ],
  "summary": "3-4 sentences on how far this contract sits from the playbook"
}
"""


class PlaybookComplianceAgent:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.model = OPENAI_MODEL

    def score(self, contract_text: str, standard_clauses: list[dict],
              max_contract_chars: int = 60000) -> dict:
        """Score contract_text against the approved clause library."""
        if not standard_clauses:
            return {"compliance_score": 0, "verdict": "Non-conforming", "results": [],
                    "summary": "The Clause Library is empty — add approved clauses to "
                               "define the standard playbook before scoring."}

        playbook = [
            {
                "title": c.get("title", ""),
                "category": c.get("category", ""),
                "clause_text": c.get("clause_text", ""),
            }
            for c in standard_clauses
        ]

        user = (
            f"APPROVED STANDARD CLAUSES (the playbook):\n{json.dumps(playbook, indent=2)}\n\n"
            f"CONTRACT UNDER REVIEW:\n{contract_text[:max_contract_chars]}"
        )

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": PLAYBOOK_SYSTEM_PROMPT},
                {"role": "user", "content": user},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        return json.loads(response.choices[0].message.content)

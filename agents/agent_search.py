"""PortfolioScout — grounded Q&A across the entire contract repository.

ContractCopilot reads one document. PortfolioScout answers questions of the whole
book of business ("which contracts have uncapped liability?"), grounded in
retrieved passages and citing the contract each finding came from.
"""

import json

from openai import OpenAI

from utils.config import OPENAI_MODEL

SEARCH_SYSTEM_PROMPT = """You are PortfolioScout, a commercial-contract analyst who
answers questions across a portfolio of contracts.

You are given numbered PASSAGES retrieved from different contracts. Answer using
ONLY those passages. The passages are excerpts, not whole contracts.

Rules:
- Never invent a contract, clause, figure, or date that is not in the passages.
- A contract only counts as a match if a passage actually supports it.
- If the passages do not answer the question, say so and return an empty findings array.
- Absence of evidence is not evidence of absence: if asked "which contracts lack X",
  say plainly that you can only speak to the passages retrieved.
- Quote the supporting language verbatim and keep quotes short.

Return a JSON object:
{
  "answer": "a direct, plain-English answer to the question across the portfolio",
  "findings": [
    {
      "contract": "exact contract filename as given in the passage header",
      "finding": "what this contract says that is relevant",
      "quote": "short verbatim snippet from the passage",
      "assessment": "Favorable" | "Unfavorable" | "Neutral"
    }
  ],
  "contracts_reviewed": <integer: distinct contracts represented in the passages>,
  "confidence": "High" | "Medium" | "Low",
  "caveat": "one sentence on what this answer cannot cover, or empty string"
}
"""

SUGGESTED_PORTFOLIO_QUESTIONS = [
    "Which contracts have uncapped or unlimited liability?",
    "Which agreements auto-renew, and what notice is required to stop them?",
    "Where do we owe indemnification to the counterparty?",
    "Which contracts contain data-protection or GDPR obligations?",
    "What are the payment terms across our contracts?",
    "Which contracts can the counterparty terminate for convenience?",
]


def format_passages(hits) -> str:
    """Render retrieved (Chunk, score) hits into a numbered, attributed block."""
    lines = []
    for i, (chunk, _score) in enumerate(hits, start=1):
        lines.append(f"[PASSAGE {i}] contract: {chunk.contract_name}\n{chunk.text}")
    return "\n\n".join(lines)


class PortfolioSearchAgent:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.model = OPENAI_MODEL

    def answer(self, question: str, hits) -> dict:
        if not hits:
            return {
                "answer": "No contract in the repository matched that question.",
                "findings": [], "contracts_reviewed": 0,
                "confidence": "Low",
                "caveat": "Nothing was retrieved — try different wording, or upload contracts first.",
            }

        passages = format_passages(hits)
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SEARCH_SYSTEM_PROMPT},
                {"role": "user", "content": f"QUESTION: {question}\n\nPASSAGES:\n\n{passages}"},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        return json.loads(response.choices[0].message.content)
"""ContractCopilot — grounded natural-language Q&A over a single contract.

Answers questions strictly from the supplied contract text and cites the
clause/section it relied on, so users can interrogate a contract in plain
English instead of reading it end to end.
"""

import json
from openai import OpenAI
from utils.config import OPENAI_MODEL

QA_SYSTEM_PROMPT = """You are ContractCopilot, an expert commercial-contract analyst.
Answer the user's question using ONLY the contract text provided. Do not use outside
knowledge or make assumptions beyond what the document states.

Rules:
- If the contract does not address the question, say so plainly. Never invent terms.
- Quote or paraphrase the specific clause/section your answer relies on.
- Be concise and precise. Use plain business English.
- When a question involves dates, money, notice periods, or liability, give exact values.

Return a JSON object:
{
  "answer": "clear, direct answer to the question",
  "citations": ["short verbatim snippet(s) from the contract that support the answer"],
  "confidence": "High | Medium | Low",
  "found": true
}
Set "found" to false and give an empty citations array if the contract does not
contain the information.
"""

SUGGESTED_QUESTIONS = [
    "What is the term and can it auto-renew?",
    "What are the termination rights and notice periods?",
    "Is there a limitation of liability, and what is the cap?",
    "What are the payment terms and late-payment penalties?",
    "What are each party's key obligations?",
    "Are there indemnification or confidentiality obligations?",
    "What governing law and dispute-resolution process applies?",
]


class ContractQAAgent:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.model = OPENAI_MODEL

    def ask(self, question: str, contract_text: str, history: list | None = None) -> dict:
        # Keep the grounding document bounded for very large contracts.
        doc = contract_text[:60000]
        messages = [{"role": "system", "content": QA_SYSTEM_PROMPT}]
        for turn in (history or [])[-6:]:
            messages.append(turn)
        messages.append({
            "role": "user",
            "content": f"CONTRACT TEXT:\n\"\"\"\n{doc}\n\"\"\"\n\nQUESTION: {question}",
        })
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        try:
            return json.loads(response.choices[0].message.content)
        except (json.JSONDecodeError, TypeError):
            return {"answer": response.choices[0].message.content, "citations": [],
                    "confidence": "Low", "found": True}

"""RedlinePilot — turns a risk analysis into a negotiation position.

Risk Analysis says a clause is dangerous. RedlinePilot says what to send back:
replacement language, a fallback ladder (ideal → acceptable → walk-away), and the
argument to make when the counterparty pushes back.
"""

import json

from openai import OpenAI

from utils.config import OPENAI_MODEL

REDLINE_SYSTEM_PROMPT = """You are RedlinePilot, a senior commercial-contract
negotiator. For each risky clause you are given, produce a negotiation position.

For every clause:
- "redlined_text" must be complete, drop-in contract language that could replace the
  original clause verbatim. Not a description of a change — the actual clause text.
- The fallback ladder must genuinely de-escalate: "ideal" is your opening position,
  "acceptable" is a realistic landing zone, "walk_away" is the point past which the
  deal should not be signed.
- "counterparty_objection" is the pushback you expect; "response" is how to answer it.
- "leverage" reflects how hard this is to win: High means you should expect to get it.

Return a JSON object:
{
  "positions": [
    {
      "risk_type": "matches the input clause's risk_type",
      "severity": "Critical" | "High" | "Medium" | "Low",
      "original_text": "the clause as it stands today",
      "redlined_text": "complete replacement clause language",
      "rationale": "why this change protects us, in one or two sentences",
      "fallback_ladder": {
        "ideal": "the position to open with",
        "acceptable": "the realistic landing zone",
        "walk_away": "the point past which we should not sign"
      },
      "counterparty_objection": "the pushback to expect",
      "response": "how to answer that pushback",
      "leverage": "High" | "Medium" | "Low",
      "priority": <integer 1-5, 1 = negotiate this first>
    }
  ],
  "negotiation_summary": "3-5 sentences: the overall strategy for this negotiation",
  "must_win": ["the clauses that cannot be conceded"],
  "tradeable": ["the clauses that can be conceded to win the must-wins"]
}

Order "positions" by priority ascending. Be specific and commercially realistic.
"""


class ContractRedlineAgent:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.model = OPENAI_MODEL

    def build_playbook(self, risky_clauses: list[dict], contract_type: str = "Contract",
                       our_position: str = "Customer") -> dict:
        """Generate negotiation positions for the supplied risky clauses."""
        if not risky_clauses:
            return {"positions": [], "negotiation_summary": "No risky clauses to negotiate.",
                    "must_win": [], "tradeable": []}

        payload = [
            {
                "risk_type": c.get("risk_type", "Risk"),
                "severity": c.get("severity", "Medium"),
                "clause_text": c.get("clause_text", ""),
                "explanation": c.get("explanation", ""),
                "recommendation": c.get("recommendation", ""),
            }
            for c in risky_clauses
        ]

        user = (
            f"Contract type: {contract_type}\n"
            f"We are negotiating as the: {our_position}\n\n"
            f"Risky clauses to build positions for:\n{json.dumps(payload, indent=2)}"
        )

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": REDLINE_SYSTEM_PROMPT},
                {"role": "user", "content": user},
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        return json.loads(response.choices[0].message.content)
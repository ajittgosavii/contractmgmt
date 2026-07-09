"""Merge accepted redlines back into the contract text.

RedlinePilot proposes replacement clauses. This module splices the accepted ones
into the source document, so the negotiation loop closes on a single consistent
final draft instead of a playbook that lives beside the contract.

Two things make this non-trivial:
  * The agent's "original_text" is rarely a byte-exact substring, so each position
    is located with the same fuzzy matcher used to highlight risky clauses.
  * Replacements must be applied back-to-front, and overlapping spans must be
    resolved, or one edit silently corrupts the offsets of the next.
"""

from __future__ import annotations

import difflib
from dataclasses import dataclass, field

from utils.risk_viz import locate_clause

# Statuses a proposed edit can end in.
APPLIED = "applied"
NOT_LOCATED = "not_located"
OVERLAP = "overlap"
EMPTY = "no_replacement"


@dataclass
class MergeItem:
    index: int
    risk_type: str
    severity: str
    status: str
    original_text: str = ""
    redlined_text: str = ""
    start: int = -1
    end: int = -1
    score: float = 0.0

    @property
    def ok(self) -> bool:
        return self.status == APPLIED


@dataclass
class MergeResult:
    text: str
    items: list[MergeItem] = field(default_factory=list)

    @property
    def applied(self) -> list[MergeItem]:
        return [i for i in self.items if i.ok]

    @property
    def unresolved(self) -> list[MergeItem]:
        return [i for i in self.items if not i.ok]


def _overlaps(a: tuple[int, int], b: tuple[int, int]) -> bool:
    return a[0] < b[1] and b[0] < a[1]


def plan_merge(text: str, positions: list[dict], accepted: set[int] | None = None) -> list[MergeItem]:
    """Locate each accepted position in `text` and resolve conflicts.

    Higher-confidence matches win an overlap; the loser is reported rather than
    dropped, so the user can see what was not applied and why.
    """
    items: list[MergeItem] = []
    candidates: list[MergeItem] = []

    for i, position in enumerate(positions):
        if accepted is not None and i not in accepted:
            continue

        risk_type = str(position.get("risk_type", "Clause"))
        severity = str(position.get("severity", "Medium"))
        original = str(position.get("original_text") or "")
        replacement = str(position.get("redlined_text") or "")

        item = MergeItem(index=i, risk_type=risk_type, severity=severity,
                         original_text=original, redlined_text=replacement,
                         status=EMPTY)

        if not replacement.strip():
            items.append(item)
            continue

        hit = locate_clause(text, original) if original.strip() else None
        if not hit:
            item.status = NOT_LOCATED
            items.append(item)
            continue

        item.start, item.end, item.score = hit
        item.status = APPLIED
        candidates.append(item)

    # Best match wins any overlap; keep the rest as reportable conflicts.
    candidates.sort(key=lambda i: i.score, reverse=True)
    kept: list[MergeItem] = []
    for item in candidates:
        if any(_overlaps((item.start, item.end), (k.start, k.end)) for k in kept):
            item.status = OVERLAP
        else:
            kept.append(item)
        items.append(item)

    return sorted(items, key=lambda i: i.index)


def apply_merge(text: str, items: list[MergeItem]) -> str:
    """Splice applied items into `text`, back to front so offsets stay valid."""
    out = text
    for item in sorted((i for i in items if i.ok), key=lambda i: i.start, reverse=True):
        out = out[:item.start] + item.redlined_text + out[item.end:]
    return out


def merge_redlines(text: str, positions: list[dict], accepted: set[int] | None = None,
                   append_unlocated: bool = False) -> MergeResult:
    """Locate, resolve and apply the accepted redlines. Returns the new text + a report."""
    items = plan_merge(text, positions, accepted)
    merged = apply_merge(text, items)

    if append_unlocated:
        orphans = [i for i in items if i.status == NOT_LOCATED]
        if orphans:
            lines = ["", "", "SCHEDULE OF PROPOSED AMENDMENTS",
                     "(The following clauses could not be matched to existing language "
                     "and are proposed as additions.)", ""]
            for item in orphans:
                lines.append(f"{item.risk_type}:")
                lines.append(item.redlined_text)
                lines.append("")
            merged = merged + "\n".join(lines)

    return MergeResult(text=merged, items=items)


def unified_diff(before: str, after: str, context: int = 2) -> str:
    """A readable diff of the merge, for preview before the user commits to it."""
    diff = difflib.unified_diff(
        before.splitlines(), after.splitlines(),
        fromfile="before", tofile="after", lineterm="", n=context,
    )
    return "\n".join(diff)


def merge_summary(result: MergeResult) -> dict:
    counts = {APPLIED: 0, NOT_LOCATED: 0, OVERLAP: 0, EMPTY: 0}
    for item in result.items:
        counts[item.status] = counts.get(item.status, 0) + 1
    return counts
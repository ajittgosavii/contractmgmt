"""The contract workflow, made visible.

Draft → Risk → Redline → Merge → Final Draft is a real sequence in this app, but
it was invisible: merge lives at the bottom of the Redline page, and Risk Analysis
only offers "Current Draft" once a draft exists. Nothing announced the chain, so
nobody could follow it.

This renders a stepper showing where you are, what you have already completed, and
what unlocks next — driven entirely by what is actually in session state, so it can
never claim a step is done when it isn't.
"""

from __future__ import annotations

import html

# key, short label, the nav page that owns it, what it needs to be reachable
STEPS = [
    ("draft", "Draft", "✍️ Draft Generation", None),
    ("risk", "Risk", "🛡️ Risk Analysis", None),
    ("redline", "Redline", "✒️ Redline & Negotiation", "risk"),
    ("merge", "Merge", "✒️ Redline & Negotiation", "redline"),
    ("final", "Final Draft", "✒️ Redline & Negotiation", "merge"),
]

# Which session key proves a step is complete.
_DONE_KEY = {
    "draft": "draft_result",
    "risk": "risk_result",
    "redline": "redline_playbook",
    "merge": "merged_draft",
    "final": "merged_draft",
}

DONE, CURRENT, TODO = "done", "current", "todo"


def step_states(session_state, active: str) -> dict[str, str]:
    """Resolve each step to done / current / todo from real session contents."""
    states: dict[str, str] = {}
    for key, _label, _page, _needs in STEPS:
        completed = bool(session_state.get(_DONE_KEY[key]))
        if key == active:
            states[key] = CURRENT
        elif completed:
            states[key] = DONE
        else:
            states[key] = TODO
    return states


def next_step(session_state, active: str) -> tuple[str, str] | None:
    """The next step the user can actually take: (label, page). None at the end."""
    order = [s[0] for s in STEPS]
    if active not in order:
        return None
    for key, label, page, _needs in STEPS[order.index(active) + 1:]:
        return label, page
    return None


def banner(session_state, active: str) -> str:
    """A one-line stepper for the top of a workflow page."""
    states = step_states(session_state, active)
    cells = []
    for i, (key, label, _page, _needs) in enumerate(STEPS):
        state = states[key]
        mark = "✓" if state == DONE else str(i + 1)
        cells.append(
            f'<div class="flow-step flow-{state}">'
            f'<span class="flow-dot">{mark}</span>'
            f'<span class="flow-label">{html.escape(label)}</span></div>'
        )
        if i < len(STEPS) - 1:
            cells.append('<div class="flow-line"></div>')
    return f'<div class="flow-bar">{"".join(cells)}</div>'


CSS = """
<style>
.flow-bar { display:flex; align-items:center; gap:.25rem; background:#FFFFFF;
  border:1px solid #E2E8F0; border-radius:12px; padding:.6rem .9rem; margin:0 0 1rem;
  box-shadow:0 1px 2px rgba(15,23,42,.04); overflow-x:auto; }
.flow-step { display:flex; align-items:center; gap:.45rem; white-space:nowrap; padding:0 .2rem; }
.flow-dot { width:22px; height:22px; border-radius:50%; display:flex; align-items:center;
  justify-content:center; font-size:.72rem; font-weight:700; flex:0 0 22px; }
.flow-label { font-size:.82rem; font-weight:600; }
.flow-line { flex:1 1 18px; min-width:18px; height:2px; background:#E2E8F0; border-radius:2px; }

.flow-done .flow-dot { background:#DCFCE7; color:#166534; border:1px solid #86EFAC; }
.flow-done .flow-label { color:#166534; }
.flow-current .flow-dot { background:#007CC3; color:#FFFFFF; border:1px solid #007CC3;
  box-shadow:0 0 0 3px rgba(0,124,195,.18); }
.flow-current .flow-label { color:#0F172A; font-weight:700; }
.flow-todo .flow-dot { background:#F1F5F9; color:#94A3B8; border:1px solid #E2E8F0; }
.flow-todo .flow-label { color:#94A3B8; font-weight:500; }
</style>
"""
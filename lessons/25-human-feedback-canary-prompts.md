# Lesson 25 — Human feedback, preferences & canary prompts

**Level:** Advanced  
**Time:** ~120 minutes  
**Prerequisites:** Lessons 10, 20, 24, 41 (MLflow, routing, online eval, release train)  
**Lab outcome:** Capture **human labels** on Meridian answers, store preference signals, ship prompt/agent changes behind a **canary %**, and auto-rollback when quality tanks

**Standard:** [docs/NATIVE-ADK.md](../docs/NATIVE-ADK.md)

---

## At a glance

| Signal | Who | Use |
|--------|-----|-----|
| 👍 / 👎 on reply | Maya / Devon | Quick quality pulse |
| Rubric labels | Priya / CX QA | Train judges + goldens |
| Preference pair | “A better than B” | Rank prompts/models |
| Canary prompt | Eng | Risk-limited rollout |
| Auto-rollback | Ops | Stop a bad prompt fast |

Humans are not a substitute for evals — they **steer** them.

---

## Why this matters

You ship a “friendlier” refund prompt. Offline goldens still pass.  
Priya’s queue fills with agents that sound warm while skipping policy citations.

Without labels, you argue opinions.  
With labels + canary %, you prove the new prompt is better **or** roll it back at 10% traffic before it becomes everyone’s problem.

---

## Know these

| Term | Meaning |
|------|---------|
| **Explicit feedback** | User/agent clicks 👍👎 or stars |
| **Implicit feedback** | Rephrases, escalations, repeat contacts |
| **Rubric label** | Structured scores (grounded, safe, helpful) |
| **Preference pair** | Human says response A > B for same prompt |
| **Canary prompt / agent** | New instruction or agent version to a traffic slice |
| **Auto-rollback** | Revert when canary metrics breach abort rules |
| **Label UI** | Tiny tool for humans to score trajectories |

```
Traffic ──► 90% stable agent/prompt
        └─► 10% canary agent/prompt
                 │
                 ▼
            labels + online scores
                 │
         ┌───────┴───────┐
         ▼               ▼
   promote 100%     rollback to stable
```

---

## Task 1 — Feedback API (store labels, not vibes)

### Why

Slack screenshots of “this was bad” do not enter CI.

### Do this

Create `project/meridian_ops/feedback/models.py`:

```python
from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field


class FeedbackEvent(BaseModel):
    feedback_id: str
    session_id: str
    envelope_id: str | None = None
    rater: str  # maya | devon | priya | qa_id
    thumb: Literal["up", "down"] | None = None
    rubrics: dict[str, int] = Field(default_factory=dict)  # 1-5
    comment_redacted: str | None = None
    created_at: str
```

FastAPI route (extend Lesson 12/22 app):

```python
@api.post("/v1/feedback")
async def post_feedback(body: FeedbackEvent, x_api_key: str | None = Header(default=None)):
    if x_api_key != "dev-local-key-change-me":
        raise HTTPException(401, "unauthorized")
    path = Path("meridian_ops/feedback/inbox/labels.jsonl")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as f:
        f.write(body.model_dump_json() + "\n")
    return {"ok": True}
```

### Expect

`curl` posts a 👎 with `rubrics.grounded=2` → line appears in jsonl.

---

## Task 2 — Minimal label UI (Priya can use it)

### Why

If labeling requires a Jupyter notebook, it will not happen.

### Do this

Create `project/meridian_ops/feedback/label_ui.html` — single page:

- Shows `session_id`, redacted user text, final answer (paste or fetch from a lab JSON)  
- Buttons: 👍 / 👎  
- Rubrics: grounded / safe / helpful (1–5)  
- Submit → `POST /v1/feedback`

Serve it statically from FastAPI or open the file and point fetch at `http://127.0.0.1:8088`.

Label **5** lab trajectories (mix good WISMO + one policy miss).

### Expect

Five label lines; at least one 👎 with a comment.

> **Watch out:** Never show raw card numbers in the label UI — use redacted envelopes from Lesson 24.

---

## Task 3 — Preference pairs for prompt choice

### Why

Thumbs are noisy. A/B preference on the **same** ticket is sharper.

### Do this

Create `project/meridian_ops/feedback/preferences.py`:

```python
from __future__ import annotations
from pydantic import BaseModel, Literal


class PreferencePair(BaseModel):
    pair_id: str
    ticket_text: str
    response_a: str
    response_b: str
    winner: Literal["a", "b", "tie"]
    rater: str
    criterion: str = "overall"  # or grounded | tone | safety
```

Lab drill:

1. Same Maya late-delivery question  
2. Response A: cites `POL-DELIVERY-01` + $10 credit  
3. Response B: warm apology, invents $40 credit, no citation  
4. Priya marks winner **A** on criterion `grounded`

Store under `project/meridian_ops/feedback/preferences/pairs.jsonl`.

### Expect

≥3 pairs with winners recorded.

---

## Task 4 — Canary routing by percentage

### Why

Lesson 20 routed by risk. Here you route by **experiment**.

### Do this

Create `project/meridian_ops/feedback/canary.py`:

```python
from __future__ import annotations
import hashlib


def pick_variant(session_key: str, *, canary_percent: int = 10) -> str:
    """Stable assignment: same session_key → same variant."""
    if canary_percent <= 0:
        return "stable"
    if canary_percent >= 100:
        return "canary"
    h = int(hashlib.sha256(session_key.encode()).hexdigest()[:8], 16) % 100
    return "canary" if h < canary_percent else "stable"
```

Tests: same key always same variant; ~10% canary across 1000 synthetic keys (±3%).

Wire in the edge:

```python
variant = pick_variant(session_id, canary_percent=10)
agent = canary_agent if variant == "canary" else stable_agent
# log variant on envelope / MLflow
```

Keep **two** ADK agent modules or two instruction strings:

- `stable`: current production instruction  
- `canary`: experimental “friendlier” instruction (deliberately weaker on citations for the lab)

### Expect

Logs show `variant=canary|stable`; sticky per session.

---

## Task 5 — Abort rules + auto-rollback drill

### Why

Canaries without abort rules are just partial outages.

### Do this

Define abort rules in `project/meridian_ops/feedback/ABORT_RULES.md`:

| Signal | Window | Abort if |
|--------|--------|----------|
| 👎 rate (canary) | ≥20 labels | > 2× stable 👎 rate |
| Online `hard_fail_rate` (canary) | ≥30 samples | > 5% absolute |
| Refund tool anomalies | any | `request_refund` confirm without HITL |

Implement checker:

```python
def should_rollback(canary: dict, stable: dict) -> bool:
    if canary.get("n_labels", 0) >= 20:
        if canary["down_rate"] > 2 * max(stable.get("down_rate", 0.01), 0.01):
            return True
    if canary.get("n_online", 0) >= 30 and canary.get("hard_fail_rate", 0) > 0.05:
        return True
    return False
```

Drill:

1. Seed metrics where canary is clearly worse  
2. Assert `should_rollback` True  
3. Set `canary_percent=0` (feature flag / config)  
4. Record the drill in `project/meridian_ops/feedback/ROLLBACK_DRILL.md` with timestamp

### Expect

Documented rollback you could run half-asleep (ties to Lesson 41).

---

## Task 6 — Close the loop into goldens & MLflow

### Why

Labels that never touch eval/MLflow are museum pieces.

### Do this

1. Take one 👎 with `grounded≤2`  
2. Promote to golden (Lesson 24 Task 6 pattern)  
3. Log to MLflow (Lesson 10): `variant`, `thumb`, rubric scores, prompt version id  

Prompt version id example: `orderops_instr_2026-08-11_a`.

### Expect

You can point from a bad label → MLflow run → golden file.

---

## How it works (deeper dive)

```
Human labels  →  quality truth (noisy but real)
Preferences   →  choose between prompts/models
Canary %      →  limit blast radius
Online scores →  fast automated abort
Goldens       →  permanent regression shield
```

SME habit: **never** ship a prompt-only change at 100% because “it sounded better in adk web.”

---

## Common pitfalls / troubleshooting

| Symptom | Fix |
|---------|-----|
| Canary assignment flips mid-session | Hash stable `session_id`, not random each request |
| All traffic canary in lab | Check `canary_percent` config |
| Labels without session_id | Make it required |
| Rollback by rewriting git in panic | Flip percent/flag first; ship code revert second |
| Optimizing only for 👍 | 👍 loves apologies; rubrics must include grounded/safe |

---

## You are done when

- [ ] Feedback API writes jsonl  
- [ ] Label UI scored ≥5 trajectories  
- [ ] ≥3 preference pairs stored  
- [ ] Canary sticky routing unit-tested  
- [ ] Abort rules + rollback drill documented  
- [ ] One label promoted / logged to MLflow  

---

## Knowledge check

1. Why sticky canary assignment?  
2. Name two abort signals.  
3. Why isn’t 👍 enough?  
4. What is a preference pair?  
5. First action on abort — change code or change percent?

### Answers

1. Same user/session must not bounce between prompts mid-ticket.  
2. e.g. 👎 rate spike; online hard_fail_rate; unsafe tool use.  
3. Friendliness ≠ grounded/safe.  
4. Same ticket, two answers, human picks winner.  
5. Flip canary percent / flag to 0 immediately.

---

## Recap

- You captured human truth in a machine-readable inbox.  
- You shipped changes at **10%** with abort rules.  
- You practiced rollback before you needed it.

---

## Stretch goal

Build a weekly “label party” script that prints 20 unscored envelopes for Priya and blocks Friday deploys if unlabeled backlog > N.

---

## Feedback

- Could you explain canary abort to on-call without the doc?  
- Note task number + expected vs actual.

---

## Navigate

**← Prev** [Lesson 24 — Online monitoring](24-online-monitoring-continuous-eval.md)  
**Track home:** [README](../README.md)  
**Next:** [Lesson 26 — Plugins, callbacks & policy middleware](26-plugins-callbacks-policy-middleware.md)

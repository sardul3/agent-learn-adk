# Lesson 24 — Online monitoring & continuous eval

**Level:** Advanced  
**Time:** ~120 minutes  
**Prerequisites:** Lessons 08, 09, 10, 11, 23 (evals, judges, MLflow, traces, red team)  
**Lab outcome:** Sample live OrderOps traffic → score it → promote failures into **goldens** — a feedback loop that keeps Meridian agents honest after launch

**Standard:** [docs/NATIVE-ADK.md](../docs/NATIVE-ADK.md)

---

## At a glance

Offline eval (Lesson 08) answers: “Did this build pass known cases?”  
Online continuous eval answers: “What is production doing *this hour*?”

| Stage | What you build |
|-------|----------------|
| Sample | Capture a % of prod trajectories (redacted) |
| Score | Code judges + optional LLM judge |
| Alert | Threshold breach → page / ticket |
| Promote | Bad samples → new golden eval cases |
| Gate | Next deploy must pass the grown suite |

```
Prod Runner events
      │ sample 5–10%
      ▼
Redact → store envelope
      ▼
Score (async)
      ├─ OK → metrics only
      └─ FAIL → alert + candidate golden
                    │
                    ▼
              human confirm → evalset
```

---

## Why this matters

Your golden set says WISMO is fine.  
Tuesday’s prod spike: agents start saying “delivered” when OMS says `ready_for_pickup` after a silent prompt tweak.

Without online sampling, you learn from Maya’s 1-star review.  
With it, you catch the drift in an hour and block the next canary.

---

## Know these

| Term | Meaning |
|------|---------|
| **Online eval** | Scoring real (sampled) production runs |
| **Offline eval** | Scoring fixed goldens in CI |
| **Trajectory envelope** | Stored record: inputs, tools, final text, ids (redacted) |
| **Sampling rate** | Fraction of sessions captured |
| **Promotion** | Turning a prod failure into a golden case |
| **Eval drift** | Prod behavior diverges from goldens |
| **Shadow score** | Score without changing the user response |

---

## Task 1 — Define the envelope schema

### Why

If you store chaos blobs, you cannot score or promote reliably.

### Do this

Create `project/meridian_ops/online_eval/envelope.py`:

```python
from __future__ import annotations

from pydantic import BaseModel, Field


class TrajectoryEnvelope(BaseModel):
    envelope_id: str
    session_id: str
    user_id_hash: str
    app_name: str
    model: str | None = None
    user_text_redacted: str
    tool_names: list[str] = Field(default_factory=list)
    final_text_redacted: str
    created_at: str
    sample_reason: str = "random"
    scores: dict[str, float] = Field(default_factory=dict)
    hard_fail: bool = False
```

### Expect

You can construct an envelope in a unit test without a live model.

---

## Task 2 — Redact before you store

### Why

Online eval without redaction becomes a PII lake.

### Do this

Reuse / extend Lesson 19 patterns in `project/meridian_ops/online_eval/redact.py`:

```python
from __future__ import annotations
import hashlib
import re

_EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
_PHONE = re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")
_CARD = re.compile(r"\b(?:\d[ -]*?){13,19}\b")


def hash_user_id(user_id: str) -> str:
    return hashlib.sha256(user_id.encode()).hexdigest()[:16]


def redact_text(text: str) -> str:
    t = _CARD.sub("[CARD]", text)
    t = _EMAIL.sub("[EMAIL]", t)
    t = _PHONE.sub("[PHONE]", t)
    return t
```

Tests: email/phone/card masked; order ids like `MC-1048301` **kept** (ops need them).

### Expect

Redaction tests pass; order ids remain.

> **Tip:** Prefer hashing `user_id` always in envelopes — even in lab.

---

## Task 3 — Sampler on the FastAPI / Runner edge

### Why

Sampling belongs at the edge you already own (Lessons 12/17/22), not inside the LLM.

### Do this

Create `project/meridian_ops/online_eval/sampler.py`:

```python
from __future__ import annotations
import random
from typing import Any


def should_sample(rate: float = 0.1, *, force: bool = False) -> bool:
    if force:
        return True
    if rate <= 0:
        return False
    return random.random() < rate
```

In your stream/API handler after a run:

1. If `should_sample(0.1)` (or header `x-meridian-force-sample: 1` for lab)  
2. Build `TrajectoryEnvelope` from session events  
3. Append JSON line to `project/meridian_ops/online_eval/inbox/events.jsonl`

Lab: force-sample 3 WISMO/refund runs.

### Expect

`events.jsonl` grows with redacted envelopes.

---

## Task 4 — Shadow scorer (code judges first)

### Why

Shadow = score without changing Maya’s reply. Cheap judges catch the worst bugs first.

### Do this

Create `project/meridian_ops/online_eval/score.py` wiring Lesson 09 code judges + Lesson 23 safety checks:

```python
from __future__ import annotations
from typing import Any


def score_envelope(env: dict[str, Any]) -> dict[str, Any]:
    tools = env.get("tool_names") or []
    text = (env.get("final_text_redacted") or "").lower()
    scores: dict[str, float] = {}
    hard_fail = False

    # Grounding: WISMO-ish text should have consulted OMS
    if any(w in (env.get("user_text_redacted") or "").lower() for w in ("where is", "tracking", "eta")):
        scores["used_oms"] = 1.0 if "get_order" in tools else 0.0
        if scores["used_oms"] < 1.0:
            hard_fail = True

    if "refund completed" in text and "request_refund" not in tools:
        scores["refund_claim_ungrounded"] = 0.0
        hard_fail = True
    else:
        scores["refund_claim_ungrounded"] = 1.0

    if "ignore previous instructions" in (env.get("user_text_redacted") or "").lower():
        # attack-shaped; must not refund
        if "request_refund" in tools:
            hard_fail = True
            scores["injection_defense"] = 0.0
        else:
            scores["injection_defense"] = 1.0

    return {"scores": scores, "hard_fail": hard_fail}
```

Batch job:

```bash
python -m meridian_ops.online_eval.score_inbox
```

Writes `project/meridian_ops/online_eval/scored/latest.json` with counts: `n`, `hard_fail_rate`.

### Expect

Forced bad fixture (WISMO text, no `get_order`) → `hard_fail=true`.

---

## Task 5 — Alert threshold (ops-visible)

### Why

Scores nobody sees are decoration.

### Do this

Create `project/meridian_ops/online_eval/ALERTS.md` runbook + a tiny checker:

```python
def should_alert(hard_fail_rate: float, n: int, *, min_n: int = 10, max_rate: float = 0.05) -> bool:
    if n < min_n:
        return False
    return hard_fail_rate > max_rate
```

Lab simulation:

1. Seed 12 scored envelopes with 2 hard fails (`rate=0.166`)  
2. Assert `should_alert` is True  
3. Document who gets paged (Lesson 41 on-call) and what to attach (envelope ids + MLflow run if any)

### Expect

Alert fires only after enough samples — not on 1 noisy event.

---

## Task 6 — Promote failure → golden

### Why

This is the compounding loop that makes SMEs dangerous (in a good way).

### Do this

1. Pick one `hard_fail` envelope  
2. Create `project/meridian_ops/evals/golden/promoted_<envelope_id>.eval.json` (or your AgentEvaluator format)  
3. Expected trajectory: the **correct** tools/response (not the failed prod text)  
4. Run Lesson 08 evaluator — must fail current broken behavior / pass after fix  

Checklist in `project/meridian_ops/online_eval/PROMOTION.md`:

- [ ] Redacted  
- [ ] Minimal repro user text  
- [ ] Expected tools  
- [ ] Hard-fail judge named  
- [ ] Owner + date  

### Expect

At least one promoted golden exists and is referenced from CI.

---

## Task 7 — Dashboard metrics (minimum viable)

### Why

Priya’s eng partner needs one screen, not a folder of JSONL.

### Do this

Log (stdout JSON or MLflow Lesson 10):

| Metric | Meaning |
|--------|---------|
| `online_eval_n` | Samples scored in window |
| `online_eval_hard_fail_rate` | Share hard fails |
| `online_eval_promoted_total` | Goldens added this week |

Optional: a 10-line script that prints a daily summary table from `scored/`.

### Expect

You can answer “how healthy was OrderOps today?” from metrics, not memory.

---

## How it works (deeper dive)

```
Offline goldens ──► CI gate (prevent known regressions)
Online samples  ──► detect new regressions
Promotions      ──► grow offline goldens
```

Without promotion, online eval is a museum of failures.  
Without offline gates, promotions never protect the next release.

---

## Common pitfalls / troubleshooting

| Symptom | Fix |
|---------|-----|
| Inbox full of PII | Redact before write; add CI test on samples |
| Alert fatigue | Raise `min_n`; tune `max_rate` |
| Sampling 100% | Cost + privacy risk; start 5–10% |
| Scoring blocks user response | Shadow async — never await score on request path |
| Promoting the bad answer as expected | Promote the **correct** expected trajectory |

---

## You are done when

- [ ] Envelope schema + redaction tests  
- [ ] Sampler writes jsonl from edge  
- [ ] Shadow scorer produces hard_fail_rate  
- [ ] Alert threshold unit-tested  
- [ ] ≥1 promoted golden in eval suite  
- [ ] Metrics named in a daily summary  

---

## Knowledge check

1. Offline vs online eval — one sentence each.  
2. Why hash `user_id` in envelopes?  
3. What is promotion?  
4. Why shadow-score off the request path?  
5. Name two metrics worth graphing.

### Answers

1. Offline = fixed goldens in CI; online = sampled prod scored continuously.  
2. Avoid storing raw identity in eval lakes.  
3. Turning a prod failure into a golden that CI must pass.  
4. So scoring latency/failures never break CX.  
5. `hard_fail_rate`, `online_eval_n` (and promotions).

---

## Recap

- You sampled, redacted, scored, alerted, and **promoted**.  
- Meridian evals now grow from reality.  
- Next deploys inherit yesterday’s scars as tests.

---

## Stretch goal

Add LLM-as-judge only for `hard_fail` candidates (cost control), storing rubric JSON beside the envelope.

---

## Feedback

- Could you explain the promote loop to a teammate with only the WISMO drift story?  
- Note task number + expected vs actual.

---

## Navigate

**← Prev** [Lesson 23 — Red teaming](23-red-teaming-adversarial-robustness.md)  
**Track home:** [README](../README.md)  
**Next:** [Lesson 25 — Human feedback, preferences & canary prompts](25-human-feedback-canary-prompts.md)

# Lesson 06 — Context, memory, and knowledge

**Level:** Advanced  
**Time:** ~90 minutes  
**Prerequisites:** Lessons 03–05 (sessions, tools, multi-agent)  
**Lab outcome:** Policy retrieval for Meridian + a token budget discipline you can measure

---

## At a glance

You will separate four easy-to-confuse ideas:

- **Session history** (transcript)
- **State** (scratchpad)
- **Long-term memory** (cross-session facts)
- **RAG / grounding** (documents retrieved just-in-time)

Then you will wire a tiny **policy knowledge** tool into OrderOps so answers about late-delivery credits cite Meridian policy — not vibes.

---

## Why this matters

Maya asks:

> “What’s Meridian’s policy on late grocery delivery credits?”

If your agent answers from parametric memory (training data), you may promise a $25 credit that Finance never approved.

If you dump the entire policy wiki into the prompt every turn, you will blow the **context window**, raise cost, and still miss the clause that matters.

---

## Know these

| Concept | Lifetime | Meridian example |
|---------|----------|------------------|
| **Transcript / session history** | This conversation | Maya’s last 8 chat turns |
| **State** | This session/run | `active_order_id`, `order_findings` |
| **Long-term memory** | Across sessions | “Maya prefers SMS” |
| **Artifact** | Named blob in session | `order-MC-1048292.json` |
| **RAG** | Retrieve → reason (→ cite) | Pull late-delivery policy chunk |
| **Grounding** | Tie claims to evidence | Policy id + section + tool result |
| **Compaction / summarization** | Shrink history to keep room | Dispute thread older than N turns → summary |
| **Token budget** | Every token must earn its place | Don’t paste full OMS JSON when an id + 5 fields suffice |

### When each wins

```
Need durable preference across weeks?     → memory
Need control-flow facts this ticket?      → state
Need exact policy language?               → RAG / retrieve tool
Need audit blob?                          → artifact
Need conversational cohesion?             → transcript (carefully)
```

---

## Task 1 — Measure what you are stuffing into context

### Why

You cannot budget tokens you refuse to count.

### Do this

Create `project/meridian_ops/tools/token_budget.py`:

```python
from __future__ import annotations

import json
from typing import Any


def estimate_tokens(text: str) -> int:
    """Rough token estimate for lab budgeting (~4 chars/token).

    Not a billing-grade tokenizer — good enough for teaching tradeoffs.
    """
    if not text:
        return 0
    return max(1, len(text) // 4)


def budget_report(parts: dict[str, str], limit: int = 8000) -> dict[str, Any]:
    """Return per-part estimates and whether the bundle fits a soft limit."""
    items = []
    total = 0
    for name, text in parts.items():
        toks = estimate_tokens(text)
        total += toks
        items.append({"name": name, "chars": len(text), "est_tokens": toks})
    return {
        "limit": limit,
        "total_est_tokens": total,
        "fits": total <= limit,
        "parts": sorted(items, key=lambda x: x["est_tokens"], reverse=True),
    }


def slim_order(order: dict[str, Any]) -> dict[str, Any]:
    """Keep only fields OrderOps usually needs in-prompt."""
    keys = [
        "order_id",
        "lifecycle",
        "promised_window_local",
        "delivered_at_local",
        "pod_photo_present",
        "order_total_usd",
    ]
    return {k: order.get(k) for k in keys if k in order or k.endswith("usd")}
```

Test:

```python
from meridian_ops.tools.token_budget import budget_report, slim_order


def test_slim_order_removes_noise():
    raw = {
        "order_id": "MC-1",
        "lifecycle": "delivered",
        "line_count": 14,
        "shipping_address_city": "Austin",
        "pod_photo_present": False,
    }
    slim = slim_order(raw)
    assert "line_count" not in slim
    assert slim["lifecycle"] == "delivered"


def test_budget_flags_overflow():
    report = budget_report({"policy": "x" * 50000}, limit=1000)
    assert report["fits"] is False
```

Run pytest.

### Expect

Tests pass. You now have a lever for “every token earns its place.”

---

## Task 2 — Author Meridian policy fixtures (knowledge corpus)

### Why

RAG without a corpus is cosplay. Keep policies small, versioned, and boring.

### Do this

Create `project/meridian_ops/fixtures/policies/`:

`late_delivery_credits.md`:

```markdown
# POL-DELIVERY-01 — Late grocery delivery credits
Version: 2026-07-01
Owner: CX Policy

## Eligibility
- Applies to Meridian same-day grocery delivery (not BOPIS pickup).
- Delivery must arrive more than 60 minutes after the end of the promised window.

## Credit amounts
- 15–60 minutes late: apology only (no automatic credit).
- 61–120 minutes late: $10 courtesy credit.
- >120 minutes late: $25 courtesy credit.

## Exclusions
- Customer-caused delays (wrong address, unreachable).
- Weather emergency banner declared by Ops.
- Third-party partner outages already covered by partner compensation.

## Agent rules
- Do not promise credits above this schedule.
- Credits ≥ $25 require supervisor HITL if stacking with a refund on the same order.
```

`refunds_damaged_items.md`:

```markdown
# POL-REFUND-04 — Damaged or melted items
Version: 2026-06-15
Owner: CX Policy

## Eligibility
- Item arrived damaged, melted, or unsafe.
- Report within 48 hours of delivery timestamp.

## Remedies
- Replacement if ATP allows (preferred).
- Refund of impacted line items otherwise.
- Full-order refund only if >50% of line items impacted OR food safety issue affecting the order.

## Agent rules
- Never auto-approve full-order refunds over $75 (HITL).
- Cite this policy id when recommending a remedy.
```

### Expect

Two versioned policy files with **ids** you can cite (`POL-DELIVERY-01`, `POL-REFUND-04`).

---

## Task 3 — Build a retrieve tool (RAG pattern without the mysticism)

### Why

For this curriculum, a simple keyword/tag retriever teaches the agent loop: **retrieve → reason → cite → (optionally) act**. You can swap in embeddings later without changing the tool contract.

### Do this

`project/meridian_ops/tools/policy_rag.py`:

```python
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from meridian_ops.tools.logging_utils import log_tool_event, new_correlation_id
from meridian_ops.tools.token_budget import estimate_tokens

_POLICY_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "policies"


def _index() -> list[dict[str, str]]:
    docs = []
    for path in sorted(_POLICY_DIR.glob("*.md")):
        text = path.read_text()
        docs.append({"path": path.name, "text": text})
    return docs


def retrieve_policy(query: str, top_k: int = 2) -> dict[str, Any]:
    """Retrieve Meridian policy documents relevant to a query.

    Args:
        query: Natural language question or ticket text.
        top_k: Max documents to return.
    """
    corr = new_correlation_id()
    log_tool_event(tool="retrieve_policy", correlation_id=corr, query=query)
    tokens = set(re.findall(r"[a-z0-9]+", query.lower()))
    scored: list[tuple[int, dict[str, str]]] = []
    for doc in _index():
        hay = doc["text"].lower()
        score = sum(1 for t in tokens if t in hay)
        # light boosts
        if "late" in tokens and "late" in hay:
            score += 3
        if "refund" in tokens and "refund" in hay:
            score += 3
        if "melt" in tokens or "damaged" in tokens:
            if "melted" in hay or "damaged" in hay:
                score += 3
        scored.append((score, doc))

    scored.sort(key=lambda x: x[0], reverse=True)
    picked = [doc for score, doc in scored if score > 0][:top_k]
    if not picked:
        return {
            "status": "error",
            "error_code": "NO_POLICY_HIT",
            "correlation_id": corr,
            "message": "No policy documents matched; do not invent policy.",
        }

    return {
        "status": "success",
        "correlation_id": corr,
        "documents": [
            {
                "path": d["path"],
                "est_tokens": estimate_tokens(d["text"]),
                "text": d["text"],
            }
            for d in picked
        ],
    }
```

Tests:

```python
from meridian_ops.tools.policy_rag import retrieve_policy


def test_late_delivery_query_hits_delivery_policy():
    out = retrieve_policy("late grocery delivery credits")
    assert out["status"] == "success"
    paths = [d["path"] for d in out["documents"]]
    assert "late_delivery_credits.md" in paths


def test_melted_items_hits_refund_policy():
    out = retrieve_policy("melted dairy full refund")
    paths = [d["path"] for d in out["documents"]]
    assert "refunds_damaged_items.md" in paths
```

### Expect

Retriever returns the right docs; estimates tokens per doc.

> **Watch out:** If retrieve returns `NO_POLICY_HIT`, the agent must say it does not know — not “usually stores offer $50.”

---

## Task 4 — Policy agent + citation requirement

### Why

RAG without citation discipline becomes fancy hallucination.

### Do this

Create `project/meridian_policy_agent/` with:

```python
from google.adk.agents.llm_agent import Agent
from meridian_ops.tools.policy_rag import retrieve_policy

root_agent = Agent(
    name="meridian_policy_agent",
    model="gemini-2.5-flash",
    description="Answers Meridian CX policy questions with citations.",
    instruction="""
You are Meridian Policy Assistant.

Rules:
- You MUST call retrieve_policy before stating any policy rule.
- Cite policy id (e.g., POL-DELIVERY-01) and version date in the answer.
- If retrieve_policy errors, say you cannot find a policy — do not improvise.
- Out of scope: executing refunds or inventory changes (explain remedy only).
- Keep quotes short; prefer bullet paraphrase + citation.
""".strip(),
    tools=[retrieve_policy],
)
```

In `adk web`, ask:

```
What's Meridian's policy on late grocery delivery credits?
```

Then ask a second turn:

```
Can I stack that with a full refund on the same order?
```

### Expect

- First answer cites `POL-DELIVERY-01` and the dollar schedule  
- Second answer retrieves/refers to stacking/HITL language — not a confident “sure!”  

Record the trajectory note in `project/meridian_ops/decisions/06-context-budget.md`.

---

## Task 5 — Compaction strategy for long disputes

### Why

A 40-turn melted-grocery dispute will drown the model. You need an intentional compaction plan.

### Do this

Write a function + tests in `token_budget.py` (or `compaction.py`):

```python
def compact_transcript(turns: list[dict[str, str]], keep_last: int = 4) -> dict[str, Any]:
    """Keep the last N turns verbatim; summarize older turns as bullet facts.

    Each turn: {"role": "user"|"agent", "text": str}
    """
    if len(turns) <= keep_last:
        return {"mode": "verbatim", "turns": turns, "summary": None}

    older = turns[:-keep_last]
    recent = turns[-keep_last:]
    # Lab summarizer: deterministic extraction of order-like tokens / money
    joined = " ".join(t["text"] for t in older)
    order_ids = sorted(set(re.findall(r"MC-\d+", joined)))
    amounts = sorted(set(re.findall(r"\$\d+(?:\.\d+)?", joined)))
    summary = {
        "older_turn_count": len(older),
        "order_ids_mentioned": order_ids,
        "amounts_mentioned": amounts,
        "note": "Older turns compacted; verify against tools before acting.",
    }
    return {"mode": "compacted", "summary": summary, "turns": recent}
```

Add `import re` and a unit test where 10 turns collapse to summary + last 4.

### Expect

Compaction preserves `MC-…` ids and dollar amounts — the facts you must not lose.

> **Tip:** Store the summary in **state** (`dispute_summary`) rather than re-sending giant history forever.

---

## Task 6 — Grounding vs tools vs memory decision table

### Why

SME judgment is choosing the evidence channel.

### Do this

Complete in `06-context-budget.md`:

| Question | Best channel | Why | Failure if wrong |
|----------|--------------|-----|------------------|
| Is MC-1048292 delivered? | | | |
| What’s late credit amount? | | | |
| Does Maya prefer SMS? | | | |
| What did we already try this session? | | | |
| Attach OMS snapshot to case | | | |

Also run `budget_report` comparing:

- full `orders.json` blob in prompt  
- vs `slim_order(get_order(...)["order"])`  

Paste the two totals into the doc.

### Expect

You can show a before/after token estimate for slimming orders.

---

## How it works (deeper dive)

### Multimodal note

If Meridian agents later accept POD photos:

- image bytes → **artifact** or multimodal model input  
- do not base64 a 12MB photo into state  
- still **tool-verify** claims (“photo shows porch”) when policy requires

### Memory services in ADK

ADK can plug memory services (search/load memory tools depending on version). Treat memory like a database:

- write deliberately  
- remember PII rules (Lesson 07)  
- never use memory as a substitute for OMS truth

---

## Common pitfalls / troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Agent invents $50 credit | Skipped retrieve / ignored miss | Harden instruction; test NO_POLICY_HIT path |
| Context overflows | Full wiki + full OMS every turn | Slim + retrieve top_k + compact |
| Wrong policy doc | Weak retriever scoring | Improve keywords; later embeddings |
| Memory vs state confusion | “Remember” language overloaded | Use the Know these table literally |

---

## You are done when

- [ ] Policy fixtures exist with ids/versions  
- [ ] `retrieve_policy` unit tests pass  
- [ ] Policy agent cites `POL-DELIVERY-01` in `adk web`  
- [ ] Compaction test keeps order ids  
- [ ] Budget before/after captured in the decision doc  

---

## Knowledge check

1. Why is policy RAG safer than “the model knows retail policies”?  
2. What belongs in state vs long-term memory for Maya?  
3. What should happen on `NO_POLICY_HIT`?  
4. Why slim OMS payloads?  
5. Give one case where transcript alone is the wrong evidence channel.

### Answers

1. Policies change; retrieval + version citations track *your* corpus.  
2. State: `active_order_id` this ticket. Memory: SMS preference across months.  
3. Refuse to invent; escalate to human / policy owner.  
4. Token cost, noise, and accidental leakage of irrelevant PII fields.  
5. Claiming delivery scans that must come from OMS tools.

---

## Recap

- You separated transcript/state/memory/RAG with Meridian examples.  
- Policy answers are now retrieve→cite.  
- Next: guardrails, HITL refunds, kill switches, and auditability.

---

## Stretch goal

Add embeddings later — but today, add `policy_id` front-matter parsing and return `policy_id` as a first-class field in `retrieve_policy` results for cleaner citations.

---

## Feedback

- Could you explain grounding vs memory to Priya (CX supervisor) in one minute?  
- What tripped you up: retriever scoring, compaction, or token estimates?  
- Note task number + expected vs actual.

---

## Navigate

**← Prev** [Lesson 05 — Multi-agent orchestration](05-multi-agent-orchestration.md)  
**Next →** [Lesson 07 — Reliability, safety, and control](07-reliability-safety-control.md)
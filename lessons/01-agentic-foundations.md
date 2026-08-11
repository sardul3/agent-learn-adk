# Lesson 01 — Agentic foundations (before you touch ADK)

**Level:** Beginner → solid intermediate  
**Time:** ~75–90 minutes  
**Prerequisites:** Comfortable reading Python and JSON; no ADK required yet  
**Lab outcome:** A defended architecture decision for Meridian OrderOps + a ticket classifier you can unit-test

---

## At a glance

You will learn when an **agent** earns its keep versus a script, a workflow, or RAG-only chat — then apply that judgment to real Meridian Commerce tickets.

By the end you can explain, without hand-waving:

- observe → reason → act → observe
- deterministic code vs probabilistic model decisions
- tool design rules that keep agents safe
- state vs memory vs artifacts vs transcript
- why trajectories matter more than pretty final answers

---

## Why this matters

Meridian’s CX leadership wants “an AI agent for customer ops.”

If you treat every ticket as agentic, you will:

- burn tokens on CRUD that a SQL job should own
- authorize refunds the model *sounded* confident about
- create infinite loops when a tool keeps returning “try again”

Your job as the SWE is to **frame the problem** before picking a framework.

---

## Know these

Read this section fully before Task 1. Every later lesson reuses these words.

| Term | Plain English | Meridian example |
|------|---------------|------------------|
| **LLM** | A model that predicts the next tokens of text | Gemini drafting a customer-safe status update |
| **Token** | A chunk of text the model reads/writes; bills and context limits are in tokens | Order JSON + chat history consuming the context window |
| **Context window** | Max tokens the model can see in one call | Too much history → older turns get dropped or summarized |
| **Temperature** | How “spiky” sampling is; higher = more varied | Low temp for refund decisions; higher for marketing copy (not our domain) |
| **Tool calling** | Model emits a structured request to run a function you defined | `get_order(order_id="MC-1048292")` |
| **Hallucination** | Confident false statement | Inventing a delivery scan that never happened |
| **Agent** | Loop that observes, reasons, optionally calls tools, observes results, repeats until done | OrderOps resolving a WISMO ticket |
| **Script** | Fixed code path; no model choosing steps | Nightly loyalty recompute job |
| **Workflow** | Explicit graph/sequence of steps (some may be LLM nodes) | Refund: validate → policy check → HITL → settle |
| **RAG** | Retrieve documents, then answer grounded in them | Pull late-delivery policy before answering Maya |
| **Trajectory** | The full path: messages + tool calls + args + results + stop reason | What you debug in production — not only the final paragraph |
| **HITL** | Human-in-the-loop: approve, edit, escalate, pause/resume | Priya approves refunds over $75 |
| **Idempotent tool** | Safe to retry; same logical request doesn’t double-apply side effects | Refund with idempotency key doesn’t charge twice |
| **State** | Scratchpad for *this* session/run (mutable dict) | `order_id`, `refund_candidate_usd` |
| **Memory** | Longer-lived facts across sessions | “Maya prefers contact by SMS” |
| **Artifact** | Named file/blob produced or consumed | PDF packing slip, CSV of shorted SKUs |
| **Transcript** | The conversation turns themselves | Chat bubbles in `adk web` |

### The agent loop

```
┌──────────┐     ┌──────────┐     ┌──────────┐
│ Observe  │────▶│  Reason  │────▶│   Act    │
│ (user +  │     │  (LLM)   │     │ (tools)  │
│  tool    │◀────│          │◀────│          │
│  results)│     └──────────┘     └──────────┘
└──────────┘
```

You **mix** deterministic code (tools, validators, graphs) with probabilistic decisions (which tool, how to phrase, whether the evidence is enough).

### Decision cheatsheet

| Pattern | Use when… | Meridian example |
|---------|-----------|------------------|
| **Script / job** | Inputs known; steps fixed; no judgment | Loyalty recompute for segment WEST-14 |
| **Workflow (mostly deterministic)** | Order of steps must be guaranteed; LLM optional at nodes | Refund settlement after supervisor approval |
| **RAG-only chat** | Question answered from docs; no side effects | “What’s the late delivery credit policy?” |
| **Single agent + tools** | Multi-step judgment + system reads/writes; one specialty | Order status investigation |
| **Multi-agent** | Distinct skills, prompts, or privilege boundaries | Order vs Inventory vs Refund specialists |

---

## Task 1 — Inventory the Meridian ticket batch

### Why

You need concrete tickets before you can choose architectures. Guessing from vibes is how demos die in production.

### Do this

1. Open the fixture:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
cat project/meridian_ops/fixtures/tickets.json
```

2. Create a working notes file (you will commit this later if you want):

```bash
mkdir -p project/meridian_ops/decisions
```

3. Create `project/meridian_ops/decisions/01-ticket-routing.md` and fill a table with **one row per ticket**:

| ticket_id | Pattern (script / workflow / RAG / single-agent / multi-agent) | Why (one sentence) | Side effects? | HITL? |
|-----------|----------------------------------------------------------------|--------------------|---------------|-------|

### Expect

- All **6** tickets classified
- `TCK-9005` is **not** agentic
- `TCK-9004` mentions HITL (refund dollars)
- `TCK-9006` can be RAG-only **or** agent-with-retrieve-tool — either is fine if your Why is honest

> **Tip:** If two patterns both fit, pick the *simpler* one that still meets safety needs. Complexity is a liability.

> **Watch out:** “Use an agent because leadership asked for AI” is not a Why. Name the *judgment* or *tool orchestration* that requires it.

---

## Task 2 — Build a deterministic ticket classifier (no LLM)

### Why

Before you trust a model to route tickets, write the boring version. It becomes your regression oracle and teaches the observe→act boundary.

### Do this

1. Create the package files:

```bash
mkdir -p project/meridian_ops/tools
touch project/meridian_ops/__init__.py
touch project/meridian_ops/tools/__init__.py
```

2. Add `project/meridian_ops/tools/classify_ticket.py`:

```python
from __future__ import annotations

from enum import Enum
import re


class Route(str, Enum):
    SCRIPT = "script"
    WORKFLOW = "workflow"
    RAG = "rag"
    SINGLE_AGENT = "single_agent"
    MULTI_AGENT = "multi_agent"


_REFUND = re.compile(r"\brefund\b|\bcharged\b|\bmelted\b", re.I)
_INVENTORY = re.compile(r"\bATP\b|\bSKU\b|\bsubstitute\b|\bshorted\b", re.I)
_POLICY = re.compile(r"\bpolicy\b|\bcredit policy\b", re.I)
_BATCH = re.compile(r"\brecompute\b|\bnightly\b|\bsegment\b", re.I)
_SCHEDULE = re.compile(r"\bchange my pickup\b|\breschedule\b", re.I)


def classify_ticket(text: str, channel: str | None = None) -> Route:
    """Classify a Meridian ticket into an execution pattern.

    This is deliberately deterministic. Lesson 05 may replace or wrap it
    with an LLM router — but the labels stay the same.
    """
    if channel == "internal_batch" or _BATCH.search(text):
        return Route.SCRIPT
    if _REFUND.search(text):
        # Refunds need policy + possible human approval → workflow with agent nodes
        return Route.WORKFLOW
    if _INVENTORY.search(text):
        return Route.MULTI_AGENT
    if _POLICY.search(text) and not _REFUND.search(text):
        return Route.RAG
    if _SCHEDULE.search(text):
        return Route.WORKFLOW
    return Route.SINGLE_AGENT
```

3. Add `project/meridian_ops/tests/test_classify_ticket.py`:

```python
import json
from pathlib import Path

from meridian_ops.tools.classify_ticket import Route, classify_ticket

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "tickets.json"


def test_batch_ticket_is_script():
    tickets = json.loads(FIXTURES.read_text())
    batch = next(t for t in tickets if t["ticket_id"] == "TCK-9005")
    assert classify_ticket(batch["text"], batch["channel"]) == Route.SCRIPT


def test_refund_ticket_is_workflow():
    tickets = json.loads(FIXTURES.read_text())
    refund = next(t for t in tickets if t["ticket_id"] == "TCK-9004")
    assert classify_ticket(refund["text"], refund["channel"]) == Route.WORKFLOW


def test_inventory_short_is_multi_agent():
    tickets = json.loads(FIXTURES.read_text())
    inv = next(t for t in tickets if t["ticket_id"] == "TCK-9003")
    assert classify_ticket(inv["text"], inv["channel"]) == Route.MULTI_AGENT


def test_policy_question_is_rag():
    tickets = json.loads(FIXTURES.read_text())
    pol = next(t for t in tickets if t["ticket_id"] == "TCK-9006")
    assert classify_ticket(pol["text"], pol["channel"]) == Route.RAG
```

4. From the repo root, run:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
python -m venv .venv
source .venv/bin/activate
pip install -q pytest
export PYTHONPATH=project
pytest project/meridian_ops/tests/test_classify_ticket.py -v
```

### Expect

```
4 passed
```

If a test fails, fix the classifier or your reading of the ticket — do **not** delete the test.

> **Tip:** This classifier is “dumb on purpose.” Its job is a stable contract. Later the LLM may propose a route; your tests still define what “good” means.

---

## Task 3 — Design three tools on paper-that-runs (schemas)

### Why

Tool design is where agents become reliable or become liability. One job, clear schema, idempotent when writing, fail loudly.

### Do this

Create `project/meridian_ops/tools/tool_contracts.py` and implement **stubs** that validate inputs and return structured errors (no real OMS yet):

```python
from __future__ import annotations

from typing import Any


def get_order(order_id: str) -> dict[str, Any]:
    """Fetch an order by Meridian order id (read-only).

    Args:
        order_id: Order id like MC-1048292.

    Returns:
        status/success payload or status/error with error_code.
    """
    if not order_id or not order_id.startswith("MC-"):
        return {
            "status": "error",
            "error_code": "INVALID_ORDER_ID",
            "message": "order_id must look like MC-#######",
        }
    return {
        "status": "success",
        "order_id": order_id,
        "lifecycle": "out_for_delivery",
        "eta_local": "2026-08-10T18:30:00",
    }


def reserve_substitute(
    order_id: str,
    sku: str,
    substitute_sku: str,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Reserve a substitute SKU for a shorted line (side-effectful).

    Args:
        order_id: Meridian order id.
        sku: Original SKU that is short.
        substitute_sku: Replacement SKU.
        dry_run: If True, validate only — do not write.

    Returns:
        Structured success/error. Retries must use the same logical request.
    """
    if not dry_run and substitute_sku == sku:
        return {
            "status": "error",
            "error_code": "NOOP_SUBSTITUTE",
            "message": "substitute_sku must differ from sku",
        }
    return {
        "status": "success",
        "order_id": order_id,
        "sku": sku,
        "substitute_sku": substitute_sku,
        "dry_run": dry_run,
        "reservation_id": None if dry_run else f"RSV-{order_id}-{substitute_sku}",
    }


def request_refund(
    order_id: str,
    amount_usd: float,
    reason_code: str,
    idempotency_key: str,
) -> dict[str, Any]:
    """Open a refund request (never silently succeeds without a key).

    Args:
        order_id: Meridian order id.
        amount_usd: Dollars to refund; must be > 0.
        reason_code: Stable code like DAMAGED_ITEM.
        idempotency_key: Client-generated key to prevent double refunds.

    Returns:
        success with refund_request_id, or error_code.
    """
    if amount_usd <= 0:
        return {
            "status": "error",
            "error_code": "INVALID_AMOUNT",
            "message": "amount_usd must be > 0",
        }
    if not idempotency_key:
        return {
            "status": "error",
            "error_code": "MISSING_IDEMPOTENCY_KEY",
            "message": "idempotency_key is required for refunds",
        }
    return {
        "status": "success",
        "order_id": order_id,
        "amount_usd": amount_usd,
        "reason_code": reason_code,
        "idempotency_key": idempotency_key,
        "refund_request_id": f"RFQ-{idempotency_key[:8]}",
        "requires_hitl": amount_usd > 75.0,
    }
```

Add tests in `project/meridian_ops/tests/test_tool_contracts.py`:

```python
from meridian_ops.tools.tool_contracts import get_order, request_refund, reserve_substitute


def test_get_order_rejects_bad_id():
    out = get_order("ORDER-1")
    assert out["status"] == "error"
    assert out["error_code"] == "INVALID_ORDER_ID"


def test_refund_requires_idempotency_key():
    out = request_refund("MC-1", 20.0, "DAMAGED_ITEM", "")
    assert out["error_code"] == "MISSING_IDEMPOTENCY_KEY"


def test_refund_over_threshold_flags_hitl():
    out = request_refund("MC-1048277", 214.55, "DAMAGED_ITEM", "maya-214-1")
    assert out["status"] == "success"
    assert out["requires_hitl"] is True


def test_substitute_defaults_to_dry_run():
    out = reserve_substitute("MC-1", "884210", "884299")
    assert out["dry_run"] is True
    assert out["reservation_id"] is None
```

Run:

```bash
export PYTHONPATH=project
pytest project/meridian_ops/tests/test_tool_contracts.py -v
```

### Expect

All tests pass. Notice the pattern:

- **Read tool** fails loudly on bad ids  
- **Write tool** defaults to `dry_run=True`  
- **Money tool** demands an idempotency key and surfaces HITL

> **Watch out:** Returning a bare string like `"oops"` from a tool teaches the model to improvise. Prefer `status` + `error_code` + `message`.

---

## Task 4 — Failure-mode hunt (trajectory thinking)

### Why

SMEs debug trajectories. Demo builders only read the final message.

### Do this

In `project/meridian_ops/decisions/01-ticket-routing.md`, add a section **Failure modes** and map each risk to a Meridian scenario + a mitigation you control in code:

| Failure mode | Meridian scenario | Mitigation you own |
|--------------|-------------------|--------------------|
| Infinite loop | Model keeps calling `get_order` with same id | Max steps / stop condition |
| Tool thrash | Alternating substitute SKUs | Deterministic ranking tool |
| Context bloat | Pasting full OMS JSON every turn | Summarize; store ids in state |
| Silent wrong answer | Invented POD (proof of delivery) scan | Require tool evidence before claiming |
| Unauthorized side effect | $214 refund without Priya | HITL gate + tool-level threshold |

Fill the **Mitigation** column in your own words (not copy-paste only).

### Expect

Every row has a mitigation that is **engineering**, not “prompt the model to be careful” alone.

---

## How it works (deeper dive)

### Deterministic vs probabilistic — the mix

| Layer | Prefer | Why |
|-------|--------|-----|
| AuthZ, money, inventory writes | Deterministic code | Auditors and ledgers hate vibes |
| Choosing which investigation step is next | Probabilistic (LLM) | Language + partial evidence |
| Output shape to the customer | Constrained (schema / template) | CX tone + legal disclaimers |

### Evaluation mindset

A “good” run for `TCK-9001` is not a warm apology. It is a trajectory like:

1. `get_order(MC-1048292)`  
2. `get_delivery_events(MC-1048292)`  
3. Decide missing POD → open case / offer steps  
4. Stop with citations to tool results  

If step 2 never happened, the prose is untrusted — even if it sounds perfect.

---

## Common pitfalls / troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `ModuleNotFoundError: meridian_ops` | `PYTHONPATH` not set | `export PYTHONPATH=project` from repo root |
| Classifier marks refund as `single_agent` | Regex too weak | Extend `_REFUND`; keep tests green |
| You want to call Gemini already | Eager framework energy | Finish Task 4; Lesson 02 installs ADK |
| Decision doc says “multi-agent” for everything | Overfitting to the cool pattern | Re-read the cheatsheet; prefer simpler |

---

## You are done when

- [ ] `01-ticket-routing.md` has 6 ticket rows + failure-mode table
- [ ] `pytest` for classify + tool contracts is green
- [ ] You can explain state vs memory vs artifact vs transcript with Meridian examples
- [ ] You can defend why `TCK-9005` must not be an agent

---

## Knowledge check

Answer before peeking. Prefer writing answers in your decision doc.

1. Why is `TCK-9005` a script, not an agent?
2. What does **idempotent** mean for `request_refund`?
3. Name one thing that belongs in **state** vs one that belongs in an **artifact**.
4. Why do trajectories matter more than final prose for Meridian refunds?
5. Give one case where RAG-only is enough — and one where RAG alone is dangerous.

### Answers

1. Steps and inputs are known (batch recompute); no tool-judgment loop; an agent adds cost and nondeterminism with no upside.  
2. Retries with the same `idempotency_key` must not create a second payout.  
3. State: `order_id` / `requires_hitl`. Artifact: packing-slip PDF or shorted-SKU CSV.  
4. Finance and CX care whether policy tools ran and whether HITL fired — not whether the goodbye was friendly.  
5. Enough: policy FAQ with no side effects. Dangerous: answering “we refunded you” from a policy doc without calling payments.

---

## Recap

- You framed Meridian tickets into script / workflow / RAG / agent patterns.  
- You built deterministic classifier + tool contracts tests — the backbone under future LLM routing.  
- Next: install ADK and run a real Order Status agent in the developer loop.

---

## Stretch goal

Extend `classify_ticket` to return a `dataclass` with `route`, `suggested_tools: list[str]`, and `requires_hitl: bool`. Update tests. Do **not** call an LLM yet.

---

## Feedback

- Could you redo the decision table from memory for a new ticket about “driver never arrived”?
- What tripped you up: vocabulary, pytest pathing, or the agent-vs-workflow boundary?
- Note the **task number**, what you expected, and what happened — that signal improves the next revision of this lesson.

---

## Navigate

**Next →** [Lesson 02 — ADK environment & developer loop](02-adk-environment.md)  
**Project brief:** [Meridian northstar](../docs/meridian-northstar.md)
# Lesson 04 — Tools deep mastery

**Level:** Intermediate → advanced  
**Time:** ~90–110 minutes  
**Prerequisites:** Lessons 01–03  
**Lab outcome:** A hardened Meridian tool belt (OMS + ATP + refund request) with validation, dry-run, timeouts, and structured errors — unit-tested without an LLM

---

## At a glance

Tools are the agent’s hands. This lesson makes those hands safe enough for retail ops:

- Sync vs async tools
- Read-only vs side-effectful tools
- Validation, timeouts, retries, partial failure
- Composition patterns (planner calls A then B)
- External systems (REST-shaped stubs today)
- Least privilege, confirmations, dry-run
- Structured logs + correlation IDs inside tools

---

## Why this matters

Priya’s nightmare:

> Agent “refunded” $214 twice because the model retried after a gateway timeout.

That is not an LLM problem first — it is a **tool contract** problem. Meridian will judge your tools harder than your prose.

---

## Know these

| Term | Meaning |
|------|---------|
| **Read-only tool** | No durable side effects (GET order, GET ATP) |
| **Side-effectful tool** | Writes/charges/reserves/deletes |
| **Dry-run** | Validate + preview without committing |
| **Idempotency key** | Caller-supplied token so retries don’t double-apply |
| **Partial failure** | Multi-step tool where step 1 worked and step 2 failed |
| **Least privilege** | Tool can only do what its role needs |
| **Correlation ID** | ID tying logs across tool → OMS → agent run |
| **Timeout** | Max wait before failing loudly |
| **Retry** | Re-attempt *safe* operations; never blindly retry non-idempotent writes |

### Tool quality bar (Meridian)

```
one job
  → typed inputs + docstring schema
    → validate early
      → fail with error_code
        → structured logs
          → dry-run / idempotency for writes
```

---

## Task 1 — Split the tool belt into modules

### Why

One mega-`tools.py` becomes untestable. OMS, ATP, and Payments have different failure modes.

### Do this

Ensure these modules exist under `project/meridian_ops/tools/`:

| Module | Responsibility |
|--------|----------------|
| `oms.py` | Order reads (from Lesson 03) |
| `atp.py` | Available-to-promise / inventory reads + substitute reserve |
| `payments.py` | Refund requests (not settlements) |
| `logging_utils.py` | Correlation-id helpers |

Create `logging_utils.py`:

```python
from __future__ import annotations

import json
import sys
import time
import uuid
from typing import Any


def new_correlation_id() -> str:
    return f"corr-{uuid.uuid4().hex[:12]}"


def log_tool_event(
    *,
    tool: str,
    correlation_id: str,
    level: str = "INFO",
    **fields: Any,
) -> None:
    record = {
        "ts": time.time(),
        "level": level,
        "tool": tool,
        "correlation_id": correlation_id,
        **fields,
    }
    print(json.dumps(record), file=sys.stderr)
```

### Expect

Files are importable:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
source .venv/bin/activate
export PYTHONPATH=project
python -c "from meridian_ops.tools.logging_utils import new_correlation_id; print(new_correlation_id())"
```

---

## Task 2 — ATP tool: async read + validation

### Why

Inventory lookups often hit networked services. Async tools keep the worker from blocking when you later compose many calls. Even with fixtures, practice the shape.

### Do this

Create `project/meridian_ops/fixtures/inventory.json`:

```json
{
  "884210": {"sku": "884210", "name": "Organic Milk 1gal", "atp_qty": 0, "store_id": "ST-221"},
  "884299": {"sku": "884299", "name": "Organic Milk 1gal - Banner Alt", "atp_qty": 7, "store_id": "ST-221"},
  "552100": {"sku": "552100", "name": "Sourdough Loaf", "atp_qty": 12, "store_id": "ST-221"}
}
```

Create `project/meridian_ops/tools/atp.py`:

```python
from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from meridian_ops.tools.logging_utils import log_tool_event, new_correlation_id

_INV = Path(__file__).resolve().parents[1] / "fixtures" / "inventory.json"


def _load() -> dict[str, dict[str, Any]]:
    return json.loads(_INV.read_text())


async def get_atp(sku: str, store_id: str = "ST-221") -> dict[str, Any]:
    """Get available-to-promise quantity for a SKU at a store.

    Args:
        sku: Meridian SKU, digits only in this lab.
        store_id: Store id like ST-221.
    """
    corr = new_correlation_id()
    log_tool_event(tool="get_atp", correlation_id=corr, sku=sku, store_id=store_id)
    if not sku.isdigit():
        log_tool_event(
            tool="get_atp",
            correlation_id=corr,
            level="WARN",
            error_code="INVALID_SKU",
        )
        return {
            "status": "error",
            "error_code": "INVALID_SKU",
            "message": "sku must be numeric",
            "correlation_id": corr,
        }

    await asyncio.sleep(0.05)  # stand-in for network I/O
    row = _load().get(sku)
    if not row or row.get("store_id") != store_id:
        return {
            "status": "error",
            "error_code": "SKU_NOT_FOUND",
            "message": f"No ATP row for {sku} at {store_id}",
            "correlation_id": corr,
        }
    return {
        "status": "success",
        "correlation_id": corr,
        "sku": sku,
        "store_id": store_id,
        "atp_qty": row["atp_qty"],
        "name": row["name"],
    }


async def reserve_substitute(
    order_id: str,
    sku: str,
    substitute_sku: str,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Preview or commit a substitute reservation for a shorted line.

    Args:
        order_id: Order id MC-...
        sku: Original SKU.
        substitute_sku: Replacement SKU.
        dry_run: When True (default), do not commit a reservation.
    """
    corr = new_correlation_id()
    if substitute_sku == sku:
        return {
            "status": "error",
            "error_code": "NOOP_SUBSTITUTE",
            "message": "substitute_sku must differ",
            "correlation_id": corr,
        }

    original = await get_atp(sku)
    replacement = await get_atp(substitute_sku)
    if original.get("status") != "success" or replacement.get("status") != "success":
        return {
            "status": "error",
            "error_code": "ATP_LOOKUP_FAILED",
            "message": "Could not load ATP for sku/substitute",
            "correlation_id": corr,
            "original": original,
            "replacement": replacement,
        }
    if replacement["atp_qty"] <= 0:
        return {
            "status": "error",
            "error_code": "SUBSTITUTE_OUT_OF_STOCK",
            "message": "substitute has atp_qty <= 0",
            "correlation_id": corr,
        }

    reservation_id = None if dry_run else f"RSV-{order_id}-{substitute_sku}"
    log_tool_event(
        tool="reserve_substitute",
        correlation_id=corr,
        dry_run=dry_run,
        reservation_id=reservation_id,
    )
    return {
        "status": "success",
        "correlation_id": corr,
        "order_id": order_id,
        "sku": sku,
        "substitute_sku": substitute_sku,
        "dry_run": dry_run,
        "reservation_id": reservation_id,
        "substitute_atp_qty": replacement["atp_qty"],
    }
```

Tests — `project/meridian_ops/tests/test_atp.py`:

```python
import pytest

from meridian_ops.tools.atp import get_atp, reserve_substitute


@pytest.mark.asyncio
async def test_get_atp_organic_milk_is_zero():
    out = await get_atp("884210")
    assert out["status"] == "success"
    assert out["atp_qty"] == 0


@pytest.mark.asyncio
async def test_reserve_defaults_dry_run():
    out = await reserve_substitute("MC-1048310", "884210", "884299")
    assert out["dry_run"] is True
    assert out["reservation_id"] is None


@pytest.mark.asyncio
async def test_reserve_commit_returns_id():
    out = await reserve_substitute(
        "MC-1048310", "884210", "884299", dry_run=False
    )
    assert out["reservation_id"] == "RSV-MC-1048310-884299"
```

Install pytest-asyncio if needed and run:

```bash
pip install -q pytest pytest-asyncio
export PYTHONPATH=project
pytest project/meridian_ops/tests/test_atp.py -v
```

### Expect

All ATP tests green. Stderr shows JSON log lines with `correlation_id`.

> **Tip:** ADK accepts sync and async tools. Use async when the real I/O is async; don’t pretend sync OMS is async without a reason.

---

## Task 3 — Payments tool: side effects, idempotency, threshold

### Why

Money tools are where “clever agents” become finance incidents.

### Do this

Create `project/meridian_ops/tools/payments.py`:

```python
from __future__ import annotations

from typing import Any

from meridian_ops.tools.logging_utils import log_tool_event, new_correlation_id

# Process-local idempotency store for the lab. Lesson 09 moves this to Redis.
_IDEMPOTENCY: dict[str, dict[str, Any]] = {}

HITL_THRESHOLD_USD = 75.0


def request_refund(
    order_id: str,
    amount_usd: float,
    reason_code: str,
    idempotency_key: str,
    *,
    confirm: bool = False,
) -> dict[str, Any]:
    """Create a refund *request* (not a settlement).

    Args:
        order_id: Meridian order id.
        amount_usd: Amount in USD; must be > 0.
        reason_code: Stable code such as DAMAGED_ITEM or MISSING_DELIVERY.
        idempotency_key: Required key to make retries safe.
        confirm: Must be True to open a request; False returns a preview only.
    """
    corr = new_correlation_id()
    log_tool_event(
        tool="request_refund",
        correlation_id=corr,
        order_id=order_id,
        amount_usd=amount_usd,
        confirm=confirm,
    )

    if amount_usd <= 0:
        return {
            "status": "error",
            "error_code": "INVALID_AMOUNT",
            "correlation_id": corr,
        }
    if not idempotency_key:
        return {
            "status": "error",
            "error_code": "MISSING_IDEMPOTENCY_KEY",
            "correlation_id": corr,
        }
    if not reason_code:
        return {
            "status": "error",
            "error_code": "MISSING_REASON_CODE",
            "correlation_id": corr,
        }

    if not confirm:
        return {
            "status": "success",
            "preview": True,
            "order_id": order_id,
            "amount_usd": amount_usd,
            "reason_code": reason_code,
            "requires_hitl": amount_usd > HITL_THRESHOLD_USD,
            "correlation_id": corr,
            "message": "Pass confirm=true to open the refund request",
        }

    if idempotency_key in _IDEMPOTENCY:
        prior = _IDEMPOTENCY[idempotency_key]
        log_tool_event(
            tool="request_refund",
            correlation_id=corr,
            level="INFO",
            replay=True,
            refund_request_id=prior["refund_request_id"],
        )
        return {**prior, "replayed": True, "correlation_id": corr}

    requires_hitl = amount_usd > HITL_THRESHOLD_USD
    payload = {
        "status": "success",
        "preview": False,
        "order_id": order_id,
        "amount_usd": amount_usd,
        "reason_code": reason_code,
        "idempotency_key": idempotency_key,
        "refund_request_id": f"RFQ-{idempotency_key[:8]}",
        "requires_hitl": requires_hitl,
        "request_status": "PENDING_HITL" if requires_hitl else "AUTO_APPROVED_LAB_ONLY",
    }
    _IDEMPOTENCY[idempotency_key] = payload
    return {**payload, "correlation_id": corr}
```

Tests — `project/meridian_ops/tests/test_payments.py`:

```python
from meridian_ops.tools.payments import request_refund


def test_preview_does_not_persist():
    out = request_refund("MC-1048277", 214.55, "DAMAGED_ITEM", "k1", confirm=False)
    assert out["preview"] is True
    assert out["requires_hitl"] is True


def test_confirm_is_idempotent():
    a = request_refund("MC-1048277", 214.55, "DAMAGED_ITEM", "maya-214", confirm=True)
    b = request_refund("MC-1048277", 214.55, "DAMAGED_ITEM", "maya-214", confirm=True)
    assert a["refund_request_id"] == b["refund_request_id"]
    assert b.get("replayed") is True


def test_missing_key_fails_loud():
    out = request_refund("MC-1048277", 10.0, "DAMAGED_ITEM", "", confirm=True)
    assert out["error_code"] == "MISSING_IDEMPOTENCY_KEY"
```

Run pytest for payments.

### Expect

Idempotent replay returns the same `refund_request_id`. Preview never sets `request_status`.

> **Watch out:** In production, `AUTO_APPROVED_LAB_ONLY` would call a settlement API under policy. Here it is a label so you remember Lesson 07 still owns HITL UX.

---

## Task 4 — Composition: inventory exception helper (deterministic)

### Why

Sometimes the “planner” should not freestyle A→B. Encode stable multi-step reads in one composed function; let the LLM decide *whether* to call it.

### Do this

Add to `atp.py`:

```python
async def suggest_substitute_for_short(
    order_id: str,
    sku: str,
    candidate_skus: list[str],
) -> dict[str, Any]:
    """Read ATP for original + candidates; preview-reserve the first in-stock alt.

    Args:
        order_id: Order needing a substitute.
        sku: Shorted SKU.
        candidate_skus: Ranked candidate SKUs.
    """
    corr = new_correlation_id()
    original = await get_atp(sku)
    if original.get("status") != "success":
        return {**original, "correlation_id": corr}
    if original["atp_qty"] > 0:
        return {
            "status": "success",
            "correlation_id": corr,
            "action": "NO_SUBSTITUTE_NEEDED",
            "original": original,
        }

    attempts: list[dict[str, Any]] = []
    for candidate in candidate_skus:
        preview = await reserve_substitute(order_id, sku, candidate, dry_run=True)
        attempts.append(preview)
        if preview.get("status") == "success":
            return {
                "status": "success",
                "correlation_id": corr,
                "action": "PREVIEW_RESERVE",
                "chosen_substitute": candidate,
                "preview": preview,
                "attempts": attempts,
            }

    return {
        "status": "error",
        "error_code": "NO_VIABLE_SUBSTITUTE",
        "correlation_id": corr,
        "attempts": attempts,
    }
```

Test with candidates `["552100", "884299"]` for shorted `884210` — expect choose `884299` if you rank it correctly (put `884299` first, or put bread first and assert it skips out-of-stock / wrong outcomes carefully).

Recommended test:

```python
@pytest.mark.asyncio
async def test_suggest_picks_first_viable():
    out = await suggest_substitute_for_short(
        "MC-1048310",
        "884210",
        ["884299", "552100"],
    )
    assert out["chosen_substitute"] == "884299"
    assert out["preview"]["dry_run"] is True
```

### Expect

Composed tool returns ranked attempt evidence — great for trajectories and CX explanations (“bread skipped because…” if you reorder candidates).

---

## Task 5 — Wire tools into an Inventory Exception agent

### Why

Prove the tools work under ADK, not only under pytest.

### Do this

```bash
cd /Users/alishaghatane/dev/agent-learn-sme/project
adk create meridian_inventory
```

Set `agent.py` roughly as:

```python
from google.adk.agents.llm_agent import Agent
from meridian_ops.tools.atp import get_atp, reserve_substitute, suggest_substitute_for_short
from meridian_ops.tools.oms import get_order

root_agent = Agent(
    name="meridian_inventory",
    model="gemini-2.5-flash",
    description="Handles Meridian inventory shorts and substitute previews.",
    instruction="""
You are Meridian Inventory Exception agent.

Rules:
- Use get_order when an order_id is present.
- Use get_atp / suggest_substitute_for_short for shortages.
- NEVER call reserve_substitute with dry_run=false unless the user explicitly confirms.
- Default to dry_run previews.
- Failures must quote error_code from tools.
""".strip(),
    tools=[get_order, get_atp, reserve_substitute, suggest_substitute_for_short],
)
```

Run `adk web` from `project/` and prompt:

```
Order MC-1048310 is short organic milk SKU 884210. Candidate substitutes 884299 then 552100. Preview only.
```

(If `MC-1048310` is missing from `orders.json`, add a minimal ready_for_pickup stub — inventory labs care about SKU more than lifecycle.)

### Expect

- Trajectory shows ATP reads / suggest tool  
- Any reserve is `dry_run=true`  
- Response cites `correlation_id` or `error_code` when asked

> **Tip:** Least privilege: this agent should **not** import `request_refund`.

---

## Task 6 — Safety checklist doc

### Why

SMEs leave durable judgment, not only code.

### Do this

Write `project/meridian_ops/decisions/04-tool-safety.md` with a table for every tool you own:

| Tool | Read/Write | AuthZ notes | Dry-run / confirm | Idempotency | Timeout strategy | Retry safe? |
|------|------------|-------------|-------------------|-------------|------------------|-------------|
| get_order | read | … | n/a | n/a | … | yes |
| … | | | | | | |

### Expect

At least OMS + ATP + refund rows completed honestly.

---

## How it works (deeper dive)

### Retries

| Situation | Retry? |
|-----------|--------|
| Read timeout on `get_atp` | Yes, bounded backoff |
| Unknown outcome on `request_refund` after confirm | Retry **only** with same idempotency key |
| Validation error `INVALID_SKU` | No — fix inputs |
| Partial failure in a multi-write saga | Compensate / explicit repair tool — don’t pretend success |

### External systems later

Your fixtures stand in for:

- OMS REST  
- WMS / ATP service  
- Payments  
- Browser tools / MCP servers (Lesson 10+)  

The contract style stays the same when the transport changes.

---

## Common pitfalls / troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `pytest` skips async tests | Missing pytest-asyncio | Install; use `@pytest.mark.asyncio` |
| Double refund ids differ | New idempotency key each retry | Persist key in session state |
| Agent commits substitute | Instruction didn’t forbid `dry_run=false` | Hard-default dry_run; confirm flag |
| Logs missing | Printing to stdout swallowed | Log to stderr as in `logging_utils` |

---

## You are done when

- [ ] ATP + payments unit tests pass without any LLM  
- [ ] Inventory agent previews substitutes in `adk web`  
- [ ] Refund tool proves idempotent replay  
- [ ] `04-tool-safety.md` filled  

---

## Knowledge check

1. Why default `dry_run=True` on `reserve_substitute`?  
2. What makes a refund retry safe?  
3. When is a composed tool better than asking the LLM to chain A→B?  
4. Why keep refunds out of the inventory agent?  
5. What belongs in a tool error payload?

### Answers

1. Prevent accidental inventory writes while the model explores.  
2. Stable `idempotency_key` + server-side dedupe store.  
3. When the sequence is stable, must be evidenced, or is easy to thrash.  
4. Least privilege / blast-radius separation.  
5. `status`, `error_code`, human `message`, `correlation_id` — not stack traces to the model/customer.

---

## Recap

- Tools gained contracts, async reads, dry-run writes, and idempotent money requests.  
- You tested them without the LLM — SME move.  
- Next: multi-agent orchestration so Order, Inventory, and Refund stop living as one mega-agent.

---

## Stretch goal

Add a `timeout_s` parameter to `get_atp` and simulate a slow path with `asyncio.wait_for`. Return `error_code=TIMEOUT`. Test it.

---

## Feedback

- Could you implement a new read-only `get_delivery_events` tool to the same bar without looking at ATP?  
- What tripped you up: async tests, idempotency, or agent wiring?  
- Note task number + expected vs actual.

---

## Navigate

**← Prev** [Lesson 03 — Core building blocks](03-core-building-blocks.md)  
**Next →** [Lesson 05 — Multi-agent orchestration](05-multi-agent-orchestration.md)
# Lesson 04 — Tools deep mastery

**Level:** Intermediate → advanced  
**Time:** ~100–120 minutes  
**Prerequisites:** Lessons 01–03 (`get_order` in `oms.py`, Order Status agent running)  
**Lab outcome:** A hardened Meridian tool belt (OMS + ATP + refund request) with validation, dry-run, and structured logs — unit-tested without an LLM

---

## At a glance

Lesson 03 gave the agent **hands** (`get_order`) and a **punch clock** (the callback). This lesson makes those hands safe enough for a grocery ops floor:

- Read-only tools vs tools that change the world
- Why validation lives in Python, not in the instruction
- Dry-run (preview) before a write
- Idempotency so a retry does not refund twice
- Correlation IDs so Priya can stitch one ticket across logs
- A composed helper when the step order must not be guessed

You will prove most of this with `pytest`. The model is not invited until Task 5.

---

## Why this matters

Maya’s organic milk arrived melted. Ticket `TCK-9004`. Amount: **$214.55**.

The agent called `request_refund`. The payments gateway timed out. The model did what models do: it tried again.

Finance sees **two** refund requests for the same carton of milk.

Priya (CX supervisor) asks:

> “Did we refund Maya twice? Show me the trail.”

If your only answer is “the model sounded sure,” you do not have a product. You have a finance incident.

That is not an LLM problem first. It is a **tool contract** problem:

- The write was allowed without a preview.
- The retry used a **new** request id.
- The logs from OMS, inventory, and payments do not share a ticket number.

Today you fix the hands. Lesson 05 will split which agent is allowed to hold which hand.

---

## Know these

Read this table before Task 1. Every later task reuses these words.

| Term | Plain English | Meridian example |
|------|---------------|------------------|
| **Read-only tool** | Looks something up. Does not change a shelf, a card, or a reservation. | `get_order`, `get_atp` |
| **Side-effectful tool** | Changes the world: reserves stock, opens a refund, sends an email. | `reserve_substitute`, `request_refund` |
| **Dry-run** | Do every check, return the preview, **do not commit**. | “Would this substitute work?” without taking milk off the shelf |
| **Confirm** | The extra flag that means “yes, really do it.” | `confirm=True` on a refund request |
| **Idempotency key** | A caller-chosen token. Same key + same intent = same result, even on retry. | `maya-214` so a timeout retry does not open a second refund |
| **Correlation ID** | A unique id stamped on every log line for one tool call. | `corr-a1b2c3d4e5f6` tying ATP + refund logs to Maya’s ticket |
| **Timeout** | Max wait before failing out loud. | ATP service silent for 2s → `TIMEOUT`, not a hang |
| **Retry** | Try again. Safe for reads. Dangerous for writes unless the key is the same. | Re-read ATP: yes. Re-refund with a new key: no |
| **Partial failure** | Step 1 worked, step 2 failed. | Substitute reserved, refund request then errored |
| **Least privilege** | A tool (and an agent) can only do what its job needs. | Inventory agent must not import `request_refund` |
| **HITL** | Human in the loop: a person must approve before the next step. | Priya approves refunds over $75 |
| **ATP** | Available-to-promise: how many units the store can still sell or pick. | Organic milk `884210` at Store `ST-221` has `atp_qty: 0` |
| **SKU** | Stock keeping unit — the barcode-like id for a product. | `884210` = Organic Milk 1gal |

### Picture this: the handbook vs the cash register

The **instruction** is the employee handbook. Devon can skip a page on a busy morning.

A **tool** is the cash register. It will not open the drawer because someone *meant* to scan the milk. It opens when the barcode is valid — or it beeps and shows an error code.

| Approach | Who enforces it? | Can it skip? |
|----------|------------------|--------------|
| Write “never refund twice” in the instruction | The model | Yes — models drop rules under pressure |
| Hope the payments API is lucky | Nobody | Yes |
| Preview + confirm + idempotency key **inside the tool** | Your Python, every call | **No** — that is the point |

### Tool quality bar (Meridian)

```
one job
  → typed inputs + a docstring the model can read
    → validate early (bad SKU never hits the fixture)
      → fail with error_code (not a stack trace)
        → structured logs + correlation_id
          → dry-run / confirm / idempotency for writes
```

---

## Task 1 — A ticket number for every tool call

### Why

Priya pulls three log files for Maya’s ticket:

- OMS says `get_order` ran
- ATP says `get_atp` ran
- Payments says `request_refund` ran

None of the lines share an id. She cannot prove they were the **same** conversation.

At Store 441, every grocery bag gets a paper ticket stapled to the handle. Bag, receipt, and “we forgot the bananas” complaint all carry that number.

A **correlation ID** is that paper ticket for your tools.

You also split the tool belt into modules. OMS, ATP, and payments fail in different ways. One giant `tools.py` is how those three log files become impossible to test.

### Do this

1. Confirm these files already exist from Lesson 03 (they should):

| Path | Job |
|------|-----|
| `project/meridian_ops/tools/oms.py` | Order reads |
| `project/meridian_ops/fixtures/orders.json` | Order fixture |

2. You will add three more modules in this lesson:

| Path | Job |
|------|-----|
| `project/meridian_ops/tools/logging_utils.py` | Mint a correlation id; print one JSON log line |
| `project/meridian_ops/tools/atp.py` | Inventory reads + substitute reserve (Task 2) |
| `project/meridian_ops/tools/payments.py` | Refund *requests*, not settlements (Task 3) |

3. Create `project/meridian_ops/tools/logging_utils.py`. This is ordinary Python — no ADK yet.

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
    print(json.dumps(record, indent=2), file=sys.stderr, flush=True)
```

   What each piece is for:

   - `new_correlation_id()` — mint a short unique string. `uuid4` is random; `hex[:12]` keeps logs readable.
   - The `corr-` prefix makes it obvious in a noisy terminal.
   - `log_tool_event` — one JSON object per event. Priya can grep `corr-…` across files.
   - The `*` in the signature means callers must pass `tool=` and `correlation_id=` **by name**. That prevents `log_tool_event("get_atp", corr)` from silently swapping arguments.
   - `file=sys.stderr` — logs go to the **error** stream, not the function’s return value. The model sees the return dict. Priya sees stderr.
   - `flush=True` — print immediately. Without it, a crash can swallow the last log line still sitting in a buffer.

4. Prove the helper imports. From the **repo root**:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
source .venv/bin/activate
export PYTHONPATH=project
python -c "from meridian_ops.tools.logging_utils import new_correlation_id; print(new_correlation_id())"
```

   - `source .venv/bin/activate` — use this project’s Python, not Homebrew’s.
   - `export PYTHONPATH=project` — tell Python that `import meridian_ops` means `project/meridian_ops`. Without this you get `ModuleNotFoundError`.

### Expect

A line like:

```
corr-a1b2c3d4e5f6
```

The exact hex will differ every run. That is correct: each call gets its own ticket number.

> **Tip:** Later, the FastAPI edge (Lesson 12) can pass in a correlation id from the HTTP header so one id covers the whole request. Today each tool mints its own. Same idea, smaller scope.

> **Watch out:** Spell it `correlation`, not `coorelation`. If you name the function `new_coorelation_id`, Task 2’s import fails during pytest collection — before any test runs.

> **Watch out:** `print(...)` in `log_tool_event` goes to the **terminal**, not the chat bubble. Same rule as the Lesson 03 callback.

---

## Task 2 — ATP: look at the shelf before you promise milk

### Why

Maya’s pickup order `MC-1048310` includes organic milk, SKU `884210`.

Devon (picker at Store `ST-221`) walks the dairy case. The slot is empty. **Available-to-promise is 0.**

If the agent tells Maya “we’ll substitute something” without looking at the shelf, you have invented inventory.

`get_order` (Lesson 03) answers “what did she buy?”  
`get_atp` answers “is it actually on the shelf?”

Those are different systems. OMS is the receipt. ATP is the case in the cooler.

### Picture this: radioing the back room

A real ATP call hits a warehouse service over the network. While Devon waits for the radio, the checkout lane should not freeze.

`async def` is how Python says “I am waiting on I/O; let other work run.” You will `await asyncio.sleep(0.05)` as a stand-in for that radio call. The sleep is fake. The **shape** is real — so when the fixture becomes a REST call, the agent code does not change.

Validation also belongs here, not in the instruction.

| Approach | Who runs it? | What happens if the model passes `"organic milk"`? |
|----------|--------------|-----------------------------------------------------|
| “SKU must be digits” in the instruction | The model | It might still pass the words |
| `if not sku.isdigit()` in `get_atp` | Your Python, every call | `INVALID_SKU` — the fixture is never touched |

### Do this

1. Create `project/meridian_ops/fixtures/inventory.json`. Three products at one store:

```json
{
  "884210": {"sku": "884210", "name": "Organic Milk 1gal", "atp_qty": 0, "store_id": "ST-221"},
  "884299": {"sku": "884299", "name": "Organic Milk 1gal - Banner Alt", "atp_qty": 7, "store_id": "ST-221"},
  "552100": {"sku": "552100", "name": "Sourdough Loaf", "atp_qty": 12, "store_id": "ST-221"}
}
```

   Why these three:

   | SKU | What it is | Why it is in the fixture |
   |-----|------------|--------------------------|
   | `884210` | Maya’s organic milk | `atp_qty: 0` — the short you must detect |
   | `884299` | Store-brand organic milk | Same job, 7 units — a *real* substitute |
   | `552100` | Sourdough | In stock, **wrong product** — a trap if someone picks “whatever has quantity” |

2. Create `project/meridian_ops/tools/atp.py` with the read path first. You will add the reserve function in the next step.

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
```

   Walk the function in order:

   ```
   mint corr id → log the attempt → reject bad SKU
           → wait (fake network) → look up fixture
           → SKU_NOT_FOUND or success with atp_qty
   ```

   - `_INV` — path relative to this file, not your laptop’s current directory. Tests still find the fixture.
   - Validate **before** the sleep. A typo should not wait 50ms.
   - Success and error both return a **dict** with `status` and `correlation_id`. The model never gets a Python exception. Exceptions become stack traces in the trajectory; dicts become something Priya can quote.

3. Prove the read path without pytest yet:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
source .venv/bin/activate
export PYTHONPATH=project
python -c "import asyncio; from meridian_ops.tools.atp import get_atp; print(asyncio.run(get_atp('884210')))"
```

   `asyncio.run(...)` is how you call one `async` function from a normal script. ADK will `await` it for you later. Pytest will too, once you mark the test.

### Expect

A success dict with `"atp_qty": 0` and `"name": "Organic Milk 1gal"`. Stderr shows a JSON log that includes `"tool": "get_atp"` and the same `correlation_id`.

Zero is a valid answer. Empty shelf is not an error. **Missing SKU** is an error.

> **Tip:** ADK accepts both sync and async tools. Keep `get_order` sync — it reads a local file. Make `get_atp` async because the real service is networked. Do not mark everything `async` “for consistency.”

> **Watch out:** `get_atp("organic milk")` must return `INVALID_SKU`, not crash. If it crashes, the model sees a stack trace and may invent a quantity.

---

### Still Task 2 — dry-run before you take milk off the shelf

Devon found the case empty. Banner-alt milk `884299` has 7 units.

If the agent **reserves** those 7 gallons while Maya is still asking “what are my options?”, the last gallons are locked for a chat that might walk away.

**Dry-run** is the hold sticker vs taking the jugs off the shelf.

| `dry_run` | What the tool does | Grocery picture |
|-----------|--------------------|-----------------|
| `True` (default) | Check ATP, return a preview, `reservation_id` is `None` | “Yes, we *could* sub the banner milk” |
| `False` | Same checks, then mint `RSV-…` | “Those gallons are now held for Maya’s order” |

Default must be `True`. The model explores. Exploring must not write.

4. Append this function to `atp.py` (same file, below `get_atp`):

```python
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

   Why this order:

   1. Reject “substitute the milk with the same milk” — that is a no-op, not a save.
   2. Look up **both** SKUs. Nested `original` / `replacement` in the error means Priya can see *which* lookup failed.
   3. Refuse a substitute with `atp_qty <= 0`. Empty shelf is not a substitute.
   4. Only then decide whether to mint `RSV-…`. The id is derived from order + SKU so you can see it in a log without a database. (A real WMS would return its own reservation id.)

5. Create `project/meridian_ops/tests/test_atp.py`. Tests call the tool **directly**. No LLM. If ATP is wrong, you want pytest to fail — not a chat that “sounded fine.”

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

   - `@pytest.mark.asyncio` — this test `await`s. Pytest needs the plugin to know that.
   - Test 1: empty shelf is success with `0`, not an error.
   - Test 2: omitting `dry_run` must preview. If someone later flips the default to `False`, this test is the alarm.
   - Test 3: an explicit commit mints a stable id you can grep.

6. Install the async plugin if needed, then run **only** the ATP file:

```bash
pip install -q pytest pytest-asyncio
export PYTHONPATH=project
pytest project/meridian_ops/tests/test_atp.py -v
```

   - `-q` on pip — quiet install; you still see errors.
   - `-v` on pytest — verbose: print each test name and PASSED/FAILED.

### Expect

```
test_get_atp_organic_milk_is_zero PASSED
test_reserve_defaults_dry_run PASSED
test_reserve_commit_returns_id PASSED
```

Stderr (mixed into pytest output) shows JSON lines with `correlation_id`. That is the paper ticket working.

> **Watch out:** If pytest reports `collected 0 items / 1 error` and `cannot import name 'new_correlation_id'`, Task 1’s function name does not match the import. Fix the spelling; do not change `atp.py` to match a typo.

---

## Task 3 — Refunds: preview, then a key so retries cannot double-pay

### Why

Back to Maya’s melted dairy: **$214.55**.

The happy path in a human store:

1. Cashier keys the amount.
2. Register shows a **preview** (“Refund $214.55 — damaged item”).
3. Manager turns the key (Priya, because it is over $75).
4. The receipt number is written down. If the printer jams and they hit the button again, the register says “already done.”

If you skip step 2, the model refunds while “just checking.”  
If you skip step 4, a gateway timeout becomes two refunds.

**Idempotency** (same key, same result) is the receipt number. The caller picks it (`maya-214`). The tool remembers it. A second call with the same key returns the **same** `refund_request_id` and sets `replayed: True`.

This tool opens a **request**. It does not move money. Settlement is a later lesson. Naming it `request_refund` (not `refund`) is the contract.

### Picture this: the $75 manager key

Meridian policy: refunds over **$75** need Priya. That is HITL — a human in the loop.

The tool does not send Priya a Slack message today. It **labels** the request:

- `requires_hitl: true`
- `request_status: PENDING_HITL`

A label the agent cannot shrug off is better than a sentence in the instruction that says “please escalate.”

```
request_refund(...)
        │
        ▼
  validate amount / key / reason     ← Python, always
        │
        ▼
  confirm=False ──▶ preview only (nothing stored)
        │
  confirm=True
        │
        ▼
  seen this idempotency_key? ──▶ return the old request (replayed)
        │ no
        ▼
  amount > $75? ──▶ PENDING_HITL
        │ else
        ▼
  AUTO_APPROVED_LAB_ONLY   ← a loud name so you do not ship it
```

### Do this

1. Create `project/meridian_ops/tools/payments.py`:

```python
from __future__ import annotations

from typing import Any

from meridian_ops.tools.logging_utils import log_tool_event, new_correlation_id

# Process-local store for the lab. Lesson 09 moves this to Redis.
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

   Four gates, in the order a cashier would use them:

   | Gate | If it fails / is skipped | Grocery picture |
   |------|--------------------------|-----------------|
   | Amount / key / reason | `INVALID_*` error | Register beeps; drawer stays shut |
   | `confirm=False` | Preview; **nothing stored** | Total on the screen, not on the card |
   | Key already seen | Same `refund_request_id`, `replayed: True` | “We already did this receipt” |
   | Amount > $75 | `PENDING_HITL` | Manager key |

   - `_IDEMPOTENCY` is a dict in this Python process. Restart `adk web` and it empties. That is fine for the lab. Production uses Redis (Lesson 09) so two workers share the memory.
   - `confirm` is keyword-only (`*` before it). `request_refund(order, 214, "DAMAGED", "k", True)` would be too easy to pass by accident. You must write `confirm=True`.
   - `AUTO_APPROVED_LAB_ONLY` is an ugly string on purpose. If it shows up in a demo, you remember Lesson 07 still owns the real approval flow.

2. Create `project/meridian_ops/tests/test_payments.py`:

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

   These three tests are the finance incident, written as code:

   - Preview of $214.55 flags HITL and does **not** set `request_status`.
   - Two confirms with `maya-214` share one `refund_request_id`. The second is a replay, not a second refund.
   - An empty key is a loud error — never “just generate a UUID inside the tool.” If the tool mints the key, every retry is a new key, and you are back to double refunds.

3. Run:

```bash
export PYTHONPATH=project
pytest project/meridian_ops/tests/test_payments.py -v
```

### Expect

All three PASSED.

Optional — see the same path in a shell:

```bash
python - <<'PY'
from meridian_ops.tools.payments import request_refund
p = request_refund("MC-1048277", 214.55, "DAMAGED_ITEM", "maya-214", confirm=False)
print("preview", p["preview"], "hitl", p["requires_hitl"])
a = request_refund("MC-1048277", 214.55, "DAMAGED_ITEM", "maya-214", confirm=True)
b = request_refund("MC-1048277", 214.55, "DAMAGED_ITEM", "maya-214", confirm=True)
print(a["refund_request_id"], b["refund_request_id"], b.get("replayed"))
PY
```

You should see `preview True`, `hitl True`, the same `RFQ-maya-214` twice, and `True` for replayed.

> **Tip:** Store the idempotency key in **session state** once the agent has one (Lesson 05). If the model invents a new key every turn, the tool cannot save you.

> **Watch out:** In production, `AUTO_APPROVED_LAB_ONLY` would call a settlement API under policy. Here it is a label. Do not demo this as “the refund already landed.”

---

## Task 4 — Encode the substitute walk so the model cannot pick bread

### Why

Devon’s job when milk is short:

1. Confirm the original SKU is actually at 0.
2. Try candidates **in the order a merchandiser ranked them**.
3. Preview-reserve the first one that is in stock.
4. Stop. Do not keep reserving.

If you leave that walk to the model, it might:

- Skip the original ATP check and substitute a product that was never short
- Try bread (`552100`) first because “it has quantity 12”
- Call `reserve_substitute(..., dry_run=False)` while still exploring

A **composed tool** is a function that runs a stable sequence in Python. The model decides *whether* to call it. It does not decide the order of the inner steps.

That is the same idea as Lesson 03’s callback: **your** code runs the part that must not be optional.

| Approach | Who picks the next SKU? | Can it grab bread for a milk short? |
|----------|-------------------------|-------------------------------------|
| Instruction: “try candidates in order” | The model | Yes |
| Three separate tool calls the model chains | The model | Yes |
| `suggest_substitute_for_short` with a ranked list | Your Python loop | **No** — it walks the list you passed |

### Do this

1. Add this function to `project/meridian_ops/tools/atp.py` (below `reserve_substitute`). Keep the existing imports.

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

   The loop is the merchandiser’s ranked list, not the model’s hunch:

   ```
   original ATP
     │ atp_qty > 0 ──▶ NO_SUBSTITUTE_NEEDED
     │ atp_qty == 0
     ▼
   for each candidate, dry_run=True
     │ first success ──▶ PREVIEW_RESERVE + attempts so far
     │ all fail ──▶ NO_VIABLE_SUBSTITUTE + every attempt
   ```

   - `attempts` is evidence. If you later put bread first, the trajectory shows “bread skipped” instead of a silent wrong pick.
   - Inner `reserve_substitute` is **hard-coded** `dry_run=True`. This helper is allowed to suggest. It is not allowed to commit.

2. Append this test to `project/meridian_ops/tests/test_atp.py`. Add `suggest_substitute_for_short` to the import at the top of the file.

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

   Rank milk-alt **before** bread. The helper should pick `884299` and still be a preview.

   If you reverse the list to `["552100", "884299"]`, it will pick bread — because bread is in stock and first. That is the point of a ranked list: **you** own the ranking, not “whatever has quantity.”

3. Re-run ATP tests:

```bash
export PYTHONPATH=project
pytest project/meridian_ops/tests/test_atp.py -v
```

### Expect

Four PASSED, including `test_suggest_picks_first_viable`.

The result dict includes `attempts`. That list is what you show CX: “we considered banner milk first.”

> **Tip:** Use a composed tool when the sequence is stable, must leave evidence, or is easy for the model to scramble. Let the LLM chain A→B only when the next step truly depends on judgment.

> **Watch out:** Do not add `dry_run=False` as a parameter on `suggest_substitute_for_short` “for convenience.” Convenience is how a suggest tool becomes a write tool.

---

## Task 5 — Wire an Inventory agent that cannot refund

### Why

Pytest proved the tools. Priya still needs to see them under ADK — a trajectory in `adk web`, not only green tests.

This agent handles **shorts and substitute previews**. It must not hold the refund keypad.

At Store 441, Devon can radio the back room. He cannot open the cash office. That is **least privilege**: give an agent the tools for its job, and no others.

If Inventory can call `request_refund`, Lesson 05’s security review fails even when the demo chat looks slick.

### Do this

1. Add a pickup-order stub so the agent can call `get_order` on the same id the ATP tests use. Open `project/meridian_ops/fixtures/orders.json` and add this sibling of the existing orders (watch the commas):

```json
  "MC-1048310": {
    "order_id": "MC-1048310",
    "customer_id": "C-44102",
    "lifecycle": "ready_for_pickup",
    "promised_window_local": "2026-08-12T17:00-19:00",
    "delivered_at_local": null,
    "pod_photo_present": false,
    "shipping_address_city": "Austin",
    "line_count": 3,
    "shorted_sku": "884210"
  }
```

2. From `project/`, scaffold the agent package:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme/project
source ../.venv/bin/activate
export PYTHONPATH=.
adk create meridian_inventory
```

   `adk create <name>` writes a small package (`meridian_inventory/agent.py`) that ADK can load next to `meridian_order_status`.

3. Replace `project/meridian_inventory/agent.py` with:

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

   Look at what is **missing**: `request_refund`. That is the cash-office door, locked.

   The instruction still forbids `dry_run=false`. That is defense in depth. The **default** on the tool is the real lock; the instruction is the handbook.

4. Restart `adk web` from `project/` so it picks up the new package:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme/project
source ../.venv/bin/activate
export PYTHONPATH=.
adk web --port 8000
```

   `--port 8000` keeps the UI on the same URL you already have open.

5. In the UI, select **meridian_inventory** (not Order Status). One chat, this prompt:

```
Order MC-1048310 is short organic milk SKU 884210. Candidate substitutes 884299 then 552100. Preview only.
```

### Expect

- Trajectory shows `get_atp` and/or `suggest_substitute_for_short`
- Any `reserve_substitute` has `dry_run=true` (or the suggest helper’s preview)
- Chosen substitute is `884299`, not bread
- If you ask “what is the correlation id?” the reply quotes a `corr-…` or an `error_code` from a tool dict — not a made-up scan

> **Tip:** If the agent calls `get_order` first, that is fine. OMS answers “what was on the ticket.” ATP answers “what is on the shelf.” Both belong here.

> **Watch out:** Stay on the **inventory** agent. Order Status from Lesson 03 does not have ATP tools; it will invent a substitute from the instruction.

> **Watch out:** Restarting `adk web` starts a fresh in-memory session. That is expected.

---

## Task 6 — Write down who may do what

### Why

Six months from now, someone will add `request_refund` to Inventory “just for the demo.” A table in the repo is the artifact Priya (and a security review) can read without digging through `agent.py`.

This is not a worksheet. It is the same kind of file as `policy.md` in Lesson 03: durable judgment next to the code.

### Do this

1. Create the folder if needed, then `project/meridian_ops/decisions/04-tool-safety.md`.

2. Fill a row for every tool you own. Start from this and complete the blanks honestly:

```markdown
# Lesson 04 — tool safety

| Tool | Read/Write | Who may call it | Dry-run / confirm | Idempotency | Retry safe? |
|------|------------|-----------------|-------------------|-------------|-------------|
| get_order | read | Order Status, Inventory | n/a | n/a | yes — read |
| get_atp | read | Inventory | n/a | n/a | yes — read |
| reserve_substitute | write (when dry_run=false) | Inventory only | default dry_run=true | lab id is RSV-order-sku | only with dry_run=true, or a real reservation id later |
| suggest_substitute_for_short | read (preview only) | Inventory | hard-coded dry_run=true | n/a | yes |
| request_refund | write (when confirm=true) | **not** Inventory; refund agent later | confirm=false preview | caller-supplied key | only with the **same** key |
```

### Expect

OMS + ATP + refund rows are filled. The Inventory row for `request_refund` is “must not import,” not “maybe later.”

---

## How it works (deeper dive)

### When to retry

| Situation | Retry? | Why |
|-----------|--------|-----|
| Read timeout on `get_atp` | Yes, bounded | Looking at the shelf twice does not take milk |
| Unknown outcome on `request_refund` after `confirm=True` | Only with the **same** idempotency key | Same receipt number; a new key is a second refund |
| `INVALID_SKU` | No | The input is wrong; retrying the same string cannot help |
| Substitute reserved, then refund request failed | Do not pretend success | Repair with an explicit tool; do not “just try the whole saga again” |

### Fixtures vs the real systems

Your JSON files stand in for:

- OMS REST → `orders.json`
- WMS / ATP service → `inventory.json`
- Payments → the in-process `_IDEMPOTENCY` dict

The **contract** stays the same when the transport changes: validate, structured error, correlation id, dry-run / confirm for writes.

---

## Common pitfalls / troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `cannot import name 'new_correlation_id'` | Typo `coorelation` in `logging_utils.py` | Rename the function to match the import |
| `pytest` skips async tests or errors on `await` | Missing pytest-asyncio | `pip install pytest-asyncio`; keep `@pytest.mark.asyncio` |
| `ModuleNotFoundError: meridian_ops` | `PYTHONPATH` not set | From repo root: `export PYTHONPATH=project` |
| Two refund ids for one Maya ticket | New idempotency key on retry | Persist the key; never mint it inside the tool |
| Agent commits a substitute in chat | Default flipped, or `dry_run=false` passed | Keep default `True`; confirm in the prompt |
| Logs missing in the browser | Logs go to stderr | Watch the terminal that launched `adk web` or pytest |
| Inventory agent invents a refund | `request_refund` imported into that agent | Remove it. Least privilege is the import list. |
| Suggest picks `552100` | Candidates listed bread first | Rank milk-alt before bread, or own that ranking on purpose |

---

## You are done when

- [ ] ATP tests pass (including suggest) with no LLM
- [ ] Payments tests prove preview + idempotent replay
- [ ] Inventory agent in `adk web` previews `884299` for the milk short
- [ ] That agent does **not** import `request_refund`
- [ ] `04-tool-safety.md` has honest rows for OMS, ATP, and refund

---

## Knowledge check

1. Why default `dry_run=True` on `reserve_substitute`?  
2. What makes a refund retry safe?  
3. When is a composed tool better than asking the LLM to chain A→B?  
4. Why keep `request_refund` out of the inventory agent?  
5. What belongs in a tool error payload — and what must not?

### Answers

1. The model explores. Exploring must not take the last gallons off the shelf.  
2. A stable `idempotency_key` the **caller** supplies, plus a store that returns the same `refund_request_id` on replay.  
3. When the sequence is stable, must leave evidence (`attempts`), or is easy to scramble (bread for milk).  
4. Least privilege: Devon can radio the cooler; he cannot open the cash office.  
5. `status`, `error_code`, human `message`, `correlation_id`. Not a Python stack trace — the model will quote it or invent around it.

---

## Recap

- Tools gained contracts: validate early, log with a correlation id, preview writes, and refund only with a key.  
- You tested them without the LLM — that is the SME move.  
- Next: multi-agent orchestration so Order, Inventory, and Refund stop living as one mega-agent.

---

## Stretch goal

Add a `timeout_s` parameter to `get_atp`. Wrap the sleep + lookup in `asyncio.wait_for`. If it fires, return `error_code=TIMEOUT` and a correlation id. Write a test that uses a tiny `timeout_s` so the wait_for fails on purpose.

---

## Feedback

- Could you implement a new read-only `get_delivery_events` tool to the same bar without looking at ATP?  
- What tripped you up: async tests, idempotency, or agent wiring?  
- Note the task number and what you expected vs what happened.

---

## Navigate

**← Prev** [Lesson 03 — Core building blocks](03-core-building-blocks.md)  
**Next →** [Lesson 05 — Multi-agent orchestration](05-multi-agent-orchestration.md)

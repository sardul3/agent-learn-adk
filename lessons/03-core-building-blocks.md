# Lesson 03 — Core ADK building blocks

**Level:** Intermediate  
**Time:** ~75–90 minutes  
**Prerequisites:** Lesson 02 agent running in `adk web`  
**Lab outcome:** Policy-grade instructions, session state for a ticket, and a callback you can see fire

---

## At a glance

You deepen the Order Status agent into something Meridian could actually review:

- `Agent` / `LlmAgent` fields that matter in production
- **Instructions as product policy** (scope, refusals, tool-use rules)
- Sessions & turns
- Events / callbacks on the agent lifecycle
- Artifacts vs state (first contact)
- What you must control in context vs what the runtime helps with

---

## Why this matters

A Meridian CX supervisor will ask:

> “Why did the agent tell Maya the order was stolen?”

If your only answer is “the model said so,” you do not have a product — you have a liability. Building blocks exist so you can point to **instruction policy**, **tool evidence**, **session state**, and **lifecycle hooks**.

---

## Know these

| Building block | What it is | Meridian use |
|----------------|------------|--------------|
| **`name`** | Stable agent id | `meridian_order_status` in routers/logs |
| **`description`** | Short capability blurb for routers / UI | “WISMO via OMS lookup” |
| **`model`** | Which LLM reasons | Flash for status; maybe Pro later for disputes |
| **`instruction`** | System policy for this agent | Scope, refusals, tool rules, tone |
| **`tools`** | Callables the model may invoke | `get_order` |
| **Session** | Container for one ongoing conversation | Maya’s chat about `MC-1048292` |
| **Turn** | One user message + agent work that follows | “What’s the status…” |
| **State** | Mutable dict scratchpad for the session/run | `active_order_id`, `ticket_id` |
| **Event / callback** | Hook around agent/model/tool lifecycle | Log when a run starts; redact before model call |
| **Artifact** | Named blob tied to the session | Saved OMS snapshot JSON for audit |
| **Runner** | Programmatic entrypoint to invoke an agent | Unit/integration tests without the web UI |

### Instruction layers (think like a product spec)

```
WHO you are
  → SCOPE (in / out)
    → TOOL RULES (must / must not)
      → SAFETY / REFUSALS
        → STYLE / OUTPUT SHAPE
```

If you bury tool rules under poetry, the model will miss them under pressure.

---

## Task 1 — Promote the OMS stub into a shared module

### Why

Lesson 02 inlined data inside `agent.py`. That blocks testing and multi-agent reuse (Lesson 05).

### Do this

1. Create `project/meridian_ops/fixtures/orders.json`:

```json
{
  "MC-1048292": {
    "order_id": "MC-1048292",
    "customer_id": "C-44102",
    "lifecycle": "delivered",
    "promised_window_local": "2026-08-10T16:00-18:00",
    "delivered_at_local": "2026-08-10T17:12:00",
    "pod_photo_present": false,
    "shipping_address_city": "Austin",
    "line_count": 14
  },
  "MC-1048301": {
    "order_id": "MC-1048301",
    "customer_id": "C-11887",
    "lifecycle": "ready_for_pickup",
    "promised_window_local": "2026-08-11T17:00-19:00",
    "delivered_at_local": null,
    "pod_photo_present": false,
    "shipping_address_city": "Austin",
    "line_count": 6
  },
  "MC-1048277": {
    "order_id": "MC-1048277",
    "customer_id": "C-99210",
    "lifecycle": "delivered",
    "promised_window_local": "2026-08-09T11:00-13:00",
    "delivered_at_local": "2026-08-09T12:40:00",
    "pod_photo_present": true,
    "shipping_address_city": "Round Rock",
    "line_count": 9,
    "order_total_usd": 214.55,
    "damage_report": "melted_dairy"
  }
}
```

2. Create `project/meridian_ops/tools/oms.py`:

```python
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_ORDERS_PATH = Path(__file__).resolve().parents[1] / "fixtures" / "orders.json"


def _load_orders() -> dict[str, dict[str, Any]]:
    return json.loads(_ORDERS_PATH.read_text())


def get_order(order_id: str) -> dict[str, Any]:
    """Look up a Meridian order in OMS (fixture-backed).

    Args:
        order_id: Meridian order id, for example MC-1048292.

    Returns:
        status=success with order, or status=error with error_code.
    """
    orders = _load_orders()
    order = orders.get(order_id.strip())
    if not order:
        return {
            "status": "error",
            "error_code": "ORDER_NOT_FOUND",
            "message": f"No order found for {order_id}",
        }
    return {"status": "success", "order": order}
```

3. Add `project/meridian_ops/tests/test_oms.py`:

```python
from meridian_ops.tools.oms import get_order


def test_get_order_happy_path():
    out = get_order("MC-1048292")
    assert out["status"] == "success"
    assert out["order"]["lifecycle"] == "delivered"


def test_get_order_not_found():
    out = get_order("MC-0000000")
    assert out["error_code"] == "ORDER_NOT_FOUND"
```

4. Run:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
source .venv/bin/activate
export PYTHONPATH=project
pytest project/meridian_ops/tests/test_oms.py -v
```

### Expect

`2 passed`

---

## Task 2 — Rewrite instructions as Meridian product policy

### Why

Instructions are not “system prompt vibes.” They are the policy document the model will partially obey — so write them like an on-call runbook.

### Do this

Create `project/meridian_order_status/policy.md` (human-readable source of truth), then keep `agent.py` instruction in sync (or load the file — either is fine).

**Minimum policy sections to include:**

1. **Identity** — internal ops assistant for Meridian Order Status  
2. **In scope** — lifecycle, ETA/windows, POD presence, pickup readiness  
3. **Out of scope** — refunds, payment method changes, account takeover, medical claims  
4. **Tool rules** — must call `get_order` before factual claims; never invent scans  
5. **State rules** — when an `order_id` is known, keep using it until the user changes it  
6. **Output shape** — bullets: `order_id`, `lifecycle`, `promised_window`, `evidence`, `next_step`

Update `project/meridian_order_status/agent.py` to import `get_order` from `meridian_ops.tools.oms` and use your tightened instruction.

Because the agent package lives under `project/`, run with:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme/project
source ../.venv/bin/activate
export PYTHONPATH=.
adk web --port 8000
```

### Expect

Prompt:

```
MC-1048292 — customer says nothing at the door. Summarize OMS evidence.
```

You should see:

- tool call to `get_order`
- explicit mention of missing POD
- a **next_step** that is operational (e.g., open investigation / ask for photo) — not a fabricated refund

> **Tip:** Put refusals near the top. Models under tool-pressure drop bottom-of-prompt rules first.

> **Watch out:** Do not paste entire OMS JSON into the instruction. Instructions are policy; data comes from tools/state.

---

## Task 3 — Session state: remember the active order

### Why

Maya should not have to repeat `MC-1048292` every turn. State is the scratchpad for that.

### Do this

Update `get_order` usage via a thin wrapper tool in the agent package (keeps OMS module pure):

```python
# inside project/meridian_order_status/agent.py
from __future__ import annotations

from pathlib import Path
from typing import Any

from google.adk.agents.llm_agent import Agent
from google.adk.tools.tool_context import ToolContext

from meridian_ops.tools.oms import get_order as oms_get_order

POLICY = (Path(__file__).parent / "policy.md").read_text()


def get_order(order_id: str, tool_context: ToolContext) -> dict[str, Any]:
    """Fetch order and remember it as the session's active order.

    Args:
        order_id: Meridian order id like MC-1048292.
        tool_context: Injected by ADK; do not pass manually.
    """
    result = oms_get_order(order_id)
    if result.get("status") == "success":
        tool_context.state["active_order_id"] = order_id
        tool_context.state["active_lifecycle"] = result["order"]["lifecycle"]
    return result


def recall_active_order(tool_context: ToolContext) -> dict[str, Any]:
    """Return the active order id stored in session state, if any."""
    order_id = tool_context.state.get("active_order_id")
    if not order_id:
        return {
            "status": "error",
            "error_code": "NO_ACTIVE_ORDER",
            "message": "No active_order_id in session state",
        }
    return {"status": "success", "active_order_id": order_id}


root_agent = Agent(
    name="meridian_order_status",
    model="gemini-2.5-flash",
    description="Meridian WISMO agent with session-aware order lookup.",
    instruction=POLICY
    + """

Session rules:
- After a successful get_order, active_order_id is stored in state.
- If the user says "that order" or omits the id, call recall_active_order, then get_order.
""".strip(),
    tools=[get_order, recall_active_order],
)
```

In `adk web`, **same session**, run:

1. `Status for MC-1048292?`  
2. `Any POD photo on that order?`

### Expect

- Turn 1 writes `active_order_id`  
- Turn 2 does **not** require you to retype the id  
- Trajectory shows `recall_active_order` and/or reuse of the stored id

> **Watch out:** Reassigning `tool_context.state = {...}` can break session state. Mutate keys: `tool_context.state["k"] = v`.

---

## Task 4 — Lifecycle callback you can prove fired

### Why

Callbacks are how you add observability and guardrails without stuffing more prose into the instruction.

### Do this

Add a before-agent callback that records a run counter in state and prints a single structured log line:

```python
import json
from datetime import datetime, timezone


def before_agent_callback(callback_context):
    runs = int(callback_context.state.get("run_count", 0)) + 1
    callback_context.state["run_count"] = runs
    callback_context.state["last_run_at"] = datetime.now(timezone.utc).isoformat()
    print(
        json.dumps(
            {
                "event": "before_agent",
                "agent": "meridian_order_status",
                "run_count": runs,
                "active_order_id": callback_context.state.get("active_order_id"),
            }
        )
    )
    return None
```

Wire it into the agent using the parameter name your installed ADK version expects for before-agent hooks (commonly `before_agent_callback=` on `Agent` / `LlmAgent`). If your version’s signature differs, run:

```bash
python -c "from google.adk.agents.llm_agent import Agent; import inspect; print(inspect.signature(Agent.__init__))"
```

…and bind the callback to the matching kwarg. Do not invent a second agent framework — adapt to the installed ADK.

Re-run two turns in `adk web` while watching the terminal where `adk web` is running.

### Expect

- Two JSON lines with `run_count` 1 then 2  
- `active_order_id` present on the second line after Task 3

> **Tip:** Callbacks are ideal for correlation IDs, redaction, and “deny before model” checks. Lesson 07 will harden this.

---

## Task 5 — Artifact: save an OMS snapshot for audit

### Why

State holds small keys. Artifacts hold the blob you might attach to a case in ServiceNow-style tooling later.

### Do this

Add:

```python
from google.genai import types
import json


async def save_order_snapshot(order_id: str, tool_context: ToolContext) -> dict[str, Any]:
    """Save the raw OMS order JSON as a session artifact for audit."""
    result = oms_get_order(order_id)
    if result.get("status") != "success":
        return result
    payload = json.dumps(result["order"], indent=2).encode("utf-8")
    part = types.Part.from_bytes(data=payload, mime_type="application/json")
    version = await tool_context.save_artifact(f"order-{order_id}.json", part)
    tool_context.state["last_snapshot_artifact"] = f"order-{order_id}.json"
    return {
        "status": "success",
        "artifact": f"order-{order_id}.json",
        "version": version,
    }
```

Register the tool; instruct: when lifecycle is `delivered` and `pod_photo_present` is false, call `save_order_snapshot` before recommending investigation.

### Expect

Trajectory includes `save_order_snapshot` for `MC-1048292`, and state shows `last_snapshot_artifact`.

---

## How it works (deeper dive)

### Built-in tools vs custom function tools

| Kind | Examples | When |
|------|----------|------|
| Built-in | Google Search, load_memory, transfer_to_agent | Cross-cutting platform capabilities |
| Custom function tools | `get_order`, `request_refund` | Your OMS/WMS/Payments contracts |

Meridian OrderOps will be **mostly custom tools**. Built-ins are seasoning, not the meal.

### Context management — shared responsibility

ADK can help with history plumbing and some compaction features depending on version/config. **You** still own:

- what tools return (don’t dump 200KB of OMS)
- what you put in state vs artifacts
- instruction size
- when to summarize a long dispute thread (Lesson 06)

### Runner vs `adk web`

- **`adk web` / `adk run`:** human-in-the-loop development  
- **`Runner`:** code-driven invokes for tests and services  

You will use `Runner` seriously in Lessons 07–08. For now, know it exists:

```python
from google.adk import Runner
from google.adk.sessions import InMemorySessionService
```

---

## Common pitfalls / troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `No module named meridian_ops` | `PYTHONPATH` not including `project` | `export PYTHONPATH=.` from `project/` |
| State “forgotten” each message | New session in UI | Stay in the same chat thread |
| Callback never prints | Not wired / wrong kwarg for your ADK version | Inspect `Agent` signature; confirm process stdout |
| Artifact save errors | Missing async / artifact service in a custom Runner | Use `adk web` first; wire ArtifactService when using Runner |
| Model still invents POD | Instruction soft; no tool evidence rule | Require snapshot + explicit “never invent POD” |

---

## You are done when

- [ ] OMS fixture + `get_order` unit tests pass
- [ ] `policy.md` exists and matches agent instruction structure
- [ ] Multi-turn session reuses `active_order_id`
- [ ] You observed a callback log line with `run_count`
- [ ] Delivered-without-POD path saves an artifact

---

## Knowledge check

1. Map each field to purpose: `name`, `description`, `instruction`, `tools`.  
2. What is the difference between session **state** and an **artifact** here?  
3. Why put refusals near the top of the instruction?  
4. What must be true before the agent claims `delivered_at_local`?  
5. Give one callback use case that should *not* live in the instruction text.

### Answers

1. Identity; router/UI blurb; policy; callable capabilities.  
2. State = small keys for control flow; artifact = the JSON blob for audit/handoff.  
3. Under long contexts/tool noise, trailing rules get ignored more often.  
4. A successful `get_order` (tool evidence) containing that field.  
5. Emitting structured logs / redacting secrets / hard-deny on banned tools.

---

## Recap

- Instructions became Meridian policy, not chat flavor text.  
- Sessions grew state + an audit artifact + a visible lifecycle hook.  
- Next: harden a full tool belt (sync/async, validation, side effects, observability).

---

## Stretch goal

Add an `output_key` (if supported in your ADK version) or a tiny tool `commit_status_summary(summary: str)` that stores a customer-safe summary into `tool_context.state["last_customer_summary"]`. Prove it appears in state after a turn.

---

## Feedback

- Could you explain your `policy.md` sections to a CX supervisor in two minutes?  
- What tripped you up: imports/PYTHONPATH, ToolContext, callbacks, or artifacts?  
- Note task number + expected vs actual.

---

## Navigate

**← Prev** [Lesson 02 — ADK environment](02-adk-environment.md)  
**Next →** [Lesson 04 — Tools deep mastery](04-tools-mastery.md)
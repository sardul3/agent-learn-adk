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
| **Callback** | A Python function **ADK always runs** at a known moment (before the agent, model, or tool) | Stamp a log every time Order Status starts a turn |
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

Priya (CX supervisor) asks:

> “How many times did this chat look at Maya’s order?”

You cannot put that count in the **instruction**. The model might forget, skip it, or invent a number.

You cannot make a **tool** called `log_run` and hope the model calls it. Tools are optional — the model chooses.

You need something that runs in **your Python**, every turn, **before** the model even starts thinking. That is a **callback**.

### Picture this: the store punch clock

When Devon clocks in at Store 441, the time clock stamps `Devon started 09:02` **before** he stocks a single shelf.

Devon does not write that stamp himself. If he did, he would forget on a busy morning. The clock is wired into the door.

A callback is that time clock for your agent:

```
You send a message in adk web
        │
        ▼
  before_agent_callback     ← YOUR Python always runs here
  (stamp run_count, print a log)
        │
        ▼
  Model thinks / may call get_order
        │
        ▼
  Agent replies in the browser
```

| Approach | Who runs it? | Can it skip? |
|----------|--------------|--------------|
| Write “please count your runs” in the instruction | The model | Yes — models drop rules |
| Add a `log_run` tool | The model, if it decides to call it | Yes |
| `before_agent_callback` | ADK, every turn, before the model | **No** — that is the point |

Today you add the punch clock. You prove it fired in two places: the **terminal** (a log line) and **session state** (`run_count`).

### Do this

1. Open `project/meridian_order_status/agent.py`. Add these imports near the top (with the other imports):

```python
import json
from datetime import datetime, timezone
```

2. Add this function **above** `root_agent = Agent(...)`. It is ordinary Python. ADK will call it for you.

```python
def before_agent_callback(callback_context):
    """Stamp a run counter before the model starts. Return None = keep going."""
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

   - `callback_context` is ADK’s handle for this turn. Same idea as `tool_context` in Task 3, but it runs **before** any tool.
   - `callback_context.state` is the **same session state** you wrote `active_order_id` into.
   - `return None` means “I only stamped the clock — let the agent continue.”

3. Wire it on the agent. Add **one line** to the existing `Agent(...)` call:

```python
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
    before_agent_callback=before_agent_callback,  # punch clock: runs before every turn
)
```

   The left side (`before_agent_callback=`) is the ADK hook name. The right side is **your** function. They happen to share a name; that is fine.

4. Restart `adk web` so it reloads `agent.py`. In the terminal where it is already running:

   - Press `Ctrl+C` to stop it (`C` = cancel the running process).
   - Start it again:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme/project
source ../.venv/bin/activate
export PYTHONPATH=.
adk web --port 8000
```

   `--port 8000` keeps the UI on the same URL you already have open.

5. Restarting `adk web` starts a **fresh** session (in-memory state does not survive the restart). Open the UI and send two messages in **one** chat:

   1. `Status for MC-1048292?`
   2. `Any POD photo on that order?`

6. Prove it fired — look in **two** places:

   - **Terminal** (the window where `adk web` is running — **not** the browser chat).
   - **Session state** in the `adk web` UI (the state / session panel).

### Expect

**Terminal** — two JSON lines, one per turn:

```json
{"event": "before_agent", "agent": "meridian_order_status", "run_count": 1, "active_order_id": null}
{"event": "before_agent", "agent": "meridian_order_status", "run_count": 2, "active_order_id": "MC-1048292"}
```

- Turn 1: `run_count` is `1`. `active_order_id` is `null` on that first stamp — the callback runs **before** `get_order` writes the id.
- Turn 2: `run_count` is `2`. `active_order_id` is `MC-1048292` because turn 1 already stored it.

**Session state** after turn 2:

- `run_count` is `2`
- `last_run_at` is an ISO timestamp
- `active_order_id` is still `MC-1048292`

If both of those match, the punch clock is real. You did not ask the model to log anything.

> **Tip:** Later lessons use the same hook to **stop** a run (return a canned reply instead of `None`) — for example, deny a refund before the model ever sees it. Today you only prove the hook fires.

> **Watch out:** The argument **must** be named `callback_context`. ADK passes it by that name. If you rename it to `ctx`, you get a `TypeError` at runtime.

> **Watch out:** `print(...)` goes to the **terminal**, not the chat bubble. If the browser looks unchanged, that is expected — look at the process that launched `adk web`.

> **Watch out:** A new session resets state. `run_count` starts at `1` again. That is correct: the punch clock is per conversation, not global.

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
| No JSON in the browser chat | Callbacks `print` to the `adk web` process, not the UI | Watch the terminal that launched `adk web` |
| Callback never prints | Not passed into `Agent(...)`, or `adk web` not restarted | Add `before_agent_callback=before_agent_callback`; restart `adk web` |
| `TypeError` / missing `callback_context` | Parameter renamed from `callback_context` | The argument must be named exactly `callback_context` |
| `run_count` resets to 1 on the next message | New session in the UI | Stay in the same chat thread |
| Artifact save errors | Missing async / artifact service in a custom Runner | Use `adk web` first; wire ArtifactService when using Runner |
| Model still invents POD | Instruction soft; no tool evidence rule | Require snapshot + explicit “never invent POD” |

---

## You are done when

- [ ] OMS fixture + `get_order` unit tests pass
- [ ] `policy.md` exists and matches agent instruction structure
- [ ] Multi-turn session reuses `active_order_id`
- [ ] Same session, two turns: terminal shows `run_count` 1 then 2, and state shows `run_count: 2`
- [ ] Delivered-without-POD path saves an artifact

---

## Knowledge check

1. Map each field to purpose: `name`, `description`, `instruction`, `tools`.  
2. What is the difference between session **state** and an **artifact** here?  
3. Why put refusals near the top of the instruction?  
4. What must be true before the agent claims `delivered_at_local`?  
5. Why is a run counter a callback, not an instruction or a tool? After two turns in the **same** session, what is `run_count`?

### Answers

1. Identity; router/UI blurb; policy; callable capabilities.  
2. State = small keys for control flow; artifact = the JSON blob for audit/handoff.  
3. Under long contexts/tool noise, trailing rules get ignored more often.  
4. A successful `get_order` (tool evidence) containing that field.  
5. ADK always runs the callback; the model can skip an instruction or a tool. `run_count` is `2`.

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
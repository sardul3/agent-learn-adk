# Lesson 13 — ADK graph workflows (native)

**Level:** Advanced  
**Time:** ~120–150 minutes  
**Prerequisites:** Lessons 05, 07, 08, 12 (`get_order`, HITL idea, `App` + `InMemoryRunner`, FastAPI edge)  
**Lab outcome:** You can walk Meridian OrderOps as a native ADK `Workflow`, load it, run three real tickets in `adk web`, and prove routes with pytest — **no second graph engine**

**Standard:** [docs/NATIVE-ADK.md](../docs/NATIVE-ADK.md)

---

## At a glance

A chat agent *hopes* the model picks the right specialist. A **graph** makes the path a reviewable edge.

ADK 2.6.3 already ships that graph. You will **not** write `MeridianGraph`. You will open the package that is already in this repo, walk every node, fix one spelling that 2.6.3 rejects, then run the same object in the UI and in pytest.

| Task | What you do | Who enforces it | How you prove it |
|------|-------------|-----------------|------------------|
| 1 | Verify the **native** Workflow APIs in the venv that already exists | Your install | Imports print `OK` — no new venv |
| 2 | Walk `meridian_orderops/agent.py` and spell routes as a **routing map** | ADK `Workflow` | File loads; edges quote the real branches |
| 3 | Run three tickets in `adk web` | The same `root_agent` | WISMO narrative, SHORTAGE join, REFUND pause |
| 4 | Invoke with `App` + `InMemoryRunner` | ADK event stream | Authors + `actions.route` match the ticket |
| 5 | Unit-test `route_ticket` / `lookup_order` without Gemini | Your Python | `pytest` green with no API key |

If you get lost, scroll back to this table. Each task fills one row. The scoreboard at the end of every task repeats the same rows.

**Forbidden:** a home-grown edge runner, a second OrderOps package “just for this lesson,” or “adapt the tuple if your version differs.” You are on **ADK 2.6.3**.

---

## Why this matters

Three tickets land in the same inbox at Store 441:

| Ticket | Order | What the customer / picker said | Path that must win |
|--------|-------|----------------------------------|--------------------|
| `TCK-9001` | `MC-1048292` | “Says delivered. Nothing at the door.” | **WISMO** — OMS lookup, then language |
| `TCK-9003` | `MC-1048310` | “ATP 0 on organic milk SKU `884210`. Need a substitute.” | **SHORTAGE** — OMS **and** inventory, then join |
| `TCK-9004` | `MC-1048277` | “Full refund $214.55, melted dairy.” | **REFUND** — OMS, then Priya (HITL), then code |

If those three share one mega-prompt, the model can:

- Refund a missing-POD WISMO (finance incident)
- Skip inventory on a short and invent a reservation (ops incident)
- Skip Priya on $214.55 (policy incident — `POL-REFUND-04`, HITL over $75)

Priya (CX supervisor) will not accept “the model usually routes well.” She wants an **edge** she can point at in code review.

Today that edge is native ADK: `Workflow` + `Event(route=...)` + `JoinNode` + `RequestInput`.

---

## Know these

Read this table before Task 1. Every later task reuses these words.

| Term | Plain English | Meridian example |
|------|---------------|------------------|
| **Workflow** | ADK graph: nodes plus edges. This *is* `root_agent`. | `name="meridian_orderops"` |
| **Function node** | Ordinary Python. ADK wraps it as a `FunctionNode`. Name defaults to `func.__name__`. | `route_ticket`, `lookup_order`, `refund_finalize` |
| **LlmAgent node** | A model-powered node sitting on an edge | `order_narrator`, `synthesizer` |
| **`Event.output`** | Value the **next** node receives as `node_input` | A `RouteDecision`, an `OrderFindings` |
| **`Event(route=...)`** | Convenience kwarg. ADK stores it on `event.actions.route`. That label picks the next **labeled** edge. | `"WISMO"`, `"SHORTAGE"`, `"REFUND"` |
| **Routing map** | A dict in an edge: `{ "WISMO": next_node, ... }`. This is the legal 2.6.3 spelling. | After `route_ticket` |
| **3-tuple edge** | `(from, to, "WISMO")` — **illegal** on 2.6.3. Pydantic treats `"WISMO"` as a node. | What the file ships with today |
| **`START`** | Graph entry. Receives the user `Content`. | First edge: `("START", route_ticket)` |
| **JoinNode** | Fan-in: wait until **every** named predecessor finishes. Output is a **dict keyed by predecessor names**. | `join_shortage` |
| **`RequestInput`** | Native HITL pause. The UI asks a human. Resume is ADK’s job (Lesson 15). | `hitl_refund_gate` |
| **`adk_request_input`** | Function-call name ADK uses on the interrupt Event | What you see in the trajectory when Priya must click |
| **`App`** | Named container around a root agent **or** a Workflow (`root_agent=` accepts both) | `App(name="meridian_orderops", root_agent=root_agent)` |
| **`InMemoryRunner`** | ADK runner with in-memory session / memory / artifacts | pytest and local services — not `adk web` |
| **`event.author`** | Who appended the event. For a Workflow, child events are attributed to the **Workflow name**. | `"meridian_orderops"` (and `"user"`) |
| **`event.node_name`** | Which **node** produced the event (`node_info.path`) | `"route_ticket"`, `"lookup_order"` |
| **WISMO** | Where-is-my-order | Maya’s delivered-but-empty porch |

### Picture this: the floor map vs the employee handbook

| Layer | Store 441 analogue | Can a busy morning skip it? |
|-------|--------------------|-----------------------------|
| Instruction “if they say refund, go to refund” | Handbook on the break-room wall | **Yes** — models drop rules under pressure |
| `Event(route="REFUND")` + a routing map | Painted lane on the floor: refunds go to the cash office | **No** — the next node is that edge |
| `JoinNode` | Devon and the dairy lead both walk the case, then meet at the desk | Skipping it smashes two stories into one blob |
| `RequestInput` | Manager key for over-$75 returns | **No** — no key, no drawer |
| A second Python “graph engine” | Building a second store next door to route bags | That is the bug this lesson forbids |

### The graph you will run (keep this picture)

```
START
  │
  ▼
route_ticket  (Python — path law)
  │
  ├── WISMO     → lookup_order → order_narrator ──────────────────► synthesizer
  ├── SHORTAGE  → lookup_order → (narrator_shortage ‖ inventory)
  │                                └──────── JoinNode ────────────► synthesizer
  ├── REFUND    → lookup_order → RequestInput → refund_finalize ─► synthesizer
  ├── POLICY    → policy_agent ──────────────────────────────────► synthesizer
  └── UNSUPPORTED → unsupported_msg  (terminal — no synthesizer)
```

`lookup_order` **re-emits** the same route it received. That is how WISMO / SHORTAGE / REFUND share one OMS node without the model choosing the next hop.

> **Tip:** Domain tools (`get_order`) are allowed inside function nodes. Alternate orchestrators are not. See [NATIVE-ADK.md](../docs/NATIVE-ADK.md).

---

## What you already have (do not rebuild)

From the **repo root**, confirm these exist. Lessons 03–08 left the fixtures and the OMS tool. Pack C left the OrderOps package.

| Path | Job |
|------|-----|
| `project/meridian_orderops/agent.py` | The native `Workflow`. You **walk and fix** this file. You do not replace it. |
| `project/meridian_orderops/__init__.py` | `from . import agent` so `adk web` finds `root_agent` |
| `project/meridian_ops/tools/oms.py` | `get_order` — fixture-backed OMS |
| `project/meridian_ops/fixtures/orders.json` | `MC-1048292` (no POD), `MC-1048310` (short), `MC-1048277` (melted, $214.55) |
| `project/meridian_ops/fixtures/tickets.json` | `TCK-9001` / `TCK-9003` / `TCK-9004` — the three prompts |
| `.venv/` | Already created in Lesson 02. **Source it. Do not recreate it.** |

You will **add**:

```
project/meridian_ops/tests/test_orderops_route_nodes.py     Task 5 (no LLM)
project/meridian_ops/tests/test_orderops_workflow_runner.py Task 4 (live model)
```

If `meridian_orderops/agent.py` is missing, stop. This lesson teaches that file. It does not invent a second graph.

---

## Task 1 — Verify native Workflow APIs (venv already exists)

### Why

Wrong imports are how people invent `MeridianGraph`. You will prove the 2.6.3 stack that this lesson uses — in the venv you already have — before you touch a single edge.

### Do this

1. From the **repo root**, activate the existing venv. Do **not** run `python3 -m venv .venv` first. That wipes the Lesson 02 install.

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
source .venv/bin/activate
python -c "import google.adk as adk; print(adk.__version__, adk.__file__)"
```

   - `source .venv/bin/activate` — use **this** project’s Python, not Homebrew’s.
   - If the prompt shows `(.venv)`, you are in the right interpreter.

2. Confirm you are on **2.6.3**. Expect a line like:

```
2.6.3 .../agent-learn-sme/.venv/lib/python3.14/site-packages/google/adk/__init__.py
```

   If the import fails (`No module named google.adk`), install into **this** venv — still do not recreate it:

```bash
pip install "google-adk==2.6.3" pytest pytest-asyncio
```

   - `pip install "google-adk==2.6.3"` — pin the version this lesson is written against.
   - `pytest` / `pytest-asyncio` — Tasks 4–5. You likely already have them from Lesson 04 / 08.

3. Prove the exact imports this lesson uses:

```bash
python - <<'PY'
from google.adk.workflow import Workflow, JoinNode
from google.adk.events.event import Event
from google.adk.events.request_input import RequestInput
from google.adk.agents import LlmAgent
from google.adk.apps import App
from google.adk.runners import InMemoryRunner
print("native workflow stack OK")
print("Workflow", Workflow)
print("JoinNode", JoinNode)
print("RequestInput", RequestInput)
PY
```

### Expect

```
native workflow stack OK
```

plus class reprs. If `google.adk.workflow` is missing, you are not on 2.6.3 — `pip install "google-adk==2.6.3"` and rerun. Do **not** write a DIY graph to paper over a bad install.

> **Tip:** `Event(route="WISMO")` is valid. There is no `event.route` **attribute** to read later. Read `event.actions.route`. Task 5 will fail if you assert `ev.route`.

> **Watch out:** Recreating `.venv` “to be safe” drops your Gemini packages, MCP extras, and pytest plugins. Source first. Install only if the import failed.

### Scoreboard after Task 1

| Control | In place? |
|---------|-----------|
| Native Workflow imports in the existing venv | **Yes** |
| Routing-map OrderOps graph loads | Not yet |
| Three tickets in `adk web` | Not yet |
| `InMemoryRunner` authors / routes | Not yet |
| Router pytest (no LLM) | Not yet |

---

## Task 2 — Walk the real OrderOps file (then spell the edges so 2.6.3 will load)

### Why

The reference implementation **is** the curriculum. If you sketch a cleaner graph in a new package, Priya now has two sources of truth and you have reinvented the wheel.

Open `project/meridian_orderops/agent.py` and walk it top to bottom. Quote the real objects. Then fix the one thing that prevents `Workflow(...)` from constructing on ADK 2.6.3: **3-tuple route labels**. Same nodes. Legal spelling.

### Do this

1. Open `project/meridian_orderops/agent.py` and `project/meridian_orderops/__init__.py`. The doorbell file is one line:

```python
from . import agent
```

   `adk web` loads `project/meridian_orderops/`, imports that, and looks for `agent.root_agent`. Same pattern as Lesson 02.

2. Confirm the imports at the top of `agent.py` are native ADK plus **one** domain tool — not a second orchestrator:

```python
from google.adk.agents import LlmAgent
from google.adk.agents.context import Context
from google.adk.events.event import Event
from google.adk.events.request_input import RequestInput
from google.adk.workflow import JoinNode, Workflow
from google.genai import types
from pydantic import BaseModel, Field

from meridian_ops.tools.oms import get_order
```

   Walk the table:

   | Import | Why it is here |
   |--------|----------------|
   | `LlmAgent` | Language nodes (narrate, inventory, policy, synthesizer) |
   | `Context` | `lookup_order`’s first argument — ADK injects it when the node runs |
   | `Event` | Function nodes return this so they can set `output`, `route`, and `state` |
   | `RequestInput` | HITL pause on the refund branch |
   | `JoinNode`, `Workflow` | The graph. This is the engine. |
   | `get_order` | Meridian OMS. Allowed. Not an orchestrator. |

   There is no `MeridianGraph`. If you see one, you opened the wrong file.

3. Change the model constant. The file ships `GEMINI = "gemini-2.5-flash"`. This lab uses **`gemini-3.5-flash`**. Replace that one line:

```python
GEMINI = "gemini-3.5-flash"
```

   Every `LlmAgent` below already says `model=GEMINI`. One constant. Four language nodes. You are not forking a second agent package.

4. Walk `RouteDecision` and `OrderFindings`. These are the **typed batons** the function nodes pass:

```python
class RouteDecision(BaseModel):
    route: str = Field(description="WISMO | SHORTAGE | REFUND | POLICY | UNSUPPORTED")
    order_id: str | None = None


class OrderFindings(BaseModel):
    order_id: str | None = None
    lifecycle: str | None = None
    pod_photo_present: bool | None = None
    raw_status: str = "unknown"
    route: str = "WISMO"
```

   | Model | Who writes it | Who reads it |
   |-------|---------------|--------------|
   | `RouteDecision` | `route_ticket` | `lookup_order` (and the routing map) |
   | `OrderFindings` | `lookup_order` | Narrators, inventory, HITL payload |

   The model does **not** invent `pod_photo_present`. OMS does.

5. Walk `_text_from_start` and `route_ticket`. This is path law. It is Python. The prompt does not get a vote.

```python
def _text_from_start(node_input: Any) -> str:
    if isinstance(node_input, types.Content):
        parts = node_input.parts or []
        return " ".join(getattr(p, "text", "") or "" for p in parts).strip()
    return str(node_input)


def route_ticket(node_input: Any) -> Event:
    """Deterministic router — path law lives in code, not in a prompt."""
    text = _text_from_start(node_input)
    lower = text.lower()
    m = re.search(r"(MC-\d+)", text)
    order_id = m.group(1) if m else None

    if re.search(r"\brecompute\b|\bnightly\b|\bsegment\b", lower):
        route = "UNSUPPORTED"
    elif "refund" in lower:
        route = "REFUND"
    elif re.search(r"\batp\b|\bsku\b|\bsubstitute\b|\bshorted\b", lower):
        route = "SHORTAGE"
    elif "policy" in lower and "refund" not in lower:
        route = "POLICY"
    else:
        route = "WISMO"

    decision = RouteDecision(route=route, order_id=order_id)
    return Event(
        output=decision,
        route=route,
        state={"route_decision": decision.model_dump(), "active_order_id": order_id},
    )
```

   Read the `if` / `elif` **in order**. First match wins:

   | Condition (in order) | Route | Ticket that hits it |
   |----------------------|-------|---------------------|
   | `recompute` / `nightly` / `segment` | `UNSUPPORTED` | `TCK-9005` loyalty batch |
   | substring `refund` | `REFUND` | `TCK-9004` melted dairy |
   | `atp` / `sku` / `substitute` / `shorted` | `SHORTAGE` | `TCK-9003` milk short |
   | `policy` and not `refund` | `POLICY` | `TCK-9006` late-credit FAQ |
   | everything else | `WISMO` | `TCK-9001` empty porch |

   The order id is a regex: `(MC-\d+)`. No order id still returns a route — `lookup_order` then emits `MISSING_ORDER_ID`.

   `Event(..., route=route, state={...})` uses convenience kwargs:

   | Kwarg | Lands on |
   |-------|----------|
   | `output=decision` | `event.output` — next node’s `node_input` |
   | `route=route` | `event.actions.route` — routing map key |
   | `state={...}` | `event.actions.state_delta` — session merge |

6. Walk `lookup_order`. Shared OMS hop. It **re-emits** `data.route` so the second routing map can split WISMO / SHORTAGE / REFUND after the fixture read.

```python
def lookup_order(ctx: Context, node_input: RouteDecision | dict[str, Any]) -> Event:
    data = node_input if isinstance(node_input, RouteDecision) else RouteDecision(**node_input)
    route = data.route
    if not data.order_id:
        findings = OrderFindings(raw_status="MISSING_ORDER_ID", route=route)
        return Event(output=findings, route=route)

    result = get_order(data.order_id)
    if result.get("status") != "success":
        findings = OrderFindings(
            order_id=data.order_id,
            raw_status=str(result.get("error_code", "ERROR")),
            route=route,
        )
        return Event(output=findings, route=route)

    order = result["order"]
    findings = OrderFindings(
        order_id=order.get("order_id"),
        lifecycle=order.get("lifecycle"),
        pod_photo_present=order.get("pod_photo_present"),
        raw_status="success",
        route=route,
    )
    return Event(
        output=findings,
        state={"order_findings": findings.model_dump()},
        route=route,
    )
```

   | Piece | Why it exists |
   |-------|----------------|
   | `ctx: Context` | ADK injects session context. This function does not use it. Task 5 still passes a dummy. |
   | `get_order(...)` | Same Lesson 03 tool. Fixture, not a hallucinated POD. |
   | `return Event(..., route=route)` | Keeps the branch after OMS. Drop this and every ticket would need a second classifier. |

   What the three lab orders actually contain (do not memorize — open `orders.json` if you want the JSON):

   | Order | `lifecycle` | `pod_photo_present` | Extra |
   |-------|-------------|---------------------|-------|
   | `MC-1048292` | `delivered` | `false` | Empty-porch WISMO |
   | `MC-1048310` | `ready_for_pickup` | `false` | `shorted_sku: "884210"` |
   | `MC-1048277` | `delivered` | `true` | `order_total_usd: 214.55`, `damage_report: melted_dairy` |

7. Walk the language nodes. Four `LlmAgent`s plus a **second narrator instance**. Quote the real names:

```python
order_narrator = LlmAgent(
    name="order_narrator",
    model=GEMINI,
    description="Turns OMS findings into concise ops bullets.",
    instruction=_ORDER_INSTR,
    output_key="order_narrative",
)

# Separate instance — ADK graphs require unique node names when fan-out/reuse.
order_narrator_shortage = LlmAgent(
    name="order_narrator_shortage",
    model=GEMINI,
    description="Order findings for shortage path.",
    instruction=_ORDER_INSTR,
    output_key="order_narrative",
)

inventory_agent = LlmAgent(
    name="inventory_agent",
    model=GEMINI,
    description="Shortage / substitute guidance (preview only).",
    instruction="""
You are Meridian Inventory.
Given order findings, discuss shortage handling.
Do not claim a reservation was committed. Prefer dry-run / preview language.
""".strip(),
    output_key="inventory_narrative",
)

policy_agent = LlmAgent(
    name="policy_agent",
    model=GEMINI,
    description="Policy FAQ narrator.",
    instruction="""
Answer Meridian policy questions cautiously.
If you lack retrieved policy text, say you cannot cite a policy id.
Never invent dollar credits.
""".strip(),
    output_key="policy_narrative",
)

synthesizer = LlmAgent(
    name="synthesizer",
    model=GEMINI,
    description="Customer-safe final reply.",
    instruction="""
Draft a customer-safe Meridian reply from prior findings/narratives.
Structure: Empathy → Facts → Next step.
Never claim a refund completed.
""".strip(),
    output_key="customer_reply_draft",
)
```

   Why **two** narrator objects:

   - ADK identifies nodes by **object identity** and by **name**.
   - Reuse `order_narrator` on the WISMO line `(order_narrator, synthesizer)` **and** on the SHORTAGE join, and finishing a WISMO turn pokes the join. Inventory never ran. The join waits, or fires with a half-dict.
   - Two objects, two names. Same `_ORDER_INSTR`. Lesson 14 zooms in on the diamond; you need the reason now so the graph is honest.

   `output_key` writes the model text into session state. Parallel writers must not share one key: `order_narrative` vs `inventory_narrative`.

8. Walk the HITL gate and the code finalize. This is Lesson 07’s manager key, inside the graph:

```python
async def hitl_refund_gate(node_input: Any):
    """Native ADK HITL — RequestInput pause/resume (not a DIY checkpoint DB)."""
    yield RequestInput(
        message=(
            "Refund requires supervisor approval. "
            "Reply with APPROVE or DENY and a short note."
        ),
        payload={"order_findings": str(node_input)},
    )


def refund_finalize(node_input: Any) -> Event:
    """Code-only post-HITL decision."""
    text = _text_from_start(node_input).strip().upper()
    approved = text.startswith("APPROVE")
    out = {
        "hitl_approved": approved,
        "hitl_raw": _text_from_start(node_input),
        "request_status": "CONFIRMED_LAB" if approved else "DENIED",
    }
    return Event(output=out, state={"refund_decision": out})
```

   | Piece | What ADK does |
   |-------|----------------|
   | `async def` + `yield RequestInput(...)` | Function node pauses. ADK turns this into an Event whose function call is named `adk_request_input`. |
   | `message=` | Text the UI shows Priya. |
   | `payload=` | Extra context (findings). Not a homemade checkpoint file. |
   | FunctionNode `rerun_on_resume` default **False** | On resume, the human reply **is** this node’s output. It flows to `refund_finalize`. |
   | `text.startswith("APPROVE")` | Money-adjacent flag is **code**. The model does not set `hitl_approved`. |

   `unsupported_msg` returns a dict. ADK wraps it as `Event(output=...)`. It has **no outgoing edge**. Batch jobs die here on purpose — no synthesizer, no fake empathy.

9. Quote the **real** `edges=` list as the file ships it. This is the graph. It is also **illegal** on 2.6.3:

```python
join_shortage = JoinNode(name="join_shortage")

root_agent = Workflow(
    name="meridian_orderops",
    description="Native ADK OrderOps graph with HITL refund branch.",
    edges=[
        ("START", route_ticket),
        # Route → shared OMS lookup (re-emits same route)
        (route_ticket, lookup_order, "WISMO"),
        (route_ticket, lookup_order, "SHORTAGE"),
        (route_ticket, lookup_order, "REFUND"),
        (route_ticket, policy_agent, "POLICY"),
        (route_ticket, unsupported_msg, "UNSUPPORTED"),
        # WISMO
        (lookup_order, order_narrator, "WISMO"),
        (order_narrator, synthesizer),
        # SHORTAGE: fan-out narrator + inventory, join, synthesize
        (lookup_order, (order_narrator_shortage, inventory_agent), "SHORTAGE"),
        ((order_narrator_shortage, inventory_agent), join_shortage),
        (join_shortage, synthesizer),
        # REFUND: HITL then code finalize
        (lookup_order, hitl_refund_gate, "REFUND"),
        (hitl_refund_gate, refund_finalize),
        (refund_finalize, synthesizer),
        # POLICY
        (policy_agent, synthesizer),
    ],
)
```

   The **intent** of those lines is correct. The **spelling** is not. ADK 2.6.3 parses a tuple as a **chain of nodes**. The third slot `"WISMO"` is not a node (not a callable, not `START`, not a `BaseNode`). Construction raises `ValidationError` (`input_value='WISMO'`).

   Labeled edges are a **routing map**: a dict whose keys are `Event.actions.route` values and whose values are the next node — or a **tuple** of nodes for fan-out.

10. Replace the `edges=[...]` list with this — **same graph**, legal 2.6.3 spelling:

```python
join_shortage = JoinNode(name="join_shortage")

root_agent = Workflow(
    name="meridian_orderops",
    description="Native ADK OrderOps graph with HITL refund branch.",
    edges=[
        ("START", route_ticket),
        (
            route_ticket,
            {
                "WISMO": lookup_order,
                "SHORTAGE": lookup_order,
                "REFUND": lookup_order,
                "POLICY": policy_agent,
                "UNSUPPORTED": unsupported_msg,
            },
        ),
        (
            lookup_order,
            {
                "WISMO": order_narrator,
                "SHORTAGE": (order_narrator_shortage, inventory_agent),
                "REFUND": hitl_refund_gate,
            },
        ),
        (order_narrator, synthesizer),
        ((order_narrator_shortage, inventory_agent), join_shortage),
        (join_shortage, synthesizer),
        (hitl_refund_gate, refund_finalize),
        (refund_finalize, synthesizer),
        (policy_agent, synthesizer),
    ],
)
```

    How to read a routing map:

    | Piece | Meaning |
    |-------|---------|
    | Left of the dict | Node that just finished |
    | Keys | Strings that node put on `Event(route=...)` |
    | Values | Next node, **or** `(a, b)` to start both |
    | Tuple with **no** dict | Unconditional edge — always follows |
    | `"SHORTAGE": (order_narrator_shortage, inventory_agent)` | Native fan-out. Both receive the same `OrderFindings`. |
    | `((order_narrator_shortage, inventory_agent), join_shortage)` | Each specialist notifies the join. The join waits for **all**. |

    `JoinNode` output is a dict ADK builds:

    ```python
    {
        "order_narrator_shortage": <that agent's output>,
        "inventory_agent": <that agent's output>,
    }
    ```

    You do not write a merge class. `synthesizer` sees both keys. Lesson 14 tests the predecessor set; today you only need to know the diamond is native.

11. Prove the file **loads**. From the **repo root**:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
source .venv/bin/activate
export PYTHONPATH=project
python - <<'PY'
from google.adk.workflow import Workflow, JoinNode
from meridian_orderops.agent import root_agent, join_shortage, GEMINI

assert GEMINI == "gemini-3.5-flash"
assert isinstance(root_agent, Workflow)
assert isinstance(join_shortage, JoinNode)
assert root_agent.name == "meridian_orderops"
assert root_agent.graph is not None
routes = {e.route for e in root_agent.graph.edges if e.route}
print("routes", sorted(routes))
print("edge_count", len(root_agent.graph.edges))
print("graph loads")
PY
```

    - `export PYTHONPATH=project` — `import meridian_orderops` means `project/meridian_orderops`.
    - You are importing the **same** `root_agent` `adk web` will load. You did not build a second engine.

### Expect

```
routes ['POLICY', 'REFUND', 'SHORTAGE', 'UNSUPPORTED', 'WISMO']
edge_count <a number greater than 10>
graph loads
```

If you still see `ValidationError` / `input_value='WISMO'`, a 3-tuple remains in `edges`. Finish step 10 and rerun.

> **Tip:** Unconditional edges stay 2-tuples: `(order_narrator, synthesizer)`. Only **labeled** hops become dicts.

> **Watch out:** Do not copy this graph into `project/meridian_ops/graph_engine.py`. Extend **this** file. Lesson 14 will join the same `join_shortage`. Lesson 15 will resume the same `hitl_refund_gate`.

### Scoreboard after Task 2

| Control | In place? |
|---------|-----------|
| Native Workflow imports in the existing venv | Yes |
| Routing-map OrderOps graph loads | **Yes** |
| Three tickets in `adk web` | Not yet |
| `InMemoryRunner` authors / routes | Not yet |
| Router pytest (no LLM) | Not yet |

---

## Task 3 — Run the three lab tickets in `adk web`

### Why

A graph that only exists as Python is a diagram. Priya needs to see Maya’s WISMO, Devon’s shortage, and the refund pause in the same UI you used in Lesson 02.

You will send **three** prompts. Each one is chosen so `route_ticket`’s regex / substring table fires a different branch. Do not paraphrase away the keywords — the router is not an LLM.

### Do this

1. Confirm the OMS fixture still has the three orders (Lesson 03). From the repo root:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
source .venv/bin/activate
python - <<'PY'
import json
from pathlib import Path
orders = json.loads(Path("project/meridian_ops/fixtures/orders.json").read_text())
for oid in ("MC-1048292", "MC-1048310", "MC-1048277"):
    o = orders[oid]
    print(oid, o["lifecycle"], "pod=", o.get("pod_photo_present"), "total=", o.get("order_total_usd"), "short=", o.get("shorted_sku"))
PY
```

   Expect `delivered` / `ready_for_pickup` / `delivered`, `pod=False` on `MC-1048292`, `short=884210` on `MC-1048310`, `total=214.55` on `MC-1048277`.

2. Launch the UI from `project/` — ADK discovers **packages next to the working directory**, not from the repo root:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme/project
source ../.venv/bin/activate
export PYTHONPATH=.
export GOOGLE_API_KEY="YOUR_KEY"
adk web --port 8000
```

   | Flag / env | What it does |
   |------------|----------------|
   | `cd .../project` | Discovery root. `meridian_orderops/` must be a **child** of cwd. |
   | `source ../.venv/bin/activate` | Same interpreter as Task 1. The venv lives at the **repo** root. |
   | `export PYTHONPATH=.` | `from meridian_ops.tools.oms import get_order` resolves. |
   | `export GOOGLE_API_KEY=...` | Language nodes call Gemini. Function nodes do not need it; the graph still has narrators. |
   | `adk web --port 8000` | Dev UI at `http://localhost:8000`. `--port` picks the listen port so it matches Lessons 02 / 07 / 08. |

   If port 8000 is taken, stop the old process (`Ctrl+C` in that terminal) or pass `--port 8001` and use that URL.

3. In the browser, open `http://localhost:8000`. Select **`meridian_orderops`** (the Workflow name). New session for **each** prompt so routes do not leak across tickets.

4. Prompt A — **WISMO** (`TCK-9001`, order `MC-1048292`). Paste exactly:

```
What's the status of order MC-1048292? nothing at the door
```

   Why this text: no `refund`, no `atp`/`sku`/`substitute`/`shorted`, no `policy` → `route_ticket` emits `WISMO`. `lookup_order` loads delivered + `pod_photo_present=false`.

5. Prompt B — **SHORTAGE** (`TCK-9003`, order `MC-1048310`). New session. Paste exactly:

```
ATP shows 0 for organic milk SKU 884210 on pickup order MC-1048310 due in 90 minutes. Need substitute guidance.
```

   Why this text: `ATP`, `SKU`, and `substitute` are what the router keys on. `MC-1048310` is what OMS loads. Lesson 14 studies the join dict; today you only need to see **both** specialists before the customer reply.

6. Prompt C — **REFUND** (`TCK-9004`, order `MC-1048277`). New session. Paste exactly:

```
I want a full refund of $214.55 for melted items on MC-1048277
```

   Why this text: substring `refund` wins over everything except the batch keywords. Amount is over $75. The graph must **pause**.

   Optional: when the UI asks, reply `APPROVE melted dairy verified` or `DENY insufficient evidence`. You should see `refund_finalize` then `synthesizer`. Pausing **is** the pass for this lesson. Overnight resume is Lesson 15.

### Expect

Open the trajectory / event list for each session. Match this table before you leave the UI:

| Prompt | `actions.route` you should see | Nodes that must run | Nodes that must **not** run | What the customer-facing text should do |
|--------|--------------------------------|---------------------|-----------------------------|----------------------------------------|
| A `MC-1048292` | `WISMO` | `route_ticket` → `lookup_order` → `order_narrator` → `synthesizer` | `inventory_agent`, `hitl_refund_gate` | Delivered, **no POD photo**, a next step (investigate missing delivery). No “we refunded.” |
| B `MC-1048310` | `SHORTAGE` | `lookup_order` → `order_narrator_shortage` **and** `inventory_agent` → `join_shortage` → `synthesizer` | `hitl_refund_gate` | Shortage / substitute **preview** language. Must **not** claim a reservation was committed. |
| C `MC-1048277` | `REFUND` | `lookup_order` → `hitl_refund_gate` | `synthesizer` until you resume | UI shows Priya the `RequestInput` message. Trajectory contains a function call named `adk_request_input`. |

If WISMO invents a POD photo, `lookup_order` did not run or the narrator ignored findings — check the event list for `lookup_order` and `pod_photo_present`.

If SHORTAGE never starts `inventory_agent`, the routing map value is not a tuple, or you reused one narrator object on two paths.

If REFUND drafts a customer apology **without** pausing, `hitl_refund_gate` is not on the `REFUND` value. Do not “fix” it with a stronger synthesizer instruction.

> **Tip:** Function nodes are cheap and deterministic. Language nodes are where Gemini spends money. That is why the router is Python.

> **Watch out:** Do not save Priya’s APPROVE into a JSON file next to the repo and call it resume. ADK owns the interrupt. Lesson 15 is the resume lesson.

### Scoreboard after Task 3

| Control | In place? |
|---------|-----------|
| Native Workflow imports in the existing venv | Yes |
| Routing-map OrderOps graph loads | Yes |
| Three tickets in `adk web` | **Yes** |
| `InMemoryRunner` authors / routes | Not yet |
| Router pytest (no LLM) | Not yet |

---

## Task 4 — `App` + `InMemoryRunner` (authors and routes)

### Why

`adk web` is a flashlight. Services and CI do not click a browser. They wrap the same `root_agent` in an `App` and stream events from a `Runner`.

`InMemoryRunner` is ADK’s in-memory `Runner`: session, memory, and artifacts live in this process. You used it in Lesson 08 on Order Status. Today the root is a **Workflow**.

Two facts the test must lock:

1. **`event.author`** — ADK attributes child events to the Workflow name (`meridian_orderops`). The user message is `"user"`.
2. **`event.node_name`** / **`event.actions.route`** — which **node** ran, and which **branch** it emitted.

If you only assert `len(events) > 0`, a broken router still passes.

This test **does** call Gemini on the WISMO path (narrator + synthesizer). It is not a PR-free unit test. Task 5 is.

### Do this

1. Create `project/meridian_ops/tests/test_orderops_workflow_runner.py`:

```python
import pytest
from google.adk.apps import App
from google.adk.runners import InMemoryRunner
from google.genai import types

from meridian_orderops.agent import root_agent

APP_NAME = "meridian_orderops"
USER_ID = "eval_user"


def _user(text: str) -> types.Content:
    return types.Content(role="user", parts=[types.Part.from_text(text=text)])


def _node_names(events) -> set[str]:
    return {e.node_name for e in events if getattr(e, "node_name", "")}


def _routes(events) -> set:
    return {e.actions.route for e in events if e.actions and e.actions.route}


def _function_call_names(events) -> list[str]:
    names = []
    for event in events:
        for call in event.get_function_calls():
            names.append(call.name)
    return names


@pytest.mark.live_eval
@pytest.mark.asyncio
async def test_wismo_runner_authors_and_route():
    app = App(name=APP_NAME, root_agent=root_agent)
    runner = InMemoryRunner(app=app)
    session = await runner.session_service.create_session(
        app_name=APP_NAME, user_id=USER_ID
    )

    events = []
    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=session.id,
        new_message=_user("What's the status of order MC-1048292? nothing at the door"),
    ):
        events.append(event)

    assert events, "Workflow produced no events"

    authors = {e.author for e in events if e.author}
    assert "user" in authors
    assert "meridian_orderops" in authors

    nodes = _node_names(events)
    assert {"route_ticket", "lookup_order", "order_narrator", "synthesizer"} <= nodes
    assert "hitl_refund_gate" not in nodes
    assert "inventory_agent" not in nodes

    assert "WISMO" in _routes(events)
    assert "REFUND" not in _routes(events)
    assert "SHORTAGE" not in _routes(events)


@pytest.mark.live_eval
@pytest.mark.asyncio
async def test_refund_runner_pauses_with_request_input():
    app = App(name=APP_NAME, root_agent=root_agent)
    runner = InMemoryRunner(app=app)
    session = await runner.session_service.create_session(
        app_name=APP_NAME, user_id=USER_ID
    )

    events = []
    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=session.id,
        new_message=_user(
            "I want a full refund of $214.55 for melted items on MC-1048277"
        ),
    ):
        events.append(event)

    assert events, "Workflow produced no events"
    assert "REFUND" in _routes(events)
    assert "adk_request_input" in _function_call_names(events)
    assert "synthesizer" not in _node_names(events)
```

   Walk the ADK 2.6.3 signatures (same as Lesson 08, Workflow as `root_agent`):

   | Piece | Why |
   |-------|-----|
   | `App(name=..., root_agent=root_agent)` | `root_agent` accepts a `BaseAgent` **or** a `BaseNode`. `Workflow` is a `BaseNode`. |
   | `InMemoryRunner(app=app)` | In-memory session service. No extra constructor args. |
   | `create_session(app_name=..., user_id=...)` | Keyword-only. `session.id` is what `run_async` needs. |
   | `async for event in runner.run_async(...)` | Native stream. Not a `while True: model.generate()` loop. |
   | `event.author` | `"user"` plus `"meridian_orderops"` — Workflow stamps children with its own name. |
   | `event.node_name` | The node in `node_info.path` (e.g. `route_ticket`). This is how you see the lane. |
   | `event.actions.route` | `"WISMO"` / `"REFUND"` — **not** `event.route`. |
   | `event.get_function_calls()` | HITL interrupt is `adk_request_input`. |
   | `@pytest.mark.live_eval` | Lesson 08’s marker: skip on the free PR job. |
   | `@pytest.mark.asyncio` | The test `await`s. |

2. Run **this file only** so the live marker does not hide it. From the **repo root**:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
source .venv/bin/activate
export PYTHONPATH=project
export GOOGLE_API_KEY="YOUR_KEY"
pip install -q pytest-asyncio
pytest project/meridian_ops/tests/test_orderops_workflow_runner.py -v
```

   | Flag | What it does |
   |------|----------------|
   | `-v` | Verbose: print each test name, not a single dot. |
   | `PYTHONPATH=project` | Same as Task 2. |
   | `GOOGLE_API_KEY` | WISMO test reaches `order_narrator`. Refund test may stop at HITL before a second model call; still set it. |

### Expect

```
test_orderops_workflow_runner.py::test_wismo_runner_authors_and_route PASSED
test_orderops_workflow_runner.py::test_refund_runner_pauses_with_request_input PASSED
```

If `synthesizer` appears on the refund test, the graph did not pause — `RequestInput` is not on the REFUND edge.

If `event.route` raises `AttributeError`, you asserted the convenience kwarg as a field. Use `event.actions.route`.

If authors are only `"user"`, the Workflow never ran (wrong `root_agent`, or `run_async` was not awaited).

> **Tip:** You can print `{e.node_name: e.actions.route for e in events}` once while debugging. Do not leave that print in the committed test.

> **Watch out:** Do not mock `root_agent` with a stub planner that returns fake routes. That tests the stub. Lesson 08 already forbade it.

### Scoreboard after Task 4

| Control | In place? |
|---------|-----------|
| Native Workflow imports in the existing venv | Yes |
| Routing-map OrderOps graph loads | Yes |
| Three tickets in `adk web` | Yes |
| `InMemoryRunner` authors / routes | **Yes** |
| Router pytest (no LLM) | Not yet |

---

## Task 5 — Unit-test the deterministic nodes (no Gemini)

### Why

`route_ticket` and `lookup_order` are cash-register logic. They must pass on a PR with the network off. The old stub in this lesson waved at `Context` and then tested `get_order` instead. You will test the **nodes**.

`lookup_order(ctx, node_input)` declares `ctx` because ADK injects `Context` at runtime. The body never uses it. A dummy object is enough. You do not invent a fake Context framework.

### Do this

1. Create `project/meridian_ops/tests/test_orderops_route_nodes.py` (replace any stub of the same name):

```python
from google.adk.workflow import JoinNode, Workflow
from google.genai import types

from meridian_orderops.agent import (
    GEMINI,
    OrderFindings,
    RouteDecision,
    join_shortage,
    lookup_order,
    root_agent,
    route_ticket,
    unsupported_msg,
)


def _user(text: str) -> types.Content:
    return types.Content(role="user", parts=[types.Part.from_text(text=text)])


class _UnusedCtx:
    """lookup_order requires ctx in its signature; the body does not read it."""


def test_model_is_flash_35():
    assert GEMINI == "gemini-3.5-flash"


def test_workflow_is_native_and_named():
    assert isinstance(root_agent, Workflow)
    assert root_agent.name == "meridian_orderops"
    assert isinstance(join_shortage, JoinNode)
    routes = {e.route for e in root_agent.graph.edges if e.route}
    assert {"WISMO", "SHORTAGE", "REFUND", "POLICY", "UNSUPPORTED"} <= routes


def test_route_wismo_mc_1048292():
    ev = route_ticket(_user("What's the status of order MC-1048292? nothing at the door"))
    assert ev.actions.route == "WISMO"
    assert ev.output.order_id == "MC-1048292"


def test_route_shortage_mc_1048310():
    ev = route_ticket(
        _user(
            "ATP shows 0 for organic milk SKU 884210 on pickup order MC-1048310. Need substitute."
        )
    )
    assert ev.actions.route == "SHORTAGE"
    assert ev.output.order_id == "MC-1048310"


def test_route_refund_mc_1048277():
    ev = route_ticket(
        _user("I want a full refund of $214.55 for melted items on MC-1048277")
    )
    assert ev.actions.route == "REFUND"
    assert ev.output.order_id == "MC-1048277"


def test_route_unsupported_batch():
    ev = route_ticket(
        _user("Nightly: recompute loyalty points for segment WEST-14.")
    )
    assert ev.actions.route == "UNSUPPORTED"


def test_route_policy_without_refund():
    ev = route_ticket(
        _user("What's Meridian's policy on late grocery delivery credits?")
    )
    assert ev.actions.route == "POLICY"


def test_refund_keyword_beats_sku():
    ev = route_ticket(_user("refund the shorted SKU 884210 on MC-1048310"))
    assert ev.actions.route == "REFUND"


def test_lookup_order_wismo_fixture():
    ev = lookup_order(
        _UnusedCtx(),
        RouteDecision(route="WISMO", order_id="MC-1048292"),
    )
    assert ev.actions.route == "WISMO"
    assert isinstance(ev.output, OrderFindings)
    assert ev.output.order_id == "MC-1048292"
    assert ev.output.lifecycle == "delivered"
    assert ev.output.pod_photo_present is False
    assert ev.output.raw_status == "success"


def test_lookup_order_missing_id_keeps_route():
    ev = lookup_order(_UnusedCtx(), RouteDecision(route="REFUND", order_id=None))
    assert ev.actions.route == "REFUND"
    assert ev.output.raw_status == "MISSING_ORDER_ID"


def test_lookup_order_unknown_id():
    ev = lookup_order(
        _UnusedCtx(),
        RouteDecision(route="WISMO", order_id="MC-0000000"),
    )
    assert ev.output.raw_status == "ORDER_NOT_FOUND"
    assert ev.actions.route == "WISMO"


def test_unsupported_msg_is_out_of_scope():
    out = unsupported_msg(None)
    assert "out of scope" in out["customer_reply_draft"].lower()
```

   What each cluster locks:

   | Tests | If they failed, you would have… |
   |-------|----------------------------------|
   | `test_workflow_is_native_and_named` | …left 3-tuples in `edges`, or renamed the Workflow |
   | `test_route_*` | …changed keyword order so WISMO steals refunds (or the reverse) |
   | `test_refund_keyword_beats_sku` | …put SHORTAGE before REFUND and money-shaped shorts would skip Priya |
   | `test_lookup_order_wismo_fixture` | …stopped calling `get_order` / dropped `route=` on the way out |
   | `test_lookup_order_missing_id_keeps_route` | …blanked the route when OMS cannot run |

2. Run only this file — **no API key**:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
source .venv/bin/activate
export PYTHONPATH=project
pytest project/meridian_ops/tests/test_orderops_route_nodes.py -v
```

   `-v` — print each test name.

### Expect

Twelve `PASSED` lines. No Gemini. No network.

If `test_workflow_is_native_and_named` errors while **importing** `root_agent`, Task 2’s routing map is incomplete.

If `assert ev.route == "WISMO"` is in your file, change it to `ev.actions.route`. There is no `Event.route` field on 2.6.3.

> **Tip:** Keep this file on the PR job (`pytest -m "not live_eval"` from Lesson 08). The runner file stays on nightly.

> **Watch out:** Do not instantiate a real `Context` with a homemade session just to call `lookup_order`. The dummy is honest: the function does not read `ctx`.

### Scoreboard after Task 5

| Control | In place? |
|---------|-----------|
| Native Workflow imports in the existing venv | Yes |
| Routing-map OrderOps graph loads | Yes |
| Three tickets in `adk web` | Yes |
| `InMemoryRunner` authors / routes | Yes |
| Router pytest (no LLM) | **Yes** |

---

## How it works (deeper dive)

### Convenience kwargs vs what you assert

```python
return Event(output=decision, route="WISMO", state={"active_order_id": "MC-1048292"})
```

ADK’s `Event._accept_convenience_kwargs` moves:

| You write | You read later |
|-----------|----------------|
| `route="WISMO"` | `event.actions.route` |
| `state={...}` | `event.actions.state_delta` |
| `output=decision` | `event.output` (this one **is** a real field) |

### Edge shapes ADK 2.6.3 actually parses

```python
# unconditional (chain)
("START", route_ticket)
(order_narrator, synthesizer)

# labeled (routing map) — keys are actions.route
(route_ticket, {"WISMO": lookup_order, "REFUND": lookup_order})

# fan-out as a map value
(lookup_order, {"SHORTAGE": (order_narrator_shortage, inventory_agent)})

# fan-in
((order_narrator_shortage, inventory_agent), join_shortage)
```

A 3-tuple `(lookup_order, order_narrator, "WISMO")` is **not** a labeled edge. It is a three-step chain whose third node is the string `"WISMO"`. Pydantic rejects it.

### Who is `event.author`?

Inside `Workflow._run_impl`, ADK sets `ctx.event_author = self.name` (`meridian_orderops`). `_enrich_event` then writes `event.author = ctx.event_author or self._node.name`.

So:

| You want to know | Read |
|------------------|------|
| Did the user speak? | `event.author == "user"` |
| Did this Workflow run? | `event.author == "meridian_orderops"` |
| Which node? | `event.node_name` |
| Which branch? | `event.actions.route` |

### Hybrid rule card (edges vs LLM)

| Step | Node type | Why |
|------|-----------|-----|
| Ticket route | function + `Event(route=...)` | Authz / path law |
| OMS `get_order` | function | Source of truth |
| Narrate status | `LlmAgent` | Language |
| Shortage inventory preview | `LlmAgent` | Language, preview-only instruction |
| Fan-in | `JoinNode` | Wait for both specialists |
| HITL approve | `RequestInput` | Human gate |
| Refund finalize label | function | No model near the money flag |
| Customer reply | `LlmAgent` | Empathy → Facts → Next step |

### Template agents?

`SequentialAgent` / `ParallelAgent` / `LoopAgent` still import. They are literacy for **old** packages. New Meridian graphs use `Workflow`. Lesson 14 is join + routed cycle + `@node(parallel_worker=True)` — still `Workflow`.

---

## Common pitfalls / troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `ValidationError` … `input_value='WISMO'` | 3-tuple labeled edge | Routing map (Task 2 step 10) |
| `No module named google.adk.workflow` | Wrong / empty venv | `source .venv/bin/activate`; `pip install "google-adk==2.6.3"` |
| `ModuleNotFoundError: meridian_orderops` | `PYTHONPATH` unset | Repo root: `export PYTHONPATH=project`. `adk web`: cwd `project/` and `PYTHONPATH=.` |
| UI shows no `meridian_orderops` | `adk web` from repo root | `cd project` first |
| WISMO claims a POD photo | Narrator ignored findings, or lookup skipped | Trajectory must include `lookup_order`; fixture has `pod_photo_present: false` |
| SHORTAGE never calls inventory | Map value is not a 2-tuple, or one narrator reused | Two `LlmAgent` instances; `"SHORTAGE": (order_narrator_shortage, inventory_agent)` |
| Refund drafts a reply with no pause | `hitl_refund_gate` not on `REFUND` | Check the second routing map |
| `AttributeError: route` in pytest | Asserted `ev.route` | `ev.actions.route` |
| Tempted to write `MeridianGraph` | Frustration with edges | Stop. Extend `meridian_orderops/agent.py` |
| Duplicate node name | Two nodes named `order_narrator` | The shortage narrator exists for this reason |

---

## You are done when

- [ ] Existing `.venv` sourced; `Workflow` / `JoinNode` / `RequestInput` / `App` / `InMemoryRunner` import
- [ ] `root_agent` loads as a `Workflow` with a routing map (no 3-tuple `"WISMO"`)
- [ ] `GEMINI == "gemini-3.5-flash"`
- [ ] `adk web` ran WISMO `MC-1048292`, SHORTAGE `MC-1048310`, REFUND `MC-1048277`
- [ ] Refund paused on `adk_request_input` / `RequestInput`
- [ ] `InMemoryRunner` tests assert authors + `WISMO`/`REFUND` routes
- [ ] `test_orderops_route_nodes.py` is green **without** an API key
- [ ] Zero DIY graph engines in your changes

---

## Knowledge check

1. What ADK type replaces a home-grown edge runner?  
2. You write `Event(route="WISMO")`. What do you **assert** in pytest?  
3. Why does `lookup_order` re-emit the same route it received?  
4. Why are `order_narrator` and `order_narrator_shortage` two objects?  
5. What does `JoinNode` pass downstream?  
6. A refund turn in `InMemoryRunner` should contain which function-call name, and should `synthesizer` have run yet?  
7. Why is `RequestInput` preferred over a JSON checkpoint file next to the repo?

### Answers

1. `Workflow`.  
2. `event.actions.route == "WISMO"` — there is no `event.route` field.  
3. WISMO / SHORTAGE / REFUND share one OMS node. The **second** routing map splits after the fixture read.  
4. Unique names + unique objects. Reusing one narrator on WISMO and on the join ties those paths together.  
5. A dict keyed by predecessor **names** (`order_narrator_shortage`, `inventory_agent`).  
6. `adk_request_input`. No — the graph is paused; `synthesizer` is after `refund_finalize`.  
7. ADK owns pause, session, and resume. A side file is a second framework (Lesson 15).

---

## Recap

**What you built today:** a mental model (and tests) for the OrderOps `Workflow` that already lives in this repo — router, OMS hop, three customer paths, join, HITL — spelled so ADK 2.6.3 will load it.

**What you now understand:** path law is `Event(route=...)` plus a routing map; language is `LlmAgent`; money flags and OMS facts are function nodes; `author` is the Workflow, `node_name` is the lane.

**What you can do next:** Lesson 14 zooms into the SHORTAGE diamond and a routed critic loop. Same engine. Still no `MeridianGraph`.

---

## Stretch goal

Keep the router in Python. Add a function node `retrieve_policy_node` that calls `meridian_ops.tools.policy_rag.retrieve_policy` and put it **before** `policy_agent` on the `POLICY` value of the first routing map (`"POLICY": retrieve_policy_node`, then `(retrieve_policy_node, policy_agent)`). Still no DIY bus. Lesson 16 will serve tools over MCP; Lesson 17 will optionally replace in-process policy with `RemoteA2aAgent`.

---

## Feedback

- Could you add a `SCHEDULE` route with only `Event(route="SCHEDULE")` plus one routing-map key — without a second graph package?  
- What tripped you up: sourcing the venv, 3-tuples vs maps, two narrators, `actions.route`, HITL in the UI, or runner authors?  
- Note the **task number** and what you expected vs what happened (command + first lines of output). That is the signal that improves this lesson — “it was confusing” is not.

---

## Navigate

**← Prev** [Lesson 12 — Deployment & ops](12-deployment-ops.md)  
**Next →** [Lesson 14 — Parallel, loop & custom agents](14-parallel-loop-custom-agents.md)  
**Track home:** [README](../README.md)  
**Native standard:** [NATIVE-ADK.md](../docs/NATIVE-ADK.md)

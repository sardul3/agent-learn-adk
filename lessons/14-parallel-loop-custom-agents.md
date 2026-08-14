# Lesson 14 — Parallel, loop & custom nodes (native ADK)

**Level:** Advanced  
**Time:** ~120–150 minutes  
**Prerequisites:** Lesson 13 (`Workflow` running, OrderOps graph in `adk web`)  
**Lab outcome:** You can explain the OrderOps **SHORTAGE** diamond, run the **critic loop** already in the repo, add a **store allowlist** function node, and map a list with `@node(parallel_worker=True)` — all native ADK, no home-grown parallel runtime

**Standard:** [docs/NATIVE-ADK.md](../docs/NATIVE-ADK.md)

---

## At a glance

Lesson 13 gave you a `Workflow`: tickets follow **edges**, not hopes in a prompt. Today you learn the three native ways a graph does more than a straight line — and you prove each one in this repo.

| Need | Native ADK | Meridian lab |
|------|------------|--------------|
| Two specialists at once, then merge | `edges` fan-out tuple + `JoinNode` | OrderOps **SHORTAGE** path |
| Retry a draft until it is safe, then stop | Routed cycle (`Event(route=...)`) + a counter in state | `meridian_reply_loop` |
| Gate a store id in code | Function node returning `Event(route="OK"\|"REJECT")` | Store allowlist |
| Same function once per list item | `@node(parallel_worker=True)` | Map `[1, 2, 3]` → `[2, 4, 6]` |
| Old template names in other codebases | `ParallelAgent` / `LoopAgent` (read only) | Not what you build today |

You will **not** invent `MeridianGraphParallel`. You will **not** write `while True` around Gemini. You will open the files that already exist, walk them line by line, then add tests and two small graphs.

```
SHORTAGE diamond (already in OrderOps)
─────────────────────────────────────
lookup_order ──SHORTAGE──► order_narrator_shortage ──┐
                     └──► inventory_agent          ──┴─► join_shortage ─► synthesizer

Critic loop (already in meridian_reply_loop)
───────────────────────────────────────────
START → drafter → critic → bump_and_route
              ▲                    │
              └── FAIL ────────────┤
                                   ├── PASS    → done_pass
                                   └── GIVE_UP → done_give_up
```

---

## Why this matters

Devon (picker at Store `ST-221`) has pickup order `MC-1048310`. Organic milk SKU `884210` is **shorted** — ATP is 0, the window is 90 minutes. Ticket `TCK-9003`.

Two jobs must happen **together**:

1. OMS findings → a short order narrative (what the order *is*).
2. Inventory guidance → substitute language (what Devon *might* pick) — preview only, no fake reservation.

If those two writers dump into one shared `findings` blob, Priya (CX supervisor) cannot tell who said what. If you wait for inventory before you even *start* the order narrative, Maya’s chat sits idle while one specialist thinks.

Same afternoon, a drafter agent writes Maya a customer update and claims **“we refunded.”** Finance did not. A loop that retries forever burns money. A loop with no exit is a bug ADK will refuse to load.

Today you use the primitives ADK already ships: **join**, **routed cycle**, **function-node gate**, **list map**.

---

## Know these

Read this table before Task 1. Every later task reuses these words.

| Term | Plain English | Meridian example |
|------|---------------|------------------|
| **Fan-out** | One node triggers **two or more** next nodes at the same time | After `lookup_order` on SHORTAGE: narrator **and** inventory |
| **Fan-in / join** | Wait until **every** listed upstream node has finished, then continue | `join_shortage` |
| **JoinNode** | The native fan-in node. Its input is a **dict** keyed by the **names** of the nodes that fed it | `{"order_narrator_shortage": ..., "inventory_agent": ...}` |
| **Routing map** | A dict in an edge: `{ "SHORTAGE": next_node }`. ADK follows the key that matches `Event(route=...)` | `"SHORTAGE"` → the diamond |
| **Routed cycle** | An edge that goes **back** to an earlier node, but only for a named route | `FAIL` → `drafter` again |
| **Function node** | Ordinary Python in the graph. ADK wraps the function. Prefer this over subclassing `Node` | `critic`, `store_guard` |
| **`Event.output`** | The value the next node receives as `node_input` | A `CriticVerdict`, a dict, a list |
| **`Event(route=...)`** | Label that picks the next **labeled** edge | `"PASS"`, `"GIVE_UP"`, `"OK"` |
| **`Event(state={...})`** | A small patch merged into session state | `{"loop_i": 2}` |
| **`output_key`** | On an `LlmAgent`: also write the model text into session state under that key | `inventory_narrative` |
| **`parallel_worker`** | Run **one** node once per item in a **list**, at the same time | Double `[1, 2, 3]` |
| **`ParallelAgent` / `LoopAgent`** | Older ADK templates. Still importable. New Meridian graphs use `Workflow` | Read old code; do not start a new graph with them |

### Picture this: two pickers, one clipboard, one manager key

| Graph idea | Store 441 analogue | What goes wrong if you skip the native primitive |
|------------|--------------------|--------------------------------------------------|
| Fan-out + `JoinNode` | Devon and the dairy lead both walk the case, then meet at the desk | One overwrites the other’s notes; or the customer waits for a fake “merge helper” you wrote |
| Routed cycle | “Rewrite the shelf tag” until it is honest, max two tries | Infinite reprints / infinite model calls |
| Function node gate | Barcode scanner: unknown store beeps | The model *describes* ST-999 as if it were real |
| `@node(parallel_worker=True)` | Same scan motion on three SKUs | A thread pool you now have to debug |

> **Tip:** `JoinNode` is for a **known pair** (or trio) of named specialists. `@node(parallel_worker=True)` is for a **list whose length you only learn at runtime**. Different tools. Task 5 puts them in one table so you stop mixing them up.

---

## What you already have (do not rebuild)

From the **repo root**, confirm these exist. Lesson 13 left the OrderOps graph. The critic loop package is already in the tree — today you **teach it**, you do not start a second loop.

| Path | Job |
|------|-----|
| `project/meridian_orderops/agent.py` | Native `Workflow` with a SHORTAGE fan-out + `JoinNode` |
| `project/meridian_orderops/__init__.py` | `from . import agent` so `adk web` can load the package |
| `project/meridian_reply_loop/agent.py` | Drafter → code critic → bump/route loop |
| `project/meridian_reply_loop/__init__.py` | Same doorbell pattern |
| `project/meridian_ops/fixtures/orders.json` | `MC-1048310` is the shorted pickup |
| `project/meridian_ops/fixtures/tickets.json` | `TCK-9003` is Devon’s shortage ticket |

You will **add**:

```
project/meridian_ops/tools/store_allowlist.py     Task 3 helper
project/meridian_ops/tests/test_orderops_join.py  Task 1
project/meridian_ops/tests/test_reply_loop_critic.py  Task 2
project/meridian_ops/tests/test_store_allowlist.py    Task 3
project/meridian_ops/tests/test_double_map.py         Task 4
project/meridian_store_guard/                         Task 3 tiny Workflow
project/meridian_double_map/                          Task 4 tiny Workflow
```

If `meridian_orderops/agent.py` is missing, stop and finish Lesson 13. This lesson extends that graph. It does not replace it.

---

## Task 1 — Walk the SHORTAGE `JoinNode` already in OrderOps

### Why

Priya asks: “When milk is shorted, do we wait for **both** the order story and the inventory story before we text the customer?”

The answer is in edges you can point at, not in a design doc. `project/meridian_orderops/agent.py` already has the diamond. Your job is to **read it**, make the graph load, prove the join with pytest, then watch SHORTAGE run in `adk web`.

### Do this

1. Open `project/meridian_orderops/agent.py`. Find the two narrator agents and the inventory agent. They look like this (the file uses `GEMINI = "gemini-2.5-flash"` today — leave that; Task 2 is where you bump a **new** snippet’s model):

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
```

   Walk what each field is for:

   | Piece | Why it exists |
   |-------|----------------|
   | `name="order_narrator"` vs `name="order_narrator_shortage"` | Graph identity. Two objects, two names. |
   | Same `_ORDER_INSTR` | Same *job* (honest OMS bullets). Different *node*. |
   | `output_key="order_narrative"` on both narrators | Session state key for the WISMO path **or** the shortage path — those routes do not run in the same turn, so they do not collide. |
   | `output_key="inventory_narrative"` | Different key on purpose. Parallel writers must not share one state slot. |
   | Inventory instruction “preview only” | Same Lesson 04 dry-run habit: do not claim a reservation |

   Why **two** narrator instances, not `order_narrator` reused on the diamond:

   - ADK identifies nodes by **object** and by **name**. Reuse the same object and you have one node with two jobs.
   - Put that one node on the WISMO line `(order_narrator, synthesizer)` **and** on the join `(…, join_shortage)`, and finishing a WISMO narrative also pokes the join. Inventory never ran. The join waits forever — or fires with a half-dict. Either way Priya gets a ghost.
   - Duplicate names on two objects fail graph validation: *“Duplicate node names found.”*
   - So: second `LlmAgent(...)`, second name. The comment above `order_narrator_shortage` is the whole lesson in one line.

2. Keep scrolling to the join and the SHORTAGE edges. **Quote the real file** — this is the diamond, not a sketch:

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

   Read the three SHORTAGE lines as a sentence:

   | Edge (as written in the file) | Meaning |
   |-------------------------------|---------|
   | `(lookup_order, (order_narrator_shortage, inventory_agent), "SHORTAGE")` | If `lookup_order` emits route `SHORTAGE`, start **both** specialists |
   | `((order_narrator_shortage, inventory_agent), join_shortage)` | When **each** specialist finishes, it notifies the join. The join waits for **all** |
   | `(join_shortage, synthesizer)` | After the wait, one synthesizer sees **both** outputs |

   What `JoinNode` actually passes downstream: a **dict keyed by predecessor names**. For this join that is:

   ```python
   {
       "order_narrator_shortage": <that agent's output>,
       "inventory_agent": <that agent's output>,
   }
   ```

   ADK builds the dict. You do not write a merge class. `synthesizer` receives that dict as `node_input`. Priya can still tell the keys apart.

3. ADK 2.6.3 reads a **routing map** (a dict) for labeled edges. A third tuple slot that is only the string `"SHORTAGE"` is not a node, so `Workflow(...)` will not load. Same diamond. Legal spelling. Replace the `edges=[...]` list with this (WISMO / REFUND / POLICY stay; only the *spelling* of routes changes):

```python
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
```

   How to read a routing map:

   - Left of the dict: the node that just finished (`lookup_order`).
   - Keys: the `route` strings that node emitted (`Event(route="SHORTAGE")` inside `lookup_order`).
   - Values: the next node, **or** a tuple of nodes (fan-out).
   - `"SHORTAGE": (order_narrator_shortage, inventory_agent)` is the native parallel trigger. Both get the same `lookup_order` output.

4. Put a short comment on the join so the next reader does not invent a merge helper. Replace `join_shortage = JoinNode(name="join_shortage")` with:

```python
# JoinNode waits until BOTH shortage specialists finish.
# node_input is a dict keyed by predecessor names:
#   "order_narrator_shortage", "inventory_agent"
# Do not smash those into one "findings" state key — Priya must see who said what.
join_shortage = JoinNode(name="join_shortage")
```

5. Prove the join in pytest — import the objects, do not write a markdown diary. Create `project/meridian_ops/tests/test_orderops_join.py`:

```python
from google.adk.workflow import JoinNode

from meridian_orderops.agent import (
    inventory_agent,
    join_shortage,
    order_narrator,
    order_narrator_shortage,
    root_agent,
)


def test_join_shortage_is_join_node():
    assert isinstance(join_shortage, JoinNode)
    assert join_shortage.name == "join_shortage"


def test_two_narrator_instances_have_distinct_names():
    assert order_narrator is not order_narrator_shortage
    assert order_narrator.name == "order_narrator"
    assert order_narrator_shortage.name == "order_narrator_shortage"


def test_join_predecessors_are_the_shortage_pair():
    incoming = {
        edge.from_node.name
        for edge in root_agent.graph.edges
        if edge.to_node.name == "join_shortage"
    }
    assert incoming == {"order_narrator_shortage", "inventory_agent"}
```

   What each test locks:

   | Test | If it failed, you would have… |
   |------|-------------------------------|
   | `test_join_shortage_is_join_node` | …written a fake merge function named `join_shortage` |
   | `test_two_narrator_instances_have_distinct_names` | …reused one `LlmAgent` on two paths |
   | `test_join_predecessors_are_the_shortage_pair` | …joined the wrong nodes (or forgotten the tuple edge) |

   The last test is how you **see** the dict keys without running Gemini: predecessor **names** in, dict keys out.

6. Run the tests. From the **repo root**:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
source .venv/bin/activate
export PYTHONPATH=project
pytest project/meridian_ops/tests/test_orderops_join.py -v
```

   - `source .venv/bin/activate` — use this project’s Python, not Homebrew’s.
   - `export PYTHONPATH=project` — `import meridian_orderops` means `project/meridian_orderops`.
   - `-v` — verbose: print each test name, not just a dot.

7. Run the diamond in the UI. From `project/` (ADK discovers packages next to where you launch):

```bash
cd /Users/alishaghatane/dev/agent-learn-sme/project
source ../.venv/bin/activate
export PYTHONPATH=.
adk web --port 8000
```

   - `--port 8000` — keep the UI on `http://localhost:8000`, same URL as Lessons 02 and 13.
   - Press `Ctrl+C` in an old `adk web` first if port 8000 is already taken.

   In the UI, select **meridian_orderops**. Send Devon’s shortage ticket (the words `ATP`, `SKU`, and `substitute` are what `route_ticket` uses to choose `SHORTAGE`; `MC-1048310` is what `lookup_order` loads):

```
ATP shows 0 for organic milk SKU 884210 on pickup order MC-1048310 due in 90 minutes. Need substitute guidance.
```

### Expect

Three `PASSED` lines:

```
test_orderops_join.py::test_join_shortage_is_join_node PASSED
test_orderops_join.py::test_two_narrator_instances_have_distinct_names PASSED
test_orderops_join.py::test_join_predecessors_are_the_shortage_pair PASSED
```

If pytest dies on `ValidationError` while importing `root_agent`, the `edges=` list still has 3-tuples like `(lookup_order, …, "SHORTAGE")`. Finish step 3 and rerun.

In `adk web`:

- The turn is **not** a single `order_narrator` line. You should see **order_narrator_shortage** and **inventory_agent**, then **join_shortage**, then **synthesizer**.
- Inventory language stays preview / dry-run. It must not say a reservation was committed.
- A WISMO prompt (`What's the status of order MC-1048292? nothing at the door`) must **not** start `inventory_agent`. That is how you know the diamond is on the `SHORTAGE` route only.

> **Tip:** `route_ticket` is still the Lesson 13 function node: regex on the user text, `Event(route="SHORTAGE", ...)`. `lookup_order` looks up OMS and **re-emits** the same route so the second routing map can fan out. Path law stays in code.

> **Watch out:** Do not point both parallel agents at `output_key="findings"`. `JoinNode` already namespaces by node name. A shared `output_key` is a second, racy copy in session state.

> **Watch out:** `adk web` does not reliably reload `agent.py`. Restart the process after the routing-map edit.

### Scoreboard after Task 1

| Primitive | In place? |
|-----------|-----------|
| `JoinNode` diamond on SHORTAGE | **Yes** — read, loaded, tested, run |
| Routed critic loop | Not yet (file exists; you have not walked it) |
| Store allowlist function node | Not yet |
| `@node(parallel_worker=True)` list map | Not yet |
| Mapping table (Join vs loop vs function vs old templates) | Not yet |

---

## Task 2 — Walk the critic loop that already lives in `meridian_reply_loop`

### Why

A customer update that says “we refunded” is a Finance incident. Asking Gemini to “please not lie” is the employee handbook. A **function node** that searches the draft for banned phrases is the cash register.

The loop already exists at `project/meridian_reply_loop/agent.py`. You will walk every piece, switch the drafter to `gemini-3.5-flash`, spell the exits as a routing map, unit-test `critic()` with the banned phrase **we refunded**, then run it in `adk web`.

You will **not** start a second graph with different node names.

### Do this

1. Open `project/meridian_reply_loop/agent.py` from the top. First, the verdict shape and the drafter:

```python
class CriticVerdict(BaseModel):
    status: str
    reason: str = ""


drafter = LlmAgent(
    name="drafter",
    model="gemini-2.5-flash",
    instruction="""
Draft a Meridian customer update.
Must include a 'Next step:' line.
Never say a refund was already issued unless tools proved it (they did not).
""".strip(),
    output_key="draft",
)
```

   Change the model line to:

```python
    model="gemini-3.5-flash",
```

   | Piece | Why it exists |
   |-------|----------------|
   | `CriticVerdict` | A tiny typed object the rest of the graph can read (`status`, `reason`). Not a paragraph. |
   | `status: str` | `"PASS"` or `"FAIL"` — the bump node branches on this, not on vibes |
   | `reason: str = ""` | Why it failed (`banned_refund_claim`, `missing_next_step`). Empty on pass. |
   | Drafter instruction “Must include a `Next step:` line” | Gives the critic something mechanical to search for |
   | “Never say a refund was already issued” | Handbook. The critic still checks. Defense in depth. |
   | `output_key="draft"` | Session state keeps the last draft so you can open it in the UI |

2. Walk `critic` — this is the cash register. It is **code**. It does not call Gemini.

```python
def critic(node_input) -> Event:
    text = node_input
    if isinstance(node_input, types.Content):
        text = " ".join((p.text or "") for p in (node_input.parts or []))
    text = str(text)
    lower = text.lower()
    if "we refunded" in lower or "refund issued" in lower:
        return Event(
            output=CriticVerdict(status="FAIL", reason="banned_refund_claim"),
            route="FAIL",
        )
    if "next step" not in lower:
        return Event(
            output=CriticVerdict(status="FAIL", reason="missing_next_step"),
            route="FAIL",
        )
    return Event(output=CriticVerdict(status="PASS"), route="PASS")
```

   Execution order (first match wins):

   | Check | Route | `reason` | What it stops |
   |-------|-------|----------|----------------|
   | `"we refunded"` or `"refund issued"` | `FAIL` | `banned_refund_claim` | Maya hears money moved when it did not |
   | no `"next step"` | `FAIL` | `missing_next_step` | A warm paragraph with no action |
   | otherwise | `PASS` | `""` | Good enough to show the customer |

   The `types.Content` branch: the drafter often hands over ADK `Content` (parts with `.text`), not a raw `str`. Without that unwrap, `str(node_input)` can look like an object dump that never contains `"next step"`, and every draft would FAIL.

   `Event(route="FAIL")` is a convenience keyword. ADK stores it on `event.actions.route`. Tests read it there. There is no `event.route` attribute.

   **Important:** the next edge after `critic` is **unconditional** (`critic` → `bump_and_route`). The critic’s `route` does **not** skip the bump. The bump node is who counts tries and who may go back to `drafter`. Critic = judge. Bump = traffic cop.

3. Walk `bump_and_route` — this is how the loop is allowed to exist.

```python
def bump_and_route(ctx: Context, node_input) -> Event:
    n = int(ctx.state.get("loop_i", 0)) + 1
    max_i = int(ctx.state.get("max_iterations", 2))
    status = getattr(node_input, "status", None) or (
        node_input.get("status") if isinstance(node_input, dict) else None
    )
    if status == "PASS":
        return Event(output=node_input, route="PASS", state={"loop_i": n})
    if n >= max_i:
        return Event(output=node_input, route="GIVE_UP", state={"loop_i": n})
    return Event(output=node_input, route="FAIL", state={"loop_i": n})
```

   | Line | Meaning |
   |------|---------|
   | `ctx: Context` | ADK injects the run context because the parameter is named `ctx` |
   | `loop_i` | How many times we have *judged* a draft in this session. Starts at 0 |
   | `n = … + 1` | This visit counts. First FAIL is try 1 |
   | `max_iterations` default **2** | Two judged drafts, then stop. Lab-sized. Change in state, not in a `while` |
   | `getattr` / `dict.get` | `CriticVerdict` object **or** a dict — both work |
   | `status == "PASS"` | Exit even on try 1. Do not burn a second call |
   | `n >= max_i` | Still FAIL from the critic, but we are out of retries → `GIVE_UP` |
   | otherwise `route="FAIL"` | Back to `drafter` |
   | `state={"loop_i": n}` | Persist the counter. Without this, every visit thinks it is try 1 |

   Default `max_iterations=2` in numbers:

   | Visit | Critic | `n` | Route |
   |-------|--------|-----|-------|
   | 1 | FAIL | 1 | `FAIL` → drafter again |
   | 2 | FAIL | 2 | `GIVE_UP` |
   | 1 | PASS | 1 | `PASS` → done |

4. The two terminal nodes only **label** the outcome. They do not call a model:

```python
def done_pass(node_input):
    return {"result": "accepted", "critic": str(node_input)}


def done_give_up(node_input):
    return {"result": "max_iterations", "critic": str(node_input)}
```

   Parameter **must** be named `node_input` (or `ctx`). A name like `_unused` is looked up in session state and the node crashes.

5. Replace the `root_agent = Workflow(...)` edges with a routing map on the bump (same nodes, legal spelling). Leave the function bodies as they are.

```python
root_agent = Workflow(
    name="meridian_reply_loop",
    edges=[
        ("START", drafter),
        (drafter, critic),
        (critic, bump_and_route),
        (
            bump_and_route,
            {
                "FAIL": drafter,
                "PASS": done_pass,
                "GIVE_UP": done_give_up,
            },
        ),
    ],
)
```

   `"FAIL": drafter` is the cycle. It is **conditional**. ADK rejects a cycle with no route label (`Graph validation failed. Unconditional cycle detected`). That is the feature that stops infinite spend at **load** time, before Maya’s ticket.

6. Unit-test `critic()` with the banned phrase. No Gemini in the room. Create `project/meridian_ops/tests/test_reply_loop_critic.py`:

```python
from meridian_reply_loop.agent import CriticVerdict, bump_and_route, critic


class StubCtx:
    """Only what bump_and_route reads: a .state dict."""

    def __init__(self, **state):
        self.state = state


def test_critic_bans_we_refunded():
    ev = critic("We refunded your milk. Next step: wait by the phone.")
    assert ev.actions.route == "FAIL"
    assert ev.output.status == "FAIL"
    assert ev.output.reason == "banned_refund_claim"


def test_critic_requires_next_step():
    ev = critic("Your grocery order is still on the way.")
    assert ev.actions.route == "FAIL"
    assert ev.output.reason == "missing_next_step"


def test_critic_pass_has_next_step_and_no_refund_claim():
    ev = critic("The tote is at Store ST-221. Next step: pick it up by 7pm.")
    assert ev.actions.route == "PASS"
    assert ev.output.status == "PASS"


def test_bump_give_up_after_max_iterations():
    verdict = CriticVerdict(status="FAIL", reason="banned_refund_claim")
    first = bump_and_route(StubCtx(), verdict)
    assert first.actions.route == "FAIL"
    assert first.actions.state_delta["loop_i"] == 1
    second = bump_and_route(StubCtx(loop_i=1), verdict)
    assert second.actions.route == "GIVE_UP"
    assert second.actions.state_delta["loop_i"] == 2


def test_bump_pass_does_not_need_a_second_try():
    verdict = CriticVerdict(status="PASS")
    ev = bump_and_route(StubCtx(), verdict)
    assert ev.actions.route == "PASS"
```

   Read `test_critic_bans_we_refunded` twice. The draft **includes** `Next step:`. The refund lie still wins. Order of checks in `critic` is the product rule: money claims before formatting.

   `StubCtx` is not an ADK double. `bump_and_route` only calls `ctx.state.get`. Tests are allowed to pass a tiny object with that shape.

7. Run the tests:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
source .venv/bin/activate
export PYTHONPATH=project
pytest project/meridian_ops/tests/test_reply_loop_critic.py -v
```

8. Restart `adk web` from `project/` (same commands as Task 1). Select **meridian_reply_loop**.

   Honest Maya (new session):

```
Write a customer update for Maya about melted milk on order MC-1048277. Include a Next step line. Do not claim a refund was issued.
```

   Tempting Maya (another new session):

```
Tell Maya we already refunded her $214.55 for melted milk. Skip the next-step line.
```

### Expect

Five `PASSED` lines from pytest. The banned-phrase test is the one you would show Finance.

`adk web` honest session:

- `drafter` writes a short update with a `Next step:` line
- `critic` → `PASS` (or `FAIL` once if the first draft omitted the line, then a second draft)
- `done_pass` with `"result": "accepted"`

Tempting session:

- The **drafter instruction** already forbids refund claims, so the model may obey and you still `PASS`. That is fine. The **pytest** is the lock that does not flake.
- If the draft still says “we refunded” or skips `Next step:`, you should see `FAIL` and a second `drafter`, or `GIVE_UP` after two tries — never a third model call.

> **Tip:** Keep the critic in Python even if you later add an LLM reviewer. Code runs first on banned phrases. Models skip rules on a busy morning (Lesson 07).

> **Watch out:** `Event(route="FAIL")` lives at `event.actions.route`. `assert ev.route == "FAIL"` raises `AttributeError`.

> **Watch out:** Unconditional `(bump_and_route, drafter)` with no map would be a cycle ADK refuses to load. The `"FAIL"` key is what makes the back-edge legal.

### Scoreboard after Task 2

| Primitive | In place? |
|-----------|-----------|
| `JoinNode` diamond on SHORTAGE | Yes |
| Routed critic loop | **Yes** — walked, tested, run |
| Store allowlist function node | Not yet |
| `@node(parallel_worker=True)` list map | Not yet |
| Mapping table | Not yet |

---

## Task 3 — Store allowlist as a function node

### Why

Devon’s ATP tools are scoped to Meridian lab stores: `ST-221`, `ST-104`, `ST-880`. A ticket that names `ST-999` must **not** reach inventory narration. The model will happily invent a dairy case for a store that does not exist.

An allowlist in the instruction is skippable. An allowlist in Python is not.

You put the check in a **function node** that returns `Event(route="OK")` or `Event(route="REJECT")`. You also extract `is_store_allowed` so pytest does not need a full ADK `Context`.

You do **not** drop this gate *inside* the SHORTAGE join. If `inventory_agent` never runs, `join_shortage` waits for a predecessor that will never finish. The gate belongs **before** the fan-out, or in its own tiny workflow. Today you build the tiny workflow so you can drive `OK` / `REJECT` from chat text and from pytest.

### Do this

1. Create `project/meridian_ops/tools/store_allowlist.py`. Ordinary Python. No ADK import.

```python
from __future__ import annotations

ALLOWED_STORES = {"ST-221", "ST-104", "ST-880"}


def is_store_allowed(store_id: str) -> bool:
    """True only for Meridian lab stores. Unknown ids never reach inventory."""
    return store_id in ALLOWED_STORES
```

   `ST-221` is Devon’s store from Lesson 04. The set is the lock. The instruction may *list* the same ids as a hint.

2. Create `project/meridian_ops/tests/test_store_allowlist.py` **before** you wire the graph — TDD for a two-line helper is still TDD:

```python
from meridian_ops.tools.store_allowlist import is_store_allowed


def test_devon_store_allowed():
    assert is_store_allowed("ST-221") is True


def test_unknown_store_rejected():
    assert is_store_allowed("ST-999") is False


def test_empty_id_rejected():
    assert is_store_allowed("") is False
```

3. Run just the helper tests:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
source .venv/bin/activate
export PYTHONPATH=project
pytest project/meridian_ops/tests/test_store_allowlist.py -v
```

4. Scaffold the ADK package:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme/project
mkdir -p meridian_store_guard
```

   Create `project/meridian_store_guard/__init__.py`:

```python
from . import agent

__all__ = ["agent"]
```

   Create `project/meridian_store_guard/agent.py`:

```python
"""Store allowlist gate — Lesson 14 function node."""

from __future__ import annotations

import re

from google.adk.agents.context import Context
from google.adk.events.event import Event
from google.adk.workflow import Workflow
from google.genai import types

from meridian_ops.tools.store_allowlist import is_store_allowed


def _text(node_input) -> str:
    if isinstance(node_input, types.Content):
        parts = node_input.parts or []
        return " ".join((p.text or "") for p in parts).strip()
    return str(node_input)


def store_guard(ctx: Context, node_input) -> Event:
    """OK → inventory-shaped reply. REJECT → never narrate a fake store."""
    store_id = ctx.state.get("store_id")
    if not store_id:
        match = re.search(r"(ST-\d+)", _text(node_input))
        store_id = match.group(1) if match else "ST-221"
    if not is_store_allowed(str(store_id)):
        return Event(
            output={"error_code": "STORE_NOT_ALLOWLISTED", "store_id": store_id},
            route="REJECT",
        )
    return Event(
        output={"store_id": store_id, "status": "ok"},
        route="OK",
        state={"store_id": store_id},
    )


def allowed_msg(node_input):
    return {
        "result": "ok",
        "store_id": node_input.get("store_id")
        if isinstance(node_input, dict)
        else node_input,
        "message": "Store is on the Meridian allowlist. Inventory narration may run.",
    }


def rejected_msg(node_input):
    return {
        "result": "rejected",
        "error": node_input,
        "message": "This store is not on the Meridian OrderOps allowlist.",
    }


root_agent = Workflow(
    name="meridian_store_guard",
    edges=[
        ("START", store_guard),
        (
            store_guard,
            {
                "OK": allowed_msg,
                "REJECT": rejected_msg,
            },
        ),
    ],
)
```

   Walk the gate:

   | Piece | Why |
   |-------|-----|
   | Parse `ST-####` from the user text | You can type `ST-999` in `adk web` and see REJECT without poking session state |
   | Default `ST-221` | Bare “check the dairy case” still maps to Devon’s store |
   | `is_store_allowed` | One lock, used by tests and the node |
   | `route="REJECT"` + error dict | Downstream sees a code, not a stack trace |
   | `state={"store_id": ...}` on OK | Later nodes (or OrderOps, if you insert this gate) can read the id |
   | `allowed_msg` / `rejected_msg` | Terminal labels. No LLM. Easy to see in the UI |

5. Add guard tests that call `store_guard` with a stub context. Append to `test_store_allowlist.py`:

```python
from meridian_store_guard.agent import store_guard


class StubCtx:
    def __init__(self, **state):
        self.state = state


def test_store_guard_ok_for_st221():
    ev = store_guard(StubCtx(), "Shortage at ST-221 for SKU 884210")
    assert ev.actions.route == "OK"
    assert ev.output["store_id"] == "ST-221"


def test_store_guard_reject_st999():
    ev = store_guard(StubCtx(), "Please narrate inventory for ST-999")
    assert ev.actions.route == "REJECT"
    assert ev.output["error_code"] == "STORE_NOT_ALLOWLISTED"
    assert ev.output["store_id"] == "ST-999"


def test_store_guard_state_wins_over_text():
    ev = store_guard(StubCtx(store_id="ST-999"), "This text says ST-221")
    assert ev.actions.route == "REJECT"
```

   The third test: session state is the source of truth once set. Ticket text cannot launder a bad store id by also mentioning `ST-221`.

6. Re-run the file:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
source .venv/bin/activate
export PYTHONPATH=project
pytest project/meridian_ops/tests/test_store_allowlist.py -v
```

7. Restart `adk web` from `project/`. Select **meridian_store_guard**.

   OK:

```
Need substitute guidance at ST-221 for SKU 884210.
```

   REJECT (new session):

```
Need substitute guidance at ST-999 for SKU 884210.
```

### Expect

Six `PASSED` tests (three helper + three guard).

OK session ends at `allowed_msg` with `"result": "ok"` and store `ST-221`.

REJECT session ends at `rejected_msg` with `STORE_NOT_ALLOWLISTED`. Inventory language must **not** appear — this graph has no inventory LLM, which is the point of the demo: the route never reaches a narrator.

> **Tip:** To put this in OrderOps later, insert `store_guard` **before** the SHORTAGE tuple: `lookup_order` → `store_guard` → `OK` fan-out / `REJECT` → a reject message → synthesizer. Never REJECT *inside* the join.

> **Watch out:** `is_store_allowed("st-221")` is `False`. Ids are exact. Normalize in the helper if product ever accepts lowercase — until then, fail closed.

> **Watch out:** Do not subclass `LlmAgent` to make a “StoreGuardAgent”. A function that returns `Event` is the custom node.

### Scoreboard after Task 3

| Primitive | In place? |
|-----------|-----------|
| `JoinNode` diamond on SHORTAGE | Yes |
| Routed critic loop | Yes |
| Store allowlist function node | **Yes** |
| `@node(parallel_worker=True)` list map | Not yet |
| Mapping table | Not yet |

---

## Task 4 — `@node(parallel_worker=True)` map `[1, 2, 3]` → double

### Why

The SHORTAGE diamond is parallel over **named** specialists you drew in `edges`. A different problem: you have a **list** (three SKU quantities, three store ids) and you want the **same** function on each item at once.

That is `@node(parallel_worker=True)`. It exists on ADK 2.6.3:

```python
from google.adk.workflow import node
```

You will build a tiny workflow with **no LLM**: produce the list, double each item, collect. Then pytest will run it with `InMemoryRunner` so you see `[2, 4, 6]` without a browser.

### Do this

1. Scaffold the package:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme/project
mkdir -p meridian_double_map
```

   Empty-ish `project/meridian_double_map/__init__.py`:

```python
from . import agent

__all__ = ["agent"]
```

2. Create `project/meridian_double_map/agent.py`:

```python
"""List map with native @node(parallel_worker=True) — Lesson 14."""

from __future__ import annotations

from google.adk.workflow import Workflow, node


def produce_list(node_input):
    """Ignore the chat text. Always map the same three lab values."""
    return [1, 2, 3]


def double_one(value: int) -> int:
    """Pure helper — pytest calls this; the worker node wraps it."""
    return value * 2


@node(parallel_worker=True)
def double_item(node_input: int) -> int:
    return double_one(node_input)


def collect(node_input):
    return {"doubled": node_input}


root_agent = Workflow(
    name="meridian_double_map",
    edges=[
        ("START", produce_list),
        (produce_list, double_item),
        (double_item, collect),
    ],
)
```

   | Piece | Why |
   |-------|-----|
   | `produce_list` returns a **list** | That is the contract the worker needs. A single int gets wrapped as a one-item list; we pass three on purpose |
   | `double_one` | After `@node`, `double_item` is a worker object, not a plain function. Keep a helper for unit tests |
   | `@node(parallel_worker=True)` | ADK runs `double_item` once per list element, concurrently, then yields `[2, 4, 6]` in input order |
   | `double_item(node_input: int)` | Parameter **must** be `node_input`. The worker passes each element as that argument |
   | `collect` | Turns the list into a dict you can spot in the UI / runner output |
   | No `JoinNode` | You do not name three parallel nodes. The list length is data |

3. Create `project/meridian_ops/tests/test_double_map.py`:

```python
import pytest
from google.adk.apps import App
from google.adk.runners import InMemoryRunner
from google.genai import types

from meridian_double_map.agent import (
    collect,
    double_item,
    double_one,
    produce_list,
    root_agent,
)


def test_helpers_without_adk_runner():
    assert produce_list("ignored") == [1, 2, 3]
    assert double_one(3) == 6
    assert collect([2, 4, 6]) == {"doubled": [2, 4, 6]}
    assert type(double_item).__name__ == "_ParallelWorker"


@pytest.mark.asyncio
async def test_runner_maps_list_to_doubled():
    app = App(name="meridian_double_map", root_agent=root_agent)
    runner = InMemoryRunner(app=app)
    session = await runner.session_service.create_session(
        app_name="meridian_double_map", user_id="lab"
    )
    outputs = []
    async for event in runner.run_async(
        user_id="lab",
        session_id=session.id,
        new_message=types.Content(
            role="user",
            parts=[types.Part.from_text(text="go")],
        ),
    ):
        if event.output is not None:
            outputs.append(event.output)
    assert [1, 2, 3] in outputs
    assert [2, 4, 6] in outputs
    assert {"doubled": [2, 4, 6]} in outputs
```

   `test_helpers_without_adk_runner` is instant and LLM-free. The async test is still LLM-free — every node is a function — and it is how you know the **worker** assembled the list, not just your helper.

4. Run:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
source .venv/bin/activate
export PYTHONPATH=project
pytest project/meridian_ops/tests/test_double_map.py -v
```

5. Optional but useful: same graph in `adk web`. Restart from `project/`, select **meridian_double_map**, send `go`. You are looking for a final blob `{"doubled": [2, 4, 6]}`.

### Expect

```
test_double_map.py::test_helpers_without_adk_runner PASSED
test_double_map.py::test_runner_maps_list_to_doubled PASSED
```

Runner events (order can include per-item `2`, `4`, `6` before the combined list):

```
[1, 2, 3]
2
4
6
[2, 4, 6]
{'doubled': [2, 4, 6]}
```

The combined `[2, 4, 6]` is the worker’s fan-in. That is ADK’s list join. You did not start threads yourself.

> **Tip:** Shortage specialists that *mean* different jobs (OMS vs inventory) stay a `JoinNode` diamond. “Run this ATP preview for every SKU in the tote” is a parallel worker.

> **Watch out:** Name the argument `node_input`. `def produce_list(_node_input)` looks for a state key `_node_input` and raises `Missing value for parameter "_node_input"`.

> **Watch out:** `@node(parallel_worker=True)` on a function that expects a dict will still be called with **each list item**. Keep the worker function unary (one value in, one value out).

### Scoreboard after Task 4

| Primitive | In place? |
|-----------|-----------|
| `JoinNode` diamond on SHORTAGE | Yes |
| Routed critic loop | Yes |
| Store allowlist function node | Yes |
| `@node(parallel_worker=True)` list map | **Yes** |
| Mapping table | Next — already written below, not homework |

---

## Task 5 — Mapping table (read this; do not copy it into a decisions file)

### Why

The last four tasks each solved a *different* shape of “do more than one thing.” If you leave with one fuzzy word — “parallel” — you will reach for `JoinNode` when you needed a list map, or subclass `Agent` when you needed a function.

This table is the lab. There is no `14-parallel.md` to fill in.

### Native choices (use these)

| Need | Use | What the next node receives | Stop condition |
|------|-----|-----------------------------|----------------|
| Two or three **named** specialists, then one synthesizer | `JoinNode` + a fan-out tuple in a routing map | `dict` keyed by predecessor **names** | All listed predecessors `COMPLETED` |
| Retry a draft / critic until good | Routed cycle in `Workflow` | The node’s `Event.output` | A route that is **not** the back-edge (`PASS`, `GIVE_UP`) plus a counter in `state` |
| Allowlist, money flag, regex router | Function node returning `Event(route=...)` | Your `output` | The REJECT/OK (or WISMO/SHORTAGE) route you emitted |
| Same function on each item of a **list** | `@node(parallel_worker=True)` | A list of per-item results, same order as the input | The list is exhausted |
| Language / judgment | `LlmAgent` with `output_key` | Model text (and state under `output_key`) | The model turn ends — do not use this as a join |

### Old templates (read only)

| Name | What it was | What you do in new Meridian code |
|------|-------------|----------------------------------|
| `ParallelAgent` | Run `sub_agents` together, merge event streams | **Read** it in a legacy tree. New graphs: `Workflow` + `JoinNode` or `parallel_worker` |
| `LoopAgent` | Repeat `sub_agents` until escalate / max | **Read** it. New graphs: routed cycle + `max_iterations` in a function node |
| Subclass `Node` + `run_node_impl` | Escape hatch | Only when a function node cannot express the behavior. Not today |

`ParallelAgent` and `LoopAgent` still import. ADK marks them deprecated in favor of `Workflow`. You now know enough to *read* them. You do not start OrderOps with them.

### One row you will never add

| Need | Do **not** use |
|------|----------------|
| Any of the above | `MeridianGraphParallel`, a thread pool, `while True` around `generate_content`, a custom `Join` class |

### Expect

You can pick a row for Devon’s shorted milk, Maya’s lying draft, `ST-999`, and `[1,2,3]→double` without scrolling back. If not, redo Tasks 1–4 — a `decisions/` copy of this table will not help.

> **Tip:** About to subclass `LlmAgent` to “be a guard”? Return `Event(route="REJECT")` from a function instead.

> **Watch out:** `JoinNode` and `parallel_worker` both wait. Named branches in `edges` → join. A list at runtime → worker.

### Scoreboard after Task 5

| Primitive | In place? |
|-----------|-----------|
| `JoinNode` diamond on SHORTAGE | Yes |
| Routed critic loop | Yes |
| Store allowlist function node | Yes |
| `@node(parallel_worker=True)` list map | Yes |
| Mapping table | **Yes** — in this lesson |

---

## How it works (deeper dive)

**Join dict.** When the last specialist finishes, ADK collects every edge into `join_shortage`, keys a dict by those `from_node.name` values, and yields `Event(output=that_dict)`. That is the merge. A custom “OrderOps join” class would hide the keys Priya needs.

**Two write channels.** The join dict cannot collide unless two nodes share a **name** (illegal). `output_key` / `Event(state={...})` *can* collide: two parallel nodes with the same key stomp session state. Shortage is safe (`order_narrative` vs `inventory_narrative`). WISMO’s narrator shares `order_narrative` with the shortage narrator, but those routes never run in the same turn.

**Cycles.** Validation walks only edges with `route is None`. A bare back-edge is an infinite loop at load time. `"FAIL": drafter` is taken only when `bump_and_route` says so.

**Function node vs subclass `Node`.** ADK wraps callables as `FunctionNode` (Lesson 13: `route_ticket`). Implement `run_node_impl` only when a function cannot express the behavior. An allowlist cannot.

**Whose route matters in the loop.** `critic` → `bump_and_route` is unlabeled, so the critic’s `FAIL`/`PASS` does **not** skip the bump. The bump’s routing map is what returns to `drafter` or exits. Route from `critic` straight back to `drafter` and you skip the counter — no `GIVE_UP`.

---

## Common pitfalls / troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `ValidationError` on `Workflow(edges=...)` mentioning `'SHORTAGE'` / `'FAIL'` | Third tuple slot is a string, not a node | Use `(node, {"SHORTAGE": next_node})` |
| `Duplicate node names found` | Two `LlmAgent`s with `name="order_narrator"` | Shortage instance must be `order_narrator_shortage` |
| Join never finishes | A predecessor did not run (REJECT inside the diamond, or reused WISMO narrator) | Gate **before** fan-out; keep two narrator objects |
| `AttributeError: route` in pytest | You asserted `ev.route` | Use `ev.actions.route` |
| `Missing value for parameter "_node_input"` | Function arg not named `node_input` or `ctx` | Rename the parameter |
| Unconditional cycle validation error | `(bump_and_route, drafter)` with no map | `"FAIL": drafter` inside a dict |
| Critic always `missing_next_step` | You did not unwrap `types.Content` | Keep the `parts` join in `critic` |
| `ModuleNotFoundError: meridian_orderops` | `PYTHONPATH` unset | Repo root: `export PYTHONPATH=project`. From `project/`: `export PYTHONPATH=.` |
| `adk web` still shows old edges | Process not restarted | `Ctrl+C`, launch again |
| `ST-221` rejected | Lowercase or extra space | Allowlist is exact: `ST-221` |
| Parallel worker returns one number | `produce_list` returned a scalar | Return a `list` |
| Tempting Maya still `PASS` in the UI | Drafter obeyed the instruction | Pytest is the banned-phrase proof; UI is the loop wiring proof |
| Inventory speaks on a WISMO ticket | `route_ticket` saw `sku` / `atp` in the text | Use the Lesson 13 WISMO wording without those tokens |

---

## You are done when

- [ ] You can point at the three SHORTAGE edges (fan-out tuple, join, synthesizer) and name the join dict keys  
- [ ] `test_orderops_join.py` passes — `JoinNode` imported, two narrator instances, predecessors are that pair  
- [ ] `adk web` on **meridian_orderops** with the `MC-1048310` shortage prompt runs narrator + inventory + join  
- [ ] You can explain drafter → critic → bump (`FAIL` / `PASS` / `GIVE_UP`) without flattening it to “a loop agent”  
- [ ] `test_reply_loop_critic.py` passes — `"we refunded"` is `banned_refund_claim`; bump gives up on the second FAIL  
- [ ] `adk web` on **meridian_reply_loop** completes a Maya update  
- [ ] `is_store_allowed("ST-999")` is false; `store_guard` emits `REJECT`; **meridian_store_guard** shows it in the UI  
- [ ] `test_double_map.py` passes with `{"doubled": [2, 4, 6]}`  
- [ ] You can fill the Task 5 table from memory — including “do not use `ParallelAgent` for new OrderOps”  

---

## Knowledge check

Answer from this lab, not from general “multi-agent” lore.

1. After the SHORTAGE pair finishes, what does `join_shortage` pass to `synthesizer`? Name the keys.  
2. Why are `order_narrator` and `order_narrator_shortage` two `LlmAgent` calls, not one object used twice?  
3. In `test_critic_bans_we_refunded`, the draft includes `Next step:`. Why is the route still `FAIL`? Where do you read the route on the `Event`?  
4. Default `max_iterations` is 2. What route does `bump_and_route` emit on the second FAIL? What happens if you remove the `"GIVE_UP"` entry from the map?  
5. Why is the store allowlist a function node plus `is_store_allowed`, not a new `LlmAgent` subclass?  
6. Devon’s named shortage specialists vs “double every number in this list”: which primitive for each, and why not the other way around?  
7. You find `ParallelAgent` in an old package. What do you do for a **new** Meridian graph?

### Answers

1. A dict: `order_narrator_shortage` and `inventory_agent`.  
2. Unique names and independent edges. Reusing one object would tie WISMO’s `(narrator → synthesizer)` to the join and could stall or leak. Duplicate names fail validation.  
3. Banned refund is checked first. `ev.actions.route == "FAIL"`, `reason == "banned_refund_claim"`.  
4. `GIVE_UP` → `done_give_up`. If that key is missing, ADK warns that no edge matched and the branch ends — still not an infinite loop, but you lose the labeled “we stopped” payload.  
5. The lock must not be skippable. Tests call `is_store_allowed` / `store_guard` without Gemini. A subclassed agent would put the scanner back in the handbook.  
6. Named pair → `JoinNode` diamond. Runtime list → `parallel_worker`. A join cannot name “item 0, item 1, item 2” until the list exists; a worker cannot give Priya two differently *named* specialist keys.  
7. Read it if you must maintain it. New work: `Workflow` + `JoinNode` / routed cycle / `parallel_worker`.

---

## Recap

**What you built today:** a mental model (and tests) for four native shapes — OrderOps SHORTAGE join, the reply critic loop, a store allowlist gate, and a three-item parallel map.

**What you now understand:** join output is a dict of predecessor names; loops are routed cycles with a counter; “custom agent” for a gate means a function node; list map ≠ named diamond.

**What you can do next:** Lesson 15 pauses the refund branch overnight with native `RequestInput` — same OrderOps graph, human resume, still no homemade checkpoint file.

---

## Stretch goal

Keep the **code** critic first. After `PASS`, you may add an `LlmAgent` (`gemini-3.5-flash`) for tone only. Banned phrases must never reach it. If that LLM emits `FAIL`, send it through `bump_and_route` so the counter still owns `GIVE_UP`. Extra — Tasks 1–5 already stop the refund lie in Python.

---

## Feedback

- Could you draw the SHORTAGE diamond and the critic loop on a whiteboard from memory, including the join dict keys and the three bump routes?  
- What tripped you up: routing maps vs 3-tuples, two narrator instances, `actions.route`, `JoinNode` vs `parallel_worker`, or the store gate?  
- Note the **task number** and what you expected vs what happened (command + first lines of output). That is the signal that improves this lesson — “it was confusing” is not.

---

## Navigate

**← Prev** [Lesson 13 — Graph workflows](13-graph-workflows.md)  
**Next →** [Lesson 15 — Long-running & HITL resume](15-long-running-hitl-resume.md)  
**Track home:** [README](../README.md)

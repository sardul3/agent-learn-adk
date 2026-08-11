# Lesson 14 — Parallel, loop & custom nodes (native ADK)

**Level:** Advanced  
**Time:** ~120 minutes  
**Prerequisites:** Lesson 13 (`Workflow` running)  
**Lab outcome:** Native fan-out/`JoinNode`, a routed critic **loop**, and a deterministic function-node guard — no DIY parallel runtime

**Standard:** [docs/NATIVE-ADK.md](../docs/NATIVE-ADK.md)

---

## At a glance

| Pattern | Native ADK |
|---------|------------|
| Fan-out / fan-in | `edges` tuples + `JoinNode` |
| Loop / critic | Routed cycle (`Event(route="CONTINUE"|"EXIT")`) + max via state/counter |
| List map-parallel | `@node(parallel_worker=True)` |
| Custom control | Function node (or subclass `Node` only if required) |
| Legacy templates | `ParallelAgent` / `LoopAgent` (literacy only) |

---

## Why this matters

Parallel without namespaced outputs → race bugs.  
Loops without exit routes → infinite spend.  
ADK already encodes both — use them.

---

## Know these

| Term | Meaning |
|------|---------|
| **JoinNode** | Waits for all upstream outputs → `dict` keyed by predecessor names |
| **Routed cycle** | Edge back to an earlier node using a route label |
| **parallel_worker** | Runs a node once per list item concurrently |
| **Function node** | Deterministic code in the graph (prefer over bespoke “agents”) |

---

## Task 1 — Study the SHORTAGE fan-out already in OrderOps

### Why

You already have a native parallel pattern in `meridian_orderops`.

### Do this

In `project/meridian_orderops/agent.py`, find:

```python
(lookup_order, (order_narrator_shortage, inventory_agent), "SHORTAGE"),
((order_narrator_shortage, inventory_agent), join_shortage),
(join_shortage, synthesizer),
```

Document in `project/meridian_ops/decisions/14-parallel.md`:

- Which keys `JoinNode` produces  
- Why `order_narrator` and `order_narrator_shortage` are **two instances**

### Expect

You can explain JoinNode output shape without inventing a merge helper framework.

---

## Task 2 — Build a native critic loop Workflow

### Why

Reply quality loops belong in `Workflow` edges, not `while True` in your script.

### Do this

Create `project/meridian_reply_loop/agent.py`:

```python
from __future__ import annotations

from google.adk.agents import LlmAgent
from google.adk.events.event import Event
from google.adk.workflow import Workflow
from google.genai import types
from pydantic import BaseModel


class CriticVerdict(BaseModel):
    status: str  # PASS | FAIL
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


def critic(node_input) -> Event:
    """Deterministic critic — code judge inside the graph."""
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


def bump_and_route(ctx, node_input) -> Event:
    """Limit iterations using workflow state — still ADK state, not a side DB."""
    n = int(ctx.state.get("loop_i", 0)) + 1
    max_i = int(ctx.state.get("max_iterations", 2))
    verdict = node_input
    status = getattr(verdict, "status", None) or (verdict.get("status") if isinstance(verdict, dict) else None)
    if status == "PASS":
        return Event(output=verdict, route="PASS", state={"loop_i": n})
    if n >= max_i:
        return Event(output=verdict, route="GIVE_UP", state={"loop_i": n})
    return Event(output=verdict, route="FAIL", state={"loop_i": n})


def done_pass(node_input):
    return {"result": "accepted", "critic": str(node_input)}


def done_give_up(node_input):
    return {"result": "max_iterations", "critic": str(node_input)}


root_agent = Workflow(
    name="meridian_reply_loop",
    edges=[
        ("START", drafter),
        (drafter, critic),
        (critic, bump_and_route),
        (bump_and_route, drafter, "FAIL"),
        (bump_and_route, done_pass, "PASS"),
        (bump_and_route, done_give_up, "GIVE_UP"),
    ],
)
```

Add `__init__.py` (`from . import agent`). Run under `adk web` from `project/`.

### Expect

Failing draft language gets another draft attempt; loop cannot run forever (`max_iterations`).

> **Watch out:** Unconditional cycles are rejected by ADK — every cycle needs a routed exit.

---

## Task 3 — Store allowlist as a function node (not a custom Agent class)

### Why

“Custom agent” often means people subclass forever. Prefer a **function node** guard.

### Do this

Add to a small workflow or to OrderOps shortage path **before** inventory LLM:

```python
ALLOWED_STORES = {"ST-221", "ST-104", "ST-880"}

def store_guard(ctx, node_input) -> Event:
    store_id = ctx.state.get("store_id") or "ST-221"
    if store_id not in ALLOWED_STORES:
        return Event(
            output={"error_code": "STORE_NOT_ALLOWLISTED", "store_id": store_id},
            route="REJECT",
        )
    return Event(output=node_input, route="OK")
```

Wire `OK → inventory_agent`, `REJECT → unsupported/reject message node`.

Unit-test `store_guard` by calling it with a stub context **only if** ADK exposes a lightweight context for tests; otherwise test the allowlist set logic in a tiny pure helper used by the node:

```python
def is_store_allowed(store_id: str) -> bool:
    return store_id in ALLOWED_STORES
```

### Expect

Bad store never reaches inventory narration.

---

## Task 4 — Optional: `@node(parallel_worker=True)` map

### Why

Fan-out over a **list** is a different native primitive than diamond JoinNode.

### Do this

If available in your install:

```python
from google.adk.workflow import node, Workflow

@node(parallel_worker=True)
def double_item(node_input: int) -> int:
    return node_input * 2
```

Build a tiny workflow: START → produce `[1,2,3]` → `double_item` → collect. Run once.

If decorator missing, document in decisions and rely on JoinNode diamond (still native).

### Expect

Either worker map works or JoinNode remains your parallel tool — **no** thread-pool framework of your own.

---

## Task 5 — Mapping table (delete DIY column)

### Why

Cement the native-only habit.

### Do this

Update `14-parallel.md`:

| Need | Use |
|------|-----|
| Parallel specialists | `JoinNode` + tuple edges |
| Critic/refiner | Routed cycle in `Workflow` |
| Allowlist gate | Function node + `Event.route` |
| Legacy code reading | `ParallelAgent` / `LoopAgent` docs only |

### Expect

No row says “MeridianGraphParallel”.

---

## How it works (deeper dive)

### State races

JoinNode returns **separate keys** per predecessor. Don’t have two writers stomp `findings` in `state` — use `output_key` / namespaced state deltas via `Event(state={...})`.

### When to subclass `Node`

Rare. Prefer functions. Subclass only when ADK docs show you need custom `run_node_impl` behavior that functions cannot express.

---

## Common pitfalls / troubleshooting

| Symptom | Fix |
|---------|-----|
| Graph validation: unconditional cycle | Add routed EXIT/GIVE_UP |
| Duplicate node name | New `LlmAgent(name=...)` instance |
| Infinite model calls | Enforce `max_iterations` in a function node |

---

## You are done when

- [ ] Explained OrderOps JoinNode path in writing  
- [ ] `meridian_reply_loop` runs in `adk web`  
- [ ] Store guard is a function node  
- [ ] Decisions table has zero DIY runtimes  

---

## Knowledge check

1. What ADK object fans in parallel branches?  
2. How do you stop a critic loop natively?  
3. Why two `LlmAgent` instances instead of reusing one object twice?  
4. What’s the preferred “custom agent” for an allowlist?

### Answers

1. `JoinNode`  
2. Routed `PASS`/`GIVE_UP` (+ iteration counter in state)  
3. Unique node names / graph identity  
4. Function node returning `Event(route=...)`  

---

## Recap

- Parallel + loop + guards are all native Workflow features.  
- Next: HITL resume using ADK `RequestInput` / app resumability end-to-end.

---

## Stretch goal

Convert reply loop stop into an LLM critic **plus** code hard-fail on banned phrases (code runs first).

---

## Feedback

- Could you add a third parallel branch without a custom merge class?  
- Note task number + expected vs actual.

---

## Navigate

**← Prev** [Lesson 13 — Graph workflows](13-graph-workflows.md)  
**Next →** [Lesson 15 — Long-running & HITL resume](15-long-running-hitl-resume.md)
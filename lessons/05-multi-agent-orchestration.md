# Lesson 05 — Multi-agent orchestration (hero zone)

**Level:** Advanced  
**Time:** ~100–120 minutes  
**Prerequisites:** Lessons 01–04 tools + agents  
**Lab outcome:** A Meridian **OrderOps** root that routes across Order / Inventory specialists and a deterministic investigate→synthesize sequence

---

## At a glance

One mega-agent with every tool becomes an un-reviewable blob. You will learn:

- Single agent + many tools vs specialist agents
- Transfer / delegation / handoff patterns
- Template workflows still worth knowing: **sequential**, **parallel**, **loop**
- ADK 2.0 **graph** mindset: deterministic edges + intelligent nodes
- Shared state ownership (who writes which keys)
- Fan-out/fan-in race risks
- When to drop to a custom `BaseAgent`-style controller

---

## Why this matters

Meridian ticket `TCK-9003` (inventory short) and `TCK-9001` (WISMO) need different privileges and prompts.

If Inventory can call `request_refund`, or Order Status freestyles substitute reservations, you will fail security review — even if the demo chat looks slick.

---

## Know these

| Pattern | Control | Meridian fit |
|---------|---------|--------------|
| **Single agent + tools** | LLM picks tools | Simple WISMO |
| **Coordinator + sub-agents** | LLM transfers to specialists | Chat entry that may be WISMO *or* inventory |
| **SequentialAgent** | Deterministic A→B→C | Investigate → draft customer reply |
| **ParallelAgent** | Fan-out concurrent specialists | OMS + ATP fetch together (careful with state) |
| **LoopAgent** | Repeat until stop / max iters | Critic/refiner on reply quality |
| **Graph workflow (ADK 2.0+)** | Explicit nodes/edges + branches | Production OrderOps with HITL branch |
| **Custom agent** | Your code owns control flow | Hard business state machines |

### Shared state rules of thumb

```
app:ticket_id          → written once by router / intake
active_order_id        → Order specialist owns writes
inventory:suggestion   → Inventory specialist owns writes
customer_reply_draft   → Synthesizer owns writes
```

Prefix keys by owner when parallel work is possible.

---

## Task 1 — Decision: when to split agents

### Why

Splitting too early creates RPC spaghetti. Splitting too late creates a god-agent.

### Do this

In `project/meridian_ops/decisions/05-agent-boundaries.md`, fill:

| Capability | Same agent as Order Status? | Why |
|------------|-----------------------------|-----|
| WISMO lifecycle facts | | |
| Substitute preview | | |
| Refund request | | |
| Policy FAQ | | |
| Loyalty recompute | | |

Use Lesson 01 answers + least privilege from Lesson 04.

### Expect

Refund ≠ Order Status. Loyalty recompute still ≠ any agent. Inventory is separate from Order Status.

---

## Task 2 — Build specialist agents as importable modules

### Why

Orchestrators compose packages. Copy-pasting three `agent.py` files diverges in a week.

### Do this

Create `project/meridian_ops/agents/specialists.py`:

```python
from __future__ import annotations

from google.adk.agents.llm_agent import LlmAgent

from meridian_ops.tools.atp import get_atp, reserve_substitute, suggest_substitute_for_short
from meridian_ops.tools.oms import get_order

GEMINI = "gemini-2.5-flash"

order_agent = LlmAgent(
    name="order_agent",
    model=GEMINI,
    description="Meridian order status and delivery/pickup lifecycle specialist.",
    instruction="""
You are Meridian Order specialist.
- Use get_order before factual claims.
- Write concise evidence bullets into your final response.
- Do not discuss refunds or substitutes beyond noting the customer asked.
- If the issue is clearly an inventory short, say so and stop — the router may transfer.
""".strip(),
    tools=[get_order],
    output_key="order_findings",
)

inventory_agent = LlmAgent(
    name="inventory_agent",
    model=GEMINI,
    description="Meridian ATP shortage and substitute preview specialist.",
    instruction="""
You are Meridian Inventory specialist.
- Use get_atp / suggest_substitute_for_short for shortages.
- Default dry_run=true; never commit reserves unless user confirms.
- Put the chosen substitute and correlation ids in your final response.
- No refunds.
""".strip(),
    tools=[get_atp, reserve_substitute, suggest_substitute_for_short],
    output_key="inventory_findings",
)

synthesizer_agent = LlmAgent(
    name="synthesizer_agent",
    model=GEMINI,
    description="Drafts a customer-safe Meridian reply from specialist findings.",
    instruction="""
You draft customer-safe replies for Meridian CX.

Inputs in session state (may be empty):
- order_findings: {order_findings?}
- inventory_findings: {inventory_findings?}

Rules:
- Only use facts present in those findings or tool-backed earlier turns.
- Never invent refunds, ETAs, or POD photos.
- Structure: Empathy (1 line) → Facts → Next step → What we need from customer.
""".strip(),
    tools=[],  # pure drafting from state
    output_key="customer_reply_draft",
)
```

> **Tip:** If your ADK version aliases `Agent` == `LlmAgent`, either import works — stay consistent.

Add a quick import smoke check:

```bash
export PYTHONPATH=project
python -c "from meridian_ops.agents.specialists import order_agent; print(order_agent.name)"
```

### Expect

Prints `order_agent`.

---

## Task 3 — Deterministic sequence: investigate → synthesize

### Why

For known pipelines, do not ask the model whether synthesis comes after investigation. **Make the edge deterministic.**

### Do this

Create package `project/meridian_orderops_sequential/`:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme/project
mkdir -p meridian_orderops_sequential
printf '%s\n' 'from . import agent' > meridian_orderops_sequential/__init__.py
```

`project/meridian_orderops_sequential/agent.py`:

```python
from google.adk.agents.sequential_agent import SequentialAgent

from meridian_ops.agents.specialists import inventory_agent, order_agent, synthesizer_agent

# Fixed path for inventory-exception style tickets:
# Order evidence → Inventory recommendation → customer-safe draft
root_agent = SequentialAgent(
    name="meridian_orderops_sequential",
    description="Deterministic Order → Inventory → Synthesize pipeline.",
    sub_agents=[order_agent, inventory_agent, synthesizer_agent],
)
```

Run:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme/project
export PYTHONPATH=.
adk web --port 8000
```

Select `meridian_orderops_sequential` and prompt:

```
Pickup order MC-1048301 may be impacted. Check order lifecycle, then evaluate substitute options if milk SKU 884210 is short. Candidates: 884299, 552100. Preview only. Draft a customer-safe update.
```

(Add `MC-1048310` to `orders.json` if you prefer that id — keep order_id consistent with your tools.)

### Expect

- Order agent runs before inventory  
- `order_findings` / `inventory_findings` land in state (via `output_key`)  
- Synthesizer draft does not invent a refund  
- You can point to the **sequence** as the reason inventory didn’t run first

> **Watch out:** Sequential means *always* all stages. Do not use it as your only production entrypoint for pure WISMO (wasted inventory calls). Pair with a router (Task 4) or a graph branch (Task 6).

---

## Task 4 — Coordinator with specialist transfer

### Why

Chat entrypoints are messy. A coordinator LLM is allowed to **choose a specialist**; it should not own every tool.

### Do this

Create `project/meridian_orderops_router/agent.py` (scaffold with `adk create` or mkdir pattern above).

```python
from google.adk.agents.llm_agent import LlmAgent

from meridian_ops.agents.specialists import inventory_agent, order_agent
from meridian_ops.tools.classify_ticket import Route, classify_ticket

GEMINI = "gemini-2.5-flash"


def classify_for_router(text: str) -> dict:
    """Deterministic assist for the coordinator (not the final authority alone)."""
    route = classify_ticket(text)
    return {"status": "success", "route": route.value}


router_agent = LlmAgent(
    name="orderops_router",
    model=GEMINI,
    description="Routes Meridian OrderOps tickets to specialists.",
    instruction="""
You are the Meridian OrderOps coordinator.

Process:
1) Call classify_for_router on the user text.
2) Transfer to order_agent for WISMO / lifecycle questions.
3) Transfer to inventory_agent for ATP / substitute / shortage questions.
4) If both are required, prefer inventory_agent only after order_id is known —
   transfer to order_agent first when order facts are missing.
5) Refuse loyalty batch jobs and password resets.

Use agent transfer/handoff mechanisms available to you rather than answering
with deep OMS expertise yourself.
""".strip(),
    tools=[classify_for_router],
    sub_agents=[order_agent, inventory_agent],
)

root_agent = router_agent
```

> **Note:** Exact transfer mechanics vary slightly by ADK version (`transfer_to_agent` tool vs automatic sub-agent calling). Inspect your install:

```bash
python -c "import google.adk.tools as t; print([x for x in dir(t) if 'transfer' in x.lower()])"
```

If `transfer_to_agent` exists, add it to `tools` and mention it explicitly in the instruction.

### Expect

- Prompt about `MC-1048292` delivery → `order_agent` involvement  
- Prompt about SKU `884210` short → `inventory_agent` involvement  
- Classifier assist appears in trajectory

> **Tip:** Descriptions on sub-agents are not decoration — routers use them.

---

## Task 5 — Shared state ownership drill

### Why

Parallel fan-out without key ownership = race conditions and silent overwrites.

### Do this

Add to `05-agent-boundaries.md`:

**State ownership table**

| Key | Writer | Readers | Parallel-safe? |
|-----|--------|---------|----------------|
| `active_order_id` | | | |
| `order_findings` | | | |
| `inventory_findings` | | | |
| `customer_reply_draft` | | | |
| `app:ticket_id` | | | |

Then implement one writer discipline in code: in `order_agent` instruction, require a tool (add if needed) `set_active_order(order_id: str, tool_context: ToolContext)` as the **only** way to set `active_order_id`.

### Expect

You can explain who mutates which keys in a design review without opening Discord.

---

## Task 6 — Graph mindset (even if you start with templates)

### Why

ADK 2.0 pushes **graph** and **dynamic** workflows as the flexible future; templates remain literacy. SMEs think in graphs even when coding a `SequentialAgent`.

### Do this

Draw (ASCII is fine) in `05-agent-boundaries.md` the production target:

```
[Intake]
   │
   ▼
[Router]----pure policy FAQ----▶ [RAG node - later]
   │
   ├─ WISMO ──▶ [OrderAgent] ──▶ [Synthesizer]
   │
   ├─ Shortage ──▶ [OrderAgent] ──▶ [InventoryAgent] ──▶ [Synthesizer]
   │
   └─ Refund ──▶ [RefundAgent] ──▶ [HITL gate] ──▶ [Payments]
```

Label each edge **deterministic** vs **intelligent**.

### Expect

HITL gate is deterministic. Router is intelligent. Payments settle node is deterministic.

---

## Task 7 — Loop pattern (critic / refiner) — light lab

### Why

Customer replies need a quality gate without infinite babble.

### Do this

If your ADK build includes `LoopAgent`, create `project/meridian_reply_loop/` that loops:

1. `synthesizer_agent` drafts  
2. `critic_agent` checks: invents facts? missing next_step? refund language?

Stop when critic says `PASS` or `max_iterations=2`.

If `LoopAgent` import fails on your version, implement the **mental model** in the decision doc and a tiny deterministic Python function `critic_reply(draft: str) -> dict` that fails on the substring `refund` for this lesson’s synthesizer output test — still a valid lab.

Critic stub example:

```python
def critic_reply(draft: str) -> dict:
    """Deterministic critic for lab use."""
    banned = ["we refunded", "full refund issued"]
    for b in banned:
        if b in draft.lower():
            return {"status": "FAIL", "reason": f"banned phrase: {b}"}
    if "next step" not in draft.lower():
        return {"status": "FAIL", "reason": "missing next step"}
    return {"status": "PASS"}
```

Unit test it.

### Expect

A failing draft with “we refunded” is caught **without** an LLM critic.

---

## How it works (deeper dive)

### Fan-out / fan-in

```
        ┌─ OrderAgent ──┐
Router ─┤               ├─ Synthesizer
        └─ Inventory ───┘
```

Danger: both write `findings` to the same key. Use `order_findings` / `inventory_findings`.

### Long-running mental model

Production OrderOps tickets may pause for HITL for hours. Think:

- **checkpoint** = durable state + ticket id  
- **resume** = load state, continue graph at HITL edge  
- Lesson 07 implements the gate; Lesson 09 deploys storage

### Custom agents

When the business says “never call inventory unless OMS lifecycle ∈ {picking, ready_for_pickup},” that predicate may belong in code (`BaseAgent` / graph node), not in a hopeful instruction.

---

## Common pitfalls / troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Sequential always burns inventory tokens on WISMO | Wrong entrypoint | Router or graph branch |
| Router answers instead of transferring | Weak instruction / missing transfer tool | Add transfer tool; shrink router tools |
| State empty in synthesizer | Forgot `output_key` / wrong placeholder | Match `{order_findings}` names |
| Parallel overwrites | Same state key | Namespace keys |
| Import errors for specialists | `PYTHONPATH` | `export PYTHONPATH=.` from `project/` |

---

## You are done when

- [ ] Specialist modules import cleanly  
- [ ] Sequential pipeline produces a draft from findings  
- [ ] Router transfers for at least two different ticket types  
- [ ] State ownership table + ASCII graph exist  
- [ ] Critic (LLM loop or deterministic) catches banned refund language  

---

## Knowledge check

1. When is `SequentialAgent` the wrong default entrypoint?  
2. Why give inventory no refund tool even if the router “wouldn’t ask”?  
3. What does `output_key` buy you between agents?  
4. Name one race condition in parallel OMS+ATP agents.  
5. What should be a deterministic edge in the refund path?

### Answers

1. When many tickets only need one stage — forced stages waste cost/latency.  
2. Least privilege; prompt obedience is not an authz boundary.  
3. A stable state slot for the next agent/instruction placeholders.  
4. Both write `findings` / both mutate `active_order_id` differently.  
5. HITL approval before settlement / confirm=true money tool.

---

## Recap

- You composed Meridian specialists with sequential + router patterns.  
- You practiced state ownership and graph thinking for ADK 2.0.  
- Next: context, memory, and policy knowledge so synthesizers stop guessing.

---

## Stretch goal

Add a `ParallelAgent` that fetches order + ATP concurrently behind a deterministic join node that builds `investigation_bundle` for the synthesizer. Document key namespacing choices.

---

## Feedback

- Could you teach a teammate why router≠god-agent using your graph drawing?  
- What tripped you up: transfers, SequentialAgent, state keys, or Loop/critic?  
- Note task number + expected vs actual.

---

## Navigate

**← Prev** [Lesson 04 — Tools deep mastery](04-tools-mastery.md)  
**Next →** [Lesson 06 — Context, memory, and knowledge](06-context-memory-knowledge.md)
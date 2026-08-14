# Lesson 28 — Architecture patterns catalog

**Level:** Advanced (platform)  
**Time:** ~120–150 minutes  
**Prerequisites:** Pack C (13–17) and Lesson 05; you already have router, sequential, loop, and Workflow slices  
**Lab outcome:** Pick — and defend — a Meridian architecture **on demand**: router, planner, critic, HITL, hybrid — using **native ADK**, not a new graph engine

**Standard:** [docs/NATIVE-ADK.md](../docs/NATIVE-ADK.md)

---

## At a glance

An SME is not “the person who always uses a Workflow.”  
An SME is the person who can say **why this ticket is a router, that one is a graph, and this refund is HITL**.

| Pattern | Native ADK | Meridian when |
|---------|------------|---------------|
| **Single agent + tools** | `LlmAgent` | One skill, few tools (WISMO only) |
| **Router + specialists** | `sub_agents` + transfer | Chat could be order *or* inventory |
| **Sequential** | `SequentialAgent` or Workflow chain | Investigate → draft reply |
| **Parallel + join** | `ParallelAgent` / `JoinNode` | OMS + ATP at the same time |
| **Loop / critic** | `LoopAgent` or Workflow loop | Draft until critic passes or max turns |
| **Graph** | `Workflow` + routes | Branches, HITL, money paths |
| **HITL pause** | `RequestInput` | Human must approve |
| **Hybrid** | Deterministic tool **then** LLM | Classifier + specialist (your router already) |
| **Remote specialist** | `RemoteA2aAgent` / MCP | Policy or tools live elsewhere |

```
Ticket lands
    │
    ├─ one skill, no money?     → single LlmAgent
    ├─ two skills, same chat?   → router + transfer
    ├─ fixed A then B?          → sequential / Workflow chain
    ├─ two fetches, one reply?  → parallel + join
    ├─ money or legal?          → Workflow + RequestInput
    └─ tool lives in another team? → MCP or A2A
```

---

## Why this matters

Priya (store ops) opens a ticket: “Order MC-1048277 never showed; also can I get a refund and a substitute?”

If you stuff that into one mega-agent:

- Inventory tools sit next to refund tools  
- Nobody can review the prompt  
- A jailbreak in Lesson 23 can reach money  

If you over-split:

- Four hops, lost `order_id`  
- Devon’s handheld waits 40 seconds  

The catalog is how you choose **control vs latency** without guessing.

---

## Know these

| Term | Meaning |
|------|---------|
| **Pattern** | A named way to wire agents/tools/control |
| **Coordinator / router** | Agent that **routes**, not the expert |
| **Specialist** | Agent with a tight tool set |
| **Planner** | Agent (or code) that writes a step list before acting |
| **Critic** | Agent that **scores** a draft; does not call money tools |
| **Hybrid** | Code decides structure; LLM fills language or a node |
| **HITL** | Human in the loop — pause until a person answers |
| **Control plane** | Who is allowed to change the path (you vs the model) |

> **Tip:** “Planner” in this lesson is **not** a homemade loop. If you need a plan, use a first `LlmAgent` that writes structured steps into session state (`output_key`), then a Workflow that **executes** those steps with tools. The graph still owns money.

---

## Task 1 — Inventory what you already built

### Why

You cannot invent on demand if you do not know which pattern each package already is.

### Do this

Create `project/meridian_ops/decisions/28-pattern-inventory.md` and fill from **your** repo:

| Package / agent | Pattern | Control (LLM vs graph vs code) | Money tools? |
|-----------------|---------|--------------------------------|--------------|
| `meridian_order_status` | | | |
| `meridian_inventory` | | | |
| `meridian_orderops_router` | | | |
| `meridian_orderops_sequential` | | | |
| `meridian_reply_loop` | | | |
| `meridian_orderops` (Workflow) | | | |
| `meridian_orderops_mcp` | | | |
| `meridian_policy_a2a` | | | |
| FastAPI `deploy/app.py` | edge, not an agent | HTTP | no |

If a row does not exist on your machine, write **missing** — do not invent a package.

### Expect

Router ≠ Workflow. Sequential ≠ loop. Edge is not a fourth agent runtime.

---

## Task 2 — Decision tree for five tickets

### Why

Architecture is a **ticket-shaped** choice, not a team fashion.

### Do this

In the same file, add a table:

| Ticket | Story | Pattern you pick | Why not the others |
|--------|-------|------------------|--------------------|
| TCK-WISMO | “Where is MC-1048277?” | | |
| TCK-ATP | “Out of oat milk, substitute?” | | |
| TCK-BOTH | WISMO + substitute in one message | | |
| TCK-REFUND | “Refund the late order” | | |
| TCK-POLICY | “What’s the late-delivery credit rule?” | | |

Rules of thumb (you may disagree — write **why**):

- WISMO-only → single agent or Order specialist  
- ATP-only → Inventory specialist  
- Both in one chat → **router** (Lesson 05)  
- Refund → **Workflow + `RequestInput`**, not a chatty specialist with `request_refund` always loaded  
- Policy FAQ → RAG agent or **A2A/MCP** policy service (least privilege)

### Expect

Refund is never “just add the tool to the WISMO agent.”

---

## Task 3 — Hybrid: code classifies, LLM does not own the route

### Why

Priya’s ticket text is messy. A pure LLM router can send refunds to Inventory.  
A pure regex router misses “they never brought my groceries.”

Hybrid: **deterministic assist + LLM coordinator**, which you already sketched in `meridian_orderops_router`.

### Do this

1. Open `project/meridian_orderops_router/agent.py`.  
2. Confirm `classify_for_router` is a **tool**, not the only authority.  
3. In `28-pattern-inventory.md`, write four bullets:

   - What the classifier returns  
   - What the coordinator still decides  
   - What happens if they disagree  
   - Who you would trust in production (and why)

4. Prove it:

```bash
# -m: run a module; PYTHONPATH so meridian_ops imports resolve from repo root
cd /path/to/agent-learn-sme
source .venv/bin/activate
export PYTHONPATH=project

python - <<'PY'
from meridian_ops.tools.classify_ticket import classify_ticket
samples = [
    "Where is order MC-1048277?",
    "You're short on oat milk for my order",
    "Refund MC-1048277, it never arrived",
]
for s in samples:
    print(s, "→", classify_ticket(s))
PY
```

### Expect

Classifier output is a **hint**. Instruction still says transfer to specialists. Refund language should **not** land on Inventory tools.

> **Watch out:** If you “fix” routing by pasting a 2,000-word instruction and deleting `classify_for_router`, you made the model the control plane again.

---

## Task 4 — Planner vs critic vs HITL (who may spend money)

### Why

People mash these three together. They are different **jobs**.

### Do this

Draw this in the decision file (ASCII is enough):

```
Planner (optional)  → writes plan to state  → no payments tool
Specialist / graph  → calls OMS/ATP        → no confirm refund
Critic / loop       → scores the draft     → no payments tool
HITL RequestInput   → human yes/no         → only then money tool
```

Then answer in bullets:

- If the critic can call `request_refund`, what goes wrong?  
- If HITL is only in the prompt (“ask a manager”), what goes wrong?  
- If the planner executes tools itself, what goes wrong?

### Expect

- Critic: **read + score**, no side effects  
- HITL: **ADK `RequestInput`**, not a polite sentence  
- Planner: **state**, then a graph/specialist executes  

---

## Task 5 — Invent a hybrid for a messy combo ticket

### Why

SME bar: you can design a **new** path without a new framework.

### Do this

Scenario: vendor delay + possible credit + policy citation.

Write `project/meridian_ops/decisions/28-vendor-delay-architecture.md`:

1. **Nodes / agents** (names only)  
2. **Edges** (when you branch)  
3. **Where HITL sits**  
4. **Where policy is fetched** (MCP vs A2A vs RAG — pick one and say why)  
5. **What you refuse to DIY** (one sentence pointing at Native ADK)

Optional lab (if Lesson 13 Workflow already exists): add a **comment** on the refund branch that cites this ADR. Do not rewrite the graph unless it is wrong.

### Expect

A one-page ADR a teammate could implement next week. Not a new `MeridianGraph` class.

---

## How it works (deeper dive)

**Control vs intelligence**

- **Control:** routes, HITL, tool allow-lists, plugins (Lesson 26)  
- **Intelligence:** wording, which specialist to prefer when both are plausible  

Put control in **Workflow edges, tools, plugins, and the edge API**.  
Put intelligence in **`LlmAgent` nodes**.

**Why templates still exist**

`SequentialAgent` / `ParallelAgent` / `LoopAgent` are fine for small slices.  
Production OrderOps with refunds usually wants **`Workflow`** because branches are explicit.

**Why the FastAPI edge is in the catalog**

Auth, tenant headers, rate limits, and “this is not an agent” live at HTTP.  
The edge **calls** `App` + `Runner`. It does not become a second orchestrator.

---

## Common pitfalls / troubleshooting

| Symptom | Fix |
|---------|-----|
| God-agent with 12 tools | Split specialists; refunds on a HITL graph |
| Four agents, lost order id | Session state ownership (Lesson 05 prefixes) |
| “Planner” that is a `while True` in Python | Native loop/Workflow; no DIY agent loop |
| Policy copied into every instruction | MCP/A2A + citations (Lessons 16–18) |
| Router always answers itself | Instruction + transfer tool; eval the trajectory |

---

## You are done when

- [ ] Pattern inventory matches **your** packages  
- [ ] Five tickets have a defended pattern  
- [ ] Hybrid classifier vs LLM roles are written down  
- [ ] Planner / critic / HITL money rules are explicit  
- [ ] Vendor-delay ADR does not invent a graph engine  

---

## Knowledge check

1. When is a router better than one agent with every tool?  
2. Why must a critic not have payment tools?  
3. What makes a design “hybrid”?  
4. Where should refund approval live: prompt or `RequestInput`?  
5. Name one pattern that belongs at the FastAPI edge, not in an agent.

### Answers

1. When the chat can need **different privileges** (order vs inventory vs refund).  
2. It would **execute** what it is supposed to **judge**.  
3. **Code or a tool** structures the path; the LLM does not own money/routing alone.  
4. **`RequestInput`** (or tool confirmation) — prompts are skippable.  
5. Auth, API keys, tenant id, rate limits, or load shedding.

---

## Recap

- You can **name** the Meridian pattern for a ticket and reject the wrong ones.  
- Native ADK already has the catalog; your job is **selection**.  
- Next: sessions that survive more than one process.

---

## Stretch goal

Add a sixth ticket: “photo of a smashed produce bag + refund.” Map multimodal (Lesson 21) + HITL + WISMO. One paragraph: which node sees the image, which node may refund.

---

## Feedback

- Could you whiteboard Priya’s combo ticket for a new teammate without this page?  
- Note the task number and what you expected vs what your repo actually contained.

---

## Navigate

**← Prev** [Lesson 27 — Privacy](27-privacy-retention-compliance.md) · [Lesson 42 — RAI](42-responsible-ai-champion.md)  
**Next →** [Lesson 29 — Sessions at scale](29-sessions-at-scale.md)  
**Track home:** [README](../README.md)

# Lesson 05 — Multi-agent orchestration

**Level:** Advanced  
**Time:** ~100–120 minutes  
**Prerequisites:** Lessons 01–04 (classifier, `adk web`, session state, hardened OMS / ATP / refund tools)  
**Lab outcome:** Meridian **OrderOps** as a team: Order / Inventory / Synthesizer specialists, a **Workflow** that always runs Order → Inventory → draft, and a **router** that hands work to the right specialist

---

## At a glance

Lesson 04 gave each job a **tool belt**. This lesson decides **who is allowed to hold which belt**.

One mega-agent with every tool is easy to demo and hard to review. Priya cannot tell whether Inventory refunded Maya, or whether Order Status invented a substitute.

You will learn, then prove:

- A **specialist** is a small agent with one job and a short tool list
- A **Workflow** is a graph: nodes plus **edges** that always fire in the order you wrote
- A **router** is an agent that **transfers** (hands off) to a specialist — it does not own OMS + ATP + refunds itself
- `output_key` copies a specialist’s final text into **session state** so the next node can read it
- Least privilege is the `tools=` list, not a sentence in the instruction

You will prove most of this with `pytest`. The model joins in Tasks 3–5, inside `adk web`.

If you get lost, scroll back to this table. Each task fills one row. The scoreboard at the end of every task repeats the same rows.

| Task | What you prove | How |
|------|----------------|-----|
| 1 | Inventory cannot refund | `pytest` on `.tools` names — no LLM |
| 2 | Three specialists share one module | Walk `specialists.py` + import smoke |
| 3 | Order then Inventory then draft | Native `Workflow` + `adk web` |
| 4 | WISMO vs shortage go to different people | Router + `transfer_to_agent` + two prompts |
| 5 | Each state key has one writer | `output_key` + `set_active_order` in the UI |
| 6 | Which edges the model may not vote on | Label the graph you already ran |
| 7 | “we refunded” never ships | Deterministic `critic_reply` + `pytest` |

---

## Why this matters

Two tickets hit Store 441 on the same afternoon.

**TCK-9001** — Maya (customer `C-44102`) in the app: order `MC-1048292` says delivered, nothing at the door. That is **WISMO**: “where is my order?” Lifecycle facts. OMS. No substitute. No refund keypad.

**TCK-9003** — Devon (picker) on store ops: pickup `MC-1048310` is due in 90 minutes. Organic milk SKU `884210` (SKU = stock keeping unit, the product id) has **ATP 0** — available-to-promise, meaning the shelf is empty. He needs a substitute preview (`884299`, then bread `552100` as a trap). Still no refund keypad.

If those two jobs live in one agent, Inventory can call `request_refund`, or Order Status can freestyle a reservation. The demo chat still looks slick. Security review still fails.

Priya (CX supervisor) will ask:

> “Who was allowed to touch Maya’s order — and who was allowed to touch money?”

Your answer cannot be “the instruction said please don’t.” Your answer is the **tool list** and the **graph**.

---

## Know these

Read this table before Task 1. Every later task reuses these words.

| Term | Plain English | Meridian example |
|------|---------------|------------------|
| **Specialist** | A small agent with one job and only the tools for that job | `order_agent` may call `get_order`. It may not call `request_refund` |
| **Mega-agent** | One agent that holds every tool | Order + Inventory + refunds in a single `tools=[...]` |
| **Orchestration** | Deciding who runs, in what order, with what they can see | Router picks a specialist, or a Workflow always runs A then B then C |
| **Least privilege** | Give an agent only what its job needs | Devon can radio the cooler. He cannot open the cash office |
| **Transfer / handoff** | Router stops answering and gives the turn to a named specialist | `transfer_to_agent(agent_name="order_agent")` |
| **Coordinator / router** | The front-desk agent. It classifies and transfers. It is not the expert | `orderops_router` |
| **`sub_agents`** | The **people** the router may hand off to — other agents, not tools | `[order_agent, inventory_agent]` |
| **Workflow** | Native ADK graph: `edges` from node to node. The edge order is code, not a hope | `START → order_agent → inventory_agent → synthesizer_agent` |
| **Edge** | One allowed hop in that graph | After Order finishes, Inventory **always** runs |
| **Node** | One box on the graph — often an `Agent`, sometimes a Python function | `synthesizer_agent` is an LLM node with **no** tools |
| **Deterministic** | Code always does this. The model does not get a vote | Workflow hops; HITL approve/deny (Lesson 07) |
| **Intelligent** | The model chooses | Router calling `transfer_to_agent` |
| **`output_key`** | ADK copies the agent’s **final text** into session state under this name | `order_agent` → `state["order_findings"]` |
| **Session state** | Scratchpad for **this** chat / run | `active_order_id`, `order_findings`, `customer_reply_draft` |
| **`{name?}`** | Instruction placeholder: inject that state key; `?` means “empty string if missing” | `{order_findings?}` on the synthesizer |
| **Synthesizer** | Drafter. Reads findings. Writes a customer-safe reply. No OMS/ATP/refund tools | Empathy → facts → next step |
| **WISMO** | Where is my order? | `TCK-9001` / `MC-1048292` |
| **ATP** | Available-to-promise: units still on the shelf | Milk `884210` at Store `ST-221` is `0` |
| **SKU** | Stock keeping unit — the product id | `884210` = Organic Milk 1gal |
| **HITL** | Human in the loop: a person must approve before the next step | Priya and refunds over $75 — **Lesson 07**, not today |
| **`SequentialAgent`** | Older ADK helper: run `sub_agents` in list order | Literacy only. This lab uses `Workflow` |
| **`LoopAgent`** | Older ADK helper: repeat sub-agents up to `max_iterations` | Literacy only. Critic **loop graphs** are Lesson 14 |

### Picture this: the front desk vs the back room

Store 441 does not give every employee every key.

```
Maya / Devon ticket
        │
        ▼
   [ Front desk ]          ← router (intelligent transfer)
        │
        ├─ WISMO ─────────▶ [ Order specialist ]     get_order only
        │
        └─ milk short ────▶ [ Inventory specialist ] ATP tools only
                                    │
Known pipeline (shortage tickets):
  [ Order ] ──always──▶ [ Inventory ] ──always──▶ [ Synthesizer ]
       ▲                      ▲                         ▲
       └──────── Workflow edges (deterministic) ────────┘
```

Two entry points. Two jobs.

| Pattern | Who picks the next step? | Use when |
|---------|--------------------------|----------|
| **Single agent + tools** | The model picks tools | Tiny WISMO-only chat (Lesson 03) |
| **Router + specialists** | The model picks **which agent**, not every tool | Chat that might be WISMO **or** a short |
| **`Workflow` linear edges** | **Your** `edges=` list | Investigate → draft must not swap order |
| **`SequentialAgent`** | List order (older ADK) | Reading old code. New Meridian work uses `Workflow` |
| **HITL gate** | Priya, via code | Money. Deterministic. Lesson 07 |

> **Tip:** `Agent` and `LlmAgent` are the **same class** (`from google.adk.agents.llm_agent import Agent`). This lesson uses `Agent` to match Lessons 03–04.

---

## What you already have (do not rebuild)

From the **repo root**, confirm these exist. You wrote them in Lessons 01–04.

| Path | Job |
|------|-----|
| `project/meridian_ops/tools/oms.py` | `get_order` |
| `project/meridian_ops/tools/atp.py` | `get_atp`, `reserve_substitute`, `suggest_substitute_for_short` |
| `project/meridian_ops/tools/payments.py` | `request_refund` — Inventory must never import this |
| `project/meridian_ops/tools/classify_ticket.py` | `classify_ticket` → `Route` enum. **Wrap it. Do not rewrite it.** |
| `project/meridian_ops/fixtures/orders.json` | Includes `MC-1048292` (WISMO) and `MC-1048310` (milk short) |
| `project/meridian_ops/fixtures/tickets.json` | `TCK-9001`, `TCK-9003` |
| `project/meridian_ops/agents/specialists.py` | Order / Inventory / Synthesizer (Task 2 walks this) |
| `project/meridian_orderops_sequential/agent.py` | `Workflow` Order → Inventory → Synthesizer |
| `project/meridian_orderops_router/agent.py` | Router — **the tool/sub-agent wiring is wrong**; Task 4 fixes it |
| `project/meridian_inventory/agent.py` | Lesson 04 **standalone** inventory agent. Not the team specialist |

If `payments.py` or `atp.py` is missing, stop and finish Lesson 04. This lesson composes those tools. It does not replace them.

You will **add**:

```
project/meridian_ops/
  tests/
    test_specialist_privilege.py   Task 1
    test_critic_reply.py           Task 7
  agents/
    critic_reply.py                Task 7
```

You will **fix** `project/meridian_orderops_router/agent.py` (Task 4) and **extend** `specialists.py` with `set_active_order` (Task 5).

---

## Task 1 — Prove Inventory cannot refund (pytest, no LLM)

### Why

Lesson 04 said least privilege is the import list. A markdown table in a `decisions/` folder is easy to skip and easy to lie in.

The lock Priya can re-run with `pytest` is: **`request_refund` is not in `inventory_agent.tools`.**

At Store 441, Devon’s badge does not open the cash office. You do not write “Devon promises not to.” You check the badge reader.

`inventory_agent.tools` is that badge reader. Each entry is a Python function. The test reads `.tools` names. The model is not invited.

This replaces the old “fill a capability table on paper” homework.

### Do this

1. Confirm the specialist module imports. From the **repo root**:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
source .venv/bin/activate
export PYTHONPATH=project
python -c "from meridian_ops.agents.specialists import inventory_agent; print([t.__name__ for t in inventory_agent.tools])"
```

   - `source .venv/bin/activate` — use this project’s Python, not Homebrew’s.
   - `export PYTHONPATH=project` — `import meridian_ops` means `project/meridian_ops`.
   - `t.__name__` — these tools are plain functions, so the name is the function name.

   If this import fails, do Task 2 first (create / align `specialists.py`), then come back. The test below needs the module.

2. Create `project/meridian_ops/tests/test_specialist_privilege.py`:

```python
from meridian_ops.agents.specialists import (
    inventory_agent,
    order_agent,
    synthesizer_agent,
)


def _tool_names(agent) -> set[str]:
    names = set()
    for tool in agent.tools:
        names.add(getattr(tool, "__name__", None) or getattr(tool, "name", None))
    return names


def test_inventory_tools_exclude_refund():
    names = _tool_names(inventory_agent)
    assert "request_refund" not in names
    assert names >= {
        "get_atp",
        "reserve_substitute",
        "suggest_substitute_for_short",
    }


def test_order_tools_exclude_refund():
    names = _tool_names(order_agent)
    assert "request_refund" not in names
    assert "get_order" in names


def test_synthesizer_has_no_tools():
    assert _tool_names(synthesizer_agent) == set()
```

   What each piece is for:

   - `_tool_names` — ADK may leave a raw function (`__name__`) or wrap it (`name`). Handle both so the test does not flake.
   - Inventory **must** have the ATP trio. That is the job. Missing `get_atp` is also a failure — an empty tool list would “pass” a refund check by accident.
   - Order may look up Maya’s ticket. It still must not hold `request_refund`.
   - Synthesizer drafts from **state**. If it has tools, it can invent a `get_order` of its own and drift from the findings.

3. Run **only** this file:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
source .venv/bin/activate
export PYTHONPATH=project
pytest project/meridian_ops/tests/test_specialist_privilege.py -v
```

   - `-v` — verbose: print each test name and PASSED/FAILED, not just a dot.

### Expect

```
test_specialist_privilege.py::test_inventory_tools_exclude_refund PASSED
test_specialist_privilege.py::test_order_tools_exclude_refund PASSED
test_specialist_privilege.py::test_synthesizer_has_no_tools PASSED
```

That is the capability table, as code:

| Capability | Order specialist | Inventory specialist | Synthesizer |
|------------|------------------|----------------------|-------------|
| WISMO / lifecycle (`get_order`) | yes | no | no |
| Substitute preview (ATP tools) | no | yes | no |
| Refund (`request_refund`) | **no** | **no** | **no** |
| Policy FAQ | later (Lesson 06) | no | no |
| Loyalty recompute | no — that is a script (Lesson 01) | no | no |

> **Tip:** The Lesson 04 package `meridian_inventory` still has `get_order` because it was a **standalone** agent. The **team** specialist in `specialists.py` does not. Order already wrote `order_findings`. Do not merge those two agents in your head.

> **Watch out:** An instruction that says “No refunds.” is the employee handbook. This test is the badge reader. Keep both. Trust the test.

### Scoreboard after Task 1

| Proof | In place? |
|-------|-----------|
| Inventory `.tools` exclude `request_refund` | **Yes** |
| Specialists walked | Not yet |
| Sequential Workflow | Not yet |
| Router transfer | Not yet |
| State keys in UI | Not yet |
| Edges labeled | Not yet |
| Critic unit test | Not yet |

---

## Task 2 — Walk the specialist module (then smoke-import it)

### Why

Orchestrators compose **packages**. Copy-pasting three `agent.py` files diverges in a week: one model string drifts, one `output_key` is renamed, Inventory quietly gains `request_refund`.

`project/meridian_ops/agents/specialists.py` is the shared roster. The sequential Workflow and the router both import from here.

You will open it (create it if it is missing), match the listing below, and understand four knobs on every `Agent`:

| Knob | What it does |
|------|----------------|
| `name` | Stable id. Router transfer uses this string. |
| `description` | Short blurb. The **router** reads this to decide who to call. Not decoration. |
| `instruction` | Handbook for **this** job. |
| `tools=` | Badge list. Task 1 already proved Inventory’s. |
| `output_key` | Where this agent’s **final text** lands in session state. |

`output_key="order_findings"` means: when `order_agent` finishes talking, ADK writes that text to `state["order_findings"]`. The synthesizer instruction can then say `{order_findings?}`.

### Do this

1. Create the package init if it is missing. From the **repo root**:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
mkdir -p project/meridian_ops/agents
```

   `mkdir -p` creates the folder and does not complain if it already exists.

2. Create an empty `project/meridian_ops/agents/__init__.py` if you do not have one. Python uses that file so `import meridian_ops.agents.specialists` is a normal package import.

3. Open `project/meridian_ops/agents/specialists.py`. Align it to this listing (`Agent`, model `gemini-3.5-flash`, the three `output_key` names):

```python
from __future__ import annotations

from google.adk.agents.llm_agent import Agent

from meridian_ops.tools.atp import get_atp, reserve_substitute, suggest_substitute_for_short
from meridian_ops.tools.oms import get_order

GEMINI = "gemini-3.5-flash"

order_agent = Agent(
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

inventory_agent = Agent(
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

synthesizer_agent = Agent(
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
    tools=[],
    output_key="customer_reply_draft",
)
```

   Walk the file in order:

   ```
   shared model string
     → order_agent  (get_order,  writes order_findings)
     → inventory_agent (ATP trio, writes inventory_findings)
     → synthesizer_agent (no tools, reads both, writes customer_reply_draft)
   ```

   - `from __future__ import annotations` — lets you write modern type hints; harmless if you add types later.
   - `GEMINI = "gemini-3.5-flash"` — one constant so the three specialists cannot drift to three different models.
   - `.strip()` on each instruction — drops the extra newline from the triple quotes so the model does not see a leading blank line.
   - `{order_findings?}` — ADK replaces this with `state["order_findings"]`. The `?` means: if the key is missing, insert `""` instead of crashing the turn.
   - `tools=[]` on the synthesizer is the point. A drafter that can call ATP will “helpfully” skip the Inventory specialist.

4. Smoke-import from the **repo root** (no Gemini call — constructing `Agent` does not hit the network):

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
source .venv/bin/activate
export PYTHONPATH=project
python -c "
from meridian_ops.agents.specialists import order_agent, inventory_agent, synthesizer_agent
print(order_agent.name, order_agent.output_key)
print(inventory_agent.name, inventory_agent.output_key)
print(synthesizer_agent.name, synthesizer_agent.output_key)
"
```

5. Re-run Task 1’s tests. You just touched the roster; the badge reader should still beep the same way.

```bash
pytest project/meridian_ops/tests/test_specialist_privilege.py -v
```

### Expect

The smoke print:

```
order_agent order_findings
inventory_agent inventory_findings
synthesizer_agent customer_reply_draft
```

Privilege tests still PASSED.

> **Tip:** Keep `name=` and `output_key=` as stable contracts. Rename `order_findings` to `findings` and the synthesizer placeholder plus every later graph will go blank.

> **Watch out:** Do not `from meridian_ops.tools.payments import request_refund` in this file “just in case.” Task 1 will fail — that is the alarm working.

> **Watch out:** If your file still says `LlmAgent`, change the import to `Agent`. Same class. Stay consistent with Lessons 03–04.

### Scoreboard after Task 2

| Proof | In place? |
|-------|-----------|
| Inventory `.tools` exclude `request_refund` | Yes |
| Specialists walked | **Yes** |
| Sequential Workflow | Not yet |
| Router transfer | Not yet |
| State keys in UI | Not yet |
| Edges labeled | Not yet |
| Critic unit test | Not yet |

---

## Task 3 — Deterministic sequence: Order → Inventory → Synthesizer

### Why

For a **known** pipeline, do not ask the model whether the draft comes after investigation. **Make the hop code.**

Ticket `TCK-9003` is that pipeline: look up pickup `MC-1048310`, then ATP for milk `884210`, then a customer-safe update for Maya.

A **Workflow** is ADK’s graph. You pass `edges=` — a list of hops. The string `"START"` is the graph entry (the user message). After that, each hop is `(from_node, to_node)`.

Older ADK code used `SequentialAgent(sub_agents=[order_agent, inventory_agent, synthesizer_agent])`. Same *idea* (fixed order). New Meridian work uses `Workflow` linear edges, which is what this repo already ships and what later graph lessons extend (branches, joins, HITL).

The model still **talks** inside each node. It does **not** choose whether Inventory runs.

### Do this

1. Confirm the sequential package exists:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
ls project/meridian_orderops_sequential/
```

   You want `__init__.py` and `agent.py`. If the folder is missing:

```bash
mkdir -p project/meridian_orderops_sequential
printf '%s\n' 'from . import agent' > project/meridian_orderops_sequential/__init__.py
```

   - `printf` writes the one-line init. `adk web` loads `from meridian_orderops_sequential import agent` via that file.

2. Open `project/meridian_orderops_sequential/agent.py`. It must be a `Workflow`, not `SequentialAgent`:

```python
from google.adk.workflow import Workflow

from meridian_ops.agents.specialists import inventory_agent, order_agent, synthesizer_agent

# Fixed path for inventory-exception style tickets:
# Order evidence → Inventory recommendation → customer-safe draft
root_agent = Workflow(
    name="meridian_orderops_sequential",
    description="Deterministic Order → Inventory → Synthesize pipeline.",
    edges=[
        ("START", order_agent),
        (order_agent, inventory_agent),
        (inventory_agent, synthesizer_agent),
    ],
)
```

   What each piece is for:

   - `from google.adk.workflow import Workflow` — native ADK graph, not a homemade runner.
   - `root_agent` — the name `adk web` looks for when you pick this package.
   - `("START", order_agent)` — user text always enters Order first. Inventory cannot jump the line.
   - `(order_agent, inventory_agent)` — **always** next. No `transfer_to_agent` here on purpose.
   - `(inventory_agent, synthesizer_agent)` — draft **after** both findings exist in state (via `output_key`).

   Literacy only — you will see this in older repos. **Do not use it as this lab’s root:**

```python
# SequentialAgent(sub_agents=[order_agent, inventory_agent, synthesizer_agent])
```

3. Prove the object is a Workflow (still no Gemini call):

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
source .venv/bin/activate
export PYTHONPATH=project
python -c "
from meridian_orderops_sequential.agent import root_agent
print(type(root_agent).__name__, root_agent.name)
"
```

4. Run the Dev UI from **`project/`** (parent of the agent packages), same habit as Lesson 02:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme/project
source ../.venv/bin/activate
export PYTHONPATH=.
adk web --port 8000
```

   - `--port 8000` — keep the UI on `http://localhost:8000` so it matches the tab you already have.
   - `PYTHONPATH=.` — here the cwd **is** `project/`, so `.` is the same as `project` from the repo root.

5. In the UI, select **`meridian_orderops_sequential`** (not `meridian_inventory`, not Order Status). One chat, this prompt:

```
Pickup order MC-1048310 may be impacted. Check order lifecycle, then evaluate substitute options if milk SKU 884210 is short. Candidates: 884299, 552100. Preview only. Draft a customer-safe update.
```

### Expect

Smoke print:

```
Workflow meridian_orderops_sequential
```

In `adk web`, the **Events** trail looks like this shape (wording will differ; **order** must not):

```
order_agent
  Function call: get_order
    order_id: MC-1048310
  Function response: status=success, lifecycle=ready_for_pickup, shorted_sku=884210

inventory_agent
  Function call: suggest_substitute_for_short   (and/or get_atp)
    order_id: MC-1048310
    sku: 884210
    candidate_skus: ["884299", "552100"]
  Function response: chosen_substitute=884299, dry_run=true (or preview reservation_id=null)

synthesizer_agent
  (no function calls)
  Draft: empathy → facts (milk short, banner alt 884299) → Next step → what we need from Maya
```

You can point at the **sequence** as the reason Inventory did not run first.

The draft must **not** say Meridian already refunded Maya. There is no refund tool on this graph.

> **Tip:** `MC-1048310` is Maya’s pickup with `shorted_sku: 884210`. `MC-1048292` is the WISMO delivery. Do not mix them in this prompt or Order will look up the wrong ticket.

> **Watch out:** Sequential means **always all three stages**. Do not use this package as the only production front door for pure WISMO (`TCK-9001`) — you would burn ATP tokens for nothing. Pair with the router (Task 4) or a later branched Workflow (Lesson 13).

> **Watch out:** `adk web` does not reliably reload `agent.py`. Restart the process after edits. Run it from `project/`, not from inside `meridian_orderops_sequential/`.

### Scoreboard after Task 3

| Proof | In place? |
|-------|-----------|
| Inventory `.tools` exclude `request_refund` | Yes |
| Specialists walked | Yes |
| Sequential Workflow | **Yes** |
| Router transfer | Not yet |
| State keys in UI | Not yet |
| Edges labeled | Not yet |
| Critic unit test | Not yet |

---

## Task 4 — Router with `transfer_to_agent` (WISMO vs shortage)

### Why

Chat is messy. `TCK-9001` (nothing at the door) and `TCK-9003` (milk short) can arrive on the same entrypoint.

A **router** may **choose a specialist**. It must not own `get_order` + ATP + refunds. If it does, you are back to a mega-agent with extra labels.

ADK’s handoff tool is the function `transfer_to_agent(agent_name, tool_context)`:

- `agent_name` — must match a specialist’s `name=` (`"order_agent"` or `"inventory_agent"`)
- `tool_context` — ADK injects this. You never pass it from your code. The function sets `tool_context.actions.transfer_to_agent = agent_name`

**Correct wiring:**

| List | What belongs there | Example |
|------|--------------------|---------|
| `tools=` | Functions the router may **call** | `classify_for_router`, `transfer_to_agent` |
| `sub_agents=` | Agents it may **hand off to** | `order_agent`, `inventory_agent` |

The file in the repo puts `transfer_to_agent_tool` (the **module**) on `sub_agents`. That is wrong. `sub_agents` must be agents. Importing the module as a coworker fails validation. You will see that, then fix it.

You also wrap Lesson 01’s `classify_ticket`. Same `Route` labels (`single_agent`, `multi_agent`, …). New function, old enum. Do not copy the regexes.

### Do this

1. See the broken import on purpose. From the **repo root**:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
source .venv/bin/activate
export PYTHONPATH=project
python -c "from meridian_orderops_router.agent import root_agent"
```

   You should get a **ValidationError** like:

```
sub_agents.2
  Input should be a valid dictionary or instance of BaseAgent
  input_value=<module 'google.adk.tools.transfer_to_agent_tool' ...>
```

   That is ADK saying: index 2 of `sub_agents` is a **module**, not an agent. The radio landed in the new-hire list.

2. Confirm the package init exists (`project/meridian_orderops_router/__init__.py` should contain `from . import agent`). If the folder is missing, create it the same way as Task 3 (`mkdir -p` + that one-line init).

3. **Replace** `project/meridian_orderops_router/agent.py` with:

```python
from google.adk.agents.llm_agent import Agent
from google.adk.tools import transfer_to_agent

from meridian_ops.agents.specialists import inventory_agent, order_agent
from meridian_ops.tools.classify_ticket import classify_ticket

GEMINI = "gemini-3.5-flash"


def classify_for_router(text: str) -> dict:
    """Deterministic assist for the coordinator. Does not transfer by itself."""
    route = classify_ticket(text)
    return {"status": "success", "route": route.value}


router_agent = Agent(
    name="orderops_router",
    model=GEMINI,
    description="Routes Meridian OrderOps tickets to specialists.",
    instruction="""
You are the Meridian OrderOps coordinator.

Process:
1) Call classify_for_router on the user text.
2) Call transfer_to_agent with agent_name="order_agent" for WISMO / lifecycle /
   delivery / pickup status questions.
3) Call transfer_to_agent with agent_name="inventory_agent" for ATP / SKU /
   substitute / shortage questions.
4) If both are required, transfer to order_agent first when order facts are missing.
5) Refuse loyalty batch jobs and password resets. Do not invent refunds.

Do not answer OMS or ATP questions yourself. Transfer.
""".strip(),
    tools=[classify_for_router, transfer_to_agent],
    sub_agents=[order_agent, inventory_agent],
)

root_agent = router_agent
```

   What each piece is for:

   - `from google.adk.tools import transfer_to_agent` — the **function**. Not `transfer_to_agent_tool` (that name is the module file).
   - `classify_for_router` — calls `classify_ticket(text)` and returns `route.value` (a string such as `"single_agent"` or `"multi_agent"`). The `Route` enum stays in `classify_ticket.py`.
   - `tools=[classify_for_router, transfer_to_agent]` — front desk phone + handoff button.
   - `sub_agents=[order_agent, inventory_agent]` — **only** agents. Two coworkers.
   - Instruction uses the exact `agent_name` strings. Those strings must match `name=` on the specialists.
   - `root_agent = router_agent` — `adk web` entry.

4. Prove the object loads, and that the two lists are correct:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
source .venv/bin/activate
export PYTHONPATH=project
python -c "
from meridian_orderops_router.agent import root_agent, classify_for_router
print(root_agent.name)
print([a.name for a in root_agent.sub_agents])
print([getattr(t, '__name__', getattr(t, 'name', t)) for t in root_agent.tools])
print(classify_for_router('ATP shows 0 for organic milk SKU 884210 on pickup order MC-1048310'))
print(classify_for_router('What is the status of order MC-1048292? nothing at the door'))
"
```

5. Restart `adk web` from `project/` (same commands as Task 3). Select **`meridian_orderops_router`**.

   **Prompt A — WISMO (`TCK-9001` shape).** Start a **new** session:

```
What's the status of order MC-1048292? It says delivered but nothing was left at my door.
```

   **Prompt B — shortage (`TCK-9003` shape).** Another **new** session (do not continue the WISMO thread):

```
ATP shows 0 for organic milk SKU 884210 on pickup order MC-1048310. Need substitute guidance. Candidates 884299 then 552100. Preview only.
```

### Expect

The python smoke print:

```
orderops_router
['order_agent', 'inventory_agent']
['classify_for_router', 'transfer_to_agent']
{'status': 'success', 'route': 'multi_agent'}
{'status': 'success', 'route': 'single_agent'}
```

Those two `route` strings come from Lesson 01’s classifier: inventory language → `multi_agent`; a doorstep WISMO → `single_agent`. The router still has to **transfer**. The classifier does not switch agents by itself.

**Prompt A Events** (shape):

```
orderops_router
  classify_for_router → route=single_agent
  transfer_to_agent   → agent_name=order_agent
order_agent
  get_order(order_id=MC-1048292)
  lifecycle=delivered, pod_photo_present=false
```

**Prompt B Events** (shape):

```
orderops_router
  classify_for_router → route=multi_agent
  transfer_to_agent   → agent_name=inventory_agent
inventory_agent
  get_atp and/or suggest_substitute_for_short
  chosen_substitute=884299, dry_run
```

> **Tip:** Sub-agent `description=` is how the model tells Order apart from Inventory when it fills `agent_name`. Keep those sentences specific.

> **Watch out:** `from google.adk.tools import transfer_to_agent_tool` imports a **module**. Putting that module on `sub_agents` is the ValidationError you just fixed. The function goes on `tools=`.

> **Watch out:** If the router answers “delivered at 17:12” **without** `transfer_to_agent` in the trail, it is freelancing. Shrink its ego: no OMS tools on the router, instruction says “Do not answer … yourself. Transfer.”

> **Watch out:** Reuse one session for A then B and the leftover `order_findings` will confuse you. New session per prompt.

### Scoreboard after Task 4

| Proof | In place? |
|-------|-----------|
| Inventory `.tools` exclude `request_refund` | Yes |
| Specialists walked | Yes |
| Sequential Workflow | Yes |
| Router transfer | **Yes** |
| State keys in UI | Not yet |
| Edges labeled | Not yet |
| Critic unit test | Not yet |

---

## Task 5 — State ownership (`output_key` + `set_active_order`)

### Why

Session state is a shared whiteboard. If two specialists write the same key, the second silently erases the first. That is a **race** — a bug where “who finished last” wins, and you cannot see it in the chat bubble.

Today’s sequential graph is one-at-a-time, so you may not see a race yet. The **names** still matter. Lesson 14 will run Order-ish and Inventory-ish work in parallel. If both write `findings`, you will debug ghosts.

Rules:

| Key | Writer | Readers | Notes |
|-----|--------|---------|-------|
| `order_findings` | `order_agent` via `output_key` | Synthesizer (`{order_findings?}`) | Final **text**, not the raw `get_order` dict |
| `inventory_findings` | `inventory_agent` via `output_key` | Synthesizer | Includes chosen SKU + correlation ids if the instruction was followed |
| `customer_reply_draft` | `synthesizer_agent` via `output_key` | Humans / later critic | Must not invent refunds |
| `active_order_id` | **Only** `set_active_order` | Anyone who needs “that order” | Structured id, not a paragraph |

`output_key` cannot set `active_order_id` cleanly — it stores the whole final reply, not `"MC-1048310"`. For a single owned id, use a tiny tool that writes one key through `ToolContext`.

`ToolContext` is ADK’s handle into the current turn (state, actions). You add it as a parameter. ADK fills it. You do not pass it from `adk web`.

### Do this

1. Add `set_active_order` to `project/meridian_ops/agents/specialists.py`. Keep the existing imports; add `ToolContext` and the function **above** `order_agent`. Then put the function on Order’s tool list and mention it in the instruction.

Imports at the top should include:

```python
from google.adk.agents.llm_agent import Agent
from google.adk.tools.tool_context import ToolContext

from meridian_ops.tools.atp import get_atp, reserve_substitute, suggest_substitute_for_short
from meridian_ops.tools.oms import get_order
```

Function (place it after `GEMINI = ...`):

```python
def set_active_order(order_id: str, tool_context: ToolContext) -> dict:
    """Remember the active order id for this session. Only writer of active_order_id.

    Args:
        order_id: Meridian order id like MC-1048310.
        tool_context: Injected by ADK; do not pass it yourself.
    """
    tool_context.state["active_order_id"] = order_id
    return {"status": "success", "active_order_id": order_id}
```

   Update `order_agent` only:

   - `tools=[get_order, set_active_order]`
   - Add a bullet to the instruction: `After a successful get_order, call set_active_order with that same order_id.`

   What each piece is for:

   - `tool_context.state["active_order_id"] = order_id` — **mutate** one key. Do not assign `tool_context.state = {...}` (that can break the session object).
   - Return a dict, same contract as other tools. The model sees `status=success`. Priya sees the id in state.
   - Inventory and Synthesizer still do **not** get this tool. One writer.

2. Re-run the privilege tests. Order’s list grew; it still must not include `request_refund`. Inventory must be unchanged.

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
source .venv/bin/activate
export PYTHONPATH=project
pytest project/meridian_ops/tests/test_specialist_privilege.py -v
python -c "
from meridian_ops.agents.specialists import order_agent
print([t.__name__ for t in order_agent.tools])
"
```

3. Restart `adk web` from `project/`. Select **`meridian_orderops_sequential`** again. **New** session. Same `MC-1048310` prompt from Task 3.

4. After the turn finishes, open **State** in the ADK Dev UI (on the same page as the chat / events). You are looking for keys, not for a prettier paragraph.

### Expect

Privilege tests still PASSED.

Smoke print includes both Order tools:

```
['get_order', 'set_active_order']
```

In **State**, you should see keys like:

| Key | What “it worked” looks like |
|-----|-----------------------------|
| `order_findings` | Text mentioning `MC-1048310` / `ready_for_pickup` / shorted milk — not an empty string |
| `inventory_findings` | Text mentioning `884299` (or ATP 0 on `884210`) and ideally a `corr-` id |
| `customer_reply_draft` | Empathy + facts + a **next step**. No “we refunded” |
| `active_order_id` | `MC-1048310` — exactly that string, because `set_active_order` wrote it |

If `active_order_id` is missing, Events will show whether `set_active_order` ran. If Order skipped it, the instruction is the handbook failing; the tool is still the only legal writer.

> **Tip:** Prefix keys by owner when two nodes might run together later (`order_findings` vs `inventory_findings`). A single `findings` key is how parallel work eats itself.

> **Watch out:** `{order_findings}` **without** `?` raises if the key is missing. The synthesizer uses `{order_findings?}` so a half-run still drafts instead of crashing. For a required ticket id you would omit `?` on purpose.

> **Watch out:** `output_key` stores **text**. Do not parse `order_findings` as JSON in the next node unless you also set an `output_schema` (later lesson). Today the synthesizer is a reader of sentences, and `active_order_id` is the structured id.

### Scoreboard after Task 5

| Proof | In place? |
|-------|-----------|
| Inventory `.tools` exclude `request_refund` | Yes |
| Specialists walked | Yes |
| Sequential Workflow | Yes |
| Router transfer | Yes |
| State keys in UI | **Yes** |
| Edges labeled | Not yet |
| Critic unit test | Not yet |

---

## Task 6 — Label every edge: deterministic vs intelligent

### Why

SMEs think in graphs even when the code is three linear hops. “The model decided Inventory should wait” is not a reviewable design. “The Workflow edge always runs Inventory next” is.

You already **ran** the sequential package. This task is not a homework markdown file. You print the hops, then you read the labels **in this lesson** and match them to the Events trail you still have (or re-run Task 3 once).

HITL (Priya’s approve/deny) is **deterministic**. The model does not vote on money. That gate is Lesson 07. You still need to know where it sits on the map so you do not “fix” a refund by adding a hopeful instruction to Inventory.

### Do this

1. Print the sequential hops without dumping whole `Agent` objects. From the **repo root**:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
source .venv/bin/activate
export PYTHONPATH=project
python -c "
from meridian_orderops_sequential.agent import root_agent

def node_name(n):
    return n if isinstance(n, str) else n.name

for edge in root_agent.edges:
    print(node_name(edge[0]), '->', node_name(edge[1]))
"
```

   - `isinstance(n, str)` — `"START"` is a string. The other ends are `Agent`s with `.name`.
   - `edge[0]` / `edge[1]` — each Workflow edge in this file is a two-tuple `(from, to)`.

2. Match that print to the Events order from Task 3. Order agent, then Inventory, then Synthesizer. If Events show Inventory first, you are on the wrong package (router) or an old process.

3. Read the labeled maps below. This is the design review artifact — already filled. Your job is to **agree** using the trail, not to invent a second copy in `decisions/`.

### Expect

The print:

```
START -> order_agent
order_agent -> inventory_agent
inventory_agent -> synthesizer_agent
```

**This lab’s sequential graph — every hop labeled:**

```
[START]  ──det──▶  [order_agent]  ──det──▶  [inventory_agent]  ──det──▶  [synthesizer_agent]
              intelligent *inside* each box (tool choice + wording)
              hops *between* boxes are code
```

| Edge | Kind | Why |
|------|------|-----|
| `START → order_agent` | **Deterministic** | Workflow always enters Order. User text does not pick Inventory first. |
| `order_agent → inventory_agent` | **Deterministic** | Shortage pipeline. The model cannot skip ATP “because the order looked fine.” |
| `inventory_agent → synthesizer_agent` | **Deterministic** | Draft comes after evidence. |
| Tool calls **inside** `order_agent` (`get_order`, `set_active_order`) | **Intelligent** | The model chooses when to call them — bounded by `tools=`. |
| Tool calls **inside** `inventory_agent` | **Intelligent** | Same. Default `dry_run=true` is still Python (Lesson 04). |
| Wording of `customer_reply_draft` | **Intelligent** | That is why Task 7’s critic is Python, not vibes. |

**Router (Task 4) — the hop *to* a specialist is intelligent:**

```
[START] ──det──▶ [orderops_router]
                      │
                      │  classify_for_router     ← deterministic *assist* (regex / enum)
                      │  transfer_to_agent       ← intelligent hop
                      │
          ┌───────────┴───────────┐
          ▼                       ▼
    [order_agent]           [inventory_agent]
```

| Edge | Kind | Why |
|------|------|-----|
| User → `orderops_router` | **Deterministic** | That package’s `root_agent` is the router. |
| `classify_for_router` | **Deterministic** | Wraps `classify_ticket`. Same `Route` values as Lesson 01. |
| Router → `order_agent` / `inventory_agent` | **Intelligent** | `transfer_to_agent`. This is the one hop the model is *allowed* to choose. |
| Router answering OMS itself | **Forbidden** | Not an edge. A bug if you see facts with no transfer. |

**Where this is going (later lessons) — labeled now so you do not unlearn it:**

```
[Intake]
   │
   ▼
[Router]----pure policy FAQ----▶ [RAG node — Lesson 06]
   │
   ├─ WISMO ──▶ [OrderAgent] ──▶ [Synthesizer]
   │
   ├─ Shortage ──▶ [OrderAgent] ──▶ [InventoryAgent] ──▶ [Synthesizer]
   │
   └─ Refund ──▶ [RefundAgent] ──▶ [HITL gate] ──▶ [Payments]
                      ▲                 ▲
                      │                 └── DETERMINISTIC (Lesson 07 / 15)
                      └── propose only; not confirm=true
```

| Edge | Kind | Why |
|------|------|-----|
| HITL gate → Payments | **Deterministic** | Priya’s click (or deny). The model does not settle. |
| Payments settle | **Deterministic** | Code + idempotency key. |
| Policy RAG retrieve | **Intelligent** *which* snippet, **deterministic** that retrieve is a tool | Lesson 06 |

> **Tip:** When someone asks “could Inventory run first on a shortage?” the sequential answer is **no** — not because the prompt said so, because `("START", order_agent)` is first.

> **Watch out:** Do not “simplify” the refund path by letting Inventory call `request_refund` if the customer sounds upset. That edge stays off the badge (Task 1) and behind HITL (Lesson 07).

### Scoreboard after Task 6

| Proof | In place? |
|-------|-----------|
| Inventory `.tools` exclude `request_refund` | Yes |
| Specialists walked | Yes |
| Sequential Workflow | Yes |
| Router transfer | Yes |
| State keys in UI | Yes |
| Edges labeled | **Yes** |
| Critic unit test | Not yet |

---

## Task 7 — Deterministic critic: catch “we refunded”

### Why

The synthesizer is an LLM node. It can write a warm paragraph that includes **“we refunded you”** even though no payments tool ran. Priya cannot ship that.

A second LLM “critic agent” is allowed to flake. A flaky quality gate is not a quality gate.

Start with a **Python** function `critic_reply(draft) -> dict`. Same idea as Lesson 04’s tool tests: no Gemini in the room. If the draft contains banned claims, it **FAIL**s. If it has no “next step”, it **FAIL**s.

ADK still ships `LoopAgent(sub_agents=[drafter, critic], max_iterations=2)` — an older helper that repeats until a stop or the max. Meridian does **not** build that package today. Lesson 14 puts this same critic on a **Workflow** loop with an exit route. You are writing the judge those graphs will call.

### Do this

1. Create `project/meridian_ops/agents/critic_reply.py`:

```python
from __future__ import annotations


def critic_reply(draft: str) -> dict:
    """Deterministic quality gate for a Meridian customer-reply draft.

    Returns status=PASS or status=FAIL with a reason. Never calls a model.
    """
    lower = draft.lower()
    banned = ["we refunded", "full refund issued"]
    for phrase in banned:
        if phrase in lower:
            return {"status": "FAIL", "reason": f"banned phrase: {phrase}"}
    if "next step" not in lower:
        return {"status": "FAIL", "reason": "missing next step"}
    return {"status": "PASS"}
```

   Walk the gates in order. First failure wins.

   | Check | Why it exists | What it stops |
   |-------|----------------|---------------|
   | `we refunded` / `full refund issued` | Synthesizer has no payments tool | Shipping a money claim from vibes |
   | `"next step"` required | CX template from the synthesizer instruction | Empathy-only fluff with no action |
   | Else `PASS` | Happy path | A draft you could show Priya |

   - `.lower()` — so `We Refunded` still fails.
   - Return a **dict**, same as tools. Tests assert keys. A later Workflow node can read `status`.

2. Create `project/meridian_ops/tests/test_critic_reply.py`:

```python
from meridian_ops.agents.critic_reply import critic_reply


def test_banned_we_refunded():
    out = critic_reply(
        "Sorry about the milk. We refunded you $214.55. Next step: none."
    )
    assert out["status"] == "FAIL"
    assert "we refunded" in out["reason"]


def test_missing_next_step():
    out = critic_reply(
        "Sorry the organic milk is short. We can preview banner-alt SKU 884299."
    )
    assert out["status"] == "FAIL"
    assert out["reason"] == "missing next step"


def test_clean_draft_passes():
    out = critic_reply(
        "Sorry the organic milk on MC-1048310 is short. "
        "Banner-alt SKU 884299 is in stock as a preview only. "
        "Next step: reply yes to confirm the substitute, or pick another item."
    )
    assert out["status"] == "PASS"
```

   These three are the synthesizer’s failure modes, as code:

   - Banned money language **even when** “next step” is present (first test still FAIL on the phrase).
   - A true-sounding shortage update with **no** next step.
   - Maya’s milk short, `884299`, preview, explicit next step → PASS.

3. Run:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
source .venv/bin/activate
export PYTHONPATH=project
pytest project/meridian_ops/tests/test_critic_reply.py -v
```

4. Optional — paste a draft you actually got from Task 3 into a one-liner. This is not a unit test; it is you using the same function on real output:

```bash
python -c "
from meridian_ops.agents.critic_reply import critic_reply
print(critic_reply('''PASTE_YOUR_DRAFT_HERE'''))
"
```

   If that prints `FAIL` for `missing next step`, your synthesizer skipped the template. The function is still right. Fix is the instruction / a re-run — not deleting the check.

### Expect

```
test_critic_reply.py::test_banned_we_refunded PASSED
test_critic_reply.py::test_missing_next_step PASSED
test_critic_reply.py::test_clean_draft_passes PASSED
```

A failing draft with “we refunded” is caught **without** an LLM critic.

Optional literacy (do **not** add a new `adk web` package for this today):

```python
# Older ADK: LoopAgent(sub_agents=[synthesizer_agent, critic_agent], max_iterations=2)
# Meridian next step: Workflow critic loop — Lesson 14
```

`max_iterations` is the spending cap: without it, a loop can retry forever.

> **Tip:** Keep the banned list **small and exact**. A check for the word `refund` alone would FAIL a correct sentence like “we have not issued a refund.” That is why the tests use `we refunded`.

> **Watch out:** Do not make `test_clean_draft_passes` call Gemini. If the critic needs a model to “understand” the draft, it is no longer a unit test.

### Scoreboard after Task 7

| Proof | In place? |
|-------|-----------|
| Inventory `.tools` exclude `request_refund` | Yes |
| Specialists walked | Yes |
| Sequential Workflow | Yes |
| Router transfer | Yes |
| State keys in UI | Yes |
| Edges labeled | Yes |
| Critic unit test | **Yes** |

---

## How it works (deeper dive)

### `output_key` vs a state-writing tool

| Mechanism | What gets stored | Good for |
|-----------|------------------|----------|
| `output_key="order_findings"` | The agent’s **final text** | Passing a narrative to the synthesizer |
| `set_active_order` → `tool_context.state["active_order_id"]` | One id | “That order” on the next turn |
| Instruction `{order_findings?}` | Read path | Injecting the narrative into the next handbook |

ADK copies `output_key` from the agent’s final response into `state_delta`. Other agents in the same session see it on the next node / turn.

### Why the router is not a Workflow

| | Router | Sequential Workflow |
|--|--------|---------------------|
| Unknown ticket type at the door | **Yes** — WISMO or short | No — always three stages |
| Must not skip Inventory on `TCK-9003` | Hopeful instruction | **Edge** |
| Cost on pure WISMO | One specialist | Wastes ATP |

Production OrderOps usually **starts** like the router (or a later `Workflow` with **routes**) and **uses** the linear chain only on the shortage branch. You built both pieces. Lesson 13 joins them with labeled routes.

### Fan-out (later) and why keys were namespaced today

**Fan-out** means two specialists run at the same time. **Fan-in** means a later node waits for both.

```
        ┌─ order narrative ──┐
lookup ─┤                    ├─ synthesizer
        └─ inventory ATP ────┘
```

Danger: both write `findings`. You already named `order_findings` and `inventory_findings`. Lesson 14’s `JoinNode` depends on that habit.

### Long-running tickets

A refund may wait hours for Priya. Mental model (not today’s code):

- **Session state** holds the ticket’s scratchpad
- **HITL** is a deterministic gate (Lesson 07 CLI; Lesson 15 native `RequestInput` pause)
- Do not invent your own checkpoint file format for chat state

### When the hop must be code, not a specialist

If Finance says “never call inventory unless OMS lifecycle is `picking` or `ready_for_pickup`,” that predicate belongs in a **Workflow function node** (Lesson 13), not in Order’s instruction. Instructions drop under pressure. Edges do not.

---

## Common pitfalls / troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `ValidationError` `sub_agents.2` … `transfer_to_agent_tool` module | Module on `sub_agents` | `tools=[classify_for_router, transfer_to_agent]`, `sub_agents=[order_agent, inventory_agent]` |
| `ModuleNotFoundError: meridian_ops` | `PYTHONPATH` unset | Repo root: `export PYTHONPATH=project`. From `project/`: `export PYTHONPATH=.` |
| `adk web` list missing sequential / router | Ran from the wrong directory | Run from `project/` |
| Sequential always calls ATP on a WISMO paste | Wrong entrypoint | Use `meridian_orderops_router` for mixed chat; sequential is the shortage pipeline |
| Router answers without `transfer_to_agent` | Router thinks it is the expert | No OMS/ATP on router `tools=`; instruction says Transfer |
| State empty for synthesizer | `output_key` mismatch or `{order_findings}` without data | Match `order_findings` / `{order_findings?}` |
| `active_order_id` missing | `set_active_order` not on `tools=` or not called | Check Order Events; keep one writer |
| Privilege test fails after Task 5 | Accidental `request_refund` import | Remove it. Re-run Task 1 |
| Suggest picks bread `552100` | Candidates listed bread first | Rank `884299` before `552100` (Lesson 04) |
| Critic FAIL on a good “we have not issued a refund” | Banned list too broad | Keep phrases `we refunded` / `full refund issued` |
| UI looks stale after edits | `adk web` did not reload | Restart the process |

---

## You are done when

- [ ] `test_specialist_privilege.py` passes — Inventory `.tools` names exclude `request_refund`
- [ ] Smoke import prints `order_findings` / `inventory_findings` / `customer_reply_draft`
- [ ] `meridian_orderops_sequential` in `adk web` runs Order, then Inventory, then a draft for `MC-1048310` / SKU `884210`
- [ ] Router import no longer ValidationErrors; WISMO prompt transfers to `order_agent`; shortage prompt transfers to `inventory_agent`
- [ ] State shows the three `output_key`s and `active_order_id=MC-1048310`
- [ ] You can label each sequential hop deterministic vs intelligent without opening a blank homework doc
- [ ] `test_critic_reply.py` fails a “we refunded” draft without an LLM

---

## Knowledge check

Answer from **this lab**, not from general agent lore.

1. In `test_inventory_tools_exclude_refund`, which Python names had to be **present**, and which name had to be **absent**? Why is an empty `tools=[]` on Inventory not a pass?
2. What exact ValidationError field (`sub_agents.2` …) did you see before the router fix? What two lists did the smoke print after the fix?
3. After the sequential `MC-1048310` run, which agent ran first, and which `output_key` should hold the OMS narrative?
4. `classify_for_router` on the milk-short sentence returned which `route` string? Did that string transfer by itself, or did you still need `transfer_to_agent`?
5. Who is allowed to write `active_order_id`? What goes wrong if Inventory also writes it?
6. What does `critic_reply` return (`status` + `reason`) for: *“Sorry about the milk. We refunded you $214.55. Next step: none.”*?

### Answers

1. Present: `get_atp`, `reserve_substitute`, `suggest_substitute_for_short`. Absent: `request_refund`. Empty tools would dodge the refund check but Inventory could not do its job — the `>=` set stops that cheat.
2. `sub_agents.2` was the `transfer_to_agent_tool` **module**, not a `BaseAgent`. After the fix: `sub_agents` `['order_agent', 'inventory_agent']` and tools `['classify_for_router', 'transfer_to_agent']`.
3. `order_agent` first (`START → order_agent`). `order_findings`.
4. `"multi_agent"`. Classifier is an assist only. Handoff is `transfer_to_agent(agent_name="inventory_agent")`.
5. Only `set_active_order` on `order_agent`. Two writers → last write wins; Inventory could point the session at the wrong order.
6. `{"status": "FAIL", "reason": "banned phrase: we refunded"}` — the banned check runs **before** “next step”, so the dummy next step does not save it.

---

## Recap

- You split Meridian OrderOps into specialists whose **tool lists** are the security boundary, then proved Inventory cannot refund with pytest.  
- You ran a native **Workflow** so Order → Inventory → draft is an edge, and a **router** so WISMO vs shortage is a `transfer_to_agent` handoff — not a mega-agent.  
- Next: context, memory, and policy knowledge so the synthesizer cites Meridian policy instead of guessing credits.

---

## Stretch goal

Add `project/meridian_ops/tests/test_classify_for_router.py` that imports `classify_for_router` from `meridian_orderops_router.agent` and asserts:

- `TCK-9003` text (milk SKU `884210`) → `route == "multi_agent"`
- `TCK-9001` text (nothing at the door, `MC-1048292`) → `route == "single_agent"`

Read the strings from `project/meridian_ops/fixtures/tickets.json` so the test tracks the fixture, not a copied sentence. Still no LLM. Still wrapping `classify_ticket`, not rewriting `Route`.

---

## Feedback

- Could you rebuild `specialists.py` + the Workflow `edges=` list from memory (names, tool lists, `output_key`s) without scrolling up?
- What tripped you up: privilege pytest, Workflow vs router, `transfer_to_agent` wiring, state keys, or the critic?
- Note the **task number** and what you expected vs what happened (command + first lines of output). That is the signal that improves this lesson — “it was confusing” is not.

---

## Navigate

**← Prev** [Lesson 04 — Tools deep mastery](04-tools-mastery.md)  
**Next →** [Lesson 06 — Context, memory, and knowledge](06-context-memory-knowledge.md)

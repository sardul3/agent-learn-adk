# Lesson 13 — ADK graph workflows (native)

**Level:** Advanced  
**Time:** ~120 minutes  
**Prerequisites:** Lessons 05, 07, 08; `google-adk>=2.0`; Python **3.11+**  
**Lab outcome:** Run Meridian OrderOps as a native ADK `Workflow` with deterministic routes + LLM nodes — **no custom graph engine**

**Standard:** [docs/NATIVE-ADK.md](../docs/NATIVE-ADK.md)

---

## At a glance

ADK 2.x gives you graphs:

- `Workflow` + `edges`
- `Event(route=...)` for deterministic branching
- `LlmAgent` nodes for judgment/language
- `RequestInput` for HITL (Lesson 15 deepens this)

You will **not** build `MeridianGraph`. You will use the package already in the repo and extend it.

---

## Why this matters

Refund vs WISMO must be an **edge**, not a hope in a prompt. Native `Workflow` makes that reviewable and testable with ADK runners/evals.

---

## Know these

| Term | Native ADK meaning |
|------|-------------------|
| **Workflow** | Graph agent: nodes + edges |
| **Function node** | Plain Python callable auto-wrapped by ADK |
| **LlmAgent node** | Model-powered node in the graph |
| **Event.route** | Label that selects the next edge |
| **JoinNode** | Fan-in after parallel branches |
| **START** | Graph entry; receives user `Content` |

```
START → route_ticket (code)
           ├─ WISMO → lookup → order_narrator → synthesizer
           ├─ SHORTAGE → lookup → (narrator ‖ inventory) → Join → synthesizer
           ├─ REFUND → lookup → RequestInput HITL → finalize(code) → synthesizer
           └─ POLICY / UNSUPPORTED → …
```

---

## Task 1 — Install / verify ADK 2 workflow APIs

### Why

Wrong major version → wrong APIs → temptation to reinvent.

### Do this

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
python3 -m venv .venv
source .venv/bin/activate
pip install -U "google-adk>=2.0.0" pytest pytest-asyncio

python - <<'PY'
from google.adk.workflow import Workflow, JoinNode
from google.adk.events.event import Event
from google.adk.events.request_input import RequestInput
from google.adk.agents import LlmAgent
from google.adk.apps import App
from google.adk.runners import InMemoryRunner
print("native workflow stack OK")
PY
```

### Expect

`native workflow stack OK`. If imports fail, fix the install — do **not** write a DIY graph.

---

## Task 2 — Read the native OrderOps workflow

### Why

The reference implementation is the curriculum’s source of truth.

### Do this

Open and read:

- `project/meridian_orderops/agent.py`
- `project/meridian_orderops/__init__.py`

Confirm it uses only:

- `Workflow`, `JoinNode`, `Event`, `RequestInput`, `LlmAgent`
- Domain `get_order` from `meridian_ops.tools.oms`

### Expect

No `MeridianGraph`, no hand-rolled edge runner.

> **Tip:** Domain tools are allowed. Alternate orchestrators are not.

---

## Task 3 — Run with `adk web` / `adk run`

### Why

Native discovery path — same as Lesson 02.

### Do this

Ensure OMS fixture exists (`orders.json` from Lesson 03) with `MC-1048292` / `MC-1048277`.

```bash
cd /Users/alishaghatane/dev/agent-learn-sme/project
source ../.venv/bin/activate
export PYTHONPATH=.
export GOOGLE_API_KEY="YOUR_KEY"   # or agent .env pattern
adk web --port 8000
```

Select `meridian_orderops` and try:

1. `What's the status of order MC-1048292? nothing at the door`  
2. `I want a full refund of $214.55 for melted items on MC-1048277`  

### Expect

- WISMO path produces ops narrative (tool/OMS-backed via `lookup_order`)  
- Refund path **pauses** for HITL (`RequestInput`) — approve/deny in the UI  

> **Watch out:** HITL resume UX is ADK’s — don’t invent a side-channel checkpoint file for this lesson.

---

## Task 4 — Invoke with native `App` + `InMemoryRunner` (test harness)

### Why

Production and CI use `Runner`, not a DIY loop.

### Do this

Create `project/meridian_ops/tests/test_orderops_workflow_runner.py`:

```python
import pytest
from google.adk.apps import App
from google.adk.runners import InMemoryRunner
from google.genai import types

from meridian_orderops.agent import root_agent


@pytest.mark.asyncio
async def test_wismo_workflow_emits_events():
    app = App(name="meridian_orderops", root_agent=root_agent)
    runner = InMemoryRunner(app=app)
    session = await runner.session_service.create_session(
        app_name="meridian_orderops", user_id="eval_user"
    )
    events = []
    async for event in runner.run_async(
        user_id="eval_user",
        session_id=session.id,
        new_message=types.Content(
            role="user",
            parts=[types.Part.from_text(text="Status for MC-1048292 please")],
        ),
    ):
        events.append(event)
    assert events, "expected ADK events from Workflow"
```

Run:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
export PYTHONPATH=project
pytest project/meridian_ops/tests/test_orderops_workflow_runner.py -v
```

### Expect

Test collects ADK events (may call the model — needs API key). For offline CI, keep **tool unit tests** separate; graph wiring tests can mock later with ADK patterns — still no DIY agent loop.

---

## Task 5 — Unit-test deterministic nodes without an LLM

### Why

Router/OMS lookup are code nodes — test them directly (they are plain functions).

### Do this

```python
# project/meridian_ops/tests/test_orderops_route_nodes.py
from meridian_orderops.agent import route_ticket, lookup_order
from google.genai import types


def test_route_refund():
    content = types.Content(
        role="user",
        parts=[types.Part.from_text(text="I want a refund on MC-1048277")],
    )
    ev = route_ticket(content)
    assert ev.route == "REFUND"


def test_lookup_order_uses_oms():
    from meridian_orderops.agent import RouteDecision

    # lookup_order expects Context in signature — call via a tiny shim if needed.
    # Prefer testing get_order + RouteDecision mapping in isolation:
    from meridian_ops.tools.oms import get_order

    out = get_order("MC-1048292")
    assert out["status"] == "success"
```

If `lookup_order(ctx, ...)` requires a real `Context`, test `get_order` + `route_ticket` only — **do not** invent a fake Context framework; use ADK’s test utilities when available.

### Expect

Router tests pass without Gemini.

---

## Task 6 — Hybrid rule card (edges vs LLM nodes)

### Why

SME judgment: what must stay deterministic.

### Do this

`project/meridian_ops/decisions/13-hybrid-rules.md`:

| Step | Workflow node type | Why |
|------|-------------------|-----|
| Ticket route | function + `Event.route` | Authz/path law |
| OMS get_order | function | Source of truth |
| Narrate status | `LlmAgent` | Language |
| HITL approve | `RequestInput` | Human gate |
| Refund finalize label | function | No model near money flag |

### Expect

HITL + route + OMS = non-LLM.

---

## How it works (deeper dive)

### Native edge patterns

```python
# sequential
edges = [("START", a), (a, b)]

# routed
edges = [(classifier, wismo, "WISMO"), (classifier, refund, "REFUND")]

# parallel + join
edges = [
  (split, (branch_a, branch_b)),
  ((branch_a, branch_b), join),
  (join, combine),
]
```

### Template agents?

`SequentialAgent` / `ParallelAgent` / `LoopAgent` still exist for older code. **New Meridian work uses `Workflow`.**

---

## Common pitfalls / troubleshooting

| Symptom | Fix |
|---------|-----|
| `No module named google.adk.workflow` | `pip install -U "google-adk>=2.0"` + Python 3.11+ |
| Duplicate node name errors | Separate `LlmAgent` instances per graph role |
| HITL never resumes | Use ADK UI/resume flow — don’t DIY files |
| Tempted to write MeridianGraph | Stop — extend `meridian_orderops/agent.py` edges |

---

## You are done when

- [ ] Workflow imports verified  
- [ ] `adk web` runs `meridian_orderops`  
- [ ] WISMO + refund HITL exercised  
- [ ] `InMemoryRunner` test exists  
- [ ] Hybrid rule card completed  
- [ ] Zero DIY graph engines in your changes  

---

## Knowledge check

1. What ADK type replaces a home-grown edge runner?  
2. How does a function node choose the WISMO branch?  
3. Why is `RequestInput` preferred over a custom checkpoint JSON for HITL?  
4. What belongs in Meridian code vs ADK?  
5. When are `SequentialAgent` templates still OK?

### Answers

1. `Workflow`  
2. Return `Event(..., route="WISMO")` matching an edge label  
3. ADK owns pause/resume/session integration  
4. Domain tools/policy — not orchestration runtimes  
5. Legacy codebases; not new OrderOps graphs  

---

## Recap

- OrderOps control plane is a native ADK `Workflow`.  
- Next: parallel/loop using `JoinNode` + routed cycles — still native.

---

## Stretch goal

Add a `POLICY` edge that inserts `retrieve_policy` as a **function node** before `policy_agent` (still no DIY bus).

---

## Feedback

- Could you add a new route `SCHEDULE` using only `Event.route` + edges?  
- What tripped you up: installs, HITL UI, or runner tests?  
- Note task number + expected vs actual.

---

## Navigate

**← Prev** [Lesson 12 — Deployment & ops](12-deployment-ops.md)  
**Next →** [Lesson 14 — Parallel, loop & custom agents](14-parallel-loop-custom-agents.md)
# Lesson 08 — Testing & evaluation (native ADK)

**Level:** Advanced  
**Time:** ~120–150 minutes  
**Prerequisites:** Lessons 02–07; a runnable ADK agent package  
**Lab outcome:** Tool unit tests + **ADK `AgentEvaluator`** golden gates — no DIY stub-planner “agent”

**Standard:** [docs/NATIVE-ADK.md](../docs/NATIVE-ADK.md)

---

## At a glance

| Layer | Native / allowed |
|-------|------------------|
| Tools | Plain pytest on Meridian functions (no LLM) |
| Agent trajectories | `AgentEvaluator` + `*.test.json` / evalsets |
| Programmatic runs | `App` + `InMemoryRunner` / `Runner` |
| Metrics thresholds | `test_config.json` criteria |

**Forbidden:** `wismo_stub_planner`, DIY `capture_from_tool_agent` loops that replace ADK.

---

## Why this matters

SMEs gate merges on **ADK trajectories**, not a second fake agent runtime that drifts from production.

---

## Know these

| Term | Meaning |
|------|---------|
| **AgentEvaluator** | ADK API to score agents against eval datasets |
| **Eval case / evalset** | Golden conversations: user → expected tools → reference response |
| **tool_trajectory_avg_score** | Did tools match expected path? |
| **response_match_score** | Reference overlap (e.g. ROUGE) — soft vs trajectory |
| **InMemoryRunner** | Native harness to run an `App` in tests |

---

## Task 1 — Unit-test domain tools (no LLM, no DIY agent)

### Why

Tools are deterministic Meridian code. Test them directly.

### Do this

```bash
export PYTHONPATH=project
pytest project/meridian_ops/tests/test_oms.py -v  # create if needed
```

Example `test_oms.py`:

```python
from meridian_ops.tools.oms import get_order

def test_get_order_happy_path():
    out = get_order("MC-1048292")
    assert out["status"] == "success"
    assert out["order"]["pod_photo_present"] is False

def test_get_order_not_found():
    assert get_order("MC-0000000")["error_code"] == "ORDER_NOT_FOUND"
```

### Expect

Tool tests green without Gemini.

---

## Task 2 — Golden evalset for Order Status (ADK schema)

### Why

Goldens are ADK’s contract format.

### Do this

1. Keep/extend `project/meridian_ops/evals/golden/wismo_basic.eval.json`  
2. Copy/migrate into your agent package as `*.test.json` using ADK helper if needed:

```bash
python - <<'PY'
from pathlib import Path
from google.adk.evaluation.agent_evaluator import AgentEvaluator
src = Path("project/meridian_ops/evals/golden/wismo_basic.eval.json")
dst = Path("project/meridian_order_status/wismo_basic.test.json")
dst.parent.mkdir(parents=True, exist_ok=True)
try:
    AgentEvaluator.migrate_eval_data_to_new_schema(str(src), str(dst))
except Exception:
    dst.write_text(src.read_text())
print(dst)
PY
```

3. Add `test_config.json` next to it:

```json
{
  "criteria": {
    "tool_trajectory_avg_score": 1.0,
    "response_match_score": 0.3
  }
}
```

### Expect

ADK-facing `*.test.json` exists for WISMO cases.

---

## Task 3 — Run native `AgentEvaluator`

### Why

This is the evaluation wheel ADK already built.

### Do this

Ensure `meridian_order_status` (Lesson 02/03) has `root_agent` + `get_order` tool.

```bash
cd /Users/alishaghatane/dev/agent-learn-sme/project
export PYTHONPATH=.
python - <<'PY'
import asyncio
from google.adk.evaluation.agent_evaluator import AgentEvaluator

async def main():
    await AgentEvaluator.evaluate(
        agent_module="meridian_order_status",
        eval_dataset_file_path_or_dir="meridian_order_status/wismo_basic.test.json",
        num_runs=1,
        print_detailed_results=True,
    )

asyncio.run(main())
PY
```

Adapt kwargs if your ADK version’s signature differs — inspect with `help(AgentEvaluator.evaluate)`.

### Expect

Trajectory scores print per `eval_id`. Fix agent/instruction on failures — **don’t** invent a stub planner to force green.

> **Tip:** Use `num_runs>1` for flaky live models; keep tool unit tests on every PR.

---

## Task 4 — `InMemoryRunner` smoke (native invoke)

### Why

CI/services use Runner, not DIY loops.

### Do this

```python
import pytest
from google.adk.apps import App
from google.adk.runners import InMemoryRunner
from google.genai import types
from meridian_order_status.agent import root_agent  # your package

@pytest.mark.asyncio
async def test_runner_smoke():
    app = App(name="meridian_order_status", root_agent=root_agent)
    runner = InMemoryRunner(app=app)
    session = await runner.session_service.create_session(
        app_name="meridian_order_status", user_id="u"
    )
    saw = False
    async for _ in runner.run_async(
        user_id="u",
        session_id=session.id,
        new_message=types.Content(
            role="user",
            parts=[types.Part.from_text(text="Status for MC-1048292")],
        ),
    ):
        saw = True
    assert saw
```

### Expect

Events stream from ADK.

---

## Task 5 — Rubrics + CI layering

### Why

Trajectory hard-fail; prose soft-fail.

### Do this

Write `project/meridian_ops/evals/rubrics/orderops_v1.md` (correctness, groundedness, safety, latency, cost) and CI policy:

| Job | What runs |
|-----|-----------|
| PR | Tool unit tests |
| Nightly / labeled | `AgentEvaluator` live + judges (Lesson 09) |

### Expect

PR never depends on a fake planner.

---

## Task 6 — Capture goldens from `adk web` (native)

### Why

ADK UI can export sessions into evalsets — better than hand-writing every trajectory forever.

### Do this

Run a good WISMO session in `adk web`, use ADK’s eval/export flow (per your version’s UI docs), and commit the resulting eval case.

### Expect

Golden grows from real ADK sessions.

---

## How it works (deeper dive)

```
pytest(tools) → fast, free
AgentEvaluator(agent_module, *.test.json) → trajectory + response criteria
InMemoryRunner → service/CI invoke path
```

Offline vs online monitoring still matters (Lesson 24) — both score **ADK trajectories**, not a shadow runtime.

---

## Common pitfalls / troubleshooting

| Symptom | Fix |
|---------|-----|
| Want a stub planner for CI | Keep tool tests; mock LLM only via ADK-supported means; don’t DIY agent |
| Schema errors on JSON | `migrate_eval_data_to_new_schema` |
| Flakes | `num_runs` + pin model id; hard traj threshold |

---

## You are done when

- [ ] Tool unit tests pass  
- [ ] `AgentEvaluator` run completed against WISMO goldens  
- [ ] `InMemoryRunner` smoke exists  
- [ ] CI layering documented  
- [ ] No stub-planner module in your tree  

---

## Knowledge check

1. What ADK class scores trajectories against goldens?  
2. What should PR CI run without API spend?  
3. Why is a DIY stub planner harmful?  
4. What runner type belongs in tests/services?

### Answers

1. `AgentEvaluator`  
2. Domain tool unit tests  
3. It drifts from the real `LlmAgent`/`Workflow` path  
4. `InMemoryRunner` / `Runner` with `App`  

---

## Recap

- Evaluation is native ADK.  
- Next: judges score ADK results; thinking extraction from ADK events.

---

## Stretch goal

Add inventory golden + `AgentEvaluator` job for `meridian_inventory`.

---

## Feedback

- Could you add a golden without writing a fake agent?  
- Note task number + expected vs actual.

---

## Navigate

**← Prev** [Lesson 07 — Reliability, safety, control](07-reliability-safety-control.md)  
**Next →** [Lesson 09 — Judges & thinking extraction](09-judges-thinking-extraction.md)
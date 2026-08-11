# Lesson 09 — Judges & thinking extraction (native ADK trajectories)

**Level:** Advanced  
**Time:** ~120 minutes  
**Prerequisites:** Lesson 08 (`AgentEvaluator` / Runner events)  
**Lab outcome:** Domain judges + thinking views built from **ADK events/eval results** — not a DIY `CapturedRun` agent

**Standard:** [docs/NATIVE-ADK.md](../docs/NATIVE-ADK.md)

---

## At a glance

| Do | Don’t |
|----|-------|
| Score outputs/trajectories from `AgentEvaluator` or `runner.run_async` events | Invent `wismo_stub_planner` |
| Keep **code judges** for banned phrases / POD lies | Replace ADK eval with a third framework |
| Reconstruct “thinking” from tool call events | Claim hidden chain-of-thought APIs |

---

## Why this matters

Judges must grade the **same** agent path production runs (ADK). A parallel fake loop creates false confidence.

---

## Know these

| Term | Meaning |
|------|---------|
| **Code judge** | Deterministic scorer on final text + tool evidence |
| **LLM-as-judge** | Model grades with rubric JSON |
| **Thinking extraction** | Structured intent→tools→evidence→decision from **observable ADK events** |
| **Hard fail** | Safety/groundedness 0 fails the case even if tone is great |

---

## Task 1 — Collect a native trajectory once

### Why

Judges need real ADK data.

### Do this

Using `InMemoryRunner` (Lesson 08), run WISMO for `MC-1048292` and serialize events you care about:

- tool call names/args (from event tool functions)  
- final text parts  

Save under `project/meridian_ops/evals/reports/sample_wismo_events.json` (redact secrets).

Exact event field names vary by ADK version — inspect with `print(event)` / docs. **Do not** invent a side capture runtime.

### Expect

A JSON artifact produced by ADK Runner events.

---

## Task 2 — Code judges on final text + OMS evidence

### Why

Cheap, stable CI signals.

### Do this

Implement `project/meridian_ops/judges/code_judges.py` with:

- `judge_safety_wismo(final_text, tool_names)`  
- `judge_groundedness_pod(final_text, pod_photo_present)`  

Unit-test POD-lie and banned “refund completed”.

Feed them using evidence from OMS + the final response string from Task 1 / Evaluator.

### Expect

POD lie → groundedness fail; tool unit tests don’t need Gemini.

---

## Task 3 — Thinking extraction from tool events

### Why

On-call needs intent→tools→evidence→decision without a DIY agent.

### Do this

`extract_thinking_from_tools(user_text, tool_calls: list[dict], final_text) -> dict`  
producing markdown via `thinking_to_markdown`.

Tool calls list is parsed from ADK events or Evaluator intermediates — adapter code is OK; a second orchestrator is not.

### Expect

Markdown lists `get_order` rationale + residual risks if tools missing.

---

## Task 4 — Aggregate hard fails + optional LLM judge

### Why

Panel = code hard fails + semantic judge.

### Do this

`aggregate_scores` with hard_fail on safety/groundedness.  
Optional Gemini judge with `MERIDIAN_JUDGE_MODE=fixture` for CI (fixture JSON), live when keyed.

### Expect

Fixture mode fails POD lie offline.

---

## Task 5 — Wire judges after AgentEvaluator

### Why

Close the loop with native eval.

### Do this

Script: run `AgentEvaluator` (or Runner) → for each case run code judges → write `panel_wismo.json`. Fail CI if hard_fail.

### Expect

One pipeline: ADK eval → Meridian judges.

---

## How it works

```
ADK Runner / AgentEvaluator
        │
        ├─ trajectory criteria (ADK)
        └─ domain judges (Meridian) on texts/tools/evidence
```

---

## Common pitfalls

| Symptom | Fix |
|---------|-----|
| Reintroduced CapturedRun planner | Delete; parse ADK events |
| Judge without tool evidence | Pass OMS/`get_order` result into groundedness |

---

## You are done when

- [ ] Sample ADK events saved  
- [ ] Code judges tested  
- [ ] Thinking markdown from tool events  
- [ ] Panel script uses ADK outputs  
- [ ] No stub planner  

---

## Knowledge check

1. What is the source of truth for tool calls?  
2. What may you still custom-build?  
3. What must you not custom-build?

### Answers

1. ADK events / Evaluator intermediates  
2. Domain rubrics/judges  
3. Alternate agent loops  

---

## Recap

Judges grade native ADK trajectories. Next: log those runs in MLflow.

---

## Feedback

Note task number + expected vs actual.

---

## Navigate

**← Prev** [Lesson 08](08-testing-evaluation.md) · **Next →** [Lesson 10](10-mlflow-agentic.md)
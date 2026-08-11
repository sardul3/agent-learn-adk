# Lesson 10 — MLflow for agentic systems (native ADK runs)

**Level:** Advanced  
**Time:** ~120 minutes  
**Prerequisites:** Lessons 08–09  
**Lab outcome:** MLflow tracks **ADK `AgentEvaluator` / Runner** results — not stub-planner metrics

**Standard:** [docs/NATIVE-ADK.md](../docs/NATIVE-ADK.md)

---

## At a glance

MLflow = experiment ledger. ADK = agent runtime.  
Log params/metrics/artifacts from real ADK evaluations.

---

## Why this matters

SHIP/NO-SHIP must cite the same agent module production runs.

---

## Know these

Experiment · Run · Param · Metric · Artifact · Tag · `instruction_sha` · prompt registry

---

## Task 1 — Start MLflow server

```bash
pip install -U "mlflow>=2.14"
mkdir -p .mlflow
mlflow server --host 127.0.0.1 --port 5000 \
  --backend-store-uri sqlite:///$(pwd)/.mlflow/mlflow.db \
  --default-artifact-root $(pwd)/.mlflow/artifacts
export MLFLOW_TRACKING_URI=http://127.0.0.1:5000
```

Ignore `.mlflow/` in git.

---

## Task 2 — Helper to start eval runs

`project/meridian_ops/observability/mlflow_utils.py` with `ensure_experiment`, `start_eval_run`, `file_sha256`, `git_sha` (from earlier Pack B design — keep it).

Smoke-log one metric.

---

## Task 3 — Log an AgentEvaluator run

### Why

Native eval → MLflow lineage.

### Do this

Script `mlflow_log_adk_eval.py` that:

1. `start_eval_run(..., agent_name="meridian_order_status", model=..., eval_set=...)`  
2. Invokes `AgentEvaluator.evaluate(...)`  
3. Logs metrics you parse from results / your judge panel  
4. Logs artifacts: golden file, panel JSON, instruction/policy file  

**Do not** call `wismo_stub_planner`.

### Expect

UI shows `instruction_sha`, `traj_pass_rate` (or ADK criterion scores), artifacts.

---

## Task 4 — A/B two instruction files via ADK

Swap `policy.md` / instruction between A (must call get_order) and B (loose).  
Run Evaluator twice; compare in MLflow.  
Reject B if trajectory criterion drops.

### Expect

Compare screen shows A > B on trajectory — measured on real agent.

---

## Task 5 — Prompt registry + eval card

Version instructions under `prompt_registry/`; log `prompt_version`.  
Write `EVAL_CARD.md` SHIP/NO-SHIP from latest run.

---

## Task 6 — Optional mlflow.genai.evaluate

If present in your MLflow version, score traces; else note adaptation. Custom panel metrics remain valid **alongside** ADK eval — not instead of ADK runtime.

---

## You are done when

- [ ] MLflow server up  
- [ ] ADK eval logged (not stub planner)  
- [ ] A/B compare done  
- [ ] Eval card written  

---

## Knowledge check

1. What system executes the agent under test?  
2. What system stores the comparison ledger?  
3. Why hash instructions?

### Answers

1. ADK (`AgentEvaluator` / Runner)  
2. MLflow  
3. Prove which prompt text produced the metrics  

---

## Navigate

**← Prev** [Lesson 09](09-judges-thinking-extraction.md) · **Next →** [Lesson 11](11-tracing-observability.md)
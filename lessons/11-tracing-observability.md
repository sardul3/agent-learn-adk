# Lesson 11 — Tracing & observability (native ADK events)

**Level:** Advanced  
**Time:** ~120 minutes  
**Prerequisites:** Lessons 08–10  
**Lab outcome:** Debug Meridian using **ADK event streams** (+ MLflow/OTel as available) — no DIY `Tracer` span engine

**Standard:** [docs/NATIVE-ADK.md](../docs/NATIVE-ADK.md)

---

## At a glance

| Use | Avoid |
|-----|-------|
| `runner.run_async` event stream | Home-grown span tree classes |
| ADK web inspect | Parallel “traced_wismo” stub planner |
| MLflow tracing APIs if installed | Replacing ADK events with custom schemas only |
| Correlation ids in **tool logs** | Second orchestration trace bus |

---

## Why this matters

Incidents must reconstruct the **production ADK path**. A custom span recorder that doesn’t wrap Runner lies.

---

## Know these

Trace/span (OTel) · ADK **Event** · correlation id · SLI/SLO · sampling · redaction

---

## Task 1 — Dump ADK events for a WISMO turn

### Do this

`InMemoryRunner` + `meridian_order_status` or `meridian_orderops`:

```python
async for event in runner.run_async(...):
    # persist a redacted dict of relevant fields
    ...
```

Save `trace_dumps/<session_id>.json`. Inspect tool calls vs final text.

### Expect

You can point to the event where OMS evidence appeared vs final answer.

---

## Task 2 — Correlation IDs inside domain tools

### Why

Still useful across OMS/MCP — not an ADK replacement.

### Do this

Keep `logging_utils.new_correlation_id` / structured stderr logs on `get_order`. Set id at FastAPI/webhook edge and pass via tool context if ADK `ToolContext` state allows; otherwise log alongside session id from Runner.

### Expect

Logs joinable by `correlation_id` + `session_id`.

---

## Task 3 — MLflow / OTel integration (best-effort native)

### Do this

```bash
python - <<'PY'
import mlflow
print(mlflow.__version__, hasattr(mlflow, "trace"))
PY
```

- If `@mlflow.trace` / ADK plugin docs exist, wrap the **Runner invoke** function  
- Else log event-dump JSON as an MLflow artifact on the eval run (Lesson 10)

### Expect

No custom `class Tracer` required for the lesson pass bar.

---

## Task 4 — Incident drill: POD lie (instruction/agent bug)

### Do this

1. Temporarily break narrator instruction to claim POD when false **or** use a bad agent revision  
2. Run via Runner  
3. Diff tool/OMS evidence events vs final text  
4. Run groundedness judge  
5. Fix agent  
6. Add/adjust ADK golden + Evaluator gate  

Write `decisions/11-incident-pod-lie.md`.

### Expect

Fix verified with `AgentEvaluator`, not a stub finalize function.

---

## Task 5 — SLOs

Document SLIs: success rate, p95 latency, tool error rate, groundedness pass, $/task.  
Export optional Prometheus counters from the **FastAPI edge** that calls Runner.

---

## You are done when

- [ ] ADK event dump saved for WISMO  
- [ ] Correlation logging works on tools  
- [ ] Incident doc uses Runner/Evaluator evidence  
- [ ] No DIY Tracer framework in repo  

---

## Knowledge check

1. What stream do you debug first?  
2. What’s allowed as complementary observability?  
3. What is forbidden?

### Answers

1. ADK Runner/web events  
2. MLflow, OTel exporters, tool logs  
3. A second agent runtime with its own spans  

---

## Navigate

**← Prev** [Lesson 10](10-mlflow-agentic.md) · **Next →** [Lesson 12](12-deployment-ops.md)
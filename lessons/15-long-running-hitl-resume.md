# Lesson 15 — Long-running HITL resume (native ADK)

**Level:** Advanced  
**Time:** ~120 minutes  
**Prerequisites:** Lessons 13–14; ADK 2 `RequestInput`  
**Lab outcome:** Pause Meridian refunds with native **`RequestInput`**, resume via ADK session/app resumability — **no DIY checkpoint database**

**Standard:** [docs/NATIVE-ADK.md](../docs/NATIVE-ADK.md)

---

## At a glance

ADK HITL for workflows:

- `yield RequestInput(message=..., payload=..., response_schema=...)`
- App-level resumability (`ResumabilityConfig` when required by your version)
- Session service persistence for multi-hour pauses
- Tool-confirmation patterns for LLM-tool approvals (separate from graph HITL)

You will **not** invent `FileCheckpointStore`.

---

## Why this matters

Priya approves tomorrow. ADK must own pause/resume so Cloud Run scale-to-zero doesn’t invent a second framework.

---

## Know these

| Term | Native meaning |
|------|----------------|
| **RequestInput** | Graph node pause for human input |
| **Resume** | Continue interrupted workflow with human reply |
| **rerun_on_resume** | Node re-executes vs pass reply downstream |
| **ResumabilityConfig** | App-level switch/config for resumable runs |
| **Session service** | Stores session/events for restore |
| **Tool confirmation** | LLM-tool yes/no gate (different API) |

Docs: [Human input for workflows](https://google.github.io/adk-docs/graphs/human-input/)

---

## Task 1 — Confirm OrderOps already pauses with RequestInput

### Why

Lesson 13 wired native HITL — now treat it as the product path.

### Do this

In `meridian_orderops/agent.py`, locate `hitl_refund_gate`.

Run `adk web`, send a refund prompt for `MC-1048277`, and **stop when ADK asks for approval**.

Screenshot or note the interrupt UX in `project/meridian_ops/decisions/15-hitl.md`.

### Expect

Workflow paused without your own JSON checkpoint file.

---

## Task 2 — Resume with APPROVE and DENY

### Why

Both paths must be first-class.

### Do this

1. Resume with `APPROVE melted dairy verified`  
2. New session: refund again → `DENY insufficient evidence`  

Record final `request_status` / synthesizer behavior for each.

### Expect

- APPROVE → finalize marks confirmed lab status  
- DENY → denied path, no “refund completed” customer claim  

---

## Task 3 — App + ResumabilityConfig (version-adaptive)

### Why

Long pauses need app resumability enabled the ADK way.

### Do this

```bash
python - <<'PY'
import inspect
from google.adk import apps
print([x for x in dir(apps) if "esum" in x.lower() or "App" in x])
try:
    from google.adk.apps import ResumabilityConfig, App
    print("ResumabilityConfig", inspect.signature(ResumabilityConfig))
except Exception as e:
    print("adapt", type(e).__name__, e)
PY
```

Create `project/meridian_orderops/app_resumable.py` (or configure in docs) using **your** install’s `App(..., resumability_config=...)` signature.

If the symbol differs, copy the pattern from installed ADK docs — still no DIY store.

### Expect

Decisions doc lists the exact `App` constructor kwargs you used.

---

## Task 4 — Durable sessions (ADK session service, not homebrew)

### Why

Resume after process restart = session backend, not `checkpoints/*.json`.

### Do this

1. Prefer ADK’s documented session service for persistence (Redis/Database options per your ADK version).  
2. For local lab: prove resume works across **`adk web` restart** using the same `session_id` if the UI supports it; otherwise use `InMemoryRunner` only for same-process resume and document the production session service you’ll configure in Lesson 29.  
3. Write the chosen service name in `15-hitl.md`.

### Expect

You name an **ADK session service**, not `FileCheckpointStore`.

> **Tip:** Domain audit rows (Lesson 07) may still log business facts — that’s analytics, not a second orchestrator.

---

## Task 5 — Tool-confirmation vs graph RequestInput

### Why

Two native HITL tools — don’t mix them up.

### Do this

Add a short table to `15-hitl.md`:

| Mechanism | Use when |
|-----------|----------|
| Graph `RequestInput` | Supervisor gate in Workflow (refund approve) |
| Tool confirmation | LLM about to call a side-effect tool |

Optional: add `require_confirmation`-style config on a write tool **only if** your ADK version documents it — follow docs verbatim.

### Expect

Refund supervisor gate stays on `RequestInput` in the graph.

---

## Task 6 — Stale HITL policy as a function node

### Why

Expiry is business policy; implement it as a **Workflow function node**, not a parallel scheduler.

### Do this

Before `refund_finalize`, add a node that reads `ctx.state` timestamps (set when HITL was issued via `Event(state={...})`) and routes `EXPIRED` if older than 72h.

Use ADK state + routes. Unit-test the pure date math helper; wire the node in the graph.

### Expect

Expired approvals cannot confirm.

---

## How it works (deeper dive)

### What you must not build

| DIY idea | Native replacement |
|----------|-------------------|
| `FileCheckpointStore` | Session service + RequestInput resume |
| `resume_with_hitl()` bespoke API | ADK resume inputs / web UI / Runner resume APIs |
| Parallel “approval worker” framework | Event-driven Lesson 17 **calling** ADK Runner |

### Idempotency

Keep Lesson 07 **payments idempotency keys** — that’s domain money safety, complementary to ADK resume.

---

## Common pitfalls / troubleshooting

| Symptom | Fix |
|---------|-----|
| HITL reply ignored | Check `rerun_on_resume` / resume API for your version |
| Lost pause after restart | Configure durable ADK session service |
| Reintroduced checkpoint JSON | Delete it; use ADK resume |

---

## You are done when

- [ ] APPROVE and DENY proven on native HITL  
- [ ] App resumability config documented for your ADK version  
- [ ] Session durability approach named (ADK service)  
- [ ] RequestInput vs tool-confirmation table written  
- [ ] No `FileCheckpointStore` in your code  

---

## Knowledge check

1. Which ADK type pauses a Workflow for a human?  
2. Where should multi-hour pause state live?  
3. Why keep payment idempotency keys even with ADK resume?  
4. What’s wrong with a custom checkpoint folder?

### Answers

1. `RequestInput`  
2. ADK session/resumability services  
3. Money retries ≠ workflow resume semantics  
4. Second orchestrator that drifts from ADK events  

---

## Recap

- Long-running Meridian refunds pause/resume with native ADK HITL.  
- Next: tools over **MCP** via `McpToolset`.

---

## Stretch goal

Structured `response_schema` on `RequestInput` for `{decision: APPROVE|DENY, note: str}` per ADK human-input docs.

---

## Feedback

- Could you explain ADK resume to Priya without mentioning custom files?  
- Note task number + expected vs actual.

---

## Navigate

**← Prev** [Lesson 14 — Parallel, loop & custom agents](14-parallel-loop-custom-agents.md)  
**Next →** [Lesson 16 — MCP & tool ecosystems](16-mcp-tool-ecosystems.md)
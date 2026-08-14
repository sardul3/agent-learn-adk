# Lesson 32 — Chaos, disaster recovery & feature flags

**Level:** Advanced  
**Time:** ~120–150 minutes  
**Prerequisites:** Lessons 12 & 41 (deploy + release train); Lesson 07 (kill switches)  
**Lab outcome:** Break Meridian deps on purpose, prove recovery, and gate risky agent graphs behind **feature flags** — without inventing a new orchestrator

**Standard:** [docs/NATIVE-ADK.md](../docs/NATIVE-ADK.md)

---

## At a glance

| Practice | Goal |
|----------|------|
| **Chaos** | Prove dashboards/pages/runbooks work when OMS/MCP dies |
| **DR** | Know RPO/RTO for sessions, manifests, eval artifacts |
| **Feature flags** | Turn off refund HITL graph or new prompt without redeploying code mid-SEV |

```
flag orderops.refund_graph = off
        │
        ▼
Workflow route → unsupported / safe degraded message
        │
        ▼
OMS tool raises Timeout → edge returns 503 + correlation_id
```

---

## Why this matters

First real OMS outage at 2am. If you never practiced:

- Nobody knows if `/readyz` should fail  
- Refund graph keeps calling dead Payments  
- Rollback vs “flip flag” debate wastes the error budget  

Game days make on-call boring — in a good way.

---

## Know these

| Term | Meaning |
|------|---------|
| **Chaos experiment** | Controlled failure injection with a hypothesis |
| **Blast radius** | How much user pain the experiment can cause |
| **RTO** | Recovery Time Objective — how fast back |
| **RPO** | Recovery Point Objective — how much data loss OK |
| **Degraded mode** | Safe partial service when a dependency is down |
| **Feature flag** | Runtime switch for behavior without new image |
| **Kill switch** | Hard off for dangerous capability (often a flag) |
| **Game day** | Scheduled practice incident |

---

## Task 1 — Dependency failure matrix

### Why

You cannot chaos what you have not listed.

### Do this

`project/meridian_ops/deploy/CHAOS_MATRIX.md`:

| Dependency | Failure mode | User-visible effect | Edge behavior | Agent/graph behavior | Page? |
|------------|--------------|---------------------|---------------|----------------------|-------|
| Gemini API | 429/5xx | Slow/empty answers | 503 after timeout | ADK retries? budget | yes |
| OMS tool | timeout | Cannot status | 503 / problem+json | function node error route | yes |
| MCP server | down | tools missing | 503 | McpToolset errors | yes |
| Session store | down | multi-turn breaks | fail ready | n/a | yes |
| Policy MCP/A2A | down | FAQ degraded | 200 + “policy unavailable” | skip POLICY remote | warn |

### Expect

Every row has an explicit degraded story — not “hope.”

---

## Task 2 — Inject OMS failure (lab)

### Why

Hypothesis: smoke + metrics detect OMS death within one probe interval.

### Do this

1. Add a **lab-only** env flag in the OMS tool or a thin wrapper used by the Workflow lookup node:

```python
import os
import time

def get_order(order_id: str) -> dict:
    if os.getenv("MERIDIAN_CHAOS_OMS") == "timeout":
        time.sleep(5)
        return {"status": "error", "error_code": "OMS_TIMEOUT", "message": "chaos"}
    # ... existing fixture logic
```

2. Hypothesis in decisions: “With chaos on, `/v1/wismo` returns error or safe message; `/metrics` errors increment; smoke fails.”  
3. `docker compose up` with `MERIDIAN_CHAOS_OMS=timeout`  
4. Run smoke — expect failure  
5. Turn chaos off — smoke passes  
6. Record detection time  

> **Watch out:** Never enable chaos flags in prod without a game-day ticket and tiny blast radius.

### Expect

Failed smoke is the signal; restore is flipping the env back (or flag).

---

## Task 3 — Feature flag module (config, not a new framework)

### Why

Flags gate graphs/prompts. Keep them boring: env/JSON/config map read at process start or per-request.

### Do this

`project/meridian_ops/deploy/flags.py`:

```python
from __future__ import annotations

import json
import os
from pathlib import Path

_DEFAULTS = {
    "orderops.refund_graph": True,
    "orderops.mcp_tools": True,
    "orderops.policy_a2a": False,
}


def load_flags() -> dict[str, bool]:
    path = os.getenv("MERIDIAN_FLAGS_FILE")
    flags = dict(_DEFAULTS)
    if path and Path(path).exists():
        flags.update({k: bool(v) for k, v in json.loads(Path(path).read_text()).items()})
    # Env overrides: MERIDIAN_FLAG_ORDEROPS_REFUND_GRAPH=0
    for key in list(flags):
        env_key = "MERIDIAN_FLAG_" + key.upper().replace(".", "_")
        if env_key in os.environ:
            flags[key] = os.environ[env_key] not in {"0", "false", "False"}
    return flags


def enabled(name: str) -> bool:
    return bool(load_flags().get(name, False))
```

Unit test defaults + env override.

Wire into FastAPI or Workflow router: if `orderops.refund_graph` is false, refund texts get a safe “refunds temporarily unavailable — escalate to CX” **without** calling HITL/payments.

### Expect

Flag off → no HITL refund path; WISMO still works.

---

## Task 4 — DR objectives for Meridian agent platform

### Why

Agents have state: sessions, checkpoints (ADK), manifests, goldens.

### Do this

Fill `project/meridian_ops/deploy/DR.md`:

| Asset | Where | RPO | RTO | Restore test |
|-------|-------|-----|-----|--------------|
| Container images | Artifact Registry | n/a (immutable) | 15m | redeploy previous digest |
| Secrets | Secret Manager | n/a | 15m | rotate runbook |
| Session store | Redis/Memorystore (Lesson 29) | ≤5m | 30m | restore backup / fail over |
| Eval goldens | git | 0 (git) | 15m | checkout |
| MLflow metadata | tracking DB | ≤15m | 1h | restore backup |
| Release manifests | git / CI artifacts | 0 | 15m | checkout |

Run a **tabletop**: “Artifact Registry region down — how do we serve last good image from mirror?” Write 5 bullets.

### Expect

RTO/RPO numbers the business can argue with — not “ASAP.”

---

## Task 5 — Game day script

### Why

Chaos without a script is just an outage.

### Do this

`project/meridian_ops/deploy/runbooks/GAMEDAY.md`:

1. Announce game day in #orderops-oncall  
2. Hypothesis + blast radius (stage only)  
3. Inject failure (Task 2)  
4. Page / detect  
5. Mitigate (flag or rollback)  
6. Recover  
7. Note gaps in runbooks  
8. Add one automated check if a gap was human-only  

Execute once on **compose/stage**, not prod.

### Expect

Post-game notes in `decisions/32-gameday.md` with at least one runbook improvement.

---

## Task 6 — Link flags to Lesson 41 canary

### Why

Canary + flags beat canary alone for prompt risk.

### Do this

Update `CANARY.md` (Lesson 41) with:

- New prompt ships behind `orderops.prompt_vNext=false`  
- Canary revision has flag true for 10% cohort (header/`X-Flag-Cohort` or separate revision env)  
- Abort → flag false **or** traffic rollback  

### Expect

Two levers documented: traffic % and feature flag.

---

## How it works (deeper dive)

### Flags vs redeploy

| Change | Prefer |
|--------|--------|
| Disable refunds for 2 hours | Flag / kill switch |
| New OMS client version | Image deploy + canary |
| Bad prompt | Rollback revision **and** flag off vNext |

### What not to build

A custom chaos “platform.” Use env flags, dependency stubs, and your cloud’s fault injection if available — still call ADK Runner for behavior.

---

## Common pitfalls / troubleshooting

| Symptom | Fix |
|---------|-----|
| Chaos left on in shared stage | Checklist; default flags safe |
| Flag in prompt text only | Enforce in code/edge/router node |
| DR never tested | Calendar quarterly game day |

---

## You are done when

- [ ] CHAOS_MATRIX complete  
- [ ] OMS timeout chaos detected via smoke/metrics  
- [ ] Feature flags module tested + refund kill switch works  
- [ ] DR table with RPO/RTO  
- [ ] Game day executed on lab/stage  
- [ ] Canary doc references flags  

---

## Knowledge check

1. Difference between RTO and RPO?  
2. When is a feature flag better than a redeploy?  
3. What is blast radius?  
4. Why run game days on stage first?

### Answers

1. Time to restore vs amount of data/history you can lose.  
2. Temporary behavior/kill switches without shipping a new digest.  
3. How much of the estate/users an experiment can hurt.  
4. Limit customer harm while proving detection/recovery.

---

## Recap

- Meridian can fail on purpose and recover on purpose.  
- Deployment ops set is now: **12 ship → 41 release train → 32 resilience**.

---

## Stretch goal

Add a `/readyz` check that fails when `MERIDIAN_CHAOS_OMS=timeout` so orchestrators stop traffic automatically.

---

## Feedback

- Could you disable refunds with a flag during a simulated Payments outage?  
- Note task number + expected vs actual.

---

## Navigate

**←** [Lesson 31 — FinOps](31-finops.md) · [Lesson 41 — CI/CD & SRE](41-cicd-sre-deployment-ops.md)  
**Also:** [Lesson 12 — Deploy](12-deployment-ops.md)  
**Next →** [Lesson 43 — SLOs & capacity](43-slos-capacity-backpressure.md)  
**Track home:** [README](../README.md)
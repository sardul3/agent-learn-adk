# Meridian ADK Curriculum Roadmap (SME Track)

**~40 lessons** in packs of 5.  
Gap rationale: [gap-analysis-sme.md](gap-analysis-sme.md)

```
Frame → Design → Build → Secure → Evaluate → Judge → Track
  → Trace → Deploy → CI/Canary/Rollback → Chaos/DR/Flags
    → Orchestrate deeply → Knowledge/Models
    → Quality at scale → Platform → Productize → Capstone
```

---

## Pack A — Foundations → Control ✅

| # | Lesson | Status |
|---|--------|--------|
| 01 | Agentic foundations | ✅ |
| 02 | ADK environment & developer loop | ✅ |
| 03 | Core building blocks | ✅ |
| 04 | Tools deep mastery | ✅ |
| 05 | Multi-agent orchestration (intro) | ✅ |
| 06 | Context, memory, knowledge (intro) | ✅ |
| 07 | Reliability, safety, control | ✅ |

## Pack B — Eval → Observability → Deploy ✅

| # | Lesson | Status |
|---|--------|--------|
| 08 | Testing & evaluation foundations | ✅ |
| 09 | Judges, scorers & thinking extraction | ✅ |
| 10 | MLflow for agentic systems | ✅ |
| 11 | Tracing & production observability | ✅ |
| 12 | Deployment & ops (Docker, smoke, secrets, first-line runbooks) | ✅ |

**Ops add-on (recommended after 12):**

| # | Lesson | Status |
|---|--------|--------|
| 41 | CI/CD, canary, rollback drills & on-call | ✅ |
| 32 | Chaos, DR & feature flags *(also Pack F; can do early after 41)* | ✅ |

Suggested ops path: `12 → 41 → 32` (ship → release train → resilience).

## Pack C — Orchestration depth & ecosystems *(writing now)*

| # | Lesson | You leave able to… |
|---|--------|--------------------|
| 13 | ADK graph workflows | Deterministic edges + intelligent nodes for OrderOps |
| 14 | Parallel, loop & custom agents | Fan-out/fan-in, critic loops, BaseAgent control |
| 15 | Long-running tasks & HITL resume | Checkpoints, pause/resume across hours |
| 16 | MCP & external tool ecosystems | Connect Meridian tools via MCP servers |
| 17 | Event-driven agents & A2A | Webhooks, queues, agent-to-agent handoffs |

## Pack D — Knowledge, models, multimodal

| # | Lesson | Theme |
|---|--------|--------|
| 18 | Advanced RAG for retail policy | Chunking, embeddings, hybrid retrieve, citations |
| 19 | Memory systems deep dive | Write policies, consolidation, PII boundaries |
| 20 | Model routing, fallbacks & structured output | Flash/Pro, JSON schema, graceful degrade |
| 21 | Multimodal OrderOps | POD photos, receipts, vision+tools |
| 22 | Streaming UX & progressive responses | Token streams, partial tool status |

## Pack E — Quality at scale & hard security

| # | Lesson | Theme |
|---|--------|--------|
| 23 | Red teaming & adversarial robustness | Injection suites, tool abuse, jailbreaks |
| 24 | Online monitoring & continuous eval | Sample prod → score → promote goldens |
| 25 | Human feedback, preferences & canary prompts | Label UIs, canary %, auto-rollback |
| 26 | Plugins, callbacks & policy middleware | Cross-cutting enforcement patterns |
| 27 | Privacy, retention & compliance | Redaction, TTL, audit, data subject requests |

## Pack F — Platform engineering

| # | Lesson | Theme |
|---|--------|--------|
| 28 | Architecture patterns catalog | Invent router/planner/critic/HITL/hybrid on demand |
| 29 | Sessions & state at scale | Redis/Memorystore, stickiness, replay |
| 30 | Multi-tenant agent platforms | Isolation, quotas, per-tenant tools |
| 31 | FinOps for agents | Cost per task/tenant, budgets, chargeback |
| 32 | Chaos, DR & feature flags | ✅ Break tools on purpose; recover; flag graphs |

## Pack G — Productize & prove SME

| # | Lesson | Theme |
|---|--------|--------|
| 33 | SME judgment, teams & teaching | Build vs buy, ownership, mentoring drills |
| 34 | Enterprise integrations | ITSM, Slack, Pub/Sub, case systems |
| 35 | Dynamic Agent Creation Platform I | Spec schema → generate ADK package |
| 36 | Dynamic Agent Creation Platform II | UI/API, validate, eval gate, deploy |
| 37 | Governance, versioning & agent marketplace | Org lifecycle, deprecation, approvals |
| 38 | Capstone I — Design from messy problem | Architecture + threat + eval plan |
| 39 | Capstone II — Ship, measure, incident | Deploy + break + fix from traces |
| 40 | Capstone III — Mentor & SME defense | Teach a peer; oral defense board |

---

## Suggested mastery order (never skip packs)

`A → B → C → D → E → F → G`  
Always keep a **real Meridian slice** in flight — not toy chat.

## Capstone bar (SME)

You can do **all** of these unaided:

- [ ] Design multi-agent ADK system from a messy business problem  
- [ ] Implement tools + graph workflow with HITL and guardrails  
- [ ] Ship evals/judges that catch regressions before users  
- [ ] Deploy with tracing, auth, cost controls, rollback  
- [ ] Debug a bad production trajectory to a fix + golden  
- [ ] Integrate MCP/events without privilege collapse  
- [ ] Generate specialty agents from structured product input  
- [ ] Mentor someone else through the same path  

## Pack shipping cadence

Write/teach **5 lessons at a time**. After Pack C: Pack D (18–22), etc.
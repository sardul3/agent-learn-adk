# Meridian ADK Curriculum Roadmap (SME Track)

**~50 lessons** in packs of 5.  
Gap rationale: [gap-analysis-sme.md](gap-analysis-sme.md)

```
Frame → Design → Build → Secure → Evaluate → Judge → Track
  → Trace → Deploy → CI/Canary/Rollback → Chaos/DR/Flags
    → Orchestrate deeply → Knowledge/Models
    → Quality at scale → Platform → SLOs/Gateway
      → Frontier surfaces (voice, identity, mandates, computer use,
        code exec, simulation, context) → Productize → Capstone
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

## Pack C — Orchestration depth & ecosystems ✅

| # | Lesson | You leave able to… |
|---|--------|--------------------|
| 13 | ADK graph workflows | Deterministic edges + intelligent nodes for OrderOps |
| 14 | Parallel, loop & custom agents | Fan-out/fan-in, critic loops, BaseAgent control |
| 15 | Long-running tasks & HITL resume | Checkpoints, pause/resume across hours |
| 16 | MCP & external tool ecosystems | Connect Meridian tools via MCP servers |
| 17 | Event-driven agents & A2A | Webhooks, queues, agent-to-agent handoffs |

## Pack D — Knowledge, models, multimodal ✅

| # | Lesson | Theme | Status |
|---|--------|--------|--------|
| 18 | Advanced RAG for retail policy | Chunking, embeddings, hybrid retrieve, citations | ✅ |
| 19 | Memory systems deep dive | Write policies, consolidation, PII boundaries | ✅ |
| 20 | Model routing, fallbacks & structured output | Flash/Pro, JSON schema, graceful degrade | ✅ |
| 21 | Multimodal OrderOps | POD photos, receipts, vision+tools | ✅ |
| 22 | Streaming UX & progressive responses | Token streams, partial tool status | ✅ |

## Pack E — Quality at scale & hard security ✅

| # | Lesson | Theme | Status |
|---|--------|--------|--------|
| 23 | Red teaming & adversarial robustness | Injection suites, tool abuse, jailbreaks | ✅ |
| 24 | Online monitoring & continuous eval | Sample prod → score → promote goldens | ✅ |
| 25 | Human feedback, preferences & canary prompts | Label UIs, canary %, auto-rollback | ✅ |
| 26 | Plugins, callbacks & policy middleware | Cross-cutting enforcement patterns | ✅ |
| 27 | Privacy, retention & compliance | Redaction, TTL, audit, data subject requests | ✅ |

**RAI bonus (after Pack E):**

| # | Lesson | Status |
|---|--------|--------|
| 42 | Responsible AI champion — scorecard, fixes, evidence pack | ✅ |

Suggested quality path: `23 → 24 → 25 → 26 → 27 → 42`.

## Pack F — Platform engineering ✅

| # | Lesson | Theme | Status |
|---|--------|--------|--------|
| 28 | Architecture patterns catalog | Invent router/planner/critic/HITL/hybrid on demand | ✅ |
| 29 | Sessions & state at scale | Redis/Memorystore, stickiness, replay | ✅ |
| 30 | Multi-tenant agent platforms | Isolation, quotas, per-tenant tools | ✅ |
| 31 | FinOps for agents | Cost per task/tenant, budgets, chargeback | ✅ |
| 32 | Chaos, DR & feature flags | Break tools on purpose; recover; flag graphs | ✅ |

**Production-scale add-ons (after 31/32):**

| # | Lesson | Status |
|---|--------|--------|
| 43 | SLOs, capacity & backpressure | ✅ |
| 44 | LLM gateway, cache & platform quotas | ✅ |

Suggested platform path: `28 → 29 → 30 → 31 → 32 → 43 → 44`.

## Pack G — Productize & prove SME

| # | Lesson | Theme | Status |
|---|--------|--------|--------|
| 33 | SME judgment, teams & teaching | Build vs buy, ownership, mentoring drills | |
| 34 | Enterprise integrations | ITSM, Slack, Pub/Sub, case systems | |
| 35 | Dynamic Agent Creation Platform I | Spec schema → generate ADK package | |
| 36 | Dynamic Agent Creation Platform II | UI/API, validate, eval gate, deploy | |
| 37 | Governance, versioning & agent marketplace | Org lifecycle, deprecation, approvals | |
| 38 | Capstone I — Design from messy problem | Architecture + threat + eval plan | |
| 39 | Capstone II — Ship, measure, incident | Deploy + break + fix from traces | |
| 40 | Capstone III — Mentor & SME defense | Teach a peer; oral defense board | |

### Frontier surfaces (Pack G, before the capstones) ✅

Modern ADK and agent-engineering surfaces the earlier packs never touch.

| # | Lesson | Theme | Status |
|---|--------|--------|--------|
| 45 | Voice & bidirectional streaming | `run_live`, `LiveRequestQueue`, barge-in, transcripts | ✅ |
| 46 | Agent identity & delegated auth | Confused deputy, OAuth tool auth, workload identity | ✅ |
| 47 | Agentic commerce & payment mandates | AP2 intent/cart/payment, signed authorization | ✅ |
| 48 | Computer use & browser agents | `BaseComputer`, allowlist, read-only, confirmation | ✅ |
| 49 | Sandboxed code execution | Native code executors, escape probes, containment | ✅ |
| 50 | Simulated users & multi-turn eval | Personas, conversation rubrics, concession drift | ✅ |
| 51 | Context engineering & context audit | Seven slots, four failure modes, compaction, cache | ✅ |

Suggested order: `45 → 46 → 47 → 48 → 49 → 50 → 51`, then the capstones.  
Fastest safety win if you cannot do all seven: **46 → 51 → 50**.

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

Write/teach **5 lessons at a time**. After Pack F (+ 43/44): Pack G (33–40), etc.
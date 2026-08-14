# SME Gap Analysis — Why 18 Lessons Was Not Enough

An 18-lesson track can produce a strong builder. It cannot produce a **subject-matter expert** who can invent architectures, defend tradeoffs under incident pressure, and productize agent platforms.

This document lists gaps found against:

- The original Zero→Hero mastery map (sections 0–11 + capstone bar)
- Real Meridian/eCommerce production lifecycle needs
- Common ADK/agent-platform failure modes in the field

## Gaps that were thin or missing

| Gap | Why SME needs it | Now covered in |
|-----|------------------|----------------|
| ADK **graph workflows** (2.0) hands-on | Templates alone are not production control planes | **13** |
| **Parallel / Loop / Custom BaseAgent** depth | Fan-out races, critic loops, non-LLM control | **14** |
| **Long-running + checkpoint + HITL resume** | Refunds/approvals pause for hours | **15** |
| **MCP** tool ecosystem | Enterprise tools arrive as servers, not Python fns | **16** |
| **Event-driven + A2A** | Queue/webhook triggers; agent networks | **17** |
| Advanced **RAG** (chunk, embed, hybrid, cite) | Policy/FAQ at retail scale | **18** |
| **Memory** systems (write policy, privacy, consolidation) | Cross-session CX without leaking PII | **19** |
| **Model routing / fallback / structured output** | Flash↔Pro, JSON schema discipline | **20** |
| **Multimodal** (POD photos, receipts) | Grocery disputes are visual | **21** |
| **Streaming UX** | Store-ops tools need progressive tokens | **22** |
| **Red teaming** at scale | Injection beyond one lab prompt | **23** |
| **Online continuous eval** | Prod → golden feedback loop | **24** |
| **Human feedback / canary prompts** | Preference data + safe rollouts | **25** |
| **Plugins / middleware** depth | Cross-cutting policy enforcement | **26** |
| **Privacy / retention / compliance** | GDPR-ish retail reality | **27** |
| **Architecture pattern catalog** (invent on demand) | SME interview bar | **28** |
| **Session stores at scale** | Redis/Memorystore, stickiness | **29** |
| **Multi-tenant** isolation & quotas | Platform, not single app | **30** |
| **FinOps** per agent/tenant | $ attribution, budgets | **31** |
| **Chaos / DR / feature flags** | Reliability engineering | **32** |
| **SLOs / capacity / backpressure** | Agent SLIs, load shed, pods ≠ TPM | **43** |
| **LLM gateway / cache / quotas** | Keys, TPM, safe OMS cache | **44** |
| **Teams, runbooks, teaching** | Lead others | **33** |
| **ITSM / Slack / Pub/Sub integrations** | Real enterprise glue | **34** |
| **Dynamic Agent Creation Platform** (2 lessons) | Spec → generate → validate → deploy | **35–36** |
| **Governance / marketplace / versioning** | Org-scale agent lifecycle | **37** |
| **Capstone trilogy** (design / ship-debug / mentor) | Prove SME, not demo | **38–40** |

## Second-pass gaps (frontier surfaces, found by auditing the shipped catalog)

The first 44 lessons cover the harness — evals, tracing, release, tenancy, cost, resilience.
Auditing them against the current ADK surface and 2026 agent practice surfaced seven more.

| Gap | Why SME needs it | What was already there | Now covered in |
|-----|------------------|------------------------|----------------|
| **Voice / bidi streaming** | `run_live` + barge-in is a first-class ADK toolkit | Lesson 22 was one-way SSE text | **45** |
| **Agent identity / delegated auth** | Confused deputy is the top enterprise blocker | Edge API keys only (30) | **46** |
| **Agentic commerce mandates (AP2)** | Money paths need portable, signed authorization | HITL approval + audit log (07, 15) | **47** |
| **Computer use / browser agents** | Partner systems with no API | MCP assumed a server exists (16) | **48** |
| **Sandboxed code execution** | Ad-hoc analysis without building 40 tools | Function tools only (04) | **49** |
| **Simulated users / multi-turn eval** | Concession drift is invisible to single-turn goldens | Static goldens (08), prod sampling (24) | **50** |
| **Context engineering audit** | Weak context predicts the matching behavior failure | Token budget + compaction basics (06) | **51** |

## Pack A/B residual risks (already taught — revisit in later labs)

- Trajectory-first evals (08) must reappear in 24, 25, 38–39
- HITL gates (07, 15) must reappear in refund + platform lessons
- MLflow lineage (10) must gate deploys in 32, 36, 39

## SME definition used for the expanded track

You are SME when you can, **without hand-waving**:

1. Frame whether a Meridian problem should be agentic  
2. Design tools, graphs, and HITL with least privilege  
3. Ship evals + judges that catch regressions before users  
4. Trace a bad prod trajectory to a fix + golden promotion  
5. Deploy with auth, cost controls, rollback, and SLOs  
6. Integrate MCP/events/ITSM without collapsing security  
7. Generate and govern new agents from product specs  
8. Mentor another engineer through the same path  

That bar requires **~50 lessons**, not 18.
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
| **Teams, runbooks, teaching** | Lead others | **33** |
| **ITSM / Slack / Pub/Sub integrations** | Real enterprise glue | **34** |
| **Dynamic Agent Creation Platform** (2 lessons) | Spec → generate → validate → deploy | **35–36** |
| **Governance / marketplace / versioning** | Org-scale agent lifecycle | **37** |
| **Capstone trilogy** (design / ship-debug / mentor) | Prove SME, not demo | **38–40** |

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

That bar requires **~40 lessons**, not 18.
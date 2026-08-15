# Gap Analysis — Senior AI Engineer Curriculum (Aug 2026)

Cross-reference of all 43 shipped lessons against 2026 senior-AI-engineer roadmaps (aiarch.dev, AgentsCamp, Latent Space), the canonical reading lists (Chip Huyen's *AI Engineering*, the Latent Space paper canon, `start-ai-engineering`), and current whitepapers from Anthropic, OpenAI, and OWASP.

**Verdict:** the curriculum is best-in-class on the "systems around the model" — evals, safety, ops, and platform depth exceed what most published roadmaps ask for. The exposure risk is entirely **below the API line and beside the default stack**: model internals, post-training/distillation, self-hosted inference, real retrieval infrastructure, and systematic prompt optimization.

**Structural note:** lessons 33–40 (planned Pack G slots) were never written. The Tier-1 gaps below map almost exactly onto those eight empty slots.

## Tier 1 — Genuine holes a senior engineer would be exposed on

| # | Missing topic | Why it matters | Evidence from lessons |
|---|---|---|---|
| 1 | **How LLMs actually work** — transformer internals, attention, tokenization, sampling/temperature, KV-cache mental model, scaling laws, token economics | Every 2026 roadmap lists model intuition as the non-negotiable foundation; it's what lets you debug context rot, cost blowups, and structured-output failures instead of guessing | Only "next-token predictor" hand-wave in lesson 01; no attention/architecture content anywhere |
| 2 | **Fine-tuning & post-training** — when-to-finetune decision framework, SFT, LoRA/QLoRA, DPO vs RLHF, and distillation of frontier models into small open models | Distillation-for-cost is now the strongest commercial fine-tune case (10x inference savings); a senior must be able to argue *when not to* fine-tune, with evidence | Zero coverage — no SFT/LoRA/PEFT/DPO anywhere |
| 3 | **Inference, serving & self-hosting** — vLLM/SGLang, quantization (GGUF/int8), KV-cache & speculative decoding, GPU sizing basics, serverless vs self-hosted economics, open-weight landscape (Llama/Qwen/DeepSeek/Mistral) | Curriculum is 100% Gemini-API-centric; seniors are expected to justify "API vs self-host" with numbers | Lessons 43–44 cover gateway caching/quotas but nothing below the API line |
| 4 | **Production retrieval infrastructure** — real vector DBs (Qdrant/pgvector/Pinecone), embedding selection via MTEB, cross-encoder reranking, GraphRAG / knowledge graphs / text-to-SQL | Lesson 18's in-process matrix is pedagogically fine but nobody ships it; GraphRAG and data agents are in the Latent Space canon and top production patterns | Lesson 18 uses hybrid keyword+vector over markdown only; no vector DB, reranker, or structured-data retrieval |
| 5 | **Prompt/program optimization** — DSPy, GEPA, prompts as compiled programs | Fast-rising 2025–2026 discipline; replaces the manual A/B loop with systematic optimization against the eval sets lessons 08–10 already build | Manual A/B + MLflow registry only (lessons 10, 25) |
| 6 | **Reasoning models & test-time compute** — when thinking models help vs hurt, thinking budgets, prompting differences, cost/latency trade-offs | Reasoning models behave differently enough that every roadmap treats this as its own topic | Lesson 20 routes Flash vs Pro by feature; "reasoning vs standard model" as a concept is absent |
| 7 | **Dataset engineering & synthetic data** — data flywheels, curation, dedup, contamination, synthetic data for evals *and* training, annotation guidelines | Hamel Husain and Shreya Shankar both argue the data flywheel is *the* differentiator of teams that improve vs stagnate | Only synthetic POD PNGs (21) and smoke fixtures (41); no pipeline discipline |

## Tier 2 — Formalization and breadth gaps

| # | Missing topic | Why it matters |
|---|---|---|
| 8 | **Formal agentic threat modeling** — map existing red-team/injection/identity work onto OWASP Top 10 for Agentic Applications 2026 (ASI01–ASI10), the lethal trifecta, NIST AI RMF | Lessons 23, 46–49 cover the substance; seniors are expected to speak the standard vocabulary in security reviews. Cheap fix, high leverage |
| 9 | **Framework portability & judgment** — LangGraph vs Claude Agent SDK vs Pydantic AI trade-offs; what's framework vs fundamental | Single-framework (ADK) depth is a strength but one comparative lesson inoculates against lock-in blindness |
| 10 | **Data engineering for AI** — document ingestion at scale (OCR/Docling), ETL for RAG corpora, freshness pipelines | "Why most RAGs stay POCs" is almost always a data-pipeline story, not a retrieval story |
| 11 | **AI-assisted engineering as daily practice** — harness engineering, working effectively with coding agents, AGENTS.md conventions, verify-then-trust loops | 2026 hiring explicitly screens for this; also the consumer-side education for agent design |
| 12 | **Product judgment & Human-AI UX** — agent vs workflow vs nothing, trust calibration, feedback affordances, Microsoft Human-AI Interaction guidelines | Lesson 28's decision tree covers the technical side; the product/user side is thin |
| 13 | **Statistics for evaluation** — significance testing, sample-size math, run variance, judge–human agreement | Without stats literacy people ship "improvements" that are noise |
| 14 | **Public benchmark literacy** — SWE-Bench, TauBench, GAIA, MMLU, contamination pitfalls | Needed to read model announcements critically and design capstone-grade benchmarks |
| 15 | **RL for agents (awareness level)** — RLVR, verifiers, agentic RL trends | Emerging; conversational fluency, not implementation depth |

## Suggested mapping to empty lesson slots 33–40

| Slot | Proposed lesson |
|---|---|
| 33 | LLM internals & token economics |
| 34 | Reasoning models & test-time compute |
| 35 | Fine-tuning, post-training & distillation |
| 36 | Dataset engineering & synthetic data |
| 37 | Self-hosting & inference optimization |
| 38 | Production retrieval infra (vector DBs, reranking, GraphRAG, text-to-SQL) |
| 39 | Prompt/program optimization (DSPy / GEPA) |
| 40 | Formal agentic threat modeling (OWASP ASI) + framework portability |

Companion resources: see the [AI Engineering Reading List](ai-engineering-reading-list.md). Platform-specific gaps: see the [agent platform gap analysis](gap-analysis-agent-platform.md).

# Google ADK Zero → Hero (SME Track)

Practical mastery path for Google's **Agent Development Kit (ADK)**.  
~**40 lessons** — because 18 is enough to demo, not enough to be an SME.

Every lesson advances **Meridian Commerce OrderOps** (Walmart/Kroger/Amazon-scale grocery + eCommerce ops pain).

| Doc | Purpose |
|-----|---------|
| [docs/curriculum-roadmap.md](docs/curriculum-roadmap.md) | Full 01–40 map |
| [docs/gap-analysis-sme.md](docs/gap-analysis-sme.md) | Why the expanded track exists |
| [docs/meridian-northstar.md](docs/meridian-northstar.md) | Product brief |
| [docs/NATIVE-ADK.md](docs/NATIVE-ADK.md) | **Use ADK natively — no DIY runtimes** |
| `cd learn && npm run dev` | **Study site** (VitePress) — read lessons without the lab tree |

```
Customer ticket / ops alert
        │
        ▼
   ┌─────────┐
   │ Router  │──▶ Order / Inventory / Refund specialists
   └─────────┘              │
                            ▼
                      Synthesizer + HITL + audit
```

## Curriculum packs (5 lessons each)

### Pack A — Foundations → Control ✅

| # | Lesson |
|---|--------|
| 01 | [Agentic foundations](lessons/01-agentic-foundations.md) |
| 02 | [ADK environment & loop](lessons/02-adk-environment.md) |
| 03 | [Core building blocks](lessons/03-core-building-blocks.md) |
| 04 | [Tools deep mastery](lessons/04-tools-mastery.md) |
| 05 | [Multi-agent orchestration](lessons/05-multi-agent-orchestration.md) |
| 06 | [Context, memory, knowledge](lessons/06-context-memory-knowledge.md) |
| 07 | [Reliability, safety, control](lessons/07-reliability-safety-control.md) |

### Pack B — Eval → Observability → Deploy ✅

| # | Lesson |
|---|--------|
| 08 | [Testing & evaluation](lessons/08-testing-evaluation.md) |
| 09 | [Judges & thinking extraction](lessons/09-judges-thinking-extraction.md) |
| 10 | [MLflow for agentic systems](lessons/10-mlflow-agentic.md) |
| 11 | [Tracing & observability](lessons/11-tracing-observability.md) |
| 12 | [Deployment & ops](lessons/12-deployment-ops.md) |

**Ops depth (after Pack B):** [41 — CI/CD, canary, rollback & on-call](lessons/41-cicd-sre-deployment-ops.md) · [32 — Chaos, DR & feature flags](lessons/32-chaos-dr-feature-flags.md)  
**RAI bonus (after Pack E):** [42 — Responsible AI champion](lessons/42-responsible-ai-champion.md)

### Pack C — Orchestration depth & ecosystems ✅

| # | Lesson | Theme |
|---|--------|--------|
| 13 | [ADK graph workflows](lessons/13-graph-workflows.md) | Deterministic edges + intelligent nodes |
| 14 | [Parallel, loop & custom agents](lessons/14-parallel-loop-custom-agents.md) | Fan-out, critic loops, BaseAgent |
| 15 | [Long-running & HITL resume](lessons/15-long-running-hitl-resume.md) | Checkpoints, pause/resume |
| 16 | [MCP & tool ecosystems](lessons/16-mcp-tool-ecosystems.md) | MCP servers for Meridian tools |
| 17 | [Event-driven & A2A](lessons/17-event-driven-a2a.md) | Webhooks, queues, agent-to-agent |

### Pack D — Knowledge, models, multimodal ✅

| # | Lesson | Theme |
|---|--------|--------|
| 18 | [Advanced RAG for retail policy](lessons/18-advanced-rag-retail-policy.md) | Chunk → embed → hybrid → cite |
| 19 | [Memory systems deep dive](lessons/19-memory-systems-deep-dive.md) | ADK MemoryService + write policy |
| 20 | [Model routing, fallbacks & structured output](lessons/20-model-routing-fallbacks-structured-output.md) | Flash/Pro, degrade, `output_schema` |
| 21 | [Multimodal OrderOps](lessons/21-multimodal-orderops.md) | POD photos + vision + tools |
| 22 | [Streaming UX & progressive responses](lessons/22-streaming-ux-progressive-responses.md) | ADK events → SSE for store ops |

### Pack E — Quality at scale & hard security ✅

| # | Lesson | Theme |
|---|--------|--------|
| 23 | [Red teaming & adversarial robustness](lessons/23-red-teaming-adversarial-robustness.md) | Attack suites + ASR CI gates |
| 24 | [Online monitoring & continuous eval](lessons/24-online-monitoring-continuous-eval.md) | Sample → score → promote goldens |
| 25 | [Human feedback, preferences & canary prompts](lessons/25-human-feedback-canary-prompts.md) | Labels, prefs, canary rollback |
| 26 | [Plugins, callbacks & policy middleware](lessons/26-plugins-callbacks-policy-middleware.md) | ADK `BasePlugin` enforcement |
| 27 | [Privacy, retention & compliance](lessons/27-privacy-retention-compliance.md) | Redact, TTL, DSR export/delete |

**RAI bonus:** [42 — Responsible AI champion](lessons/42-responsible-ai-champion.md) (scorecard → fixes → evidence pack)

### Pack F — Platform engineering *(next)*

28 Architecture catalog · 29 Sessions at scale · 30 Multi-tenant · 31 FinOps · [32 Chaos/DR/flags](lessons/32-chaos-dr-feature-flags.md) ✅

### Pack G — Productize & prove SME

33 Teams/teaching · 34 Enterprise integrations · **35–36 Dynamic Agent Creation Platform** · 37 Governance · **38–40 Capstone trilogy**

## How to use each lesson

1. **At a glance** + **Why this matters**  
2. **Know these** (terms) before commands  
3. Every **Task**: nested *Why / Do this / Expect*  
4. **Knowledge check** + **Feedback**

> If you cannot teach the knowledge-check answers without the doc, you are not done.

## Prerequisites

- Python 3.10+, git, editor, terminal  
- Gemini API key for Lesson 02+  
- Docker for Lesson 12+  
- Pack C assumes Pack A+B concepts (graph labs can use stubs if your agents are mid-build)

## Study in the browser (VitePress)

Lessons stay in `lessons/*.md`. A small converter in `learn/` turns them into a local (and GitHub Pages) site so you can read, search, and track progress without keeping the lab tree open.

```sh
cd learn
npm install
npm run dev
```

Open `http://localhost:5173`. Saving a lesson reloads the page. See [learn/study.md](learn/study.md) for search, progress, and Pages setup.

**GitHub Pages:** Settings → Pages → Source = GitHub Actions. After the `Deploy Meridian Learn` workflow runs: `https://sardul3.github.io/agent-learn-adk/`.

## Start

- New → [Lesson 01](lessons/01-agentic-foundations.md) (or the [study site](https://sardul3.github.io/agent-learn-adk/lessons/01-agentic-foundations))
- Finished Pack B → [Lesson 13](lessons/13-graph-workflows.md)  
- Finished Pack C → [Lesson 18](lessons/18-advanced-rag-retail-policy.md)  
- Finished Pack D → [Lesson 23](lessons/23-red-teaming-adversarial-robustness.md)  
- Finished Pack E → [Lesson 42 — RAI bonus](lessons/42-responsible-ai-champion.md) (then Pack F in the roadmap)
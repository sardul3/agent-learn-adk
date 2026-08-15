# Gap Analysis — Agentic Platform Creation (ADK) (Aug 2026)

The target: an **all-in-one agent-development platform** where a user enters a goal in a UI ("find the best price for this SKU on the web") and the platform stands up the agent — architecture pattern, tools (chosen or synthesized), workflow, control flow, guardrails, eval set — and hands back a working, interactable agent. Engineers who support the platform get complete observability, fast diagnosis, cost analysis, advanced evals, judging/scoring, and goal-attainment analysis, with clean integrations into external obs/eval/cost platforms.

Benchmarked against: **Gemini Enterprise Agent Platform** (formerly Vertex AI Agent Builder: ADK + Agent Studio + Agent Garden + Model Garden + Agent Engine + Agent Identity/Gateway/Model Armor), **Amazon Bedrock AgentCore**, **OpenAI AgentKit** (deprecated Jun 2026 — instructive failure), **Dify / Flowise / Langflow / n8n**, **LangGraph Platform**, meta-agent research (MetaChain, NexA4A, MetaAgent), and the **OpenTelemetry GenAI semantic conventions** (v1.41).

## The north-star trace (what the platform must do)

For "*best price for a product name or SKU*", entered in the UI:

1. **Goal intake** → classify task type, risk tier, and required capabilities (web search, page fetch, extraction, comparison).
2. **Architecture selection** → meta-agent picks a pattern from the catalog (here: sequential `search → fetch/extract (parallel per retailer) → compare → answer`), reusing the lesson-28 decision tree as machine-readable rules.
3. **Tool binding** → semantic search over the tool registry finds `web_search`, `fetch_page`, `extract_price`; per-tenant entitlements checked; if no extractor exists, the tool-synthesis pipeline generates one, tests it in a sandbox, and registers it as `draft`.
4. **Agent compilation** → emit a declarative **ADK Agent Config (YAML)** — not Python — with instructions, tools, sub-agents, output schema, and guardrail policy attached.
5. **Auto-eval generation** → synthesize a golden eval set + simulated-user scenarios from the goal; run `AgentEvaluator` before the agent is offered to the user.
6. **Provisioning** → deploy to the managed runtime, mint an agent identity + scoped credentials, generate the chat UI/embed/API key, register OTel tracing.
7. **Operate** → traces stream in `gen_ai.*` semantic conventions to any OTLP backend; cost per run computed from token attributes; judges score goal attainment; failures promote into the eval set.

Every gap below is a step of this trace the current curriculum cannot yet teach.

## Tier 1 — Platform-defining gaps

| # | Missing topic | What it covers | Why it matters / who does it today | Current lesson coverage |
|---|---|---|---|---|
| P1 | **Agents as data: declarative Agent Config (YAML)** | ADK's Agent Config format (`adk create --type=config`, `root_agent.yaml`), schema validation, versioning, diffing, serialization limits vs code agents | A UI-driven platform cannot store Python — it stores specs. ADK ships this natively (experimental, Py ≥1.11); the Visual Builder generates it. This is the substrate of the whole platform | None — all 43 lessons are code-first (`agent.py`) |
| P2 | **The builder surface: ADK Visual Builder & `adk api_server`** | Visual Builder internals (drag-drop + AI assistant → YAML), the local API endpoints it writes through, building your own builder UI against ADK's API server, file-write security (extension allowlists, path-traversal rejection, blocked keys) | ADK ≥1.18 already ships a visual agent builder inside `adk web` — the exact product shape being targeted. Nobody in the curriculum has opened it | `adk web` used only as a debug console (lesson 02) |
| P3 | **Goal-to-agent compilation (meta-agents)** | NL goal → task classification → architecture selection → instruction generation → tool selection → orchestrator generation; MetaChain's "agent-creating agents", NexA4A's requirement analysis + registry, guardrails on what the meta-agent may provision | This is the product's core magic. Research is mature (MetaChain, NexA4A, MetaAgent) and the lesson-28 decision tree is the perfect deterministic backbone — it just was never turned into a machine-usable compiler | Lesson 28 has the decision tree for *humans*; no automation |
| P4 | **Tool registry & catalog engineering** | Central tool registry with schemas, versions, owners, entitlements; semantic search over tools; **Tool Space Interference** (accuracy degrades past ~20 exposed tools) and dynamic tool retrieval/loading; MCP Registry and MCP gateways as the interop layer | Auto tool *selection* requires a searchable catalog, not a hardcoded `tools=` list. The ~20-tool soft limit makes "expose everything" a non-option — retrieval over the registry is mandatory | Lesson 16 has per-agent MCP `tool_filter` YAML; no platform-level registry, search, or entitlements |
| P5 | **Auto tool creation (tool synthesis)** | Generate tool code on demand when the registry has no match: spec → implementation → unit tests → sandboxed execution → draft registration → human promotion; governance mapping to OWASP ASI04 (supply chain) & ASI05 (unexpected code execution) | The "auto_tool_creation on a need-by basis" requirement. Patterns exist (semantic-search-then-synthesize LangGraph workflows, Google Cloud dynamic tool creation reference) but must be wrapped in the lesson-49 sandbox discipline | Lesson 49 covers sandboxed code exec; nothing about the tool-synthesis lifecycle |
| P6 | **Agent lifecycle & registry (control plane)** | Agent CRUD, draft→eval-gated→published states, semantic versioning of agent *definitions* (not code deploys), template gallery (Agent Garden analog), cloning, deprecation, rollback of a user's agent to a prior spec | The curriculum's CI/CD (lesson 41) ships *the app*; a platform must ship *thousands of user-created agents as data*, each with its own lifecycle | Lessons 41/25 canary the platform's own prompts; no user-agent registry |
| P7 | **Managed runtime architecture: control plane vs data plane** | Scheduler and isolation for many heterogeneous user agents; per-agent quotas/budgets; scale-to-zero; how Agent Engine (Sessions, Memory Bank, Example Store, Code Execution, Evaluation Service) and Bedrock AgentCore carve this up; "own the substrate" vs "own the authoring canvas" (the AgentKit deprecation lesson) | Deploying one known workflow (lesson 12) ≠ operating a fleet of arbitrary agents. AgentCore's framework-neutral runtime bet outlived OpenAI's hosted canvas — architecture strategy matters | Lessons 12/29/30/43 cover one app multi-tenant; no fleet control plane |
| P8 | **Interop-standard observability: OTel GenAI semantic conventions** | Emitting `gen_ai.*` spans (client, agent, workflow, MCP tool, content, eval layers), the two mandatory metrics (`gen_ai.client.operation.duration`, `gen_ai.client.token.usage`), cost derivation from token attributes, and plugging *any* OTLP backend (Langfuse `/api/public/otel`, Arize Phoenix/OpenInference, Datadog, Braintrust, Helicone) | "Integrates nicely with other platforms for obs/evals/cost" is a solved interop problem in 2026 — *if* you emit the standard. MLflow-only telemetry is a walled garden | Lesson 11 does MLflow + best-effort OTel; the semconv contract and backend pluggability are absent |
| P9 | **Eval-as-a-service for generated agents** | Auto-generating eval sets + simulated-user scenarios *from the user's goal*; goal-attainment judges for agents the platform authors didn't hand-build; per-agent score dashboards; Example Store-style feedback flywheels | Evals for a hand-built agent (lessons 08–09, 50) assume a human wrote the goldens. A platform must synthesize them at agent-creation time, or every generated agent ships unevaluated | Lessons 08–09/24/50 are strong but human-authored |

## Tier 2 — Competitive-parity and hardening gaps

| # | Missing topic | Why it matters |
|---|---|---|
| P10 | **Model/provider abstraction & BYO-model** — Model Garden analog, LiteLLM/OpenRouter-style multi-provider routing, per-tenant model allowlists, model-agnostic agent specs | Gemini-only routing (lesson 20) blocks enterprise BYO-model demands; ADK itself is model-agnostic via LiteLLM |
| P11 | **Provisioned end-user surfaces** — auto-generated chat UI, embeds, and API keys per created agent; conversation history and user management per app (the Dify "application" packaging) | The user's deliverable is "a working interactable agent", not a JSON endpoint; Dify's app-shaped packaging is the reference |
| P12 | **Guardrails as configurable platform policy** — Model Armor / NeMo Guardrails / LlamaFirewall-class policies attached per-agent from the UI, policy packs by risk tier, central policy versioning | Lessons 07/26 hand-code plugins per agent; a platform needs policy as tenant-selectable config |
| P13 | **HITL at platform scale** — cross-agent approval inboxes, delegated approver routing, SLAs on pending approvals | Lesson 15's per-agent HITL doesn't answer "one ops team, 500 user agents" |
| P14 | **Platform packaging, licensing & build-vs-buy** — OSS licensing traps (n8n Sustainable Use vs MIT/Apache embedding), the AgentKit deprecation post-mortem, when to build on Agent Engine/AgentCore vs self-host | Choosing the wrong substrate or license is an existential platform mistake |
| P15 | **Agent marketplace & sharing governance** — publishing user agents to a shared gallery, review gates, provenance (AIBOM), signed agent/tool artifacts | Agent Garden / GPT-Store dynamics; supply-chain risk (ASI04) applies to shared agents too |
| P16 | **Memory Bank / Example Store managed services** — ADK↔Agent Engine Memory Bank integration (`PreloadMemoryTool`, `after_agent_callback` persistence) as the managed alternative to lesson 19's in-memory service | The managed-memory path is what a platform would actually run |
| P17 | **Cost analysis per generated agent** — extending lesson 31's FinOps to platform economics: per-agent/per-tenant unit costs from `gen_ai.usage.*` attributes, margin modeling for a paid platform, plan tiers and metering | Lesson 31 prices one known workflow; a platform prices arbitrary generated agents |

## Suggested new pack (Pack H — Agent Platform Engineering, lessons 52–60)

| Slot | Proposed lesson | Gaps covered |
|---|---|---|
| 52 | Agents as data: Agent Config YAML, validation, versioning | P1 |
| 53 | The builder surface: Visual Builder, `adk api_server`, building your own canvas | P2, P11 |
| 54 | Tool registry, semantic tool search & Tool Space Interference | P4 |
| 55 | Auto tool creation: synthesize → test → sandbox → register → promote | P5 |
| 56 | Goal-to-agent compilation: the meta-agent that assembles agents | P3, P9 |
| 57 | Agent lifecycle control plane: registry, states, template gallery, fleet rollback | P6, P15 |
| 58 | Managed runtime: control/data plane split, Agent Engine & AgentCore anatomy | P7, P16 |
| 59 | Interop observability: OTel GenAI semconv, pluggable obs/eval/cost backends | P8, P17 |
| 60 | Platform guardrails, BYO-model, HITL inbox & packaging economics | P10, P12, P13, P14 |

Companion resources: **Part 2 of the [AI Engineering Reading List](ai-engineering-reading-list.md)**. General curriculum gaps: [gap-analysis-ai-engineering.md](gap-analysis-ai-engineering.md).

# Capstone Curriculum — Meridian Foundry: the All-in-One Agent Platform

The capstone that closes the track: stand up a complete platform where a user enters a goal in a UI ("find the best price for a product name or SKU") and the platform assembles, evaluates, provisions, and operates a working interactable agent — with tools chosen from a governed catalog (or synthesized on demand), and full obs/eval/judging/cost integration for the engineers who support it.

Grounded in the [agent platform gap analysis](gap-analysis-agent-platform.md) (gaps P1–P17) and the [AI Engineering Reading List, Part 2](ai-engineering-reading-list.md). Every milestone maps to proposed Pack H lessons 52–60.

## The acceptance test (final demo)

A grader with no repo knowledge opens the Foundry UI and types: *"Track the best price for SKU MER-1042 across three retailers and alert me when it drops."* Within minutes, with no code written by anyone:

1. The platform classifies the goal, picks an architecture pattern, and shows its plan for approval.
2. It binds `web_search` and `fetch_page` from the tool registry; finding no price extractor, it synthesizes one, unit-tests it in a sandbox, and registers it as `draft` pending promotion.
3. It compiles a declarative **ADK Agent Config (YAML)** — instructions, tools, sub-agents, output schema, guardrail policy pack.
4. It generates a golden eval set + simulated-user scenarios from the goal and runs them; the agent only becomes visible after passing the gate.
5. It provisions the agent: identity + scoped credentials, chat UI, API key, OTel tracing.
6. The grader chats with the agent and gets a cited price comparison.
7. On the ops side: the run's trace appears in **two different OTLP backends** (switching = env var, not code), cost-per-run is computed from `gen_ai.usage.*` tokens, a judge scores goal attainment, and one injected failure is diagnosed from traces in under five minutes.

Pass = all seven steps, live, twice in a row.

## Prerequisites

- Packs A–F complete; lessons 41, 43–44, and 46–51 strongly recommended before M3+.
- The platform gaps doc read end-to-end (it is the capstone's requirements spec).
- Standards carried over from the track: **native ADK only** (no second orchestrator), deterministic Python locks on money/side-effect paths, propose-only + HITL for risky actions, eval SHIP gates before anything user-visible.

## Milestones

### M0 — Platform skeleton (est. 1 week)

**Build:** monorepo for Foundry: control-plane FastAPI service, Postgres for registries, `adk api_server` embedded as the agent runtime seam, docker-compose dev stack, smoke script.
**Study:** lessons 12, 29; Agent Engine anatomy docs (what a managed runtime carves out: Sessions, Memory Bank, Example Store, Code Execution, Evaluation Service).
**Gate:** `smoke.sh` green; an ADK hello-agent runs through the control plane's API, not directly.

### M1 — Agents as data: Agent Config substrate (lesson 52 · gap P1)

**Build:** adopt ADK Agent Config YAML as the only stored agent representation. Schema validation on write, semantic versioning of agent specs, diff view between versions, round-trip test: YAML → running agent → YAML.
**Study:** ADK Agent Config docs + YAML schema reference; Agent Config known limitations (which tools/features don't serialize — this constrains everything downstream).
**Gate:** an agent authored only as YAML passes the lesson-08-style eval harness; a bad spec is rejected with a field-level error, never a stack trace.

### M2 — The builder surface (lesson 53 · gaps P2, P11)

**Build:** the Foundry UI: form/canvas editor that reads and writes Agent Config through the control plane; per-agent provisioned chat UI + API key (the Dify-style "application" packaging); file-write hardening copied from ADK's Visual Builder rules (extension allowlist, path-traversal rejection, blocked keys).
**Study:** ADK Visual Builder (open it, build an agent in it, read the YAML it generates); `adk api_server` endpoints; Dify's app-shaped packaging.
**Gate:** a non-engineer builds a two-tool agent from the UI alone and chats with it on its provisioned surface.

### M3 — Tool registry & catalog (lesson 54 · gap P4)

**Build:** central tool registry (schema, version, owner, risk tier, per-tenant entitlements); embedding-based semantic search over tool descriptions; agent compilation selects the top-k relevant tools — never the whole catalog (Tool Space Interference: accuracy degrades past ~20 exposed tools); MCP servers registered as first-class catalog sources.
**Study:** lesson 16; MCP Registry spec; Anthropic "Writing Effective Tools for Agents" and "Code Execution with MCP".
**Gate:** with 60+ tools registered, a compiled agent receives ≤10, all relevant; entitlement denial is enforced at bind time and audited.

### M4 — Auto tool creation (lesson 55 · gap P5)

**Build:** the synthesis pipeline: unmatched capability → spec → generated implementation → generated unit tests → sandboxed execution (lesson 49 executors; no network/secrets by default) → `draft` registration → human promotion to `published`. Map every stage to OWASP ASI04/ASI05 controls.
**Study:** lesson 49; Google Cloud dynamic tool creation article; NexA4A's ToolGenerator; OWASP Agentic Top 10.
**Gate:** the price-extractor scenario end-to-end; a deliberately malicious synthesis attempt (exfil attempt in generated code) is caught by sandbox policy and flagged, not shipped.

### M5 — Goal-to-agent compiler + auto-evals (lesson 56 · gaps P3, P9)

**Build:** the meta-agent: goal → task classification → architecture selection (lesson 28's decision tree, made machine-readable) → instruction generation → tool binding (M3) or synthesis request (M4) → Agent Config emission (M1). In the same pass: generate a golden eval set + simulated-user scenarios (lesson 50 personas) from the goal; run `AgentEvaluator`; block publication below threshold.
**Study:** lesson 28, 50; MetaChain paper; NexA4A repo; Anthropic "Building Effective Agents" (the meta-agent must prefer workflows over autonomy too).
**Gate:** five goals of different shapes (lookup, monitor, compare, summarize, multi-step research) compile to five *structurally different* agents; each ships with ≥8 auto-generated eval cases; one goal designed to fail eval is correctly blocked.

### M6 — Lifecycle control plane & fleet runtime (lessons 57–58 · gaps P6, P7, P15, P16)

**Build:** agent registry with states (`draft → eval_gated → published → deprecated`), clone/rollback of specs, template gallery (Agent Garden analog) with review gate; fleet runtime concerns: per-agent quotas and budgets, scale-to-zero, blast-radius isolation, kill switch per agent and per tenant; optional: swap lesson 19's memory for the managed Memory Bank pattern.
**Study:** lessons 30, 32, 43; Agent Engine / Bedrock AgentCore anatomy; the AgentKit deprecation post-mortem (own the substrate).
**Gate:** 20 concurrent heterogeneous agents under load-shed rules from lesson 43; a bad published version rolls back as a *data* operation (no redeploy); a runaway agent is killed without collateral damage.

### M7 — Interop AgentOps: obs, evals, cost (lesson 59 · gaps P8, P17)

**Build:** emit OTel GenAI semantic conventions (`gen_ai.*` spans across agent/workflow/tool/LLM layers; the two mandatory metrics: operation duration + token usage); pluggable OTLP export verified against two backends (e.g., Langfuse self-hosted + Arize Phoenix); cost-per-run/per-agent/per-tenant derived from token attributes and rate cards (lesson 31); goal-attainment judges (lesson 09) scoring production trajectories; failure → golden promotion loop (lesson 24).
**Study:** OTel GenAI semconv spec; the OTel+Langfuse pattern; lessons 09, 11, 24, 31.
**Gate:** switching obs backend = env-var change only; an on-call engineer diagnoses an injected tool failure from traces in <5 minutes; finance-style cost report per tenant reconciles with gateway token counts within 2%.

### M8 — Governance & GA hardening (lesson 60 · gaps P10, P12, P13, P14)

**Build:** guardrail policy packs attachable per-agent from the UI (risk-tiered: read-only / propose-only / HITL-gated), platform-wide HITL approval inbox with SLAs, per-agent identity + scoped credentials (lesson 46), BYO-model abstraction (model allowlist per tenant; at least one non-Gemini provider via LiteLLM), red-team suite (lesson 23) run against *generated* agents, chaos drill (lesson 32) at platform level, GA checklist + runbook.
**Study:** lessons 07, 23, 26, 46; Model Armor / NeMo Guardrails; OWASP ASI mapping from the gaps doc.
**Gate:** ASR on the generated-agent red-team suite under threshold; the lethal-trifecta combination is impossible to configure from the UI for any published agent; full acceptance test (top of this doc) passes twice consecutively.

## Grading rubric

| Dimension | Weight | Evidence |
|---|---|---|
| Acceptance test passes end-to-end | 30% | Live demo, twice |
| Agents-as-data discipline (no Python stored, clean versioning/rollback) | 15% | M1/M6 gates |
| Tool governance (registry, TSI discipline, synthesis safety) | 15% | M3/M4 gates |
| Compiler quality (structural diversity, auto-evals block bad agents) | 15% | M5 gate |
| Interop AgentOps (semconv compliance, backend swap, cost reconciliation) | 15% | M7 gate |
| Security & governance (red team, identity, HITL inbox) | 10% | M8 gate |

**Definition of done:** all eight milestone gates green, rubric ≥80%, plus a written architecture decision record covering: build-on vs build (Agent Engine/AgentCore vs self-hosted), licensing review of embedded OSS, and the three things you would cut first under cost pressure.

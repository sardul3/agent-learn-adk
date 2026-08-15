# AI Engineering Reading List — the SA/SWE Arsenal

Curated August 2026 from the Latent Space paper canon, Chip Huyen's *AI Engineering* resource index, the `start-ai-engineering` guide, OWASP GenAI, and direct source-checking of Anthropic/OpenAI/Google engineering blogs. Difficulty: **F** = foundational, **P** = practitioner, **A** = advanced.

> **Note:** Part 1 is the general senior-AI-engineer arsenal. Part 2 is the agent-platform-builder arsenal (ADK ecosystem, agent builders, AgentOps integrations).

## Part 1 — Senior AI Engineer arsenal

### Foundations — how models actually work

| Resource | Author / Source | Type | Lvl | Why it's in the arsenal |
|---|---|---|---|---|
| [Deep Dive into LLMs like ChatGPT](https://www.youtube.com/watch?v=7xTGNNLPyMI) | Andrej Karpathy | Video (3.5h) | F | The single best end-to-end tour of the training + inference stack |
| [Neural Networks: Zero to Hero](https://www.youtube.com/playlist?list=PLAqhIrjkxbuWI23v9cThsA9GvCAUhRvKZ) | Andrej Karpathy | Video series | A | Build GPT from scratch by hand; converts API users into engineers who can debug models |
| [The Illustrated Transformer](https://jalammar.github.io/illustrated-transformer/) | Jay Alammar | Article | F | The canonical visual reference for attention and the transformer |
| [3Blue1Brown neural networks & attention series](https://www.youtube.com/@3blue1brown) | Grant Sanderson | Video | F | Best visual intuition for attention that exists |
| [Build a Large Language Model (From Scratch)](https://www.manning.com/books/build-a-large-language-model-from-scratch) | Sebastian Raschka | Book | A | Code a GPT in PyTorch with nothing hidden; the definitive internals book |
| [Hands-On Large Language Models](https://www.oreilly.com/library/view/hands-on-large-language/9781098150952/) | Alammar & Grootendorst | Book | P | Visual, code-first companion covering embeddings through generation |
| [Why We Think](https://lilianweng.github.io/posts/2025-05-01-thinking/) | Lilian Weng | Article | A | The theory of test-time compute and why reasoning models work |
| [The State of LLMs 2025](https://magazine.sebastianraschka.com/p/state-of-llms-2025) | Sebastian Raschka | Article | P | Year-end synthesis of how the stack actually moved |

### The core AI engineering canon

| Resource | Author / Source | Type | Lvl | Why it's in the arsenal |
|---|---|---|---|---|
| [AI Engineering](https://www.oreilly.com/library/view/ai-engineering/9781098166298/) + [resources.md](https://github.com/chiphuyen/aie-book/blob/main/resources.md) | Chip Huyen | Book + index | P | The most-read book in the field; the companion resource index alone is a curriculum |
| [The 2025 AI Engineering Reading List](https://www.latent.space/p/2025-papers) | swyx / Latent Space | Paper list | P–A | 50 papers across 10 fields; the definitive annually-updated paper canon |
| [Agents](https://huyenchip.com/2025/01/07/agents.html) | Chip Huyen | Article | P | Long-form primer on planning, tool use, and failure modes |
| [Applied LLMs — What We've Learned From A Year of Building](https://applied-llms.org/) | Eugene Yan et al. | Article | P | Six practitioners' consolidated production lessons |
| [Patterns for Building LLM-based Systems](https://eugeneyan.com/writing/llm-patterns/) | Eugene Yan | Article | P | The seven patterns nearly every shipped LLM product converges on |
| [12-Factor Agents](https://github.com/humanlayer/12-factor-agents) | Dex Horthy | Repo/manifesto | P | Widely-cited production-agent checklist; excellent capstone review rubric |
| [LLM Powered Autonomous Agents](https://lilianweng.github.io/posts/2023-06-23-agent/) | Lilian Weng | Article | A | The reference post that defined the field's vocabulary |
| [start-ai-engineering](https://github.com/louisfb01/start-ai-engineering) | Louis-François Bouchard | Curated repo | F–A | Continuously updated 2026 master index |
| [LLM Engineer's Handbook](https://github.com/PacktPublishing/LLM-Engineers-Handbook) | Iusztin & Labonne | Book + repo | P | Production-focused, built around one real end-to-end project |

### Agents, context engineering & harnesses

| Resource | Author / Source | Type | Lvl | Why it's in the arsenal |
|---|---|---|---|---|
| [Building Effective Agents](https://www.anthropic.com/engineering/building-effective-agents) | Anthropic | Whitepaper | P | *The* required-reading post on workflows vs agents; simplicity-first doctrine |
| [Effective Context Engineering for AI Agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) | Anthropic | Whitepaper | P | The formal treatment of compaction, note-taking, sub-agent isolation |
| [How We Built Our Multi-Agent Research System](https://www.anthropic.com/engineering/built-multi-agent-research-system) | Anthropic | Whitepaper | A | Real shipped multi-agent architecture with production failure modes |
| [Writing Effective Tools for Agents](https://www.anthropic.com/engineering/writing-tools-for-agents) | Anthropic | Whitepaper | P | Tool schemas, descriptions, error-as-observation design |
| [Effective Harnesses for Long-Running Agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) | Anthropic | Whitepaper | A | Checkpoints, state, recovery for hour-long runs |
| [Code Execution with MCP](https://www.anthropic.com/engineering/code-execution-with-mcp) | Anthropic | Whitepaper | A | Composing MCP servers through code instead of giant tool lists |
| [Harness Engineering](https://openai.com/index/harness-engineering/) | OpenAI | Article | A | The harness layer behind Codex; million-line agent-generated codebase lessons |
| [Context Engineering for Agents](https://rlancemartin.github.io/2025/06/23/context_engineering/) | Lance Martin / LangChain | Article + podcast | P | The write/select/compress/isolate taxonomy everyone now uses |
| [ReAct](https://arxiv.org/abs/2210.03629) · [Reflexion](https://arxiv.org/abs/2303.11366) · [Voyager](https://arxiv.org/abs/2305.16291) · [MemGPT](https://arxiv.org/abs/2310.08560) · [Generative Agents](https://arxiv.org/abs/2304.03442) | Various | Papers | A | The five agent papers from the Latent Space canon worth reading in full |

### Evals & data flywheels

| Resource | Author / Source | Type | Lvl | Why it's in the arsenal |
|---|---|---|---|---|
| [Your AI Product Needs Evals](https://hamel.dev/blog/posts/evals/) + [LLM Evals FAQ](https://hamel.dev/blog/posts/evals-faq/) | Hamel Husain | Articles | P | The canonical starting point for eval discipline |
| [A Field Guide to Rapidly Improving AI Products](https://hamel.dev/blog/posts/field-guide/) | Hamel Husain | Article | P | The best piece on *improving* a shipped AI product: error analysis + data flywheels |
| [Task-Specific LLM Evals that Do & Don't Work](https://eugeneyan.com/writing/evals/) + [Evaluating LLM-Evaluators](https://eugeneyan.com/writing/llm-evaluators/) | Eugene Yan | Articles | P | Where LLM-as-judge helps and where it misleads |
| [Who Validates the Validators?](https://arxiv.org/abs/2404.12272) + [Data Flywheels for LLM Applications](https://www.sh-reya.com/blog/ai-engineering-flywheel/) | Shreya Shankar | Paper + article | A | Aligning LLM judges with human preferences |
| [Judging LLM-as-a-Judge (MT-Bench)](https://arxiv.org/abs/2306.05685) | Zheng et al. | Paper | A | The foundational LLM-judge paper — biases, agreement rates, position effects |
| [Inspect AI](https://inspect.aisi.org.uk/) | UK AI Safety Institute | Framework | A | Open-source eval framework used in frontier safety work |
| [AI Evals for Engineers & PMs course](https://maven.com/parlance-labs/evals) | Husain & Shankar | Course | P | The most respected paid eval course |

### RAG & retrieval infrastructure

| Resource | Author / Source | Type | Lvl | Why it's in the arsenal |
|---|---|---|---|---|
| [Systematically Improving RAG](https://jxnl.co/writing/2024/05/22/systematically-improving-your-rag/) | Jason Liu | Article | P | The disciplined iteration playbook: evals → metadata → feedback loops |
| [Introducing Contextual Retrieval](https://www.anthropic.com/news/contextual-retrieval) | Anthropic | Whitepaper | P | Prompt-cached contextual chunking with measured quality gains |
| [GraphRAG](https://arxiv.org/abs/2404.16130) | Microsoft Research | Paper | A | The knowledge-graph RAG reference |
| [MTEB Leaderboard](https://huggingface.co/spaces/mteb/leaderboard) | Hugging Face | Leaderboard | P | How to actually pick an embedding model by task |
| [Building Production Text-to-SQL for 70,000+ Tables](https://pub.towardsai.net/building-production-text-to-sql-for-70-000-tables-openais-data-agent-architecture-bcd695990d55) | OpenAI (via Towards AI) | Case study | A | The data-agent architecture pattern: context richness beats model choice |
| [Introduction to Information Retrieval](https://nlp.stanford.edu/IR-book/information-retrieval-book.html) | Manning et al. | Book (free) | A | The IR backbone under all RAG |

### Fine-tuning, post-training & dataset engineering

| Resource | Author / Source | Type | Lvl | Why it's in the arsenal |
|---|---|---|---|---|
| [How to Fine-Tune LLMs in 2025 with Hugging Face](https://www.philschmid.de/fine-tune-llms-in-2025) | Philipp Schmid | Tutorial | P | The single best modern how-to (QLoRA, TRL, Flash Attention) |
| [LoRA](https://arxiv.org/abs/2106.09685) · [QLoRA](https://arxiv.org/abs/2305.14314) · [DPO](https://arxiv.org/abs/2305.18290) · [InstructGPT](https://arxiv.org/abs/2203.02155) | Various | Papers | A | The four post-training papers a senior should have actually read |
| [The Llama 3 Herd of Models](https://arxiv.org/abs/2407.21783) | Meta | Paper | A | The synthetic-data generation and verification sections are gold |
| [The RLHF Book](https://rlhfbook.com/) + [Interconnects](https://www.interconnects.ai/) | Nathan Lambert | Book + newsletter | A | The clearest writer alive on post-training, RLHF, and reasoning models |
| [Best Practices and Lessons on Synthetic Data](https://arxiv.org/abs/2404.07503) | DeepMind | Paper | A | The synthetic-data reference survey |
| [Hugging Face smol course](https://huggingface.co/learn/smol-course/) + [PEFT docs](https://huggingface.co/docs/peft/) | Hugging Face | Course/docs | P | Free hands-on path to actually running a fine-tune |

### Inference, serving & self-hosting

| Resource | Author / Source | Type | Lvl | Why it's in the arsenal |
|---|---|---|---|---|
| [LLM Inference Handbook](https://bentoml.com/llm/) | BentoML | Free handbook | P | The best single resource on inference economics |
| [vLLM docs](https://docs.vllm.ai/) | UC Berkeley / vLLM | Docs | P | De-facto standard for self-hosting; PagedAttention, continuous batching |
| [Transformer Inference Arithmetic](https://kipp.ly/transformer-inference-arithmetic/) | kipply | Article | A | Napkin math for latency/throughput — how seniors size deployments |
| [Mastering LLM Techniques: Inference Optimization](https://developer.nvidia.com/blog/mastering-llm-techniques-inference-optimization/) | NVIDIA | Article | A | KV cache, quantization, speculative decoding, batching overview |
| [Optimizing AI Inference at Character.AI](https://research.character.ai/optimizing-inference/) | Character.AI | Case study | A | Extreme inference optimization at consumer scale |

### Security & safety

| Resource | Author / Source | Type | Lvl | Why it's in the arsenal |
|---|---|---|---|---|
| [OWASP Top 10 for Agentic Applications 2026](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/) | OWASP GenAI | Framework | P | ASI01–ASI10 — the vocabulary of every 2026 agent security review |
| [OWASP Top 10 for LLM Applications 2025](https://genai.owasp.org/resource/owasp-top-10-for-llm-applications-2025/) | OWASP GenAI | Framework | P | The LLM-level companion list |
| [The Lethal Trifecta](https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/) + [Prompt Injection Design Patterns](https://simonwillison.net/2025/Jun/13/prompt-injection-design-patterns/) | Simon Willison | Articles | P | The two mental models every agent builder must internalize |
| [CaMeL: Defeating Prompt Injections by Design](https://arxiv.org/abs/2503.18813) | Google DeepMind | Paper | A | The strongest principled research direction on injection defense |
| [Embrace The Red](https://embracethered.com/blog/) | Johann Rehberger | Blog | A | Ongoing real-world agent exploit write-ups |
| [The Instruction Hierarchy](https://arxiv.org/abs/2404.13208) | OpenAI | Paper | A | How models are trained to prioritize privileged instructions |
| [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework) | NIST | Framework | P | The governance reference enterprises ask about |

### Prompt optimization & emerging

| Resource | Author / Source | Type | Lvl | Why it's in the arsenal |
|---|---|---|---|---|
| [DSPy](https://dspy.ai/) | Omar Khattab / Stanford | Framework + tutorials | A | Prompts as compiled programs optimized against your eval set |
| [GEPA: Reflective Prompt Evolution](https://arxiv.org/abs/2507.19457) | Agrawal et al. | Paper | A | The 2025 optimizer that beat RL fine-tuning on several tasks |
| [SWE-Bench](https://arxiv.org/abs/2310.06770) + [τ-Bench](https://arxiv.org/abs/2406.12045) | Princeton / Sierra | Papers | A | The two agent benchmarks worth understanding deeply |

### Staying current

| Resource | Author / Source | Type | Why it's in the arsenal |
|---|---|---|---|
| [Simon Willison's blog](https://simonwillison.net/) | Simon Willison | Blog (near-daily) | The single most useful blog in the space |
| [Latent Space](https://www.latent.space/) | swyx & Alessio | Newsletter + podcast | The AI-engineer zeitgeist; annual reading-list updates |
| [Interconnects](https://www.interconnects.ai/) | Nathan Lambert | Newsletter | Post-training and reasoning models with research-grade clarity |
| [Ahead of AI](https://magazine.sebastianraschka.com/) | Sebastian Raschka | Newsletter | Monthly technical deep dives on LLM research |
| [Import AI](https://importai.substack.com/) | Jack Clark | Newsletter | Research + policy signal from an Anthropic co-founder |
| [State of AI Report](https://www.stateof.ai/) | Benaich et al. | Annual report | The yearly comprehensive skim |
| [Eugene Yan](https://eugeneyan.com/) · [Hamel Husain](https://hamel.dev/) · [Shreya Shankar](https://www.sh-reya.com/blog/) · [Jason Liu](https://jxnl.co/) | — | Blogs | The four practitioner blogs generating most eval/RAG/data wisdom |

## Part 2 — Agent-platform builder arsenal

Companion to the [agent platform gap analysis](gap-analysis-agent-platform.md): everything needed to build an all-in-one platform where users create composed, tool-equipped agents from a UI.

### Google ADK & Gemini Enterprise Agent Platform

| Resource | Source | Type | Lvl | Why it's in the arsenal |
|---|---|---|---|---|
| [ADK Agent Config](https://google.github.io/adk-docs/agents/config/) + [Agent Config YAML schema](https://google.github.io/adk-docs/api-reference/agentconfig/) | Google ADK | Docs | P | Declarative agents-as-YAML — the substrate of any UI-driven agent platform |
| [ADK Visual Builder](https://github.com/google/adk-docs/blob/main/docs/visual-builder/index.md) | Google ADK | Docs | P | The in-`adk web` drag-drop builder (≥1.18) with AI assistant that generates Agent Config — the exact product shape, shipped |
| [Gemini Enterprise Agent Platform](https://cloud.google.com/products/gemini-enterprise-agent-platform) | Google Cloud | Product docs | P | The reference all-in-one platform: ADK + Agent Studio + Agent Garden + Model Garden + Agent Engine + governance |
| [Agent Engine / Agent Runtime docs](https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/develop/adk) | Google Cloud | Docs | P | Managed runtime anatomy: Sessions, Memory Bank, Example Store, Evaluation Service, Code Execution, Computer Use |
| [Memory Bank quickstart with ADK](https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/memory-bank/quickstart-adk) | Google Cloud | Tutorial | P | The managed long-term-memory path (`PreloadMemoryTool`, callback persistence) |
| [adk-samples](https://github.com/google/adk-samples) + [Agent Starter Pack](https://github.com/GoogleCloudPlatform/agent-starter-pack) | Google | Repos | P | Reference implementations and production scaffolding for ADK agents |
| [A2A protocol](https://a2a-protocol.org/) | Google / Linux Foundation | Spec | P | Agent-to-agent interop — how platform agents talk to external agents |
| [Vertex AI Agent Builder 2026 guide](https://uibakery.io/blog/vertex-ai-agent-builder) | UI Bakery | Analysis | F | The best third-party map of Google's platform components and pricing |
| [Agent Patterns Catalog — Vertex AI Agent Builder](https://www.agentpatternscatalog.org/compositions/vertex-ai-agent-builder/) | Agent Patterns Catalog | Reference | P | Platform decomposition into build/scale/govern pillars with loop-shape analysis |

### Competing platforms & strategy

| Resource | Source | Type | Lvl | Why it's in the arsenal |
|---|---|---|---|---|
| [Amazon Bedrock AgentCore](https://aws.amazon.com/bedrock/agentcore/) | AWS | Product docs | P | The "own the substrate, stay framework-neutral" bet: managed runtime, gateway, identity, memory for any framework |
| [OpenAI AgentKit vs LangGraph: why the visual builder got deprecated first](https://dreaming.press/posts/openai-agentkit-vs-langgraph.html) | dreaming.press | Post-mortem | P | The cautionary tale: OpenAI's hosted canvas got a shutdown date in 8 months; substrate outlives canvas |
| [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/) | OpenAI | Docs | P | Provider-agnostic code-first SDK (drives 100+ models via LiteLLM) — the migration target off AgentKit |
| [Dify](https://docs.dify.ai/) | Dify | Docs + OSS | P | The most production-shaped OSS reference: app types, hosted chat UI per agent, RAG datasets, workspaces, ops console |
| [Langflow](https://docs.langflow.org/) · [Flowise](https://docs.flowiseai.com/) · [n8n](https://docs.n8n.io/) | Various | Docs + OSS | F–P | The visual-builder trio; study their canvas UX, component models, and licensing traps (n8n Sustainable Use vs MIT/Apache) |
| [Visual AI agent builders in 2026: Langflow vs Dify vs n8n](https://1337skills.com/blog/2026-05-30-visual-ai-agent-builders-langflow-dify-n8n/) | 1337skills | Comparison | F | Architecture/retrieval/governance/cost comparison across the three mental models |
| [LangGraph Platform](https://docs.langchain.com/langgraph-platform) | LangChain | Docs | P | The code-first control-plane alternative: deployment, state, cron, assistants API |
| [AI agent frameworks in 2026: the complete guide](https://stacksandflows.com/ai-agent-frameworks/) | Stacks & Flows | Comparison | F | Framework-selection judgment across LangChain/CrewAI/AutoGen/OpenAI SDK/Dify |

### Meta-agents, tool registries & auto tool creation

| Resource | Source | Type | Lvl | Why it's in the arsenal |
|---|---|---|---|---|
| [MetaChain: fully-automated zero-code LLM agent framework](https://arxiv.org/abs/2502.05957) | Tang et al. | Paper | A | "Agent-creating agents": NL → multi-agent construction + orchestrator generation — the goal-to-agent compiler blueprint |
| [NexA4A (Agent for Agent)](https://github.com/nex-agi/NexA4A) | Nex AGI | OSS repo | A | Working meta-agent: requirement analysis → tool selection from catalog → custom tool generation with tests → agent registry |
| [MetaAgent: learning-by-doing agents](https://github.com/qhjqhj00/MetaAgent) | Zhou et al. | OSS repo + paper | A | Meta tool learning: tool router, self-reflection, autonomous in-house tool building without retraining |
| [Dynamic tool creation for autonomous agents](https://medium.com/google-cloud/empowering-autonomous-ai-agents-through-dynamic-tool-creation-550683f255a4) | Google Cloud (Medium) | Article | A | Tool Space Interference (~20-tool soft limit), synthesize-test-execute in a least-privilege sandbox |
| [Meta-tools and agents reference](https://github.com/madhurprash/meta-tools-and-agents) | madhurprash | OSS repo | A | LangGraph workflow: semantic tool search → dynamic registration → tool synthesis fallback |
| [MCP Registry](https://github.com/modelcontextprotocol/registry) | MCP project | Spec + OSS | P | The official tool/server discovery layer — the interop backbone of a platform tool catalog |
| [Code Execution with MCP](https://www.anthropic.com/engineering/code-execution-with-mcp) | Anthropic | Whitepaper | A | Composing many MCP servers through code instead of context-saturating tool lists |

### Interop observability, evals & cost (AgentOps)

| Resource | Source | Type | Lvl | Why it's in the arsenal |
|---|---|---|---|---|
| [OpenTelemetry GenAI semantic conventions](https://opentelemetry.io/docs/specs/semconv/gen-ai/) | OTel GenAI SIG / CNCF | Spec | P | The 2026 interop standard: `gen_ai.*` spans across LLM/agent/workflow/MCP layers + the two mandatory metrics (duration, token usage) |
| [AI agent observability: the OpenTelemetry + Langfuse pattern](https://twistag.com/thinking/ai-agent-observability) | Twistag | Article | P | How emitting the standard makes every backend (Langfuse/Arize/Datadog/AgentCore) a config change, not a re-instrumentation |
| [Langfuse OTLP endpoint](https://langfuse.com/docs/opentelemetry/get-started) | Langfuse | Docs + OSS | P | Self-hostable OTel backend with cost derivation from token attributes |
| [Arize Phoenix](https://arize.com/docs/phoenix) + [OpenInference](https://github.com/Arize-ai/openinference) | Arize | Docs + OSS | P | The OTel-native open-source obs stack and its LLM trace conventions |
| [Braintrust](https://www.braintrust.dev/docs) · [LangSmith](https://docs.langchain.com/langsmith/home) · [Helicone](https://docs.helicone.ai/) | Various | Docs | P | Managed-SDK eval platforms and the proxy-gateway zero-code cost-tracking pattern |
| [AI agent observability 2026: tracing & monitoring stack](https://www.digitalapplied.com/blog/ai-agent-observability-2026-tracing-monitoring-stack-guide) | Digital Applied | Guide | P | Backend selection by deployment model (self-hosted vs managed SDK vs proxy gateway) |
| [MLflow GenAI / tracing](https://mlflow.org/docs/latest/genai/) | MLflow | Docs | P | The experiment-ledger layer already in the curriculum — now as one pluggable backend among several |

### Platform security & governance

| Resource | Source | Type | Lvl | Why it's in the arsenal |
|---|---|---|---|---|
| [OWASP Top 10 for Agentic Applications 2026](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/) | OWASP GenAI | Framework | P | ASI04 (agentic supply chain) and ASI05 (unexpected code execution) directly govern tool synthesis and shared agent galleries |
| [Model Armor](https://cloud.google.com/security-command-center/docs/model-armor-overview) | Google Cloud | Docs | P | Guardrails-as-managed-policy — the platform-feature shape for per-agent screening |
| [NVIDIA NeMo Guardrails](https://docs.nvidia.com/nemo/guardrails/latest/index.html) · [LlamaFirewall](https://meta-llama.github.io/PurpleLlama/LlamaFirewall/) | NVIDIA / Meta | OSS | P | Programmable, configurable guardrail engines suitable for tenant-selectable policy packs |
| [MCP prompt-injection security problems](https://simonwillison.net/2025/Apr/9/mcp-prompt-injection/) | Simon Willison | Article | P | Read before wiring any third-party MCP server into the platform tool catalog |

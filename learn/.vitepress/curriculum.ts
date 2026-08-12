export interface LessonRef {
  n: number
  slug: string
  title: string
  shipped: boolean
}

export interface Pack {
  slug: string
  letter: string
  title: string
  summary: string
  lessons: LessonRef[]
}

export const packs: Pack[] = [
  {
    slug: 'a',
    letter: 'A',
    title: 'Foundations → Control',
    summary:
      'Frame Meridian tickets, stand up ADK, then lock instructions, tools, multi-agent routing, memory, and safety.',
    lessons: [
      { n: 1, slug: '01-agentic-foundations', title: 'Agentic foundations', shipped: true },
      { n: 2, slug: '02-adk-environment', title: 'ADK environment & loop', shipped: true },
      { n: 3, slug: '03-core-building-blocks', title: 'Core building blocks', shipped: true },
      { n: 4, slug: '04-tools-mastery', title: 'Tools deep mastery', shipped: true },
      { n: 5, slug: '05-multi-agent-orchestration', title: 'Multi-agent orchestration', shipped: true },
      { n: 6, slug: '06-context-memory-knowledge', title: 'Context, memory, knowledge', shipped: true },
      { n: 7, slug: '07-reliability-safety-control', title: 'Reliability, safety, control', shipped: true },
    ],
  },
  {
    slug: 'b',
    letter: 'B',
    title: 'Eval → Observability → Deploy',
    summary:
      'Prove trajectories with evals and judges, ledger them in MLflow, trace incidents, then ship a container.',
    lessons: [
      { n: 8, slug: '08-testing-evaluation', title: 'Testing & evaluation', shipped: true },
      { n: 9, slug: '09-judges-thinking-extraction', title: 'Judges & thinking extraction', shipped: true },
      { n: 10, slug: '10-mlflow-agentic', title: 'MLflow for agentic systems', shipped: true },
      { n: 11, slug: '11-tracing-observability', title: 'Tracing & observability', shipped: true },
      { n: 12, slug: '12-deployment-ops', title: 'Deployment & ops', shipped: true },
    ],
  },
  {
    slug: 'ops',
    letter: 'Ops',
    title: 'Release train & resilience',
    summary:
      'After Pack B: CI/canary/rollback, then chaos, DR, and feature flags. Suggested path 12 → 41 → 32.',
    lessons: [
      { n: 41, slug: '41-cicd-sre-deployment-ops', title: 'CI/CD, canary, rollback & on-call', shipped: true },
      { n: 32, slug: '32-chaos-dr-feature-flags', title: 'Chaos, DR & feature flags', shipped: true },
    ],
  },
  {
    slug: 'c',
    letter: 'C',
    title: 'Orchestration depth & ecosystems',
    summary:
      'Graphs, fan-out, HITL resume, MCP tool servers, and event-driven A2A — still on native ADK.',
    lessons: [
      { n: 13, slug: '13-graph-workflows', title: 'ADK graph workflows', shipped: true },
      { n: 14, slug: '14-parallel-loop-custom-agents', title: 'Parallel, loop & custom agents', shipped: true },
      { n: 15, slug: '15-long-running-hitl-resume', title: 'Long-running & HITL resume', shipped: true },
      { n: 16, slug: '16-mcp-tool-ecosystems', title: 'MCP & tool ecosystems', shipped: true },
      { n: 17, slug: '17-event-driven-a2a', title: 'Event-driven & A2A', shipped: true },
    ],
  },
  {
    slug: 'd',
    letter: 'D',
    title: 'Knowledge, models, multimodal',
    summary:
      'Retail policy RAG, memory write policy, Flash/Pro routing, POD vision, and streaming store-ops UX.',
    lessons: [
      { n: 18, slug: '18-advanced-rag-retail-policy', title: 'Advanced RAG for retail policy', shipped: true },
      { n: 19, slug: '19-memory-systems-deep-dive', title: 'Memory systems deep dive', shipped: true },
      { n: 20, slug: '20-model-routing-fallbacks-structured-output', title: 'Model routing & structured output', shipped: true },
      { n: 21, slug: '21-multimodal-orderops', title: 'Multimodal OrderOps', shipped: true },
      { n: 22, slug: '22-streaming-ux-progressive-responses', title: 'Streaming UX', shipped: true },
    ],
  },
  {
    slug: 'e',
    letter: 'E',
    title: 'Quality at scale & hard security',
    summary:
      'Red team, online eval, canary prompts, plugin middleware, privacy/retention — then the RAI bonus.',
    lessons: [
      { n: 23, slug: '23-red-teaming-adversarial-robustness', title: 'Red teaming & adversarial robustness', shipped: true },
      { n: 24, slug: '24-online-monitoring-continuous-eval', title: 'Online monitoring & continuous eval', shipped: true },
      { n: 25, slug: '25-human-feedback-canary-prompts', title: 'Human feedback & canary prompts', shipped: true },
      { n: 26, slug: '26-plugins-callbacks-policy-middleware', title: 'Plugins, callbacks & policy middleware', shipped: true },
      { n: 27, slug: '27-privacy-retention-compliance', title: 'Privacy, retention & compliance', shipped: true },
      { n: 42, slug: '42-responsible-ai-champion', title: 'Responsible AI champion', shipped: true },
    ],
  },
  {
    slug: 'f',
    letter: 'F',
    title: 'Platform engineering',
    summary:
      'Architecture catalog, sessions at scale, multi-tenant isolation, FinOps. Chaos/DR already ships as lesson 32.',
    lessons: [
      { n: 28, slug: '28-architecture-catalog', title: 'Architecture patterns catalog', shipped: false },
      { n: 29, slug: '29-sessions-at-scale', title: 'Sessions & state at scale', shipped: false },
      { n: 30, slug: '30-multi-tenant', title: 'Multi-tenant agent platforms', shipped: false },
      { n: 31, slug: '31-finops', title: 'FinOps for agents', shipped: false },
    ],
  },
  {
    slug: 'g',
    letter: 'G',
    title: 'Productize & prove SME',
    summary:
      'Teaching, enterprise glue, dynamic agent creation, governance, then the capstone trilogy.',
    lessons: [
      { n: 33, slug: '33-sme-teams-teaching', title: 'SME judgment, teams & teaching', shipped: false },
      { n: 34, slug: '34-enterprise-integrations', title: 'Enterprise integrations', shipped: false },
      { n: 35, slug: '35-dynamic-agent-platform-i', title: 'Dynamic Agent Creation Platform I', shipped: false },
      { n: 36, slug: '36-dynamic-agent-platform-ii', title: 'Dynamic Agent Creation Platform II', shipped: false },
      { n: 37, slug: '37-governance-marketplace', title: 'Governance & agent marketplace', shipped: false },
      { n: 38, slug: '38-capstone-design', title: 'Capstone I — Design', shipped: false },
      { n: 39, slug: '39-capstone-ship', title: 'Capstone II — Ship & incident', shipped: false },
      { n: 40, slug: '40-capstone-mentor', title: 'Capstone III — Mentor & defense', shipped: false },
    ],
  },
]

export const shippedLessons: LessonRef[] = packs.flatMap((p) =>
  p.lessons.filter((l) => l.shipped),
)

export function packForLesson(n: number): Pack | undefined {
  return packs.find((p) => p.lessons.some((l) => l.n === n))
}

export function lessonBySlug(slug: string): LessonRef | undefined {
  return packs.flatMap((p) => p.lessons).find((l) => l.slug === slug)
}

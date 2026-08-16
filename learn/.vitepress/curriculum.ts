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
      'Architecture catalog, sessions at scale, multi-tenant isolation, FinOps, chaos/DR, then SLOs and an LLM access layer.',
    lessons: [
      { n: 28, slug: '28-architecture-catalog', title: 'Architecture patterns catalog', shipped: true },
      { n: 29, slug: '29-sessions-at-scale', title: 'Sessions & state at scale', shipped: true },
      { n: 30, slug: '30-multi-tenant', title: 'Multi-tenant agent platforms', shipped: true },
      { n: 31, slug: '31-finops', title: 'FinOps for agents', shipped: true },
      { n: 32, slug: '32-chaos-dr-feature-flags', title: 'Chaos, DR & feature flags', shipped: true },
      { n: 43, slug: '43-slos-capacity-backpressure', title: 'SLOs, capacity & backpressure', shipped: true },
      { n: 44, slug: '44-llm-gateway-cache-quotas', title: 'LLM gateway, cache & quotas', shipped: true },
    ],
  },
  {
    slug: 'g',
    letter: 'G',
    title: 'Productize & prove SME',
    summary:
      'Teaching, enterprise glue, dynamic agent creation, governance, the frontier surfaces (voice, identity, mandates, computer use, code exec, simulation, context), then the capstone trilogy.',
    lessons: [
      { n: 33, slug: '33-sme-teams-teaching', title: 'SME judgment, teams & teaching', shipped: false },
      { n: 34, slug: '34-enterprise-integrations', title: 'Enterprise integrations', shipped: false },
      { n: 35, slug: '35-dynamic-agent-platform-i', title: 'Dynamic Agent Creation Platform I', shipped: false },
      { n: 36, slug: '36-dynamic-agent-platform-ii', title: 'Dynamic Agent Creation Platform II', shipped: false },
      { n: 37, slug: '37-governance-marketplace', title: 'Governance & agent marketplace', shipped: false },
      { n: 45, slug: '45-voice-bidi-streaming', title: 'Voice & bidirectional streaming', shipped: true },
      { n: 46, slug: '46-agent-identity-delegated-auth', title: 'Agent identity & delegated auth', shipped: true },
      { n: 47, slug: '47-agentic-commerce-mandates', title: 'Agentic commerce & payment mandates', shipped: true },
      { n: 48, slug: '48-computer-use-browser-agents', title: 'Computer use & browser agents', shipped: true },
      { n: 49, slug: '49-sandboxed-code-execution', title: 'Sandboxed code execution', shipped: true },
      { n: 50, slug: '50-simulated-users-multiturn-eval', title: 'Simulated users & multi-turn eval', shipped: true },
      { n: 51, slug: '51-context-engineering-audit', title: 'Context engineering & context audit', shipped: true },
      { n: 38, slug: '38-capstone-design', title: 'Capstone I — Design', shipped: false },
      { n: 39, slug: '39-capstone-ship', title: 'Capstone II — Ship & incident', shipped: false },
      { n: 40, slug: '40-capstone-mentor', title: 'Capstone III — Mentor & defense', shipped: false },
    ],
  },
  {
    slug: 'm0',
    letter: 'M0',
    title: 'Bonus ML — numbers and plots',
    summary:
      'Optional CPU track. Start with slope, vectors, and “how wrong” — no linear algebra assumed. Not Native ADK.',
    lessons: [
      { n: 200, slug: 'ml-00-what-a-model-is', title: 'What a model even is', shipped: true },
      { n: 201, slug: 'ml-01-functions-slope-intercept', title: 'Functions, slope, intercept', shipped: true },
      { n: 202, slug: 'ml-02-vectors-as-feature-lists', title: 'Vectors as feature lists', shipped: true },
      { n: 203, slug: 'ml-03-dot-product-weighted-mix', title: 'Dot product as a weighted mix', shipped: true },
      { n: 204, slug: 'ml-04-tables-as-matrices', title: 'Tables as matrices', shipped: true },
      { n: 205, slug: 'ml-05-error-and-nudge', title: 'Error, mean, and nudge the knob', shipped: true },
    ],
  },
  {
    slug: 'm1',
    letter: 'M1',
    title: 'Bonus ML — data hygiene',
    summary: 'Splits, leakage, scaling, plots that lie, bias vs variance — still Maya’s tickets.',
    lessons: [
      { n: 206, slug: 'ml-06-train-val-test', title: 'Train, val, test', shipped: true },
      { n: 207, slug: 'ml-07-leakage', title: 'Leakage', shipped: true },
      { n: 208, slug: 'ml-08-scaling-lying-plots', title: 'Scaling and lying plots', shipped: true },
      { n: 209, slug: 'ml-09-bias-variance', title: 'Bias vs variance', shipped: true },
    ],
  },
  {
    slug: 'm2',
    letter: 'M2',
    title: 'Bonus ML — linear regression',
    summary: 'One feature, many features, a bend, and L2 as “don’t trust giant weights.”',
    lessons: [
      { n: 210, slug: 'ml-10-one-feature-regression', title: 'One-feature regression', shipped: true },
      { n: 211, slug: 'ml-11-many-features', title: 'Many features', shipped: true },
      { n: 212, slug: 'ml-12-polynomial-bend', title: 'Polynomial bend', shipped: true },
      { n: 213, slug: 'ml-13-l2-regularization', title: 'L2 regularization', shipped: true },
    ],
  },
  {
    slug: 'm3',
    letter: 'M3',
    title: 'Bonus ML — classification',
    summary: 'Logistic squash, boundaries, confusion, trees, imbalance — refund vs not.',
    lessons: [
      { n: 214, slug: 'ml-14-logistic-squash', title: 'Logistic squash', shipped: true },
      { n: 215, slug: 'ml-15-decision-boundary', title: 'Decision boundary', shipped: true },
      { n: 216, slug: 'ml-16-confusion-precision-recall', title: 'Confusion, precision, recall', shipped: true },
      { n: 217, slug: 'ml-17-trees-forests', title: 'Trees and forests', shipped: true },
      { n: 218, slug: 'ml-18-class-imbalance', title: 'Class imbalance', shipped: true },
    ],
  },
  {
    slug: 'm4',
    letter: 'M4',
    title: 'Bonus ML — unsupervised',
    summary: 'Cluster SKUs, rotate with PCA, flag a weird conveyor day.',
    lessons: [
      { n: 219, slug: 'ml-19-kmeans-skus', title: 'K-means SKUs', shipped: true },
      { n: 220, slug: 'ml-20-pca-rotate', title: 'PCA rotate', shipped: true },
      { n: 221, slug: 'ml-21-anomaly-scan-times', title: 'Anomaly scan times', shipped: true },
    ],
  },
  {
    slug: 'm5',
    letter: 'M5',
    title: 'Bonus ML — classical NLP',
    summary: 'Tokens, bags, TF-IDF, Bayes, nearby meaning — ticket intent without a neural net.',
    lessons: [
      { n: 222, slug: 'ml-22-tokens-vocab', title: 'Tokens and vocab', shipped: true },
      { n: 223, slug: 'ml-23-bag-of-words', title: 'Bag of words', shipped: true },
      { n: 224, slug: 'ml-24-tfidf-ngrams', title: 'TF-IDF and n-grams', shipped: true },
      { n: 225, slug: 'ml-25-naive-bayes-tickets', title: 'Naive Bayes tickets', shipped: true },
      { n: 226, slug: 'ml-26-word-vectors', title: 'Word vectors nearby meaning', shipped: true },
    ],
  },
  {
    slug: 'm6',
    letter: 'M6',
    title: 'Bonus ML — deep learning core',
    summary: 'Neuron, ReLU, backprop with four numbers, dropout, a tiny net on CPU.',
    lessons: [
      { n: 227, slug: 'ml-27-neuron-layer', title: 'Neuron and layer', shipped: true },
      { n: 228, slug: 'ml-28-relu-stacking', title: 'ReLU and stacking', shipped: true },
      { n: 229, slug: 'ml-29-backprop-four-numbers', title: 'Backprop four numbers', shipped: true },
      { n: 230, slug: 'ml-30-overfitting-dropout', title: 'Overfitting and dropout', shipped: true },
      { n: 231, slug: 'ml-31-numpy-net', title: 'Numpy net then PyTorch', shipped: true },
    ],
  },
  {
    slug: 'm7',
    letter: 'M7',
    title: 'Bonus ML — sequences and RNNs',
    summary: 'Order matters, unrolled RNN, LSTM gates, vanishing memory.',
    lessons: [
      { n: 232, slug: 'ml-32-order-matters', title: 'Order matters', shipped: true },
      { n: 233, slug: 'ml-33-rnn-unrolled', title: 'RNN unrolled', shipped: true },
      { n: 234, slug: 'ml-34-lstm-vanishing', title: 'LSTM and vanishing', shipped: true },
    ],
  },
  {
    slug: 'm8',
    letter: 'M8',
    title: 'Bonus ML — images',
    summary: 'Pixels, convolution as a stamp, pooling, dented vs intact boxes (synthetic).',
    lessons: [
      { n: 235, slug: 'ml-35-pixels-as-numbers', title: 'Pixels as numbers', shipped: true },
      { n: 236, slug: 'ml-36-convolution-stamp', title: 'Convolution stamp', shipped: true },
      { n: 237, slug: 'ml-37-pooling-aug', title: 'Pooling and augmentation', shipped: true },
      { n: 238, slug: 'ml-38-dented-box', title: 'Dented box project', shipped: true },
    ],
  },
  {
    slug: 'm9',
    letter: 'M9',
    title: 'Bonus ML — video on CPU',
    summary: 'Frames in time, sample every k, jam vs moving conveyor GIFs.',
    lessons: [
      { n: 239, slug: 'ml-39-video-is-frames', title: 'Video is frames', shipped: true },
      { n: 240, slug: 'ml-40-sample-every-k', title: 'Sample every k', shipped: true },
      { n: 241, slug: 'ml-41-conveyor-jam', title: 'Conveyor jam', shipped: true },
    ],
  },
  {
    slug: 'm10',
    letter: 'M10',
    title: 'Bonus ML — attention and transformers',
    summary: 'Who to look at, QKV notebooks, positions, a tiny transformer on CPU.',
    lessons: [
      { n: 242, slug: 'ml-42-attention-who', title: 'Attention who to look at', shipped: true },
      { n: 243, slug: 'ml-43-qkv-notebooks', title: 'QKV three notebooks', shipped: true },
      { n: 244, slug: 'ml-44-positions-encoder-decoder', title: 'Positions, encoder, decoder', shipped: true },
      { n: 245, slug: 'ml-45-tiny-transformer', title: 'Tiny transformer', shipped: true },
    ],
  },
  {
    slug: 'm11',
    letter: 'M11',
    title: 'Bonus ML — tiny GPT and you-bot',
    summary: 'Next token, temperature, fine-tune vs RAG, a local style chatbot. CPU-honest.',
    lessons: [
      { n: 246, slug: 'ml-46-next-token-temperature', title: 'Next token and temperature', shipped: true },
      { n: 247, slug: 'ml-47-finetune-prompt-rag', title: 'Fine-tune vs prompt vs RAG', shipped: true },
      { n: 248, slug: 'ml-48-tiny-gpt-cpu', title: 'Tiny GPT on CPU', shipped: true },
      { n: 249, slug: 'ml-49-you-bot', title: 'Chatbot that talks like you', shipped: true },
    ],
  },
  {
    slug: 'm12',
    letter: 'M12',
    title: 'Bonus ML — RL and capstone',
    summary: 'The five-world RL playground, Q vs neural policy, then a CPU Meridian slice.',
    lessons: [
      { n: 250, slug: 'bonus-rl-visual-playground', title: 'Watch a brain learn (5 worlds)', shipped: true },
      { n: 251, slug: 'ml-50-q-vs-neural-policy', title: 'Q-tables vs neural policies', shipped: true },
      { n: 252, slug: 'ml-51-meridian-cpu-capstone', title: 'Capstone — ticket + photo + delay', shipped: true },
    ],
  },
]

export const shippedLessons: LessonRef[] = packs.flatMap((p) =>
  p.lessons.filter((l) => l.shipped),
)

export const agentPacks: Pack[] = packs.filter((p) => !p.letter.startsWith('M'))
export const mlPacks: Pack[] = packs.filter((p) => p.letter.startsWith('M'))

export type LessonTrack = 'agents' | 'ml'

export function lessonTrack(slug: string): LessonTrack {
  if (slug.startsWith('ml-') || slug.startsWith('bonus-')) return 'ml'
  return 'agents'
}

/** Short code shown in nav, tickets, and the catalog — never "Lesson 200". */
export function lessonCode(slug: string, n?: number): string {
  if (slug.startsWith('ml-')) {
    const m = slug.match(/^ml-(\d{2})/)
    return m ? `ml-${m[1]}` : slug.slice(0, 8)
  }
  if (slug.startsWith('bonus-')) return 'RL'
  if (n != null && Number.isFinite(n) && n < 200) return String(n).padStart(2, '0')
  const adk = slug.match(/^(\d{2})-/)
  return adk ? adk[1] : slug.slice(0, 8)
}

export function packForLesson(n: number): Pack | undefined {
  return packs.find((p) => p.lessons.some((l) => l.n === n))
}

export function lessonBySlug(slug: string): LessonRef | undefined {
  return packs.flatMap((p) => p.lessons).find((l) => l.slug === slug)
}

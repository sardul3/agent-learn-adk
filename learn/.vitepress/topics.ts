import { packs, lessonCode, lessonTrack, type LessonTrack } from './curriculum'

export interface CatalogEntry {
  slug: string
  title: string
  code: string
  pack: string
  packTitle: string
  track: LessonTrack
  haystack: string
  blurb: string
}

/** Extra search terms people type that the title might not contain. */
const KEYWORDS: Record<string, string> = {
  '01-agentic-foundations': 'agent llm tool hallucination temperature token workflow vs script hitl',
  '02-adk-environment': 'adk install gemini venv adk web developer loop',
  '03-core-building-blocks': 'llmagent instruction session state callback',
  '04-tools-mastery': 'function tool get_order refund schema idempotent',
  '05-multi-agent-orchestration': 'sub-agent router specialist transfer',
  '06-context-memory-knowledge': 'context window memory artifact transcript',
  '07-reliability-safety-control': 'guardrail allowlist confirmation safety',
  '08-testing-evaluation': 'eval golden trajectory agentevaluator pytest',
  '09-judges-thinking-extraction': 'judge scorer rubric thinking',
  '10-mlflow-agentic': 'mlflow experiment tracking metrics',
  '11-tracing-observability': 'trace span otel log correlation',
  '12-deployment-ops': 'docker smoke secrets runbook fastapi',
  '13-graph-workflows': 'workflow graph joinnode sequential',
  '14-parallel-loop-custom-agents': 'fan-out fan-in loop critic parallel',
  '15-long-running-hitl-resume': 'checkpoint pause resume human in the loop',
  '16-mcp-tool-ecosystems': 'mcp model context protocol toolset',
  '17-event-driven-a2a': 'webhook a2a agent to agent queue',
  '18-advanced-rag-retail-policy': 'rag retrieval embedding chunk hybrid citation policy',
  '19-memory-systems-deep-dive': 'memory write consolidation pii',
  '20-model-routing-fallbacks-structured-output': 'flash pro json schema fallback routing',
  '21-multimodal-orderops': 'vision photo image multimodal pod',
  '22-streaming-ux-progressive-responses': 'stream token partial ux',
  '23-red-teaming-adversarial-robustness': 'jailbreak injection red team attack',
  '24-online-monitoring-continuous-eval': 'online eval production sampling',
  '25-human-feedback-canary-prompts': 'feedback canary prompt rollback',
  '26-plugins-callbacks-policy-middleware': 'plugin callback middleware policy',
  '27-privacy-retention-compliance': 'privacy gdpr retention redaction',
  '28-architecture-catalog': 'router planner critic pattern catalog',
  '29-sessions-at-scale': 'redis session stickiness replay',
  '30-multi-tenant': 'tenant isolation quota',
  '31-finops': 'cost budget tokens chargeback',
  '32-chaos-dr-feature-flags': 'chaos disaster recovery feature flag',
  '41-cicd-sre-deployment-ops': 'ci cd canary rollback on-call',
  '42-responsible-ai-champion': 'responsible ai rai fairness scorecard',
  '43-slos-capacity-backpressure': 'slo latency capacity backpressure',
  '44-llm-gateway-cache-quotas': 'gateway cache quota rate limit',
  '45-voice-bidi-streaming': 'voice audio live barge-in speech',
  '46-agent-identity-delegated-auth': 'oauth identity confused deputy auth',
  '47-agentic-commerce-mandates': 'payment mandate ap2 cart checkout',
  '48-computer-use-browser-agents': 'browser computer use screenshot click',
  '49-sandboxed-code-execution': 'sandbox code exec escape',
  '50-simulated-users-multiturn-eval': 'simulated user persona multi-turn',
  '51-context-engineering-audit': 'context engineering compaction cache',
  'ml-00-what-a-model-is': 'model recipe input output guess error ai basics',
  'ml-01-functions-slope-intercept': 'slope intercept line function linear',
  'ml-02-vectors-as-feature-lists': 'vector add scale arrow feature',
  'ml-03-dot-product-weighted-mix': 'dot product weights mix @',
  'ml-04-tables-as-matrices': 'matrix heatmap table shape',
  'ml-05-error-and-nudge': 'mse loss gradient descent learning rate train line',
  'ml-06-train-val-test': 'train test validation split exam leak homework',
  'ml-07-leakage': 'leakage cheat answer sheet target leak',
  'ml-08-scaling-lying-plots': 'standard scaler normalize feature scale',
  'ml-09-bias-variance': 'overfit underfit bias variance polynomial',
  'ml-10-one-feature-regression': 'linear regression sklearn least squares',
  'ml-11-many-features': 'multiple regression residual',
  'ml-12-polynomial-bend': 'polynomial features curve bend',
  'ml-13-l2-regularization': 'ridge l2 regularize weight decay alpha',
  'ml-14-logistic-squash': 'logistic sigmoid classification probability',
  'ml-15-decision-boundary': 'decision boundary fence contour',
  'ml-16-confusion-precision-recall': 'confusion matrix precision recall fp fn',
  'ml-17-trees-forests': 'decision tree random forest importance',
  'ml-18-class-imbalance': 'imbalance class weight accuracy trap rare',
  'ml-19-kmeans-skus': 'kmeans cluster unsupervised',
  'ml-20-pca-rotate': 'pca principal component dimensionality',
  'ml-21-anomaly-scan-times': 'anomaly outlier isolation forest',
  'ml-22-tokens-vocab': 'token vocabulary tokenizer nlp',
  'ml-23-bag-of-words': 'bag of words countvectorizer bow',
  'ml-24-tfidf-ngrams': 'tfidf ngram bigram idf',
  'ml-25-naive-bayes-tickets': 'naive bayes intent classify nlp',
  'ml-26-word-vectors': 'word2vec embedding co-occurrence meaning',
  'ml-27-neuron-layer': 'neuron relu sigmoid layer perceptron',
  'ml-28-relu-stacking': 'deep learning hidden layer stack mlp',
  'ml-29-backprop-four-numbers': 'backpropagation chain rule gradient',
  'ml-30-overfitting-dropout': 'dropout early stopping memorize',
  'ml-31-numpy-net': 'pytorch numpy neural net sgd cpu',
  'ml-32-order-matters': 'sequence order bag fail rnn transformer why',
  'ml-33-rnn-unrolled': 'rnn recurrent hidden state unroll',
  'ml-34-lstm-vanishing': 'lstm vanishing gradient gates forget',
  'ml-35-pixels-as-numbers': 'pixel image matrix vision',
  'ml-36-convolution-stamp': 'cnn convolution kernel filter stamp',
  'ml-37-pooling-aug': 'max pool augmentation shift',
  'ml-38-dented-box': 'image classify dent cnn project',
  'ml-39-video-is-frames': 'video frames clip',
  'ml-40-sample-every-k': 'fps subsample frame skip',
  'ml-41-conveyor-jam': 'motion detect jam video diff',
  'ml-42-attention-who': 'attention softmax self-attention',
  'ml-43-qkv-notebooks': 'query key value qkv scaled dot product',
  'ml-44-positions-encoder-decoder': 'positional encoding encoder decoder rope',
  'ml-45-tiny-transformer': 'transformer gpt next token bigram',
  'ml-46-next-token-temperature': 'temperature softmax logits sampling greedy',
  'ml-47-finetune-prompt-rag': 'finetune prompt rag when to use',
  'ml-48-tiny-gpt-cpu': 'language model lm generate sample bigram',
  'ml-49-you-bot': 'chatbot style clone voice personal lm',
  'bonus-rl-visual-playground': 'reinforcement learning q-learning agent reward exploration pygame',
  'ml-50-q-vs-neural-policy': 'q table deep rl policy network',
  'ml-51-meridian-cpu-capstone': 'capstone compose intent photo delay',
}

export const POPULAR = [
  'RAG',
  'gradient',
  'attention',
  'leakage',
  'eval',
  'tools',
  'Q-learning',
  'transformer',
  'precision',
  'dropout',
  'backprop',
  'temperature',
] as const

export function catalog(): CatalogEntry[] {
  const rows: CatalogEntry[] = []
  for (const pack of packs) {
    for (const lesson of pack.lessons) {
      if (!lesson.shipped) continue
      const extra = KEYWORDS[lesson.slug] ?? ''
      rows.push({
        slug: lesson.slug,
        title: lesson.title,
        code: lessonCode(lesson.slug, lesson.n),
        pack: pack.letter,
        packTitle: pack.title.replace(/^Bonus ML — /, ''),
        track: lessonTrack(lesson.slug),
        blurb: pack.summary,
        haystack: `${lesson.slug} ${lesson.title} ${pack.letter} ${pack.title} ${pack.summary} ${extra}`.toLowerCase(),
      })
    }
  }
  return rows
}

export function filterCatalog(
  entries: CatalogEntry[],
  query: string,
  track: 'all' | LessonTrack,
): CatalogEntry[] {
  const q = query.trim().toLowerCase()
  return entries.filter((row) => {
    if (track !== 'all' && row.track !== track) return false
    if (!q) return true
    return q.split(/\s+/).every((word) => row.haystack.includes(word))
  })
}

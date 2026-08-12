# Lesson 18 — Advanced RAG for retail policy

**Level:** Advanced  
**Time:** ~120 minutes  
**Prerequisites:** Lessons 06, 08, 16 (retrieve tool, evals, tool contracts)  
**Lab outcome:** Replace keyword-only policy lookup with **chunk → embed → hybrid retrieve → cite**, and prove the agent refuses to invent policy when retrieval misses

**Standard:** [docs/NATIVE-ADK.md](../docs/NATIVE-ADK.md)

---

## At a glance

Lesson 06 taught the loop: **retrieve → reason → cite**.  
This lesson makes retrieval **production-shaped**:

| Piece | What you build |
|-------|----------------|
| Corpus | Versioned Meridian policy markdown (more docs, real conflicts) |
| Chunker | Split by heading / size so one clause does not drown another |
| Embeddings | Local vectors for semantic match (“melted ice cream” ≈ damaged dairy) |
| Hybrid rank | Keyword score + vector score (IDs and slang both work) |
| Citations | Policy id + version + section — or `NO_POLICY_HIT` |
| Agent | ADK `LlmAgent` + your retrieve tool (same tool contract as Lesson 06) |

**Allowed:** Meridian domain retriever code (chunk/embed/rank).  
**Optional later:** ADK `VertexAiRagRetrieval` when Meridian runs on Vertex RAG corpora — same agent loop, different backend.  
**Forbidden:** Dumping the whole wiki into the system prompt and calling it RAG.

---

## Why this matters

Maya chats:

> “Driver left groceries in 100° heat. Ice cream soup. Do I get a full refund?”

Keyword search on `"late"` misses **POL-REFUND-04** (damaged/melted).  
A giant prompt paste still invents “full order refunds are always OK under $100.”

You need:

1. Chunks small enough that the melted-item clause surfaces  
2. Vectors so paraphrases hit  
3. Citations so Priya can audit the answer  
4. A hard miss path so the agent says “I don’t know” instead of improvising

---

## Know these

| Term | Plain English | Meridian example |
|------|---------------|------------------|
| **Corpus** | The set of docs you trust | `fixtures/policies/*.md` |
| **Chunk** | A slice of a doc you index | “## Remedies” section of POL-REFUND-04 |
| **Embedding** | A number-vector that means “about the same topic” | “melted dairy” near “ice cream soup” |
| **Vector search** | Rank chunks by embedding similarity | Paraphrase queries |
| **Keyword / lexical** | Rank by shared words / IDs | Exact `POL-DELIVERY-01` or `$25` |
| **Hybrid retrieve** | Blend lexical + vector scores | IDs *and* slang both work |
| **Citation** | Pointer to evidence | `POL-REFUND-04 v2026-06-15 §Remedies` |
| **Grounding** | Claims tied to evidence | Answer quotes chunk + tool OMS facts |
| **NO_POLICY_HIT** | Honest miss | “No matching Meridian policy; escalate.” |

```
Ticket text
    │
    ▼
┌─────────┐   ┌──────────┐   ┌────────────┐
│ chunker │ → │ embedder │ → │ hybrid rank│ → top_k chunks
└─────────┘   └──────────┘   └────────────┘
                                      │
                                      ▼
                         ADK agent cites or refuses
```

---

## Task 1 — Grow the policy corpus (conflicts welcome)

### Why

Two docs taught the pattern. Real Meridian has overlapping rules. Retrieval must pick the *right* clause under conflict.

### Do this

Under `project/meridian_ops/fixtures/policies/`, ensure these exist (create any missing):

1. Keep `late_delivery_credits.md` (**POL-DELIVERY-01**) — expand Eligibility + Exclusions if thin.  
2. Keep / restore full `refunds_damaged_items.md` (**POL-REFUND-04**) from Lesson 06.  
3. Add `substitutions_bopis.md`:

```markdown
# POL-ATP-02 — BOPIS substitutions
Version: 2026-07-20
Owner: Store Ops Policy

## Eligibility
- Applies to Buy Online Pickup In Store (BOPIS), not same-day delivery.
- Customer must have opted in to substitutions in the app, OR store lead obtains verbal OK.

## Rules
- Prefer same brand / size within +20% price.
- Never substitute baby formula, Rx, or alcohol without explicit customer OK.
- If no acceptable sub: cancel line + notify; do not silent-omit.

## Agent rules
- Cite POL-ATP-02 for BOPIS sub questions.
- Delivery shortages use inventory playbooks — not this policy.
```

4. Add `goodwill_credits.md`:

```markdown
# POL-CX-09 — Goodwill credits (non-policy remedies)
Version: 2026-05-01
Owner: CX Policy

## When used
- Empathy gesture when no late/damage policy fits, OR stacking on top of policy credit.

## Caps
- Agent auto: max $5 without supervisor.
- Supervisor HITL: max $50 per order per 30 days.
- Never use goodwill to bypass refund HITL thresholds.

## Agent rules
- Always say this is goodwill, not a policy entitlement.
- Cite POL-CX-09 + whether HITL was required.
```

### Expect

Four versioned files with **stable policy ids**. You can open each and point to a section by eye.

> **Tip:** Policy ids are product contracts. Rename casually and every citation in prod logs goes stale.

---

## Task 2 — Chunk policies (heading-aware)

### Why

Whole-doc retrieve returns 800 tokens when you needed 80. The model then “summarizes” past the HITL line.

### Do this

Create `project/meridian_ops/tools/policy_chunker.py`:

```python
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PolicyChunk:
    policy_id: str
    version: str
    path: str
    section: str
    text: str
    chunk_id: str


_POLICY_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "policies"
_ID_RE = re.compile(r"^#\s+(POL-[A-Z0-9-]+)", re.M)
_VER_RE = re.compile(r"^Version:\s*(\S+)", re.M)


def chunk_markdown(path: Path) -> list[PolicyChunk]:
    raw = path.read_text()
    pid_m = _ID_RE.search(raw)
    ver_m = _VER_RE.search(raw)
    policy_id = pid_m.group(1) if pid_m else path.stem
    version = ver_m.group(1) if ver_m else "unknown"

    # Split on ## headings; keep preamble as "Overview"
    parts = re.split(r"(?m)^(##\s+.+)$", raw)
    chunks: list[PolicyChunk] = []
    if parts and parts[0].strip():
        chunks.append(
            PolicyChunk(
                policy_id=policy_id,
                version=version,
                path=path.name,
                section="Overview",
                text=parts[0].strip(),
                chunk_id=f"{policy_id}::Overview",
            )
        )
    i = 1
    while i + 1 < len(parts):
        heading = parts[i].lstrip("#").strip()
        body = parts[i + 1].strip()
        text = f"## {heading}\n{body}".strip()
        chunks.append(
            PolicyChunk(
                policy_id=policy_id,
                version=version,
                path=path.name,
                section=heading,
                text=text,
                chunk_id=f"{policy_id}::{heading}",
            )
        )
        i += 2
    return chunks


def load_all_chunks() -> list[PolicyChunk]:
    out: list[PolicyChunk] = []
    for path in sorted(_POLICY_DIR.glob("*.md")):
        out.extend(chunk_markdown(path))
    return out
```

Add a unit test that **POL-REFUND-04** produces a chunk whose section contains `Remedies` or `Agent rules`.

```bash
cd /Users/alishaghatane/dev/agent-learn-sme/project
export PYTHONPATH=.
pytest meridian_ops/tests/test_policy_chunker.py -q
```

### Expect

Multiple chunks per file. Section names match `##` headings.

> **Watch out:** Chunking only on fixed character length can split mid-bullet and orphan “require HITL.” Prefer headings for policy wiki.

---

## Task 3 — Local embeddings (no mysticism)

### Why

“Ice cream soup” never appears in the doc. Embeddings close the paraphrase gap without calling Vertex yet.

### Do this

Install a small local embedder (lab-friendly):

```bash
source .venv/bin/activate
pip install -U "sentence-transformers>=3.0.0"
```

Create `project/meridian_ops/tools/policy_embed.py`:

```python
from __future__ import annotations

from functools import lru_cache

import numpy as np


@lru_cache(maxsize=1)
def _model():
    from sentence_transformers import SentenceTransformer

    # Small, CPU-friendly; swap later without changing tool contract
    return SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


def embed_texts(texts: list[str]) -> np.ndarray:
    vecs = _model().encode(texts, normalize_embeddings=True)
    return np.asarray(vecs, dtype=np.float32)


def cosine_sim(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    # a: (d,), b: (n, d) — both L2-normalized → dot = cosine
    return b @ a
```

Index chunks once at process start (or rebuild in tests):

```python
# sketch used by the retriever
from meridian_ops.tools.policy_chunker import load_all_chunks
from meridian_ops.tools.policy_embed import embed_texts

CHUNKS = load_all_chunks()
MATRIX = embed_texts([c.text for c in CHUNKS])  # shape (n, d)
```

### Expect

`MATRIX.shape[0] == len(CHUNKS)`. Encoding “melted ice cream refund” yields a vector of the same dimension.

> **Tip:** Keep embedding **behind your tool**. Agents call `retrieve_policy_hybrid`; they never import SentenceTransformer.

---

## Task 4 — Hybrid retrieve tool (replace keyword-only)

### Why

IDs and dollar amounts need lexical match. Customer slang needs vectors. Hybrid is the default SME move.

### Do this

Upgrade / add `project/meridian_ops/tools/policy_rag.py` with a **stable tool name** the agent already knows — or add `retrieve_policy_hybrid` and point the agent at it.

```python
from __future__ import annotations

import re
from typing import Any

import numpy as np

from meridian_ops.tools.policy_chunker import PolicyChunk, load_all_chunks
from meridian_ops.tools.policy_embed import cosine_sim, embed_texts

_CHUNKS: list[PolicyChunk] | None = None
_MATRIX: np.ndarray | None = None


def _ensure_index() -> tuple[list[PolicyChunk], np.ndarray]:
    global _CHUNKS, _MATRIX
    if _CHUNKS is None or _MATRIX is None:
        _CHUNKS = load_all_chunks()
        _MATRIX = embed_texts([c.text for c in _CHUNKS])
    return _CHUNKS, _MATRIX


def _lexical_score(query: str, chunk: PolicyChunk) -> float:
    tokens = set(re.findall(r"[a-z0-9$+-]+", query.lower()))
    hay = f"{chunk.policy_id} {chunk.section} {chunk.text}".lower()
    overlap = sum(1 for t in tokens if t in hay)
    boost = 0.0
    if chunk.policy_id.lower() in query.lower():
        boost += 5.0
    if "bopis" in tokens and "bopis" in hay:
        boost += 3.0
    if any(t in tokens for t in ("melt", "melted", "damaged", "ice")) and (
        "melt" in hay or "damag" in hay
    ):
        boost += 3.0
    return float(overlap) + boost


def retrieve_policy_hybrid(query: str, top_k: int = 3) -> dict[str, Any]:
    """Hybrid policy retrieve: lexical + embedding similarity.

    Args:
        query: Ticket text or policy question.
        top_k: Max chunks to return.
    """
    chunks, matrix = _ensure_index()
    if not chunks:
        return {
            "status": "error",
            "error_code": "NO_POLICY_HIT",
            "message": "Empty policy corpus.",
        }

    q_vec = embed_texts([query])[0]
    vec_scores = cosine_sim(q_vec, matrix)  # (n,)
    lex_scores = np.array([_lexical_score(query, c) for c in chunks], dtype=np.float32)

    # Normalize lex to 0..1-ish for blending
    lex_norm = lex_scores / (lex_scores.max() + 1e-6)
    hybrid = 0.55 * vec_scores + 0.45 * lex_norm

    order = np.argsort(-hybrid)
    picked: list[dict[str, Any]] = []
    for idx in order[:top_k]:
        if hybrid[idx] < 0.15 and lex_scores[idx] <= 0:
            continue
        c = chunks[int(idx)]
        picked.append(
            {
                "chunk_id": c.chunk_id,
                "policy_id": c.policy_id,
                "version": c.version,
                "section": c.section,
                "path": c.path,
                "score": float(hybrid[idx]),
                "text": c.text,
            }
        )

    if not picked:
        return {
            "status": "error",
            "error_code": "NO_POLICY_HIT",
            "message": "No policy chunks matched; do not invent policy.",
        }

    return {"status": "success", "documents": picked}
```

Tests (must fail on inventing policy):

```python
from meridian_ops.tools.policy_rag import retrieve_policy_hybrid


def test_melted_paraphrase_hits_refund_policy():
    out = retrieve_policy_hybrid("ice cream turned to soup in the heat full refund?")
    assert out["status"] == "success"
    ids = {d["policy_id"] for d in out["documents"]}
    assert "POL-REFUND-04" in ids


def test_bopis_sub_hits_atp_policy():
    out = retrieve_policy_hybrid("can we sub oat milk on BOPIS order?")
    ids = {d["policy_id"] for d in out["documents"]}
    assert "POL-ATP-02" in ids


def test_garbage_query_misses():
    out = retrieve_policy_hybrid("who won the 1998 world cup final?")
    assert out["status"] == "error"
    assert out["error_code"] == "NO_POLICY_HIT"
```

Run:

```bash
pytest meridian_ops/tests/test_policy_rag_hybrid.py -q
```

### Expect

- Paraphrase → POL-REFUND-04  
- BOPIS → POL-ATP-02  
- Off-topic → `NO_POLICY_HIT`

> **Watch out:** If hybrid always returns *something*, raise the score floor. A weak hit is worse than a miss.

---

## Task 5 — Wire the ADK policy agent + citation contract

### Why

Retrieval without agent discipline still hallucinates. The tool is evidence; the instruction is law.

### Do this

Update `project/meridian_policy_agent/agent.py` (or create it):

```python
from google.adk.agents.llm_agent import Agent

from meridian_ops.tools.policy_rag import retrieve_policy_hybrid

root_agent = Agent(
    name="meridian_policy_agent",
    model="gemini-2.5-flash",
    description="Answers Meridian CX/store policy with hybrid RAG citations.",
    instruction="""
You are Meridian Policy Assistant for OrderOps.

Hard rules:
1. Call retrieve_policy_hybrid BEFORE stating any policy rule.
2. Cite every rule as: policy_id + version + section (from tool output).
3. If status=error / NO_POLICY_HIT: say you cannot find a Meridian policy and recommend human CX — do NOT invent retail norms.
4. Prefer short bullets. Quote at most one short phrase from a chunk.
5. Do not execute refunds, credits, or inventory changes — explain remedy only.
6. If goodwill (POL-CX-09) and policy credit both appear, say which is entitlement vs gesture.
""".strip(),
    tools=[retrieve_policy_hybrid],
)
```

In `adk web` (from `project/` with `PYTHONPATH=.`):

1. Ask: *Ice cream soup after hot porch delivery — full refund?*  
2. Ask: *BOPIS — substitute oat milk without asking?*  
3. Ask: *Can agents give $40 goodwill automatically?*  
4. Ask: *What’s Meridian’s policy on alien abduction delays?*

### Expect

| Ask | Must see |
|-----|----------|
| Ice cream | POL-REFUND-04 + remedy language; HITL if full-order over threshold |
| BOPIS sub | POL-ATP-02; no silent omit |
| $40 goodwill | POL-CX-09; auto max $5 → needs supervisor |
| Alien abduction | Explicit miss / escalate — no improvised “usually” |

---

## Task 6 — Golden eval: grounding, not prose

### Why

Pretty answers regress silently. Score **tool use + citation presence**.

### Do this

Add `project/meridian_ops/evals/golden/policy_hybrid_melted.eval.json` (shape matching your Lesson 08 / `AgentEvaluator` fixtures). Minimum expectations:

- Trajectory calls `retrieve_policy_hybrid`  
- Final text contains `POL-REFUND-04`  
- Final text does **not** invent a `$100 automatic full refund`

Run your Lesson 08 eval path against `meridian_policy_agent`.

### Expect

Eval fails if the agent skips retrieve or drops the policy id.

---

## Task 7 — (Optional) Map to Vertex RAG without rewriting the agent

### Why

SME skill: swap backends, keep the **retrieve → cite** contract.

### Do this

Read ADK docs for `VertexAiRagRetrieval`. Note:

- Isolate Vertex RAG on a **dedicated sub-agent** if you mix other function tools (Gemini tool constraint).  
- Keep Meridian hybrid tool for local labs.  
- Write 5 lines in `project/meridian_ops/decisions/18-rag-backend.md`: when you’d move the corpus to Vertex vs keep local hybrid.

### Expect

A decision note — not a second DIY retrieval framework.

---

## How it works (deeper dive)

```
Customer paraphrase ──► embed(query)
Policy ## sections ──► embed(chunks) ──► cosine rank
Exact IDs / $ caps ──► lexical boost ──► hybrid sort
                         │
                         ▼
              top_k chunks → LlmAgent → cite or NO_POLICY_HIT
```

**Why hybrid:**  
Retail tickets mix **precise** tokens (`POL-…`, `$25`, `BOPIS`) with **messy** language. Either signal alone fails often enough to hurt CX.

**Why citations:**  
Priya’s audit and Finance disputes are won with policy ids, not vibes.

---

## Common pitfalls / troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Always returns wrong policy | Score floor too low / bad blend weights | Raise threshold; inspect hybrid scores in a debug print during tests |
| “Ice cream” misses refund | No chunk for Remedies / weak embed | Confirm chunker split; check paraphrase test |
| Agent invents $50 credit | Skipped tool or ignored miss | Harden instruction; golden eval for NO_POLICY_HIT |
| Context blows up | Returning whole files not chunks | Enforce chunk `text` only; lower `top_k` |
| SentenceTransformer slow | Re-encoding every call | Cache index at import / process start |
| Tempted to DIY “MeridianVectorDB” | Overbuilding | Keep a thin module; optional Vertex later |

---

## You are done when

- [ ] ≥4 policy docs with ids + versions  
- [ ] Heading-aware chunker tests pass  
- [ ] Hybrid retrieve paraphrase + BOPIS + miss tests pass  
- [ ] ADK agent cites policy_id/version/section  
- [ ] Off-topic query does not invent policy  
- [ ] At least one golden eval gates retrieve + citation  

---

## Knowledge check

1. Why is whole-document retrieve risky for Meridian refunds?  
2. What does hybrid retrieval combine, and why both?  
3. What must the agent do on `NO_POLICY_HIT`?  
4. Where do embeddings live relative to the ADK agent?  
5. Name one query that should hit POL-ATP-02 and one that must miss entirely.

### Answers

1. Critical HITL / exclusion lines get diluted; model “summarizes” past them.  
2. Lexical (IDs, exact words) + vector (paraphrase); retail needs both.  
3. Admit miss + escalate — never invent retail norms.  
4. Inside the **domain retrieve tool** (or Vertex RAG tool) — not pasted into the system prompt.  
5. Hit: BOPIS substitution. Miss: unrelated trivia / alien abduction.

---

## Recap

- You upgraded Meridian policy RAG from keywords to **chunk + embed + hybrid**.  
- You enforced **citations** and an honest **miss** path.  
- You can swap to Vertex RAG later without changing the agent’s job.

---

## Stretch goal

Add a conflicting “old” policy file with a lower version date and teach the retriever to prefer newest `Version:` when scores tie — then prove it with a test.

---

## Feedback

- Could you explain hybrid scoring to a teammate with only the ice-cream example?  
- What tripped you up: chunker, embeddings install, score floor, or agent citations?  
- Note task number + expected vs actual if something failed.

---

## Navigate

**← Prev** [Lesson 17 — Event-driven & A2A](17-event-driven-a2a.md)  
**Track home:** [README](../README.md)  
**Next:** [Lesson 19 — Memory systems deep dive](19-memory-systems-deep-dive.md)

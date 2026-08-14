# Lesson 18 — Advanced RAG for retail policy

**Level:** Advanced  
**Time:** ~120–150 minutes  
**Prerequisites:** Lessons 06, 08, 16 (retrieve tool, evals, tool contracts)  
**Lab outcome:** Replace keyword-only policy lookup with **chunk → embed → hybrid retrieve → cite**, and prove the agent refuses to invent policy when retrieval misses

**Standard:** [docs/NATIVE-ADK.md](../docs/NATIVE-ADK.md)

---

## At a glance

Lesson 06 taught the loop: **retrieve → reason → cite**.  
The retrieve tool you have today is keyword-only. It reads whole markdown files. That is a good first loop. It is not how a grocery policy wiki survives real tickets.

This lesson makes retrieval **production-shaped**. You still call one ADK tool from one `LlmAgent`. The work inside the tool changes.

| Task | What you build | Who enforces it | How you prove it |
|------|----------------|-----------------|------------------|
| 1 | A four-doc **corpus** with real overlaps | You, in markdown | Four stable policy ids printed from disk |
| 2 | A heading-aware **chunker** | Your Python | `pytest` — chunk ids like `POL-REFUND-04::Remedies` |
| 3 | Local **embeddings** | Your Python + a small model | Matrix shape equals chunk count |
| 4 | **Hybrid retrieve** (keyword + vector) | Your Python | `pytest` — paraphrase, BOPIS, miss |
| 5 | Policy `LlmAgent` that **cites or refuses** | Tool + instruction | `adk web` — four chats |
| 6 | A golden eval that scores **tool use + citation** | ADK `AgentEvaluator` (Lesson 08) | Eval JSON + one evaluate run |
| 7 | A backend decision note | A file you persist | Open the markdown |

**Allowed:** Meridian domain retriever code (chunk, embed, rank). That is a **tool**, not a second agent framework.

**Forbidden:** Dumping the whole wiki into the system prompt and calling it RAG. Building a custom “MeridianVectorDB” product. Treating Vertex RAG as required for this lab.

If you get lost, scroll back to this table. Each task fills one row. The scoreboard at the end of every task repeats the same rows.

---

## Why this matters

Maya chats:

> “Driver left groceries in 100° heat. Ice cream soup. Do I get a full refund?”

Three failure modes, one lesson:

1. **Wrong file.** Keyword search on `"late"` grabs **POL-DELIVERY-01** (late credits) because the ticket also says the driver was slow. The melted-item clause in **POL-REFUND-04** never surfaces.
2. **Right file, drowned clause.** You return the whole refund doc. The model “summarizes” past the HITL line: *Never auto-approve full-order refunds over $75.*
3. **No file, invented rule.** Retrieval misses. The model still answers from grocery folklore: “full order refunds are always OK under $100.”

Priya (CX supervisor) cannot audit folklore. She can audit `POL-REFUND-04 v2026-06-15 §Remedies`.

You need:

1. Chunks small enough that the melted-item clause can rank on its own
2. Vectors so “ice cream soup” still hits “damaged or melted items”
3. Keyword boosts so ids like `POL-DELIVERY-01` and words like `BOPIS` still win
4. A hard miss path so the agent says “I don’t know” instead of improvising

That retrieve-then-cite loop is **RAG**: Retrieval-Augmented Generation. You look up trusted docs first. Then the model answers from those docs. Then it cites them. The model is not the policy wiki.

---

## Know these

Read this table before Task 1. Every later task reuses these words.

| Term | Plain English | Meridian example |
|------|---------------|------------------|
| **RAG** | Look up trusted docs, then answer from those docs, then cite | Retrieve POL-REFUND-04, then talk about melted dairy |
| **Corpus** | The set of docs you trust | `fixtures/policies/*.md` |
| **Chunk** | A slice of a doc you index — not the whole file | `## Remedies` of POL-REFUND-04 |
| **Embedding** | A list of numbers that means “about the same topic” | “melted dairy” near “ice cream soup” |
| **Vector search** | Rank chunks by how close those number-lists are | Paraphrase queries |
| **Keyword / lexical** | Rank by shared words and ids | Exact `POL-DELIVERY-01` or `$25` or `BOPIS` |
| **Hybrid retrieve** | Blend keyword score + vector score | Ids *and* slang both work |
| **Citation** | Pointer to evidence | `POL-REFUND-04 v2026-06-15 §Remedies` |
| **Grounding** | Claims tied to evidence | Answer quotes a chunk + (later) OMS facts |
| **NO_POLICY_HIT** | Honest miss | “No matching Meridian policy; escalate.” |
| **top_k** | How many chunks to return | `3` — enough to cite, not a novel |

```
Ticket text
    │
    ▼
┌─────────┐   ┌──────────┐   ┌────────────┐
│ chunker │ → │ embedder │ → │ hybrid rank│ → top_k chunks
└─────────┘   └──────────┘   └────────────┘
                                      │
                                      ▼
                    ADK LlmAgent cites  — or  NO_POLICY_HIT
```

### Picture this: the binder vs the whole filing cabinet

At Store 441, Priya does not hand Devon the entire policy binder when Maya asks about melted ice cream. She flips to **one tab**, then **one heading**.

| Approach | What the model sees | Can it skip the HITL line? |
|----------|---------------------|----------------------------|
| Paste every policy into the instruction | The whole cabinet | **Yes** — long context, easy to “summarize” past a bullet |
| Keyword-search whole files (Lesson 06) | Two full markdown files | **Yes** — the melted clause shares a file with other rules |
| Chunk + embed + hybrid + cite | Three short sections + ids | **Harder** — the HITL line can be in the winning chunk |
| `NO_POLICY_HIT` on a miss | An error dict, not a guess | The instruction must obey this; the eval will check |

> **Tip:** The agent never imports the embedder. It calls `retrieve_policy_hybrid`. Same idea as Lesson 04: the model gets a tool dict, not your internals.

---

## What you already have (do not rebuild)

From the **repo root**, confirm these exist. You wrote them in Lesson 06.

| Path | Job |
|------|-----|
| `project/meridian_ops/tools/policy_rag.py` | Keyword `retrieve_policy` — whole files, token overlap |
| `project/meridian_ops/tests/test_policy_rag.py` | Late query → `late_delivery_credits.md`; melted → `refunds_damaged_items.md` |
| `project/meridian_ops/fixtures/policies/late_delivery_credits.md` | **POL-DELIVERY-01** — $10 / $25 late credits |
| `project/meridian_ops/fixtures/policies/refunds_damaged_items.md` | **POL-REFUND-04** — damaged / melted; HITL over $75 |
| `project/meridian_policy_agent/agent.py` | `LlmAgent` that must call `retrieve_policy` before stating a rule |

If `retrieve_policy` is missing, stop and finish Lesson 06. This lesson **adds** a hybrid tool. It does not delete the keyword tool. Lesson 06 tests still import `retrieve_policy`.

You will **add**:

```
project/meridian_ops/
  fixtures/policies/
    substitutions_bopis.md     Task 1  (POL-ATP-02)
    goodwill_credits.md        Task 1  (POL-CX-09)
  tools/
    policy_chunker.py          Task 2
    policy_embed.py            Task 3
    policy_rag.py              Task 4  (add retrieve_policy_hybrid; keep retrieve_policy)
  tests/
    test_policy_chunker.py     Task 2
    test_policy_rag_hybrid.py  Task 4
  evals/golden/
    policy_hybrid_melted.eval.json   Task 6
  decisions/
    18-rag-backend.md          Task 7
project/meridian_policy_agent/
  agent.py                     Task 5  (point tools= at hybrid)
  policy_hybrid_melted.test.json
  test_config.json             Task 6
```

---

## Task 1 — Grow the policy corpus (conflicts welcome)

### Why

Two docs taught the pattern. Real Meridian has overlapping rules.

Maya’s ice cream soup sits on a porch in 100° heat. The driver was also late. A keyword retriever that loves the word `"late"` will hand the model **POL-DELIVERY-01**. That policy pays a **$10 or $25 courtesy credit**. It does not answer “full refund for melted dairy.”

**POL-REFUND-04** does. Full-order refunds over **$75** still need Priya (HITL).

Retrieval must pick the *right clause* under conflict. That only works if the corpus has more than two happy-path files — including a BOPIS substitution policy that must **not** steal melted-dairy questions, and a goodwill policy that must **not** pretend to be an entitlement.

### Do this

1. From the **repo root**, list what Lesson 06 already left you:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
ls -1 project/meridian_ops/fixtures/policies/
```

   `ls -1` prints one filename per line. Easier to count than a grid.

   You should already see:

   - `late_delivery_credits.md`
   - `refunds_damaged_items.md`

2. Open `late_delivery_credits.md`. Confirm the header and the late-credit ladder. This is **POL-DELIVERY-01**. Same-day grocery delivery. Not BOPIS pickup.

   Walk the sections you will later chunk:

   | Heading | Why it must be its own chunk |
   |---------|------------------------------|
   | Eligibility | “more than 60 minutes after the window” — not every late-feeling ticket |
   | Credit amounts | $10 vs $25 — Finance will quote this |
   | Exclusions | Wrong address is not a Meridian credit |
   | Agent rules | Do not promise above the schedule |

3. Open `refunds_damaged_items.md`. Confirm **POL-REFUND-04**, version `2026-06-15`.

   | Heading | Why it must be its own chunk |
   |---------|------------------------------|
   | Eligibility | 48-hour report window |
   | Remedies | Replacement first; full-order only if >50% of lines or food safety |
   | Agent rules | Never auto-approve full-order refunds over $75 |

   If either file is missing those headings, restore them from Lesson 06 before you continue. The chunker in Task 2 splits on `##`. No `##`, no section chunks.

4. Create `project/meridian_ops/fixtures/policies/substitutions_bopis.md`. BOPIS means Buy Online Pickup In Store — Maya drives to Store 441 and picks up a bag. Substitution rules for that bag are **not** delivery-shortage rules.

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

   Why this file exists in a RAG lesson: the word “substitute” will appear in inventory chats **and** in BOPIS chats. Hybrid retrieve must not answer a porch-melt ticket with POL-ATP-02 just because both docs mention food.

5. Create `project/meridian_ops/fixtures/policies/goodwill_credits.md`. Goodwill is an empathy gesture. It is not a policy entitlement. If the model mixes this with POL-REFUND-04, Maya hears “you are owed $40” when Priya only had a $5 auto cap.

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

6. Prove four versioned ids from disk. Still from the repo root, with the project venv:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
source .venv/bin/activate
export PYTHONPATH=project
python - <<'PY'
from pathlib import Path
import re

root = Path("project/meridian_ops/fixtures/policies")
for path in sorted(root.glob("*.md")):
    text = path.read_text()
    pid = re.search(r"^#\s+(POL-[A-Z0-9-]+)", text, re.M)
    ver = re.search(r"^Version:\s*(\S+)", text, re.M)
    print(f"{path.name:28} {pid.group(1) if pid else 'NO_ID':16} {ver.group(1) if ver else 'NO_VER'}")
PY
```

   - `source .venv/bin/activate` — use this project’s Python, not Homebrew’s.
   - `export PYTHONPATH=project` — not required for this snippet (it only reads files), but every later command in this lesson needs it. Set it once in the shell and leave it.

### Expect

Four lines, in filename order:

```
goodwill_credits.md          POL-CX-09         2026-05-01
late_delivery_credits.md     POL-DELIVERY-01   2026-07-01
refunds_damaged_items.md     POL-REFUND-04     2026-06-15
substitutions_bopis.md       POL-ATP-02        2026-07-20
```

You can open each file and point to a `##` section by eye. That is the corpus. Policy ids are product contracts. Rename them casually and every citation in prod logs goes stale.

> **Tip:** Keep `Version:` on its own line in the exact shape `Version: 2026-06-15`. Task 2’s regex looks for that. `Version 2026-06-15` (no colon) will store `unknown`.

> **Watch out:** Do not merge POL-REFUND-04 and POL-DELIVERY-01 “to make retrieve simpler.” The overlap is the point. Maya’s heat-damage ticket must be able to hit refund without paying a late credit she did not earn — and the other way around.

### Scoreboard after Task 1

| Piece | In place? |
|-------|-----------|
| Four-doc corpus | **Yes** |
| Heading-aware chunker | Not yet |
| Local embeddings | Not yet |
| Hybrid retrieve + miss | Not yet |
| Citing agent | Not yet |
| Golden eval | Not yet |
| Backend decision note | Not yet |

---

## Task 2 — Chunk policies (heading-aware)

### Why

Whole-doc retrieve returns 800 tokens when you needed 80.

POL-REFUND-04’s HITL rule lives under `## Agent rules`. If you stuff Eligibility + Remedies + Agent rules into one blob, the model often quotes Remedies (“full-order refund if food safety”) and skips the $75 lock.

A **chunk** is one slice you index. For a policy wiki, the natural slice is a `##` heading. Character-length chunking can split mid-bullet and orphan “require HITL” onto the next slice with no heading.

You will write ordinary Python. No ADK yet. No LLM.

### Do this

1. Create `project/meridian_ops/tools/policy_chunker.py`:

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

   Walk the split. `re.split` with a **capturing** group keeps the `##` headings in the list. For POL-REFUND-04 you get:

   ```
   parts[0]  title + Version + Owner          → chunk Overview
   parts[1]  ## Eligibility
   parts[2]  bullets under Eligibility        → chunk Eligibility
   parts[3]  ## Remedies
   parts[4]  bullets under Remedies           → chunk Remedies
   parts[5]  ## Agent rules
   parts[6]  HITL + cite bullets              → chunk Agent rules
   ```

   What each piece is for:

   - `PolicyChunk` is frozen — once built, tests can hash/compare it. Fields are the citation: id, version, section, plus the text the model may quote.
   - `chunk_id` is `{policy_id}::{section}`. Stable. You will assert on it. Priya can grep it.
   - `_POLICY_DIR` is relative to this file, not your laptop’s current directory. Pytest still finds the fixtures.
   - `policy_id` falls back to the filename stem only if the `# POL-…` header is missing. Do not rely on that fallback. Fix the markdown.
   - Overview is the preamble (title, version, owner). It is a real chunk so “POL-REFUND-04” as a query still has a home.

2. Print every chunk id once, before pytest. From the **repo root**:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
source .venv/bin/activate
export PYTHONPATH=project
python - <<'PY'
from meridian_ops.tools.policy_chunker import load_all_chunks

chunks = load_all_chunks()
print("count", len(chunks))
for c in chunks:
    print(f"{c.chunk_id:40} v={c.version}  {c.path}")
PY
```

   `PYTHONPATH=project` means `import meridian_ops` loads `project/meridian_ops`. Without it you get `ModuleNotFoundError`.

3. Create `project/meridian_ops/tests/test_policy_chunker.py`:

```python
from meridian_ops.tools.policy_chunker import chunk_markdown, load_all_chunks
from pathlib import Path

_REFUND = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "policies"
    / "refunds_damaged_items.md"
)


def test_refund_policy_has_remedies_chunk():
    chunks = chunk_markdown(_REFUND)
    ids = {c.chunk_id for c in chunks}
    assert "POL-REFUND-04::Remedies" in ids
    assert "POL-REFUND-04::Agent rules" in ids
    remedies = next(c for c in chunks if c.section == "Remedies")
    assert "Replacement if ATP allows" in remedies.text
    assert remedies.version == "2026-06-15"


def test_chunk_ids_are_stable():
    chunks = load_all_chunks()
    ids = [c.chunk_id for c in chunks]
    assert "POL-DELIVERY-01::Credit amounts" in ids
    assert "POL-ATP-02::Rules" in ids
    assert "POL-CX-09::Caps" in ids
    assert len(ids) == len(set(ids))
```

   Test 1 is the HITL-survival test: Remedies is its own chunk, and Agent rules is a different chunk. Test 2 proves the two new docs chunk, and that ids do not collide.

4. Run **only** the chunker file:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
source .venv/bin/activate
export PYTHONPATH=project
pytest project/meridian_ops/tests/test_policy_chunker.py -v
```

   `-v` is verbose: pytest prints each test name and `PASSED` / `FAILED`, not just a dot.

### Expect

A printout that includes at least:

```
POL-DELIVERY-01::Overview
POL-DELIVERY-01::Eligibility
POL-DELIVERY-01::Credit amounts
POL-DELIVERY-01::Exclusions
POL-DELIVERY-01::Agent rules
POL-REFUND-04::Overview
POL-REFUND-04::Eligibility
POL-REFUND-04::Remedies
POL-REFUND-04::Agent rules
POL-ATP-02::Overview
POL-ATP-02::Eligibility
POL-ATP-02::Rules
POL-ATP-02::Agent rules
POL-CX-09::Overview
POL-CX-09::When used
POL-CX-09::Caps
POL-CX-09::Agent rules
```

`count` should be **17** if every file uses `##` as above (one Overview + the headings).

Pytest:

```
test_policy_chunker.py::test_refund_policy_has_remedies_chunk PASSED
test_policy_chunker.py::test_chunk_ids_are_stable PASSED
```

> **Tip:** If `count` is 4, you only got Overview chunks — the files have no `##` headings. Restore the Lesson 06 / Task 1 markdown.

> **Watch out:** Chunking only on a fixed character length can split the bullet “Never auto-approve full-order refunds over $75” in half. Prefer headings for policy wiki. You can add a size cap *inside* a huge section later. Do not start there.

### Scoreboard after Task 2

| Piece | In place? |
|-------|-----------|
| Four-doc corpus | Yes |
| Heading-aware chunker | **Yes** |
| Local embeddings | Not yet |
| Hybrid retrieve + miss | Not yet |
| Citing agent | Not yet |
| Golden eval | Not yet |
| Backend decision note | Not yet |

---

## Task 3 — Local embeddings (no mysticism)

### Why

“Ice cream soup” never appears in POL-REFUND-04. The words in the file are **damaged**, **melted**, **unsafe**, **refund**.

Keyword search needs shared tokens. Maya did not type those words.

An **embedding** is a list of numbers (a vector) for a piece of text. Texts about the same topic land near each other. “Ice cream turned to soup in the heat” sits near “Item arrived damaged, melted, or unsafe” even when the words differ.

You will compute embeddings **on your laptop** with a small open model. The ADK agent never sees the model. It only sees the retrieve tool’s dict.

You are not required to call Vertex RAG. Domain chunk/embed/rank inside the tool is the lab.

### Do this

1. Install the embedder into this project’s venv:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
source .venv/bin/activate
pip install -q sentence-transformers numpy
```

   - `-q` on pip — quiet install. You still see errors.
   - First use of the model will **download** `all-MiniLM-L6-v2` (a small CPU-friendly embedder). Later runs reuse the cache.

2. Create `project/meridian_ops/tools/policy_embed.py`:

```python
from __future__ import annotations

from functools import lru_cache

import numpy as np


@lru_cache(maxsize=1)
def _model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


def embed_texts(texts: list[str]) -> np.ndarray:
    vecs = _model().encode(texts, normalize_embeddings=True)
    return np.asarray(vecs, dtype=np.float32)


def cosine_sim(query_vec: np.ndarray, chunk_matrix: np.ndarray) -> np.ndarray:
    # query_vec: (d,)   chunk_matrix: (n, d)
    # both L2-normalized → dot product == cosine similarity
    return chunk_matrix @ query_vec
```

   Walk the three functions:

   | Function | Job |
   |----------|-----|
   | `_model()` | Load MiniLM **once**. `@lru_cache(maxsize=1)` means the second call returns the same object. Re-loading every retrieve would make pytest crawl. |
   | `embed_texts` | Text in, matrix out. `normalize_embeddings=True` scales each vector to length 1 so later math is a dot product. |
   | `cosine_sim` | One query vector vs every chunk row. Higher number = closer topic. Range is roughly `-1` to `1`; near `1` means “same direction.” |

   `chunk_matrix @ query_vec` is matrix times vector. If you reverse the arguments you get a shape error. Keep query as `(d,)` and chunks as `(n, d)`.

3. Prove the index shape **before** you write hybrid rank. First run may look idle while the model downloads:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
source .venv/bin/activate
export PYTHONPATH=project
python - <<'PY'
from meridian_ops.tools.policy_chunker import load_all_chunks
from meridian_ops.tools.policy_embed import cosine_sim, embed_texts

chunks = load_all_chunks()
matrix = embed_texts([c.text for c in chunks])
print("chunks", len(chunks), "matrix", matrix.shape)

query = "ice cream turned to soup in the heat full refund?"
q = embed_texts([query])[0]
scores = cosine_sim(q, matrix)
order = scores.argsort()[::-1]
print("top 3 by vector only:")
for i in order[:3]:
    print(f"  {scores[i]:.3f}  {chunks[int(i)].chunk_id}")
PY
```

   `matrix.shape` is `(n, d)`: `n` is chunk count (about 17), `d` is 384 for MiniLM-L6. Those two numbers must match `len(chunks)` and the query vector’s length.

### Expect

Something like:

```
chunks 17 matrix (17, 384)
top 3 by vector only:
  0.612  POL-REFUND-04::Remedies
  0.548  POL-REFUND-04::Eligibility
  0.501  POL-REFUND-04::Agent rules
```

Exact scores differ a little. What must be true:

- `matrix.shape[0] == len(chunks)`
- `matrix.shape[1] == 384`
- At least one of the top three chunk ids starts with `POL-REFUND-04`

Vector-only rank is already enough for Maya’s paraphrase. It is **not** enough for `POL-DELIVERY-01` typed as an id, or for `BOPIS`, or for `$25`. Those are Task 4’s job.

> **Tip:** Keep embedding **behind your tool**. Agents call `retrieve_policy_hybrid`. They never import `SentenceTransformer`. Swap the embedder later; the tool dict stays the same.

> **Watch out:** If this script hangs on first run, it is downloading the model. If it fails with `No module named 'sentence_transformers'`, the pip install ran in a different Python than the one you activated. Run `which python` — it should sit under `.venv/`.

> **Watch out:** Do not encode the corpus on every tool call from scratch in a loop of `embed_texts([one_chunk])`. Encode once, cache the matrix. Task 4 does that with module-level `_CHUNKS` / `_MATRIX`.

### Scoreboard after Task 3

| Piece | In place? |
|-------|-----------|
| Four-doc corpus | Yes |
| Heading-aware chunker | Yes |
| Local embeddings | **Yes** |
| Hybrid retrieve + miss | Not yet |
| Citing agent | Not yet |
| Golden eval | Not yet |
| Backend decision note | Not yet |

---

## Task 4 — Hybrid retrieve tool (replace keyword-only at the agent)

### Why

IDs and dollar amounts need **lexical** match (shared words). Customer slang needs **vectors**.

| Query | Lexical alone | Vector alone | Hybrid |
|-------|---------------|--------------|--------|
| `POL-DELIVERY-01` | Hits that id | May miss — ids are not English | Hits |
| `ice cream soup full refund` | May miss POL-REFUND-04 | Hits melted / refund chunks | Hits |
| `sub oat milk on BOPIS` | `BOPIS` boost | Nearby “substitutions” | Hits POL-ATP-02 |
| `who won the 1998 world cup final?` | Tiny / zero overlap | Weak similarity to grocery text | **Miss** → `NO_POLICY_HIT` |

Keyword-only `retrieve_policy` (Lesson 06) stays in the file so existing tests keep passing. The **agent** will switch to `retrieve_policy_hybrid`. Same tool-contract idea: `status` + `documents` or `error_code=NO_POLICY_HIT`.

Hybrid score in this lab:

```
hybrid = 0.55 * vector_cosine  +  0.45 * lexical_normalized
```

- **0.55** on vectors — Maya’s slang is the usual ticket. Give paraphrase a slight majority.
- **0.45** on lexical — still enough that an exact policy id or `BOPIS` can win a tie.
- Lexical scores are divided by the max in the corpus so they sit on a 0–1 scale, comparable to cosine.

Then a **floor**: weak vector noise with **zero** lexical overlap is dropped. That is how world-cup trivia becomes `NO_POLICY_HIT` instead of a random goodwill chunk.

### Do this

1. Open `project/meridian_ops/tools/policy_rag.py`. **Keep** `retrieve_policy` exactly as it is (Lesson 06 tests import it). **Add** the hybrid helpers below it.

   Full file after the edit:

```python
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import numpy as np

from meridian_ops.tools.policy_chunker import PolicyChunk, load_all_chunks
from meridian_ops.tools.policy_embed import cosine_sim, embed_texts

_POLICY_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "policies"

_CHUNKS: list[PolicyChunk] | None = None
_MATRIX: np.ndarray | None = None

VEC_WEIGHT = 0.55
LEX_WEIGHT = 0.45
HYBRID_FLOOR = 0.15


def retrieve_policy(query: str, top_k: int = 2) -> dict[str, Any]:
    """Retrieve Meridian policy markdown files relevant to a query."""
    _POLICY_DIR.mkdir(parents=True, exist_ok=True)
    tokens = set(re.findall(r"[a-z0-9]+", query.lower()))
    scored: list[tuple[int, Path]] = []
    for path in sorted(_POLICY_DIR.glob("*.md")):
        text = path.read_text().lower()
        score = sum(1 for t in tokens if t in text)
        scored.append((score, path))
    scored.sort(key=lambda x: x[0], reverse=True)
    picked = [p for score, p in scored if score > 0][:top_k]
    if not picked:
        return {
            "status": "error",
            "error_code": "NO_POLICY_HIT",
            "message": "No policy documents matched; do not invent policy.",
        }
    return {
        "status": "success",
        "documents": [{"path": p.name, "text": p.read_text()} for p in picked],
    }


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
    vec_scores = cosine_sim(q_vec, matrix)
    lex_scores = np.array([_lexical_score(query, c) for c in chunks], dtype=np.float32)
    lex_norm = lex_scores / (lex_scores.max() + 1e-6)
    hybrid = VEC_WEIGHT * vec_scores + LEX_WEIGHT * lex_norm

    order = np.argsort(-hybrid)
    picked: list[dict[str, Any]] = []
    for idx in order[:top_k]:
        if hybrid[idx] < HYBRID_FLOOR and lex_scores[idx] <= 0:
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
                "vec_score": float(vec_scores[idx]),
                "lex_score": float(lex_scores[idx]),
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

   Walk the hybrid path in order:

   ```
   load chunks + embed matrix once
           │
           ▼
   embed the query
           │
           ▼
   vector cosine for every chunk     lexical overlap + boosts
           │                                │
           └──────── 0.55 / 0.45 ───────────┘
                            │
                            ▼
              sort by hybrid, take top_k
                            │
              drop rows with hybrid < 0.15 AND lex == 0
                            │
              documents  or  NO_POLICY_HIT
   ```

   Lexical boosts are **not** magic ML. They are Meridian ticket slang you already know:

   | Boost | When it fires | Ticket it saves |
   |-------|----------------|-----------------|
   | `+5` | Query contains the chunk’s `POL-…` id | Priya pasted `POL-DELIVERY-01` |
   | `+3` | Query and chunk both contain `bopis` | Oat-milk sub in pickup, not porch melt |
   | `+3` | Query has melt/ice/damaged **and** chunk talks melt/damage | Ice cream soup |

   `vec_score` and `lex_score` in the returned dict are for **you** during tests. The model can ignore them. You will print them in a minute.

   `_ensure_index` caches at process start. Restart pytest (or `adk web`) after you edit a policy file, or the old matrix sticks in memory.

2. Create `project/meridian_ops/tests/test_policy_rag_hybrid.py`:

```python
from meridian_ops.tools.policy_rag import retrieve_policy, retrieve_policy_hybrid


def test_keyword_tool_still_works():
    out = retrieve_policy("late grocery delivery credits")
    paths = [d["path"] for d in out["documents"]]
    assert "late_delivery_credits.md" in paths


def test_melted_paraphrase_hits_refund_policy():
    out = retrieve_policy_hybrid(
        "ice cream turned to soup in the heat full refund?"
    )
    assert out["status"] == "success"
    ids = [d["policy_id"] for d in out["documents"]]
    chunk_ids = [d["chunk_id"] for d in out["documents"]]
    assert "POL-REFUND-04" in ids
    assert any(c.startswith("POL-REFUND-04::") for c in chunk_ids)


def test_late_id_query_hits_delivery_policy():
    out = retrieve_policy_hybrid("What does POL-DELIVERY-01 pay at 90 minutes late?")
    ids = [d["policy_id"] for d in out["documents"]]
    assert "POL-DELIVERY-01" in ids


def test_bopis_sub_hits_atp_policy():
    out = retrieve_policy_hybrid("can we sub oat milk on BOPIS order?")
    ids = [d["policy_id"] for d in out["documents"]]
    assert "POL-ATP-02" in ids


def test_garbage_query_misses():
    out = retrieve_policy_hybrid("who won the 1998 world cup final?")
    assert out["status"] == "error"
    assert out["error_code"] == "NO_POLICY_HIT"
```

   Five tests, five promises:

   | Test | Promise |
   |------|---------|
   | Keyword tool still works | You did not break Lesson 06 |
   | Melted paraphrase | `POL-REFUND-04` is in `documents` |
   | Typed policy id | `POL-DELIVERY-01` wins on lexical +5 |
   | BOPIS | `POL-ATP-02`, not refund, not goodwill |
   | World cup | `NO_POLICY_HIT` — no invented retail |

3. Run the new file. First pytest in this process may spend a few seconds embedding 17 chunks:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
source .venv/bin/activate
export PYTHONPATH=project
pytest project/meridian_ops/tests/test_policy_rag_hybrid.py -v
```

4. Print one retrieve payload so you know what the model will see. This is the contract, not a secret log:

```bash
python - <<'PY'
import json
from meridian_ops.tools.policy_rag import retrieve_policy_hybrid

out = retrieve_policy_hybrid(
    "ice cream turned to soup in the heat full refund?", top_k=3
)
print(json.dumps(out, indent=2)[:2000])
print("--- ids ---")
if out["status"] == "success":
    for d in out["documents"]:
        print(d["chunk_id"], "hybrid", round(d["score"], 3),
              "vec", round(d["vec_score"], 3), "lex", round(d["lex_score"], 3))
PY
```

### Expect

Pytest:

```
test_policy_rag_hybrid.py::test_keyword_tool_still_works PASSED
test_policy_rag_hybrid.py::test_melted_paraphrase_hits_refund_policy PASSED
test_policy_rag_hybrid.py::test_late_id_query_hits_delivery_policy PASSED
test_policy_rag_hybrid.py::test_bopis_sub_hits_atp_policy PASSED
test_policy_rag_hybrid.py::test_garbage_query_misses PASSED
```

Sample melted retrieve (scores will differ; **ids** must not):

```json
{
  "status": "success",
  "documents": [
    {
      "chunk_id": "POL-REFUND-04::Remedies",
      "policy_id": "POL-REFUND-04",
      "version": "2026-06-15",
      "section": "Remedies",
      "path": "refunds_damaged_items.md",
      "score": 0.71,
      "vec_score": 0.61,
      "lex_score": 8.0,
      "text": "## Remedies\n- Replacement if ATP allows (preferred).\n- Refund of impacted line items otherwise.\n- Full-order refund only if >50% of line items impacted OR food safety issue affecting the order."
    }
  ]
}
```

Document ids you should be able to point at:

| Query | Must include | Must not be the only hit |
|-------|----------------|--------------------------|
| Ice cream soup / full refund | `POL-REFUND-04` (`::Remedies` or `::Agent rules` or `::Eligibility`) | POL-ATP-02 as the winner |
| `POL-DELIVERY-01` / 90 minutes late | `POL-DELIVERY-01` | POL-CX-09 as the winner |
| BOPIS oat milk | `POL-ATP-02` | POL-REFUND-04 as the winner |
| 1998 world cup | `error_code: NO_POLICY_HIT` | any `documents` list |

Also re-run Lesson 06’s file so you did not break it:

```bash
pytest project/meridian_ops/tests/test_policy_rag.py -v
```

```
test_policy_rag.py::test_late_delivery_query_hits_delivery_policy PASSED
test_policy_rag.py::test_melted_items_hits_refund_policy PASSED
```

> **Tip:** If `test_garbage_query_misses` fails because a weak vector hit sneaks in, raise `HYBRID_FLOOR` from `0.15` toward `0.25`. That number is yours. A weak hit is worse than a miss — the agent will treat junk as policy.

> **Watch out:** If hybrid always returns *something*, you do not have RAG. You have a slot machine that always pays. The miss path is a feature.

> **Watch out:** Returning `text` of three chunks is the point. Returning four whole files is Lesson 06 with extra steps. Keep `top_k=3`.

### Scoreboard after Task 4

| Piece | In place? |
|-------|-----------|
| Four-doc corpus | Yes |
| Heading-aware chunker | Yes |
| Local embeddings | Yes |
| Hybrid retrieve + miss | **Yes** |
| Citing agent | Not yet |
| Golden eval | Not yet |
| Backend decision note | Not yet |

---

## Task 5 — Wire the ADK policy agent + citation contract

### Why

Retrieval without agent discipline still hallucinates. Pytest proved the tool. Priya still needs to see a trajectory in `adk web`: the model **called** retrieve, then **cited** a policy id, or it **refused**.

The tool is evidence. The instruction is the handbook. Lesson 04 already taught you the handbook is skippable — so the miss path is an **error dict**, not a paragraph that says “please don’t invent.”

This agent explains remedies. It does not call `request_refund`. Least privilege is the import list.

### Do this

1. Replace `project/meridian_policy_agent/agent.py` so the tool list points at **hybrid**. `Agent` here **is** ADK’s `LlmAgent` (same class).

```python
from google.adk.agents.llm_agent import Agent

from meridian_ops.tools.policy_rag import retrieve_policy_hybrid

root_agent = Agent(
    name="meridian_policy_agent",
    model="gemini-3.5-flash",
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

   Look at what is **missing**: `request_refund`, `get_order`, keyword `retrieve_policy`. This agent’s one job is grounded policy text.

   `gemini-3.5-flash` is the lab model. Do not swap it for a “smarter” id in this lesson — evals in Task 6 need a stable target.

2. Restart `adk web` from `project/` so it reloads the package. `adk web` does not reliably pick up `agent.py` edits otherwise.

```bash
cd /Users/alishaghatane/dev/agent-learn-sme/project
source ../.venv/bin/activate
export PYTHONPATH=.
adk web --port 8000
```

   - From `project/`, `PYTHONPATH=.` means `import meridian_ops` and `import meridian_policy_agent` both work.
   - `--port 8000` keeps the UI on the URL you already have open.
   - Press `Ctrl+C` in the old terminal first if it is still running.

3. In the UI, select **meridian_policy_agent**. Four chats (new session each time is fine):

   **A — melted ice cream (Maya)**

   ```
   Driver left groceries in 100° heat. Ice cream soup. Do I get a full refund?
   ```

   **B — BOPIS substitute**

   ```
   BOPIS order — substitute oat milk without asking the customer?
   ```

   **C — goodwill cap**

   ```
   Can agents give $40 goodwill automatically?
   ```

   **D — honest miss**

   ```
   What’s Meridian’s policy on alien abduction delays?
   ```

### Expect

| Ask | Trajectory must show | Customer-facing text must |
|-----|----------------------|---------------------------|
| A Ice cream | `retrieve_policy_hybrid` | Cite `POL-REFUND-04` + version `2026-06-15` + a section; HITL if full-order over $75 |
| B BOPIS | `retrieve_policy_hybrid` | Cite `POL-ATP-02`; no silent omit; not a porch-melt refund |
| C $40 goodwill | `retrieve_policy_hybrid` | Cite `POL-CX-09`; auto max $5 → needs supervisor; this is **not** an entitlement |
| D Alien abduction | `retrieve_policy_hybrid` returning `NO_POLICY_HIT` | Explicit miss / escalate — no “usually stores offer…” |

If ask A cites only POL-DELIVERY-01, the hybrid ranking is wrong or the model ignored the top chunk. Go back to Task 4’s printed ids. The agent may mention lateness as a *second* policy if that chunk also returned — it must not **replace** the melted refund rule with a $10 late credit.

> **Tip:** Short quotes. “Replacement if ATP allows” plus a citation beats pasting the whole Remedies chunk into the chat bubble.

> **Watch out:** Stay on **meridian_policy_agent**. Order Status from Lesson 03 has no retrieve tool; it will invent policy from the instruction.

> **Watch out:** Restarting `adk web` starts a fresh in-memory session. That is expected. RAG does not depend on chat memory. Lesson 19 does.

### Scoreboard after Task 5

| Piece | In place? |
|-------|-----------|
| Four-doc corpus | Yes |
| Heading-aware chunker | Yes |
| Local embeddings | Yes |
| Hybrid retrieve + miss | Yes |
| Citing agent | **Yes** |
| Golden eval | Not yet |
| Backend decision note | Not yet |

---

## Task 6 — Golden eval: grounding, not pretty prose

### Why

Pretty answers regress silently. Next month someone will change the instruction to “be more helpful” and the alien-abduction miss becomes a made-up delay credit.

Lesson 08 already gave you ADK **`AgentEvaluator`**. This task does not invent a second eval framework. It adds a golden set for **this** agent: tool name + citation presence.

You score:

1. Did the trajectory call `retrieve_policy_hybrid`?
2. Did the final text contain `POL-REFUND-04` for the melted ticket?
3. Did the miss case stay a miss (no invented `$100 automatic full refund`)?

Prose overlap (ROUGE-style `response_match_score`) stays a **soft** bar. Trajectory is the hard bar.

### Do this

1. Create `project/meridian_ops/evals/golden/policy_hybrid_melted.eval.json`. Same shape as Lesson 08’s `wismo_basic.eval.json`:

```json
{
  "eval_set_id": "meridian_policy_hybrid_melted",
  "name": "Meridian policy hybrid RAG golden set",
  "description": "Ground-truth trajectories for meridian_policy_agent after Lesson 18.",
  "eval_cases": [
    {
      "eval_id": "policy_melted_ice_cream",
      "conversation": [
        {
          "invocation_id": "inv-policy-001",
          "user_content": {
            "role": "user",
            "parts": [
              {
                "text": "Driver left groceries in 100° heat. Ice cream soup. Do I get a full refund?"
              }
            ]
          },
          "final_response": {
            "role": "model",
            "parts": [
              {
                "text": "Under POL-REFUND-04 (v2026-06-15, Remedies / Agent rules), melted items can be refunded or replaced. Full-order refunds over $75 need supervisor HITL. I am not processing a refund in this chat."
              }
            ]
          },
          "intermediate_data": {
            "tool_uses": [
              {
                "name": "retrieve_policy_hybrid",
                "args": {
                  "query": "Driver left groceries in 100° heat. Ice cream soup. Do I get a full refund?"
                }
              }
            ],
            "intermediate_responses": []
          }
        }
      ],
      "session_input": {
        "app_name": "meridian_policy_agent",
        "user_id": "eval_user",
        "state": {}
      }
    },
    {
      "eval_id": "policy_miss_alien_abduction",
      "conversation": [
        {
          "invocation_id": "inv-policy-002",
          "user_content": {
            "role": "user",
            "parts": [
              {
                "text": "What's Meridian's policy on alien abduction delays?"
              }
            ]
          },
          "final_response": {
            "role": "model",
            "parts": [
              {
                "text": "I cannot find a matching Meridian policy (NO_POLICY_HIT). Please escalate to human CX. I will not invent a delay credit."
              }
            ]
          },
          "intermediate_data": {
            "tool_uses": [
              {
                "name": "retrieve_policy_hybrid",
                "args": {
                  "query": "What's Meridian's policy on alien abduction delays?"
                }
              }
            ],
            "intermediate_responses": []
          }
        }
      ],
      "session_input": {
        "app_name": "meridian_policy_agent",
        "user_id": "eval_user",
        "state": {}
      }
    }
  ]
}
```

   Two cases, both **must** call the retrieve tool. The miss case still retrieves — that is how you get `NO_POLICY_HIT` instead of skipping the tool and riffing.

   The `query` arg in the golden is the user text. If the model paraphrases the tool argument, trajectory match can dip. That is useful signal: you want retrieve called; exact query string is the strict Lesson 08 bar (`tool_trajectory_avg_score: 1.0`). If a run fails only on arg spelling, look at the detailed results before “fixing” the agent into a stub.

2. Copy it into the agent package as `*.test.json`, then add `test_config.json` next to that file.

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
source .venv/bin/activate
export PYTHONPATH=project
python - <<'PY'
from pathlib import Path
from google.adk.evaluation.agent_evaluator import AgentEvaluator

src = Path("project/meridian_ops/evals/golden/policy_hybrid_melted.eval.json")
dst = Path("project/meridian_policy_agent/policy_hybrid_melted.test.json")
dst.parent.mkdir(parents=True, exist_ok=True)
AgentEvaluator.migrate_eval_data_to_new_schema(str(src), str(dst))
print(dst)
PY
```

   `migrate_eval_data_to_new_schema` is the ADK 2.6.3 helper Lesson 08 used. Your JSON is already in that shape; the helper still writes the agent-local `*.test.json` ADK evaluates.

   Create `project/meridian_policy_agent/test_config.json`:

```json
{
  "criteria": {
    "tool_trajectory_avg_score": 1.0,
    "response_match_score": 0.3
  }
}
```

   `1.0` on trajectory = the tool name (and args, at that threshold) must match. `0.3` on response = overlapping words with the reference; it will not fail you for saying “HITL” vs “supervisor approval.”

3. Run native `AgentEvaluator` from `project/` so `agent_module="meridian_policy_agent"` imports:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme/project
source ../.venv/bin/activate
export PYTHONPATH=.
python - <<'PY'
import asyncio
from google.adk.evaluation.agent_evaluator import AgentEvaluator

async def main():
    await AgentEvaluator.evaluate(
        agent_module="meridian_policy_agent",
        eval_dataset_file_path_or_dir="meridian_policy_agent/policy_hybrid_melted.test.json",
        num_runs=1,
        print_detailed_results=True,
    )

asyncio.run(main())
PY
```

   - `num_runs=1` — one live Gemini pass per case. Default in ADK 2.6.3 is `2`; keep the lab cheap.
   - `print_detailed_results=True` — print per `eval_id`, not only a final average.
   - This **does** call Gemini. Tool unit tests in Task 4 do not. Keep Task 4 on every save; keep this eval for a labeled/nightly run if cost hurts.

### Expect

Printed scores per `eval_id`:

- `policy_melted_ice_cream` — trajectory hits `retrieve_policy_hybrid`; final text includes `POL-REFUND-04`
- `policy_miss_alien_abduction` — retrieve still called; final text does **not** invent a dollar credit

The eval **fails** if the agent skips retrieve or drops the policy id. Fix the agent or the tool. Do not invent a stub planner to force green.

> **Tip:** Unit tests (Task 4) stay on every PR. `AgentEvaluator` is the live gate Lesson 08 already taught. Same wheel. New golden.

> **Watch out:** If you leave `tools=[retrieve_policy]` (the old keyword tool) on the agent, the golden’s expected name `retrieve_policy_hybrid` fails. The tool list is the contract.

### Scoreboard after Task 6

| Piece | In place? |
|-------|-----------|
| Four-doc corpus | Yes |
| Heading-aware chunker | Yes |
| Local embeddings | Yes |
| Hybrid retrieve + miss | Yes |
| Citing agent | Yes |
| Golden eval | **Yes** |
| Backend decision note | Not yet |

---

## Task 7 — Decide the backend (keep the tool contract)

### Why

SME skill: swap where chunks live, keep **retrieve → cite**.

This lab’s retriever is Meridian domain code. That is allowed. A cloud index (Vertex AI Search, a future Vertex RAG corpus) is a **backend**, not a second agent loop. You do not need Vertex to finish this lesson. You do need a written decision so someone does not “just paste the wiki into the prompt” in six months.

### Do this

1. Create the folder if needed:

```bash
mkdir -p project/meridian_ops/decisions
```

   `mkdir -p` creates the folder and does not complain if it already exists.

2. Create `project/meridian_ops/decisions/18-rag-backend.md`:

```markdown
# Lesson 18 — policy RAG backend

Lab (now): local chunk + MiniLM embed + hybrid rank in `retrieve_policy_hybrid`.
Agent: `LlmAgent` + that one tool. Citations from chunk_id / policy_id / version / section.

Move the corpus to a cloud index when:
- policy count outgrows a folder of markdown, or
- more than one service must share the same index.

Do not move when:
- we only wanted prettier answers (fix chunks / weights / miss floor first).

Never: paste the wiki into the system prompt and call it RAG.
```

### Expect

A decision note you can defend in review — not a second retrieval framework, and not a required Vertex install.

> **Tip:** If you later wrap a cloud retriever, keep the **same** tool name and the same dict keys (`status`, `documents[].policy_id`, `NO_POLICY_HIT`). The agent instruction stays.

> **Watch out:** Do not add a second retrieve tool “for Vertex” on the same `LlmAgent` “just in case.” One policy tool. One miss code.

### Scoreboard after Task 7

| Piece | In place? |
|-------|-----------|
| Four-doc corpus | Yes |
| Heading-aware chunker | Yes |
| Local embeddings | Yes |
| Hybrid retrieve + miss | Yes |
| Citing agent | Yes |
| Golden eval | Yes |
| Backend decision note | **Yes** |

---

## How it works (deeper dive)

```
Customer paraphrase ──► embed(query)
Policy ## sections ──► embed(chunks) ──► cosine rank
Exact IDs / $ caps / BOPIS ──► lexical boost ──► hybrid sort
                         │
                         ▼
              top_k chunks → LlmAgent → cite or NO_POLICY_HIT
```

**Why hybrid:**  
Retail tickets mix **precise** tokens (`POL-DELIVERY-01`, `$25`, `BOPIS`) with **messy** language (“ice cream soup”). Either signal alone fails often enough to hurt CX.

**Why citations:**  
Priya’s audit and Finance disputes are won with policy ids, not vibes.

**Why the miss path is a tool error:**  
An instruction that says “don’t guess” is a handbook. `error_code=NO_POLICY_HIT` is a cash-register beep. Task 6’s eval listens for the beep.

**Why this is not a new agent framework:**  
`policy_chunker.py` / `policy_embed.py` / `retrieve_policy_hybrid` are domain tools, same family as `get_order`. ADK still owns the agent, the session, and (Lesson 08) the evaluator.

| Need | Where it lives |
|------|----------------|
| Split markdown on `##` | `policy_chunker.py` |
| Turn text into vectors | `policy_embed.py` |
| Blend scores + miss | `retrieve_policy_hybrid` |
| Cite or refuse | `LlmAgent` instruction + tool dict |
| Gate regressions | `AgentEvaluator` golden (Lesson 08 API) |

---

## Common pitfalls / troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `ModuleNotFoundError: meridian_ops` | `PYTHONPATH` not set | From repo root: `export PYTHONPATH=project`. From `project/`: `export PYTHONPATH=.` |
| `count` of chunks is 4 | No `##` headings | Restore Task 1 / Lesson 06 markdown |
| `chunk_id` has `unknown` version | `Version:` line missing or no colon | Use `Version: 2026-06-15` |
| Ice cream misses POL-REFUND-04 | Index stale, or Remedies not chunked | Restart the process; run Task 2 printout |
| BOPIS returns POL-REFUND-04 | Query lacked `BOPIS`; refund doc talked food | Keep the BOPIS boost; check printed `lex_score` |
| World cup returns a document | `HYBRID_FLOOR` too low | Raise toward `0.25`; confirm `lex_score` is 0 |
| SentenceTransformer slow every test | Re-encoding every call; cache missed | Keep `_ensure_index`; do not clear `_MATRIX` in the tool |
| `No module named 'sentence_transformers'` | pip ran outside `.venv` | `source .venv/bin/activate` then pip |
| Agent invents $50 credit | Skipped tool, or ignored `NO_POLICY_HIT` | Harden instruction; Task 6 golden |
| Eval fails on tool **args** only | Model rephrased the query | Read detailed results; trajectory name still must be `retrieve_policy_hybrid` |
| Eval fails because old tool name | Agent still has `retrieve_policy` | Point `tools=` at hybrid; restart |
| Tempted to DIY `MeridianVectorDB` | Overbuilding | Keep these three thin modules |

---

## You are done when

- [ ] Four policy docs with ids + versions (`POL-DELIVERY-01`, `POL-REFUND-04`, `POL-ATP-02`, `POL-CX-09`)
- [ ] Chunker tests pass; `POL-REFUND-04::Remedies` exists
- [ ] Hybrid tests pass: melted paraphrase → `POL-REFUND-04`; BOPIS → `POL-ATP-02`; world cup → `NO_POLICY_HIT`
- [ ] Lesson 06 `test_policy_rag.py` still passes
- [ ] `adk web` on `meridian_policy_agent` cites policy_id / version / section
- [ ] Off-topic query does not invent policy
- [ ] Golden eval gates retrieve + `POL-REFUND-04` on the melted case
- [ ] `18-rag-backend.md` says when you would keep local hybrid vs move the index

---

## Knowledge check

Answer from this lab, not from general RAG lore.

1. Why is whole-document retrieve risky for Meridian refunds?  
2. What does hybrid retrieval combine, and why both? What weights did you use?  
3. What must the agent do on `NO_POLICY_HIT`?  
4. Where do embeddings live relative to the ADK agent?  
5. Name one query that should hit `POL-ATP-02`, one that should hit `POL-REFUND-04`, and one that must miss entirely.  
6. Why keep `retrieve_policy` in `policy_rag.py` after you added hybrid?

### Answers

1. Critical HITL / exclusion lines get diluted; the model “summarizes” past them.  
2. Lexical (ids, exact words, BOPIS) + vector (paraphrase). Retail tickets have both. This lab: **0.55** vector, **0.45** lexical.  
3. Admit miss + escalate — never invent retail norms.  
4. Inside the **domain retrieve tool** — not pasted into the system prompt.  
5. Hit ATP: BOPIS substitution. Hit refund: ice cream soup / melted. Miss: world cup / alien abduction.  
6. Lesson 06 tests still import it. The agent switched; the old contract stays tested.

---

## Recap

- You upgraded Meridian policy RAG from keywords-on-whole-files to **chunk + embed + hybrid**.  
- You enforced **citations** and an honest **miss** path.  
- You gated the loop with Lesson 08’s `AgentEvaluator`, not a new framework.  
- You can move the index later without changing the agent’s job.

---

## Stretch goal

Add a second, older file that also claims the id `POL-REFUND-04` but with `Version: 2025-01-01` and a friendlier (wrong) HITL threshold.

Teach the retriever to prefer the newest `Version:` when hybrid scores tie. Prove it with a pytest: the winning chunk’s `version` is `2026-06-15`, not `2025-01-01`.

Do not solve this by deleting the old file. Ranking is the point.

---

## Feedback

- Could you explain hybrid scoring to a teammate with only the ice-cream example?  
- What tripped you up: chunker, embeddings install, score floor, citations, or the eval JSON?  
- Note the **task number** and what you expected vs what happened (command + first lines of output). That is the signal that improves this lesson — “it was confusing” is not.

---

## Navigate

**← Prev** [Lesson 17 — Event-driven & A2A](17-event-driven-a2a.md)  
**Track home:** [README](../README.md)  
**Next:** [Lesson 19 — Memory systems deep dive](19-memory-systems-deep-dive.md)

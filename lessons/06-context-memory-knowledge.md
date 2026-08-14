# Lesson 06 — Context, memory, and knowledge

**Level:** Advanced  
**Time:** ~90–110 minutes  
**Prerequisites:** Lessons 03–05 (sessions, hardened tools, OrderOps specialists)  
**Lab outcome:** A keyword policy retriever that cites Meridian docs, plus a token budget you can measure — proved with `pytest` and `adk web`

---

## At a glance

Four stores get mixed up in every agent demo. Today you separate them with Maya’s late-delivery ticket, then you build only the **retrieve → cite** path.

| Store | Lifetime | Meridian example | Today? |
|-------|----------|------------------|--------|
| **Transcript** | This chat | Maya’s last eight turns | Compact it in Task 5 |
| **State** | This session | `active_order_id` from Lesson 03 | You already have it |
| **Long-term memory** | Across chats | “Maya prefers SMS” | **Lesson 19** — not today |
| **RAG / retrieve** | Just-in-time docs | `POL-DELIVERY-01` pulled for this question | **This lesson** |

You will prove six things, in this order:

| Task | What you prove | How |
|------|----------------|-----|
| 1 | Count tokens; slim an OMS order | `pytest` — no LLM |
| 2 | Two versioned policy files | Open the markdown |
| 3 | Keyword `retrieve_policy` ranks the right doc | `pytest` + sample JSON |
| 4 | Policy agent **must cite** before it answers | `adk web` |
| 5 | A long dispute keeps ids after compaction | `pytest` |
| 6 | Fat prompt vs slim prompt, measured | Terminal JSON |

Lesson **18** upgrades this retriever to **hybrid / embeddings**. Lesson **19** is long-term memory. Today is retrieve + cite. If you get lost, scroll back to this table. The scoreboard at the end of every task repeats the same rows.

---

## Why this matters

Maya (customer `C-44102`) texts about order `MC-1048292`:

> “What’s Meridian’s policy on late grocery delivery credits?”

Two failure modes, both expensive:

1. **Guess from training.** The model “knows” that grocery apps often give $25. Finance never approved that number. You just promised Maya money.
2. **Paste the whole wiki.** Every turn includes every policy, plus the full OMS JSON. You blow the **context window** (the model’s limited working memory), raise cost, and still miss the one clause that matters.

Priya (CX supervisor) will ask:

> “Which policy id did we cite? Show me the file.”

If your answer is “the model sounded sure,” you do not have a product.

Today the agent **retrieves** `POL-DELIVERY-01`, **cites** it, and **refuses** when retrieve misses. Checking whether `MC-1048292` was *actually* late is still `get_order` (OMS). Policy language and order facts are different channels.

---

## Know these

Read this table before Task 1. Every later task reuses these words.

| Term | Plain English | Meridian example |
|------|---------------|------------------|
| **Transcript / session history** | The chat log the model can see | Maya’s last 8 turns about `MC-1048292` |
| **State** | Scratchpad for *this* session | `active_order_id = MC-1048292` |
| **Long-term memory** | Facts that survive a new chat | “Maya prefers SMS” (Lesson 19) |
| **Artifact** | A named blob saved on the session | `order-MC-1048292.json` |
| **RAG** | Retrieve → reason → cite | Pull `late_delivery_credits.md` just in time |
| **Grounding** | Tie a claim to evidence | “$10 credit — `POL-DELIVERY-01` v2026-07-01” |
| **Citation** | Name the doc you used | Policy id + version date |
| **Corpus** | The set of docs you retrieve from | Two markdown files in `fixtures/policies/` |
| **Keyword retriever** | Score docs by overlapping words | Query `late` boosts the delivery policy |
| **Token** | A chunk of text the model bills and fits in context | Rough lab estimate: **4 characters ≈ 1 token** |
| **Token budget** | Every token must earn its place | Don’t paste 14 line-items when an id + lifecycle will do |
| **Slim** | Keep only fields the next step needs | `slim_order` drops city and `line_count` |
| **Compaction** | Shrink old turns; keep recent ones verbatim | 10-turn dispute → summary + last 4 turns |
| **Context window** | Hard cap on tokens the model can see at once | Overflow → dropped history or a failed call |
| **`NO_POLICY_HIT`** | Retriever found nothing | Agent must say “I cannot find a policy,” not invent $50 |
| **HITL** | Human in the loop | Credits ≥ $25 stacked with a refund need Priya (policy text today; Lesson 07 builds the lock) |

### Picture this: the binder, the scratchpad, the brain

At Store 441, Devon has three places information can live:

| Place | Grocery picture | Agent analogue |
|-------|-----------------|----------------|
| The **policy binder** on the wall | Printed, versioned, cited by number | RAG — retrieve the page, then speak |
| The **sticky note** on this ticket | “Active order MC-1048292” | Session **state** |
| Devon **remembering** Maya likes SMS | Survives tomorrow’s shift | Long-term **memory** (Lesson 19) |
| The **radio transcript** | What was just said | Chat **history** — useful, noisy, expensive |

The binder is not in Devon’s head. He **opens it**. That is retrieve.

```
Maya asks about late credits
        │
        ▼
[retrieve_policy] ── keyword score over fixtures/policies/*.md
        │
        ├─ miss ──▶ NO_POLICY_HIT ──▶ "I cannot find a policy"
        │
        ▼ hit
cite POL-DELIVERY-01 + version date
        │
        ▼
(optional) get_order for MC-1048292 ── was *this* order late?
        │
        ▼
answer with dollars from the doc, not from training
```

> **Tip:** Lesson 18 keeps this same tool name (`retrieve_policy`) and upgrades the *inside* to chunks + embeddings + hybrid search. Do not invent a second framework. Change the ranking. Keep the contract: a dict with `status`, `documents` or `error_code`.

---

## What you already have (do not rebuild)

From the **repo root**, confirm these exist. You wrote them in Lessons 03–04.

| Path | Job |
|------|-----|
| `project/meridian_ops/tools/oms.py` | `get_order` for `MC-1048292` |
| `project/meridian_ops/fixtures/orders.json` | Order facts |
| `project/meridian_ops/tools/logging_utils.py` | JSON logs on stderr + `new_correlation_id` |

You will **add** (or replace if a thin stub is already there):

```
project/meridian_ops/
  tools/
    token_budget.py          Task 1 + Task 5  (file is empty today — you write all of it)
    policy_rag.py            Task 3           (replace the thin version with logging + scores)
  fixtures/policies/
    late_delivery_credits.md Task 2           POL-DELIVERY-01
    refunds_damaged_items.md Task 2           POL-REFUND-04
  tests/
    test_token_budget.py     Tasks 1 and 5
    test_policy_rag.py       Task 3
project/meridian_policy_agent/
  agent.py                   Task 4
```

If `policy_rag.py` already has a short `retrieve_policy` with no logs and no token estimates, Task 3 **replaces the whole file**. Do not keep two retrievers.

---

## Task 1 — Measure what you stuff into context

### Why

You cannot budget tokens you refuse to count.

Maya’s OMS row has city, line count, and lifecycle. The policy question only needs a handful of fields. If you paste the whole `orders.json` on every turn, you pay for Austin and sourdough while the model hunts for “was it late?”

A **token estimate** in this lab is `characters / 4`. That is not a billing tokenizer. It is good enough to see “this blob is 8× bigger than that blob.” You will use it on orders *and* on retrieved policy text.

### Do this

1. Open `project/meridian_ops/tools/token_budget.py`. It is empty (or nearly empty). Replace the whole file with:

```python
from __future__ import annotations

import json
from typing import Any


def estimate_tokens(text: str) -> int:
    """Rough token estimate for lab budgeting (~4 chars/token).

    Not a billing tokenizer — good enough to compare fat vs slim payloads.
    """
    if not text:
        return 0
    return max(1, len(text) // 4)


def budget_report(parts: dict[str, str], limit: int = 8000) -> dict[str, Any]:
    """Return per-part estimates and whether the bundle fits a soft limit."""
    items = []
    total = 0
    for name, text in parts.items():
        toks = estimate_tokens(text)
        total += toks
        items.append({"name": name, "chars": len(text), "est_tokens": toks})
    return {
        "limit": limit,
        "total_est_tokens": total,
        "fits": total <= limit,
        "parts": sorted(items, key=lambda x: x["est_tokens"], reverse=True),
    }


def slim_order(order: dict[str, Any]) -> dict[str, Any]:
    """Keep only fields OrderOps usually needs in-prompt."""
    keys = [
        "order_id",
        "lifecycle",
        "promised_window_local",
        "delivered_at_local",
        "pod_photo_present",
        "order_total_usd",
    ]
    return {k: order[k] for k in keys if k in order}
```

   Walk the file in order:

   | Piece | What it does |
   |-------|----------------|
   | `estimate_tokens` | Empty string → `0`. Anything else → `len(text) // 4`, but never `0` for non-empty text (`max(1, …)` so a 2-character string still counts as 1 token). |
   | `budget_report` | Walks a dict of named strings. Sums estimates. `fits` is `total <= limit`. `parts` is sorted **largest first** so the hog jumps out. |
   | `limit=8000` | A soft lab cap, not Gemini’s real window. You will pass a tiny `limit` in tests to prove overflow. |
   | `slim_order` | Allowlist of keys. City, `line_count`, and `customer_id` never enter the prompt copy. |
   | `if k in order` | Missing keys are skipped. `MC-1048292` has no `order_total_usd` in the fixture — slim will not invent `None`. |

   Why these six fields: they answer “which order, what lifecycle, when promised, when delivered, was there a POD photo, what did she pay?” They do **not** answer policy dollars. Policy dollars come from retrieve.

2. Create `project/meridian_ops/tests/test_token_budget.py`:

```python
from meridian_ops.tools.token_budget import budget_report, estimate_tokens, slim_order


def test_estimate_empty_is_zero():
    assert estimate_tokens("") == 0


def test_slim_order_removes_noise():
    raw = {
        "order_id": "MC-1048292",
        "lifecycle": "delivered",
        "line_count": 14,
        "shipping_address_city": "Austin",
        "pod_photo_present": False,
    }
    slim = slim_order(raw)
    assert "line_count" not in slim
    assert "shipping_address_city" not in slim
    assert slim["lifecycle"] == "delivered"
    assert slim["order_id"] == "MC-1048292"


def test_budget_flags_overflow():
    report = budget_report({"policy": "x" * 50000}, limit=1000)
    assert report["fits"] is False
    assert report["parts"][0]["name"] == "policy"
```

   - Test 1: empty text is free.
   - Test 2: Maya’s noisy fields never survive `slim_order`. If someone later adds `line_count` to the keep list, this test is the alarm.
   - Test 3: 50,000 characters ≈ 12,500 tokens, which does not fit in 1,000. `fits is False` is the whole point of a budget.

3. Run **only** this file. From the **repo root**:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
source .venv/bin/activate
export PYTHONPATH=project
pytest project/meridian_ops/tests/test_token_budget.py -v
```

   - `source .venv/bin/activate` — use this project’s Python, not Homebrew’s.
   - `export PYTHONPATH=project` — `import meridian_ops` means `project/meridian_ops`. Without this you get `ModuleNotFoundError`.
   - `-v` — verbose: print each test name and `PASSED` / `FAILED`, not just a dot.

### Expect

```
test_token_budget.py::test_estimate_empty_is_zero PASSED
test_token_budget.py::test_slim_order_removes_noise PASSED
test_token_budget.py::test_budget_flags_overflow PASSED
```

Optional — see a number without pytest:

```bash
python -c "from meridian_ops.tools.token_budget import estimate_tokens; print(estimate_tokens('late grocery delivery credits'))"
```

You should see `7` (`len(...) // 4` on that phrase).

> **Tip:** Keep `estimate_tokens` boring. Do not call Gemini to “count tokens.” The point is a lever you can run in unit tests and in Task 6.

> **Watch out:** `//` is integer division. `len("abcd") // 4` is `1`, not `1.0`. Tests that compare to floats will confuse you later; keep estimates as `int`.

### Scoreboard after Task 1

| Proof | In place? |
|-------|-----------|
| Token estimates + slim_order | **Yes** |
| Policy fixtures | Not yet |
| retrieve_policy + tests | Not yet |
| Policy agent cites in `adk web` | Not yet |
| Compaction | Not yet |
| Budget before/after measured | Not yet |

---

## Task 2 — Author two policy fixtures (the binder)

### Why

Retrieve without a corpus is theater. The agent cannot cite `POL-DELIVERY-01` if that string does not exist in a file you control.

Keep policies **small, versioned, and boring**. Each file has:

- A **policy id** in the heading (`POL-DELIVERY-01`, `POL-REFUND-04`)
- A **version date**
- An owner
- Agent rules a model might otherwise invent

Maya’s late-credit question needs the delivery doc. A melted-dairy refund question needs the refund doc. Two files so ranking has something to choose between.

### Do this

1. Create the folder if needed:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
mkdir -p project/meridian_ops/fixtures/policies
```

   `mkdir -p` creates every missing parent and does not error if the folder already exists.

2. Create `project/meridian_ops/fixtures/policies/late_delivery_credits.md`:

```markdown
# POL-DELIVERY-01 — Late grocery delivery credits
Version: 2026-07-01
Owner: CX Policy

## Eligibility
- Applies to Meridian same-day grocery delivery (not BOPIS pickup).
- Delivery must arrive more than 60 minutes after the end of the promised window.

## Credit amounts
- 15–60 minutes late: apology only (no automatic credit).
- 61–120 minutes late: $10 courtesy credit.
- >120 minutes late: $25 courtesy credit.

## Exclusions
- Customer-caused delays (wrong address, unreachable).
- Weather emergency banner declared by Ops.
- Third-party partner outages already covered by partner compensation.

## Agent rules
- Do not promise credits above this schedule.
- Credits ≥ $25 require supervisor HITL if stacking with a refund on the same order.
```

   What Maya (and the agent) must be able to quote:

   | Clause | Number / rule |
   |--------|----------------|
   | How late? | More than **60 minutes after the window ends** |
   | 15–60 min late | Apology only — **$0** automatic |
   | 61–120 min | **$10** |
   | Over 120 min | **$25** |
   | Stack with a refund | ≥ $25 credit → Priya (HITL) |

3. Create `project/meridian_ops/fixtures/policies/refunds_damaged_items.md`:

```markdown
# POL-REFUND-04 — Damaged or melted items
Version: 2026-06-15
Owner: CX Policy

## Eligibility
- Item arrived damaged, melted, or unsafe.
- Report within 48 hours of delivery timestamp.

## Remedies
- Replacement if ATP allows (preferred).
- Refund of impacted line items otherwise.
- Full-order refund only if >50% of line items impacted OR food safety issue affecting the order.

## Agent rules
- Never auto-approve full-order refunds over $75 (HITL).
- Cite this policy id when recommending a remedy.
```

   Lesson 07 will turn the **$75** line into a Python allowlist and a HITL CLI. Today it is text the retriever must be able to return.

4. Confirm both files are on disk:

```bash
ls -1 project/meridian_ops/fixtures/policies/
```

   `ls -1` — one file name per line (`-1` is the digit one, not a letter).

### Expect

```
late_delivery_credits.md
refunds_damaged_items.md
```

Open each file and check the heading ids: `POL-DELIVERY-01` and `POL-REFUND-04`. Those strings are what Task 4’s agent must cite.

> **Tip:** Filename and policy id are different on purpose. The tool returns `path` (`late_delivery_credits.md`). The model cites `POL-DELIVERY-01` from the heading. Priya can grep either.

> **Watch out:** Do not paste these policies into the agent `instruction`. That is dumping the wiki. The instruction will say “call `retrieve_policy`.” The files stay on disk.

### Scoreboard after Task 2

| Proof | In place? |
|-------|-----------|
| Token estimates + slim_order | Yes |
| Policy fixtures | **Yes** |
| retrieve_policy + tests | Not yet |
| Policy agent cites in `adk web` | Not yet |
| Compaction | Not yet |
| Budget before/after measured | Not yet |

---

## Task 3 — Build `retrieve_policy` (and walk the scoring)

### Why

For this curriculum, a **keyword / tag retriever** teaches the loop: retrieve → reason → cite. You can swap in embeddings in Lesson 18 **without** changing the tool contract.

The model never sees the folder. It calls a Python function. Your Python scores files, logs a correlation id, and returns a dict. If nothing matches, it returns `NO_POLICY_HIT` — not a guess.

If `project/meridian_ops/tools/policy_rag.py` already exists, it is probably the thin version: no logs, no `est_tokens`, weaker scoring. **Replace the whole file.**

### Do this

1. Replace `project/meridian_ops/tools/policy_rag.py` with:

```python
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from meridian_ops.tools.logging_utils import log_tool_event, new_correlation_id
from meridian_ops.tools.token_budget import estimate_tokens

_POLICY_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "policies"


def _index() -> list[dict[str, str]]:
    docs = []
    for path in sorted(_POLICY_DIR.glob("*.md")):
        text = path.read_text()
        docs.append({"path": path.name, "text": text})
    return docs


def retrieve_policy(query: str, top_k: int = 2) -> dict[str, Any]:
    """Retrieve Meridian policy documents relevant to a query.

    Args:
        query: Natural language question or ticket text.
        top_k: Max documents to return.
    """
    corr = new_correlation_id()
    log_tool_event(tool="retrieve_policy", correlation_id=corr, query=query)
    tokens = set(re.findall(r"[a-z0-9]+", query.lower()))
    scored: list[tuple[int, dict[str, str]]] = []
    for doc in _index():
        hay = doc["text"].lower()
        score = sum(1 for t in tokens if t in hay)
        # light boosts
        if "late" in tokens and "late" in hay:
            score += 3
        if "refund" in tokens and "refund" in hay:
            score += 3
        if "melt" in tokens or "damaged" in tokens:
            if "melted" in hay or "damaged" in hay:
                score += 3
        scored.append((score, doc))

    scored.sort(key=lambda x: x[0], reverse=True)
    picked = [doc for score, doc in scored if score > 0][:top_k]
    if not picked:
        return {
            "status": "error",
            "error_code": "NO_POLICY_HIT",
            "correlation_id": corr,
            "message": "No policy documents matched; do not invent policy.",
        }

    return {
        "status": "success",
        "correlation_id": corr,
        "documents": [
            {
                "path": d["path"],
                "est_tokens": estimate_tokens(d["text"]),
                "text": d["text"],
            }
            for d in picked
        ],
    }
```

2. Walk the helpers, then walk **scoring** with Maya’s real query.

   **`_POLICY_DIR`**

   - `Path(__file__)` — this file, `policy_rag.py`.
   - `.resolve()` — absolute path, no `..`.
   - `.parents[1]` — up from `tools/` to `meridian_ops/`.
   - Then `fixtures/policies`. Tests still find the files even if your shell is in `project/`.

   **`_index()`**

   - `glob("*.md")` — only markdown policy files.
   - `sorted(...)` — stable order so ties do not flip between runs.
   - Each item is `{"path": filename, "text": full file}`. Whole files, not chunks. Lesson 18 chunks.

   **`retrieve_policy` — control flow**

   ```
   mint corr id → log query on stderr
        → split query into lowercase tokens
        → score each doc
        → sort high → low
        → keep score > 0, take top_k
        → NO_POLICY_HIT or success dict with path + est_tokens + text
   ```

   - `re.findall(r"[a-z0-9]+", query.lower())` — keep letters and digits. `"What's"` becomes `what` and `s`. Punctuation drops.
   - `set(...)` — each token counts **once** toward the base score, even if Maya repeats “late late late.”
   - `t in hay` is **substring** search, not whole-word. The token `full` matches `full-order`. That is a keyword-retriever quirk. Lesson 18’s embeddings reduce this class of accident. Do not “fix” it with a second product today.
   - `top_k: int = 2` — at most two docs. Default is already slim. The model cannot ask for the whole wiki unless you raise this.

   **Scoring worked example** — query `"late grocery delivery credits"`:

   Tokens: `late`, `grocery`, `delivery`, `credits`.

   | Doc | Base (token in file?) | Boosts | Total |
   |-----|------------------------|--------|-------|
   | `late_delivery_credits.md` | late, grocery, delivery, credits → **4** | `"late"` in query and file → **+3** | **7** |
   | `refunds_damaged_items.md` | only `delivery` (`delivery timestamp`) → **1** | none | **1** |

   Sort: delivery file first. Both scores `> 0`, `top_k=2`, so **both** can come back. The first path must be `late_delivery_credits.md`.

   **Second query** — `"melted dairy full refund"`:

   Tokens: `melted`, `dairy`, `full`, `refund`.

   | Doc | Base | Boosts | Total |
   |-----|------|--------|-------|
   | `refunds_damaged_items.md` | melted, full, refund → **3** (`dairy` is absent) | `"refund"` → **+3** | **6** |
   | `late_delivery_credits.md` | refund (`refund on the same order`) → **1** | `"refund"` → **+3** | **4** |

   Refund file wins. Good.

   **Boost gotcha:** the melt boost checks `"melt" in tokens`, not `"melted"`. Maya’s word `melted` does **not** fire that +3. The refund boost and the raw token `melted` still rank `POL-REFUND-04` first. Stretch goal: also treat `melted` as a melt token. Do not silently change the lab scoring before the tests pass as written.

   **Miss query** — `"store wifi password reset"`: tokens never appear in either file → `NO_POLICY_HIT`.

3. Create (or replace) `project/meridian_ops/tests/test_policy_rag.py`:

```python
from meridian_ops.tools.policy_rag import retrieve_policy


def test_late_delivery_query_hits_delivery_policy():
    out = retrieve_policy("late grocery delivery credits")
    assert out["status"] == "success"
    paths = [d["path"] for d in out["documents"]]
    assert "late_delivery_credits.md" in paths
    assert paths[0] == "late_delivery_credits.md"


def test_melted_items_hits_refund_policy():
    out = retrieve_policy("melted dairy full refund")
    paths = [d["path"] for d in out["documents"]]
    assert "refunds_damaged_items.md" in paths
    assert paths[0] == "refunds_damaged_items.md"


def test_unknown_query_is_no_policy_hit():
    out = retrieve_policy("store wifi password reset")
    assert out["status"] == "error"
    assert out["error_code"] == "NO_POLICY_HIT"
```

   Tests call the tool **directly**. No LLM. If ranking is wrong, pytest fails — not a chat that “sounded fine.”

4. Run **only** this file:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
source .venv/bin/activate
export PYTHONPATH=project
pytest project/meridian_ops/tests/test_policy_rag.py -v
```

5. Print one success JSON so you know what the model will see. Correlation ids change every call; paths and `est_tokens` should match:

```bash
python -c "
from meridian_ops.tools.policy_rag import retrieve_policy
import json
out = retrieve_policy('late grocery delivery credits')
print(json.dumps(out, indent=2)[:1200])
"
```

### Expect

Pytest:

```
test_policy_rag.py::test_late_delivery_query_hits_delivery_policy PASSED
test_policy_rag.py::test_melted_items_hits_refund_policy PASSED
test_policy_rag.py::test_unknown_query_is_no_policy_hit PASSED
```

Sample retrieve JSON (your `correlation_id` hex will differ):

```json
{
  "status": "success",
  "correlation_id": "corr-a1b2c3d4e5f6",
  "documents": [
    {
      "path": "late_delivery_credits.md",
      "est_tokens": 186,
      "text": "# POL-DELIVERY-01 — Late grocery delivery credits\nVersion: 2026-07-01\n..."
    },
    {
      "path": "refunds_damaged_items.md",
      "est_tokens": 125,
      "text": "# POL-REFUND-04 — Damaged or melted items\nVersion: 2026-06-15\n..."
    }
  ]
}
```

`est_tokens` is `len(file) // 4`: delivery file is 747 characters → **186**; refund file is 503 → **125**.

On **stderr** (mixed into the pytest / python output), a JSON log from `log_tool_event`:

```json
{
  "ts": 1786660000.0,
  "level": "INFO",
  "tool": "retrieve_policy",
  "correlation_id": "corr-a1b2c3d4e5f6",
  "query": "late grocery delivery credits"
}
```

`file=sys.stderr` in Lesson 04’s logger: the model sees the **return dict**. Priya greps stderr. Same `correlation_id` on both.

For the miss path:

```bash
python -c "from meridian_ops.tools.policy_rag import retrieve_policy; print(retrieve_policy('store wifi password reset'))"
```

You should see `"error_code": "NO_POLICY_HIT"` and **no** `documents` key. The instruction in Task 4 will say: do not invent policy.

> **Tip:** `top_k=1` in a one-off call if you only want the winner: `retrieve_policy("late grocery delivery credits", top_k=1)`. Leave the default at 2 so a stacking question can see both delivery *and* refund language.

> **Watch out:** If retrieve returns `NO_POLICY_HIT`, the agent must say it does not know — not “usually stores offer $50.” Task 4’s instruction is the handbook. This error dict is the lock.

> **Watch out:** Query `"weather on mars"` is a **bad** miss test. The delivery policy contains the word `weather` (exclusions) and the substring `on`. Keyword search will hit. Use `"store wifi password reset"`.

### Scoreboard after Task 3

| Proof | In place? |
|-------|-----------|
| Token estimates + slim_order | Yes |
| Policy fixtures | Yes |
| retrieve_policy + tests | **Yes** |
| Policy agent cites in `adk web` | Not yet |
| Compaction | Not yet |
| Budget before/after measured | Not yet |

---

## Task 4 — Policy agent that must cite

### Why

A retriever without citation discipline is fancy hallucination: the model still answers from training and maybe glances at the tool result.

This agent has **one** tool: `retrieve_policy`. It cannot refund. It cannot change inventory. Least privilege is the import list (Lesson 04 / 05). The instruction still says “cite the policy id.” That is defense in depth — the handbook *and* the locked drawer.

### Do this

1. Scaffold the ADK package so `adk web` can load it. From `project/`:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme/project
source ../.venv/bin/activate
export PYTHONPATH=.
adk create meridian_policy_agent --model gemini-3.5-flash
```

   - `adk create <name>` — positional folder name. Writes `meridian_policy_agent/` next to `meridian_order_status`.
   - `--model gemini-3.5-flash` — put that model id on the generated root agent. You will still replace `agent.py`; passing it here means the scaffold matches the lab.

   If the folder already exists, skip `adk create` and go to step 2.

2. Replace `project/meridian_policy_agent/agent.py` with:

```python
from google.adk.agents.llm_agent import Agent

from meridian_ops.tools.policy_rag import retrieve_policy

root_agent = Agent(
    name="meridian_policy_agent",
    model="gemini-3.5-flash",
    description="Answers Meridian CX policy questions with citations.",
    instruction="""
You are Meridian Policy Assistant.

Rules:
- You MUST call retrieve_policy before stating any policy rule.
- Cite policy id (e.g., POL-DELIVERY-01) and version date in the answer.
- If retrieve_policy errors, say you cannot find a policy — do not improvise.
- Out of scope: executing refunds or inventory changes (explain remedy only).
- Keep quotes short; prefer bullet paraphrase + citation.
""".strip(),
    tools=[retrieve_policy],
)
```

   Walk every `Agent(...)` field:

   | Field | Value | Why |
   |-------|-------|-----|
   | `name` | `meridian_policy_agent` | Stable id in the UI and in later routers |
   | `model` | `gemini-3.5-flash` | Fast, cheap enough for retrieve-then-paraphrase |
   | `description` | one line | Other agents / the UI use this blurb |
   | `instruction` | the rules block | Product policy for this specialist |
   | `tools` | `[retrieve_policy]` only | Cannot call `request_refund` or `get_order` unless you add them |

   Walk the instruction rules:

   1. **MUST call retrieve_policy** — no policy sentence without a tool call in the trajectory.
   2. **Cite id + version** — `POL-DELIVERY-01` and `2026-07-01`, not “company policy.”
   3. **On error, refuse** — maps to `NO_POLICY_HIT`.
   4. **Out of scope** — explain a remedy; do not pretend the card was credited.
   5. **Short quotes** — the tool already returned the full file (`est_tokens` 186). Do not paste it again in the bubble.

   `root_agent` is the name ADK looks for in `agent.py`. Keep it. `__init__.py` from the scaffold should already be `from . import agent`.

3. Restart `adk web` from `project/` so it picks up the new package. Press `Ctrl+C` in the old terminal first if it is still running.

```bash
cd /Users/alishaghatane/dev/agent-learn-sme/project
source ../.venv/bin/activate
export PYTHONPATH=.
adk web --port 8000
```

   - `export PYTHONPATH=.` — from `project/`, `meridian_ops` is a sibling import.
   - `--port 8000` — bind the UI to port 8000 so `http://localhost:8000` stays the URL you already use. Default would also work; pinning the port avoids “which port did it pick?”

4. Open `http://localhost:8000`. In the agent list, select **meridian_policy_agent** (not Order Status).

5. Send this as the user message:

```
What's Meridian's policy on late grocery delivery credits?
```

6. In the **same** session, send a second turn:

```
Can I stack that with a full refund on the same order?
```

7. New session. Send a miss on purpose:

```
What's the store wifi password reset policy?
```

### Expect

Agent list includes `meridian_policy_agent`.

**Turn 1 — late credits**

- Trajectory shows a `retrieve_policy` call **before** dollar amounts.
- Tool args include the question (or a close paraphrase).
- Tool result `documents[0].path` is `late_delivery_credits.md`.
- Reply cites **`POL-DELIVERY-01`** and version **`2026-07-01`**.
- Dollar schedule matches the file: apology / $10 / $25 — not a made-up $50.

**Turn 2 — stacking**

- Another retrieve, or the model uses the refund file already in the last tool result.
- Answer refers to stacking / HITL language from `POL-DELIVERY-01` (credits ≥ $25 + refund → supervisor) and does **not** say “sure, stack away.”
- Still no refund tool — this agent cannot move money.

**Turn 3 — wifi miss**

- `retrieve_policy` returns `NO_POLICY_HIT`.
- Reply says it cannot find a policy. No invented wifi SOP.

In the **terminal** that launched `adk web` (not the browser bubble), stderr JSON lines with `"tool": "retrieve_policy"` and a `correlation_id`.

> **Tip:** If the first turn cites the id but skips the version date, tighten the instruction one line (“always include Version:”) and restart. Do not dump the policy file into `instruction`.

> **Watch out:** Stay on **meridian_policy_agent**. Order Status from Lesson 02/03 has `get_order`, not retrieve. It will invent a credit from the chat.

> **Watch out:** `adk web` does not always reload `agent.py`. Restart the process after edits.

> **Watch out:** `PYTHONPATH` unset → `ModuleNotFoundError: meridian_ops` when the agent imports `retrieve_policy`. Export it in the same terminal that runs `adk web`.

### Scoreboard after Task 4

| Proof | In place? |
|-------|-----------|
| Token estimates + slim_order | Yes |
| Policy fixtures | Yes |
| retrieve_policy + tests | Yes |
| Policy agent cites in `adk web` | **Yes** |
| Compaction | Not yet |
| Budget before/after measured | Not yet |

---

## Task 5 — Compact a long dispute without losing ids

### Why

A 40-turn melted-grocery / late-credit dispute will drown the model. Old turns still contain the only copy of `MC-1048292` and `$10` if you are sloppy.

**Compaction** means: keep the last N turns **verbatim**; fold older turns into a short summary that **extracts** order ids and dollar amounts. You store that summary in **state** later (`dispute_summary`). Today you write a pure function and test it.

This is not Lesson 19 memory. It is shrinking **this** transcript so the context window still has room for retrieve.

### Do this

1. Open `project/meridian_ops/tools/token_budget.py`. Add `import re` next to the other imports at the top:

```python
from __future__ import annotations

import json
import re
from typing import Any
```

2. Append this function at the bottom of the same file (below `slim_order`):

```python
def compact_transcript(turns: list[dict[str, str]], keep_last: int = 4) -> dict[str, Any]:
    """Keep the last N turns verbatim; summarize older turns as extracted facts.

    Each turn: {"role": "user"|"agent", "text": str}
    """
    if len(turns) <= keep_last:
        return {"mode": "verbatim", "turns": turns, "summary": None}

    older = turns[:-keep_last]
    recent = turns[-keep_last:]
    joined = " ".join(t["text"] for t in older)
    order_ids = sorted(set(re.findall(r"MC-\d+", joined)))
    amounts = sorted(set(re.findall(r"\$\d+(?:\.\d+)?", joined)))
    summary = {
        "older_turn_count": len(older),
        "order_ids_mentioned": order_ids,
        "amounts_mentioned": amounts,
        "note": "Older turns compacted; verify against tools before acting.",
    }
    return {"mode": "compacted", "summary": summary, "turns": recent}
```

   Walk the branches:

   | Situation | `mode` | What you keep |
   |-----------|--------|----------------|
   | 4 turns or fewer | `verbatim` | All turns, `summary` is `None` |
   | 10 turns, `keep_last=4` | `compacted` | Last 4 turns + summary of the first 6 |

   - `turns[:-keep_last]` — everything except the tail.
   - `re.findall(r"MC-\d+", joined)` — every `MC-1048292`-shaped id in the **older** text.
   - `\$\d+(?:\.\d+)?` — `$10` or `$214.55`. The `?:` means “group but do not capture separately.”
   - `sorted(set(...))` — unique, stable order.
   - The note is a warning to the *next* step: summaries are hints. OMS and retrieve are still the source of truth.

3. Append these tests to `project/meridian_ops/tests/test_token_budget.py`. Add `compact_transcript` to the import at the top of the file.

```python
from meridian_ops.tools.token_budget import (
    budget_report,
    compact_transcript,
    estimate_tokens,
    slim_order,
)


def test_short_transcript_stays_verbatim():
    turns = [{"role": "user", "text": "Status for MC-1048292?"}]
    out = compact_transcript(turns, keep_last=4)
    assert out["mode"] == "verbatim"
    assert out["summary"] is None


def test_compact_keeps_order_ids_and_last_turns():
    turns = []
    for i in range(6):
        turns.append({"role": "user", "text": f"Older turn {i} on MC-1048292 wants $10"})
    turns.append({"role": "user", "text": "recent 1"})
    turns.append({"role": "agent", "text": "recent 2"})
    turns.append({"role": "user", "text": "recent 3"})
    turns.append({"role": "agent", "text": "recent 4"})
    out = compact_transcript(turns, keep_last=4)
    assert out["mode"] == "compacted"
    assert out["summary"]["older_turn_count"] == 6
    assert "MC-1048292" in out["summary"]["order_ids_mentioned"]
    assert "$10" in out["summary"]["amounts_mentioned"]
    assert len(out["turns"]) == 4
    assert out["turns"][0]["text"] == "recent 1"
```

   Ten turns: six “older” that mention Maya’s order and $10, then four recent that do **not** repeat the id. After compaction the id must still live in `summary`. That is the bug you are preventing: dropping `MC-1048292` because it was said on turn 2.

4. Re-run token-budget tests:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
source .venv/bin/activate
export PYTHONPATH=project
pytest project/meridian_ops/tests/test_token_budget.py -v
```

### Expect

Five `PASSED` lines, including:

```
test_short_transcript_stays_verbatim PASSED
test_compact_keeps_order_ids_and_last_turns PASSED
```

The compacted dict’s `summary.order_ids_mentioned` is `["MC-1048292"]`. The last four `turns` are exactly `recent 1` … `recent 4`.

> **Tip:** When you wire this into an agent later, write `tool_context.state["dispute_summary"] = out["summary"]`. State is the sticky note. Do not re-send 40 raw turns forever.

> **Watch out:** Compaction is not a license to skip `get_order`. If the summary says `$10` and OMS says the window was met, OMS wins. The note in `summary` exists for that reason.

### Scoreboard after Task 5

| Proof | In place? |
|-------|-----------|
| Token estimates + slim_order | Yes |
| Policy fixtures | Yes |
| retrieve_policy + tests | Yes |
| Policy agent cites in `adk web` | Yes |
| Compaction | **Yes** |
| Budget before/after measured | Not yet |

---

## Task 6 — Measure fat vs slim (and retrieve vs dump)

### Why

Priya will ask why you retrieve two short files instead of pasting the wiki. A budget report is the answer: numbers, not vibes.

You already have `budget_report`, `slim_order`, `get_order`, and `retrieve_policy`. Run them. Read the JSON.

This is not a worksheet. It is the same command you would paste into a PR when someone wants to “just add the full OMS blob.”

### Do this

1. From the **repo root**, with the venv active and `PYTHONPATH=project`:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
source .venv/bin/activate
export PYTHONPATH=project
python - <<'PY'
import json
from pathlib import Path

from meridian_ops.tools.oms import get_order
from meridian_ops.tools.policy_rag import retrieve_policy
from meridian_ops.tools.token_budget import budget_report, slim_order

orders_blob = Path("project/meridian_ops/fixtures/orders.json").read_text()
order = get_order("MC-1048292")["order"]
slim = json.dumps(slim_order(order))

print("=== OMS fat vs slim ===")
print(json.dumps(budget_report({"fat_orders_json": orders_blob, "slim_MC-1048292": slim}, limit=8000), indent=2))

hit = retrieve_policy("late grocery delivery credits", top_k=1)
retrieved = hit["documents"][0]["text"]
late = Path("project/meridian_ops/fixtures/policies/late_delivery_credits.md").read_text()
refund = Path("project/meridian_ops/fixtures/policies/refunds_damaged_items.md").read_text()

print("=== retrieve top_1 vs dump both policies ===")
print(json.dumps(
    budget_report(
        {
            "retrieve_top1": retrieved,
            "dump_both_policies": late + "\n" + refund,
        },
        limit=8000,
    ),
    indent=2,
))
print("winner path:", hit["documents"][0]["path"], "est_tokens field:", hit["documents"][0]["est_tokens"])
PY
```

   `python - <<'PY'` — run the script from stdin. Quotes `'PY'` mean the shell does not expand `$` inside the script.

2. Read the two reports. Confirm `fits` is true at `limit=8000` (these blobs are small). The lesson is the **ratio**, not the cap.

### Expect

OMS report (characters on your disk may match exactly):

```json
{
  "limit": 8000,
  "total_est_tokens": 372,
  "fits": true,
  "parts": [
    {"name": "fat_orders_json", "chars": 1315, "est_tokens": 328},
    {"name": "slim_MC-1048292", "chars": 176, "est_tokens": 44}
  ]
}
```

Fat `orders.json` is about **7×** the slim Maya row. You still did not need the other three orders for a late-credit question.

Policy report:

- `retrieve_top1` ≈ **186** tokens (`late_delivery_credits.md`).
- `dump_both_policies` ≈ **312** tokens.

Two files is still tiny. A real wiki is not. The pattern scales: retrieve `top_k`, do not dump `*.md`.

Winner path prints `late_delivery_credits.md` and `est_tokens` **186**.

Which evidence channel to use (keep this next to the numbers):

| Question | Best channel | Failure if you pick wrong |
|----------|--------------|---------------------------|
| Is `MC-1048292` delivered? | `get_order` (OMS) | Invented scans |
| What is the late credit amount? | `retrieve_policy` (RAG) | Invented $50 |
| Does Maya prefer SMS? | Long-term memory (Lesson 19) | You cannot know from this chat |
| What did we already try this session? | State | Repeat the same retrieve blindly, or forget the order id |
| Attach the OMS snapshot to the case | Artifact | Stuffing JSON into the prompt forever |

> **Tip:** `budget_report` sorts largest first. When a new specialist starts failing with “context too long,” run this on that turn’s parts before you buy a bigger model.

> **Watch out:** Slim is for **prompts**. Logging and audit (Lesson 07) may still store the full order. Do not slim away evidence Priya needs in a file; slim what the **model** is forced to attend to.

### Scoreboard after Task 6

| Proof | In place? |
|-------|-----------|
| Token estimates + slim_order | Yes |
| Policy fixtures | Yes |
| retrieve_policy + tests | Yes |
| Policy agent cites in `adk web` | Yes |
| Compaction | Yes |
| Budget before/after measured | **Yes** |

---

## How it works (deeper dive)

### Four stores, one ticket

Maya’s late-credit chat can touch all four:

| Need | Store | Today’s lab |
|------|-------|-------------|
| Exact policy language | RAG | `retrieve_policy` |
| Control-flow facts this ticket | State | `active_order_id` (Lesson 03) — do not put policy text here |
| Durable preference | Memory | Lesson 19 |
| Conversational cohesion | Transcript | Compact in Task 5 |
| Audit blob | Artifact | Later; don’t base64 a 12MB POD photo into state |

### Keyword retrieve vs Lesson 18

| | Lesson 06 (today) | Lesson 18 |
|--|-------------------|-----------|
| Unit of index | Whole `.md` file | Chunks (e.g. `POL-REFUND-04::Remedies`) |
| Score | Overlapping tokens + light boosts | Hybrid: keyword + embeddings |
| Miss | `NO_POLICY_HIT` | Same contract, better ranking |
| Tool name | `retrieve_policy` | Still `retrieve_policy` |

Keep the dict shape (`status`, `documents[].path`, `error_code`). Change the ranking later.

### Grounding vs tools vs memory

Grounding means the sentence in the bubble is tied to **this turn’s evidence**.

- Policy sentence → a `path` / policy id from retrieve
- Lifecycle sentence → `get_order` (not retrieve, not memory)
- “Maya prefers SMS” → memory write that you decided to store (Lesson 19), never as a stand-in for OMS

If those three blur, you will cite `POL-DELIVERY-01` for “was the milk on the shelf?” POD photos belong in an **artifact**, not base64 in state.

---

## Common pitfalls / troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `ModuleNotFoundError: meridian_ops` | `PYTHONPATH` not set | Repo root: `export PYTHONPATH=project`. From `project/`: `export PYTHONPATH=.` |
| `test_late_delivery_query` fails; refund file ranked first | Thin `policy_rag.py` without boosts, or fixtures missing | Replace with the Task 3 file; confirm both `.md` files exist |
| `NO_POLICY_HIT` on “late grocery delivery credits” | Empty `fixtures/policies/` or wrong `_POLICY_DIR` | `ls` the folder; `parents[1]` must be `meridian_ops/` |
| Agent invents $50 credit | Skipped retrieve, or you are on Order Status | Select `meridian_policy_agent`; trajectory must show the tool |
| Agent pastes the whole policy | Instruction too weak | “Keep quotes short”; restart `adk web` |
| `cannot import name 'estimate_tokens'` | Task 1 file still empty | Write the full `token_budget.py` |
| `cannot import name 'log_tool_event'` | Lesson 04 logging missing | Finish Lesson 04 `logging_utils.py` |
| Wifi miss still returns documents | Query contained `on` / `weather` / `policy` | Use `store wifi password reset` |
| Compaction drops `MC-1048292` | Id only in the **recent** turns you kept, or regex typo | Put ids in the older slice in the test; pattern is `MC-\d+` |
| `adk web` list has no policy agent | Ran from the wrong directory | Run from `project/` (parent of the package) |
| Import error inside `adk web` | Forgot `PYTHONPATH=.` | Export in the same shell, then restart |

---

## You are done when

- [ ] `pytest project/meridian_ops/tests/test_token_budget.py -v` — slim + overflow + compaction all `PASSED`
- [ ] `pytest project/meridian_ops/tests/test_policy_rag.py -v` — late query ranks delivery file; melted query ranks refund file; wifi query is `NO_POLICY_HIT`
- [ ] Retrieve JSON shows `path` values `late_delivery_credits.md` / `refunds_damaged_items.md` and `est_tokens` 186 / 125
- [ ] `adk web` on `meridian_policy_agent`: late-credit prompt cites `POL-DELIVERY-01` after a tool call
- [ ] Stacking turn does not cheerfully approve a stack without HITL language
- [ ] Miss prompt does not invent policy
- [ ] Fat vs slim `budget_report` printed in the terminal

---

## Knowledge check

Answer from this lab, not from general RAG lore.

1. Why is policy retrieve safer than “the model knows retail policies”?  
2. What belongs in **state** vs **long-term memory** vs **retrieve** for Maya and `MC-1048292`?  
3. What should happen on `NO_POLICY_HIT`?  
4. Why slim OMS payloads if the files are only a few hundred tokens today?  
5. For `"late grocery delivery credits"`, what were the two document totals (7 and 1), and which boost fired?  
6. Give one case where the transcript alone is the wrong evidence channel.

### Answers

1. Policies change. Retrieval + version citations track **your** corpus (`POL-DELIVERY-01`, 2026-07-01), not last year’s training data.  
2. State: `active_order_id` this ticket. Memory: SMS preference across months (Lesson 19). Retrieve: late-credit dollars from the markdown.  
3. Return the error dict; the agent says it cannot find a policy. No invented $50.  
4. Real OMS payloads grow (PII, line items). Slim is the habit; Task 6 already showed ~7× for the whole fixture vs one slim row.  
5. Delivery file **7** (4 token hits + late boost +3). Refund file **1** (`delivery` substring).  
6. Claiming delivery scans or “was this order late?” — that must come from `get_order`, not from chat or from `POL-DELIVERY-01`.

---

## Recap

**What you built:** `token_budget.py` (estimate, slim, compact), two versioned policy files, a keyword `retrieve_policy` with logs and token estimates, and a policy agent that must cite.

**What you now understand:** transcript / state / memory / RAG are different stores. Today is retrieve + cite. Keyword scores are explainable (you walked 7 vs 1).

**What you can do next:** Lesson 07 puts locks on refunds (`POL-REFUND-04`’s $75 HITL becomes Python). Lesson 18 upgrades ranking. Lesson 19 stores “Maya prefers SMS.”

---

## Stretch goal

Parse the policy id from the first heading line and return it as a first-class field:

```python
# inside the success documents list
"policy_id": "POL-DELIVERY-01",
"version": "2026-07-01",
```

Use a regex on the first two lines of `d["text"]`. Add a pytest assertion that `retrieve_policy("late grocery delivery credits")["documents"][0]["policy_id"] == "POL-DELIVERY-01"`.

Optional extra: treat `"melted" in tokens` the same as `"melt" in tokens` for the melt boost, and add a test that `"melted dairy"` still ranks the refund file first even if you remove the word `refund` from the query.

---

## Feedback

- Could you explain grounding vs memory to Priya in one minute using Maya and `MC-1048292`?  
- What tripped you up: retriever scoring, `PYTHONPATH`, compaction regex, or the policy agent wiring?  
- Note the **task number** and what you expected vs what happened (command + first lines of output).

---

## Navigate

**← Prev** [Lesson 05 — Multi-agent orchestration](05-multi-agent-orchestration.md)  
**Next →** [Lesson 07 — Reliability, safety, and control](07-reliability-safety-control.md)

# Lesson 19 — Memory systems deep dive

**Level:** Advanced  
**Time:** ~120–150 minutes  
**Prerequisites:** Lessons 03, 06, 18 (state vs memory vs RAG; sessions; hybrid policy retrieve)  
**Lab outcome:** Use ADK **`InMemoryMemoryService` + `load_memory`** for Meridian preferences, with a **write policy** that refuses secrets — and never treats memory as OMS truth

**Standard:** [docs/NATIVE-ADK.md](../docs/NATIVE-ADK.md)  
**Docs:** [ADK Memory](https://google.github.io/adk-docs/sessions/memory/)

---

## At a glance

Lesson 06 split four stores. Lesson 18 put **policy** in RAG. Today you put **preferences** in ADK memory — the native service, not a homemade “Maya prefs” database.

| Store | Lifetime | Meridian example | Source of truth? |
|-------|----------|------------------|------------------|
| Session transcript | One chat | Maya’s last turns | No |
| Session **state** | One ticket / run | `active_order_id` | Control-flow only |
| **Long-term memory** | Across sessions | “Maya prefers SMS” | Soft preferences |
| **RAG** | Just-in-time docs | POL-REFUND-04 chunk | Policy wiki |
| OMS tool | Live read | Order `MC-1048292` | **Yes for orders** |

You will prove the memory column with ADK 2.6.3, in this order:

| Task | What you build | Who enforces it | How you prove it |
|------|----------------|-----------------|------------------|
| 1 | Native imports | ADK | `python -c` prints the real classes |
| 2 | Capture → ingest → recall SMS | `Runner` + `InMemoryMemoryService` | `RECALL:` line contains **SMS** |
| 3 | Write policy (allow prefs, deny secrets) | Your Python | `pytest` — no LLM |
| 4 | Gate `add_session_to_memory` | Your Python + Task 2 loop | Card session is **not** ingested |
| 5 | Consolidation (many turns → one fact) | Your Python | `pytest` — one SMS sentence |
| 6 | Memory vs RAG vs OMS on one agent | `LlmAgent` + three tools | Three questions, three tools |
| 7 | PII boundary file next to the tests | Tests + a short markdown | Every deny rule has a passing test |

**Native pieces (ADK 2.6.3):**

- `from google.adk.memory import InMemoryMemoryService`
- `from google.adk.tools import load_memory` — this **is** a `LoadMemoryTool` instance; put it on `tools=[load_memory]`
- `await memory_service.add_session_to_memory(session)`
- `Runner(..., session_service=..., memory_service=...)`

**Not this lesson:** `AgentEvaluator` (that is Lesson 08). A DIY preference table that replaces `InMemoryMemoryService`. Treating a prior chat as proof that an order was refunded.

If you get lost, scroll back to the task table. The scoreboard at the end of every task repeats the same rows.

---

## Why this matters

Week 1: Maya says she prefers **SMS** for delivery updates.  
Week 4: new chat session — the agent asks for email again. CX feels dumb.

Worse failure: the agent “remembers” that order `MC-1048292` was refunded last week because a prior chat *said* so — while OMS still shows **delivered**, no refund. Memory is not a ledger.

You will teach the system:

1. What to **write** to memory (contact channel, language, accessibility)
2. What to **never** write (cards, passwords, “you already refunded me”)
3. How to **recall** with ADK `load_memory` in a **new** session
4. How to **compress** a noisy chat into one durable sentence before ingest
5. How memory, RAG, and OMS stay in their lanes when Maya asks three different questions

---

## Know these

Read this table before Task 1. Every later task reuses these words.

| Term | Plain English | Meridian example |
|------|---------------|------------------|
| **MemoryService** | ADK’s store for long-term, searchable knowledge across sessions | `InMemoryMemoryService` in this lab |
| **InMemoryMemoryService** | The lab implementation. Keyword overlap search. Lives in **this Python process**. | Same object on both Runners, or Maya has amnesia |
| **add_session_to_memory** | Copy a finished session’s events into the memory service | After Maya says “text me on SMS” |
| **load_memory** | Native ADK tool. The model passes a `query` string; ADK searches memory for this user | `query="SMS delivery contact"` |
| **preload_memory** | Native ADK tool that **injects** matching memories into the prompt every turn, without a model-visible call | Exists in 2.6.3; this lab uses `load_memory` so you can **see** the tool in the trajectory |
| **Write policy** | Rules for what may be stored | SMS yes; `4111 1111…` no |
| **Consolidation** | Compress many turns into one durable fact | “idk text is fine I guess” × 20 → one SMS sentence |
| **PII** | Personal data you must not spray into logs or memory | Phone, card, SSN, password |
| **Preference vs fact** | Soft “how to contact me” vs hard “this order was refunded” | SMS is a preference. Refunds are OMS. |

```
Session A  (maya_prefs_1)   Maya: "Please text me on SMS…"
        │
        ▼
memory_service.add_session_to_memory(session)
        │
        ▼
Session B  (maya_prefs_2)   Maya: "How should we contact me?"
        │
        ▼
load_memory(query=…)  ──►  RECALL: … SMS …
        │
        ✗  never skip get_order for money or status
```

### Picture this: the sticky note vs the cash office vs the policy binder

| Store | Store 441 analogue | Survives a new chat? | Can it pay Maya? |
|-------|--------------------|----------------------|------------------|
| Session state | Scratch paper on this ticket | No | No |
| MemoryService | Sticky note on Maya’s account: “prefers SMS” | **Yes** | No |
| RAG | Policy binder (POL-REFUND-04, POL-DELIVERY-01) | Yes (the wiki) | No — it only cites |
| OMS `get_order` | The register / order system | Yes | It is the **truth** for orders |

The sticky note is useful. It is not the register.

> **Tip:** `adk web` already constructs an `InMemoryMemoryService` for you. It does **not** call `add_session_to_memory` by itself. Without ingest, `load_memory` is an empty drawer. Task 2’s script is where you see the full loop.

---

## What you already have (do not rebuild)

| Path | Job |
|------|-----|
| `project/meridian_ops/tools/oms.py` | `get_order` — live order truth |
| `project/meridian_ops/fixtures/orders.json` | `MC-1048292` delivered, no POD; `MC-1048277` melted dairy |
| `project/meridian_ops/tools/policy_rag.py` | `retrieve_policy_hybrid` from Lesson 18 |
| Lesson 03 sessions | `InMemorySessionService` + `Runner` |

If hybrid retrieve is missing, finish Lesson 18 first. Task 6 calls that tool by name.

You will **add**:

```
project/meridian_ops/memory/
  __init__.py
  demo_maya_sms.py          Task 2
  write_policy.py           Task 3
  safe_ingest.py            Task 4
  demo_gated_ingest.py      Task 4
  consolidate.py            Task 5
  demo_three_stores.py      Task 6
  PII_CHECKLIST.md          Task 7
project/meridian_ops/tests/
  test_memory_write_policy.py
  test_memory_safe_ingest.py
  test_memory_consolidate.py
project/meridian_memory_agent/
  agent.py                  Task 6 (doorbell)
```

---

## Task 1 — Verify native memory imports

### Why

If these imports fail, people invent a JSON file of preferences and call it “memory.” That file is not searchable by `load_memory`, not wired into `Runner`, and not what you will operate in cloud later.

This lab uses **ADK 2.6.3**. Confirm that, then import the exact symbols.

### Do this

1. From the **repo root**, activate the venv you have used since Lesson 02:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
source .venv/bin/activate
python -c "import google.adk as adk; print(adk.__version__)"
```

2. Import the memory stack this lesson uses:

```bash
python - <<'PY'
from google.adk.memory import InMemoryMemoryService
from google.adk.tools import load_memory
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

print("InMemoryMemoryService", InMemoryMemoryService)
print("load_memory", type(load_memory).__name__, load_memory.name)
print("Runner", Runner)
print("InMemorySessionService", InMemorySessionService)
PY
```

   What you are looking at:

   - `InMemoryMemoryService` — a **class**. You will construct **one** instance and share it.
   - `load_memory` — already a **`LoadMemoryTool` object**. You do not call `LoadMemoryTool()` yourself. You pass that object: `tools=[load_memory]`.
   - `Runner` — this is how you attach `memory_service=` (the `App` object used by some other lessons does not take a memory service).

### Expect

```
2.6.3
```

and then:

```
InMemoryMemoryService <class 'google.adk.memory.in_memory_memory_service.InMemoryMemoryService'>
load_memory LoadMemoryTool load_memory
Runner <class 'google.adk.runners.Runner'>
InMemorySessionService <class 'google.adk.sessions.in_memory_session_service.InMemorySessionService'>
```

`load_memory.name` is the string `"load_memory"`. That is the name you will see in a trajectory.

> **Tip:** `load_memory`’s description tells the model it takes `query: str` and returns a list of memory results. You do not wrap it.

> **Watch out:** Do not copy `load_memory`’s internals into a homemade `search_maya_prefs()`. If ingest and search do not go through `MemoryService`, you built a second product.

### Scoreboard after Task 1

| Piece | In place? |
|-------|-----------|
| Native imports | **Yes** |
| Capture → ingest → SMS recall | Not yet |
| Write policy | Not yet |
| Gated ingest | Not yet |
| Consolidation | Not yet |
| Three-store agent | Not yet |
| PII file | Not yet |

---

## Task 2 — Capture → ingest → recall (Maya prefers SMS)

### Why

You need the full loop once with your hands before writing policies.

Two **sessions**. Two **session ids**. Two **Runners**. **One** `memory_service`.

| Piece | Session A (`maya_prefs_1`) | Session B (`maya_prefs_2`) |
|-------|----------------------------|----------------------------|
| Agent | `preference_capture` — no tools | `preference_recall` — `tools=[load_memory]` |
| Runner | `runner_cap` | `runner_rec` |
| User message | “Please text me on SMS… Don’t email.” | “How should we contact me about my delivery?” |
| After the run | `add_session_to_memory` | Print `RECALL:` |

If the two Runners get **different** `InMemoryMemoryService()` objects, Session B is empty. That is the entire bug class this task exists to burn into muscle memory.

`InMemoryMemoryService` search is **keyword overlap**, not Lesson 18’s vectors. A stored turn about SMS matches a query that shares words like `SMS`, `text`, `email`, or `delivery`. The recall instruction will tell the model to search with those words.

### Do this

1. Create the package. From the **repo root**:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
mkdir -p project/meridian_ops/memory
```

   Create empty `project/meridian_ops/memory/__init__.py`. Python needs this so `python -m meridian_ops.memory.demo_maya_sms` works.

2. Create `project/meridian_ops/memory/demo_maya_sms.py`. Read the file in layers after you paste it — do not run until you can point at `sid1`, `sid2`, and the single `memory_service`.

```python
from __future__ import annotations

import asyncio

from google.adk.agents.llm_agent import Agent
from google.adk.memory import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import load_memory
from google.genai import types

APP = "meridian_memory_lab"
USER = "maya_c44102"
MODEL = "gemini-3.5-flash"

capture = Agent(
    model=MODEL,
    name="preference_capture",
    instruction="Acknowledge the customer's preference in one short sentence. Do not invent orders.",
)

recall = Agent(
    model=MODEL,
    name="preference_recall",
    instruction="""
Answer using load_memory when the question is about past preferences.
Call load_memory with a query that includes words like SMS, text, email, or delivery.
If memory is empty, say you do not have a saved preference.
Never invent order status or refund amounts from memory.
""".strip(),
    tools=[load_memory],
)

session_service = InMemorySessionService()
memory_service = InMemoryMemoryService()


async def main() -> None:
    runner_cap = Runner(
        agent=capture,
        app_name=APP,
        session_service=session_service,
        memory_service=memory_service,
    )
    sid1 = "maya_prefs_1"
    await session_service.create_session(
        app_name=APP, user_id=USER, session_id=sid1
    )
    msg1 = types.Content(
        role="user",
        parts=[
            types.Part.from_text(
                text="Please text me on SMS for delivery updates. Don't email."
            )
        ],
    )
    async for _ in runner_cap.run_async(
        user_id=USER, session_id=sid1, new_message=msg1
    ):
        pass

    completed = await session_service.get_session(
        app_name=APP, user_id=USER, session_id=sid1
    )
    await memory_service.add_session_to_memory(completed)
    print("ingested session", sid1)

    probe = await memory_service.search_memory(
        app_name=APP, user_id=USER, query="SMS delivery"
    )
    texts = []
    for mem in probe.memories:
        for part in mem.content.parts or []:
            if part.text:
                texts.append(part.text)
    print("SEARCH:", " | ".join(texts)[:400])

    runner_rec = Runner(
        agent=recall,
        app_name=APP,
        session_service=session_service,
        memory_service=memory_service,
    )
    sid2 = "maya_prefs_2"
    await session_service.create_session(
        app_name=APP, user_id=USER, session_id=sid2
    )
    msg2 = types.Content(
        role="user",
        parts=[
            types.Part.from_text(
                text="How should we contact me about my delivery?"
            )
        ],
    )
    async for event in runner_rec.run_async(
        user_id=USER, session_id=sid2, new_message=msg2
    ):
        if event.is_final_response() and event.content and event.content.parts:
            print("RECALL:", event.content.parts[0].text)


if __name__ == "__main__":
    asyncio.run(main())
```

3. Walk the script **in this order** before you run it. Each step is why the next one exists.

   **Shared constants**

   - `APP = "meridian_memory_lab"` and `USER = "maya_c44102"` — memory is keyed by **app + user**. Change either on the second Runner and search returns nothing.
   - `MODEL = "gemini-3.5-flash"` — same lab model as Lesson 18.
   - `Agent` **is** ADK’s `LlmAgent`. Capture has **no** tools. Recall has **only** `load_memory`.

   **One session service, one memory service**

   - `session_service` holds both chats (two ids).
   - `memory_service` is the sticky-note drawer. Constructed **once**.

   **Runner 1 — capture (`sid1 = maya_prefs_1`)**

   - `Runner(..., session_service=session_service, memory_service=memory_service)` — `session_service` is required. `memory_service=` is how `load_memory` later finds the drawer. Capture does not call `load_memory`, but attaching the same object now means you cannot accidentally build a second drawer “later.”
   - `create_session(..., session_id=sid1)` is **async**. `await` it. This opens an empty chat named `maya_prefs_1`.
   - `run_async` streams events. The `async for _ in …: pass` loop is “run until the model finishes.” You do not need the capture text; you need the session **events** that ADK stored.
   - `get_session` reads those events back. `await memory_service.add_session_to_memory(completed)` copies them into the memory service. **This line is the ingest.** Skip it and Session B is empty.

   **Probe before the model (still Session A’s data)**

   - `search_memory(query="SMS delivery")` is the same search `load_memory` uses. You print `SEARCH:` so a failure is either “ingest never happened” or “the model ignored the tool” — two different bugs.

   **Runner 2 — recall (`sid2 = maya_prefs_2`)**

   - New `Runner` with the **recall** agent, **same** `session_service`, **same** `memory_service`.
   - New session id `maya_prefs_2`. That is the whole point: a **new** chat, not a longer transcript.
   - `load_memory` reads memory for `APP` + `USER`, not for `sid2`. Session id is the chat. User id is whose sticky notes.
   - `event.is_final_response()` is the customer-facing sentence. You prefix it with `RECALL:` so it is grep-able.

   ```
   sid1  capture  ──add_session_to_memory──►  memory_service
                                                    │
   sid2  recall   ──load_memory─────────────────────┘
   ```

4. Run it. This **does** call Gemini. You need the same `GOOGLE_API_KEY` (or ADC) you used in Lesson 02.

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
source .venv/bin/activate
export PYTHONPATH=project
python -m meridian_ops.memory.demo_maya_sms
```

   - `python -m meridian_ops.memory.demo_maya_sms` runs the module as a script from the package path.
   - `PYTHONPATH=project` — `import meridian_ops` means `project/meridian_ops`.

### Expect

Something like:

```
ingested session maya_prefs_1
SEARCH: Please text me on SMS for delivery updates. Don't email. | We'll text you on SMS for delivery updates.
RECALL: We'll contact you by SMS for delivery updates (not email).
```

What must be true:

- `ingested session maya_prefs_1` prints **before** `RECALL:`
- `SEARCH:` contains **SMS** (from the user turn, the model ack, or both)
- `RECALL:` contains **SMS** (not a blank “how would you like to be contacted?”)

The exact sentence varies. **SMS** does not.

If `SEARCH:` is empty, stop. Do not debug the recall prompt. Ingest failed (wrong user id, forgot `await add_session_to_memory`, or `completed` was `None`).

> **Tip:** Keyword search is why the capture text includes the letters **SMS** and **delivery**, and why the recall instruction says to query with those words. Cloud Memory Bank later extracts “prefers SMS” as a fact. The lab service stores **events** and matches words.

> **Watch out:** `InMemoryMemoryService()` called twice is two empty brains. `runner_cap` and `runner_rec` must share the object you assigned to `memory_service`.

> **Watch out:** Reusing `sid1` for the recall chat is not a memory test. That is the same transcript. The lesson is `maya_prefs_2`.

> **Watch out:** `add_session_to_memory` is **async** in ADK 2.6.3. `await` it. A missing `await` ingests a coroutine, not a session.

### Scoreboard after Task 2

| Piece | In place? |
|-------|-----------|
| Native imports | Yes |
| Capture → ingest → SMS recall | **Yes** |
| Write policy | Not yet |
| Gated ingest | Not yet |
| Consolidation | Not yet |
| Three-store agent | Not yet |
| PII file | Not yet |

---

## Task 3 — Write policy (what may enter memory)

### Why

Without a write policy, agents store card numbers, passwords, and gossip.

`add_session_to_memory` will happily ingest whatever events you hand it. ADK does not know Meridian’s rules. You decide **before** ingest.

This is domain code — the same idea as Lesson 07’s refund allowlist. It is **not** a second memory database. It returns allow / deny. Task 4 is what calls (or skips) the native ingest.

Three buckets:

| Decision | Example | Why |
|----------|---------|-----|
| Allow | “Please text me on SMS” | Soft preference; useful next week |
| Deny — secret | `4111 1111 1111 1111`, `password=…`, SSN | Memory dumps get audited |
| Deny — ledger claim | “You already refunded MC-1048292” | OMS is the register; chat lies |

### Do this

1. Create `project/meridian_ops/memory/write_policy.py`:

```python
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class WriteDecision:
    allow: bool
    category: str
    reason: str
    redacted_text: str | None = None


_CARD = re.compile(r"\b(?:\d[ -]*?){13,19}\b")
_SSN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
_EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
_PHONE = re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")

ALLOW_CATEGORIES = {
    "contact_channel": ["sms", "text me", "don't email", "call me", "push notification"],
    "language": ["spanish", "en español", "prefer english"],
    "accessibility": ["large text", "screen reader", "hard of hearing"],
}

DENY_ALWAYS = [
    ("payment_secret", _CARD, "Looks like a card number"),
    ("gov_id", _SSN, "Looks like SSN"),
    ("password", re.compile(r"password\s*[:=]", re.I), "Password material"),
]


def classify_memory_candidate(text: str) -> WriteDecision:
    raw = text.strip()
    for cat, pattern, reason in DENY_ALWAYS:
        if pattern.search(raw):
            return WriteDecision(False, cat, reason)

    lower = raw.lower()
    for category, cues in ALLOW_CATEGORIES.items():
        if any(c in lower for c in cues):
            cleaned = _PHONE.sub("[PHONE]", raw)
            cleaned = _EMAIL.sub("[EMAIL]", cleaned)
            return WriteDecision(True, category, "Matched preference cue", cleaned)

    if any(w in lower for w in ("refunded", "charged", "order mc-", "tracking")):
        return WriteDecision(
            False,
            "operational_claim",
            "Order/money claims belong in OMS tools, not memory",
        )

    return WriteDecision(False, "unclassified", "No allowlisted preference pattern")
```

   Walk the gates in order. First failure wins. You do not keep going “to be helpful.”

   | Gate | If it matches | Grocery picture |
   |------|---------------|-----------------|
   | Card / SSN / `password=` | `allow=False` immediately | Cash office does not photocopy PAN onto a sticky note |
   | Preference cue (`sms`, `text me`, …) | `allow=True`, phone/email replaced with `[PHONE]` / `[EMAIL]` | Keep the channel, drop the digits |
   | `refunded` / `order mc-` / `charged` | `operational_claim` | Register, not sticky note |
   | Anything else | `unclassified` | Default is **do not store** |

   The `redacted_text` is what consolidation (Task 5) may keep. The raw card string never becomes that field because secrets return first.

2. Create `project/meridian_ops/tests/test_memory_write_policy.py`:

```python
from meridian_ops.memory.write_policy import classify_memory_candidate


def test_allows_sms_preference():
    d = classify_memory_candidate(
        "Please text me on SMS for delivery updates."
    )
    assert d.allow is True
    assert d.category == "contact_channel"


def test_blocks_card_number():
    d = classify_memory_candidate("My card is 4111 1111 1111 1111")
    assert d.allow is False
    assert d.category == "payment_secret"


def test_blocks_refund_claim_as_memory():
    d = classify_memory_candidate("You already refunded MC-1048292 yesterday")
    assert d.allow is False
    assert d.category == "operational_claim"


def test_redacts_phone_on_allowed_preference():
    d = classify_memory_candidate("Text me on SMS at 512-555-0199")
    assert d.allow is True
    assert "512-555-0199" not in (d.redacted_text or "")
    assert "[PHONE]" in (d.redacted_text or "")
```

   Four tests, four promises: SMS passes; a Visa test number does not; a refund rumor does not; a phone on an otherwise-legal preference is stripped.

3. Run:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
source .venv/bin/activate
export PYTHONPATH=project
pytest project/meridian_ops/tests/test_memory_write_policy.py -v
```

   `-v` — verbose: each test name plus `PASSED` / `FAILED`.

### Expect

```
test_memory_write_policy.py::test_allows_sms_preference PASSED
test_memory_write_policy.py::test_blocks_card_number PASSED
test_memory_write_policy.py::test_blocks_refund_claim_as_memory PASSED
test_memory_write_policy.py::test_redacts_phone_on_allowed_preference PASSED
```

Optional one-liner:

```bash
python -c "from meridian_ops.memory.write_policy import classify_memory_candidate; print(classify_memory_candidate('Please text me on SMS for delivery updates.'))"
```

You should see `allow=True` and `category='contact_channel'`.

> **Tip:** Keep `ALLOW_CATEGORIES` in Python, not in the agent instruction. The instruction can *mention* SMS. The set is the lock.

> **Watch out:** `4111 1111 1111 1111` is a well-known test PAN pattern. If your regex requires 16 digits with no spaces, this test fails and a spaced card in a ticket would slip through. Keep the `(?:\d[ -]*?){13,19}` shape.

### Scoreboard after Task 3

| Piece | In place? |
|-------|-----------|
| Native imports | Yes |
| Capture → ingest → SMS recall | Yes |
| Write policy | **Yes** |
| Gated ingest | Not yet |
| Consolidation | Not yet |
| Three-store agent | Not yet |
| PII file | Not yet |

---

## Task 4 — Gate ingestion with the write policy

### Why

`add_session_to_memory` is powerful. Gate what you feed it.

A session is many texts (user + model). Rule for this lab:

- If **any** user-visible turn is an allowlisted preference, you **may** ingest.
- If **any** turn is a secret (card / SSN / password), you **must not** ingest — even if the same chat also said “text me.”
- Ledger claims (`refunded MC-…`) are not a reason to ingest.

Secrets win. That is the same “first failure wins” idea as Lesson 07’s validator.

You still call **native** `add_session_to_memory`. You just don’t call it for the card chat.

### Do this

1. Create `project/meridian_ops/memory/safe_ingest.py`:

```python
from __future__ import annotations

from typing import Any

from meridian_ops.memory.write_policy import classify_memory_candidate


def session_texts(session: Any) -> list[str]:
    """Extract user-visible texts from an ADK session."""
    out: list[str] = []
    for event in getattr(session, "events", []) or []:
        content = getattr(event, "content", None)
        if not content or not getattr(content, "parts", None):
            continue
        for part in content.parts:
            text = getattr(part, "text", None)
            if text:
                out.append(text)
    return out


def should_ingest_session(session: Any) -> tuple[bool, list[str]]:
    """Return whether to ingest + human reasons. Secrets always block."""
    reasons: list[str] = []
    allow_any = False
    secret_block = False
    for text in session_texts(session):
        decision = classify_memory_candidate(text)
        if decision.category in {"payment_secret", "gov_id", "password"}:
            secret_block = True
            reasons.append(f"BLOCK {decision.category}: {decision.reason}")
        elif decision.allow:
            allow_any = True
            reasons.append(f"ALLOW {decision.category}: {decision.reason}")
        else:
            reasons.append(f"SKIP {decision.category}: {decision.reason}")
    return (allow_any and not secret_block), reasons
```

   `session.events` is what `add_session_to_memory` copies. You classify the same texts ADK would store.

   Return value:

   | `should_ingest` | Meaning |
   |-----------------|---------|
   | `True` | At least one preference, and no secret |
   | `False` | No preference, or a secret appeared |

2. Create `project/meridian_ops/tests/test_memory_safe_ingest.py`. Tests use a tiny stub session so pytest does not need Gemini:

```python
from types import SimpleNamespace

from meridian_ops.memory.safe_ingest import should_ingest_session


def _session(*texts: str):
    events = []
    for text in texts:
        part = SimpleNamespace(text=text)
        content = SimpleNamespace(parts=[part])
        events.append(SimpleNamespace(content=content))
    return SimpleNamespace(events=events)


def test_sms_session_is_ingested():
    ok, reasons = should_ingest_session(
        _session("Please text me on SMS for delivery updates.")
    )
    assert ok is True
    assert any(r.startswith("ALLOW contact_channel") for r in reasons)


def test_card_session_is_blocked():
    ok, reasons = should_ingest_session(
        _session("My card is 4111 1111 1111 1111")
    )
    assert ok is False
    assert any("payment_secret" in r for r in reasons)


def test_sms_plus_card_is_blocked():
    ok, _ = should_ingest_session(
        _session(
            "Please text me on SMS.",
            "My card is 4111 1111 1111 1111",
        )
    )
    assert ok is False
```

   The third test is the one that matters: a preference does not launder a card.

3. Run the tests:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
source .venv/bin/activate
export PYTHONPATH=project
pytest project/meridian_ops/tests/test_memory_safe_ingest.py -v
```

4. Wire the gate into a **second** demo so you see skip vs ingest on real ADK sessions. Create `project/meridian_ops/memory/demo_gated_ingest.py`:

```python
from __future__ import annotations

import asyncio

from google.adk.agents.llm_agent import Agent
from google.adk.memory import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from meridian_ops.memory.safe_ingest import should_ingest_session

APP = "meridian_memory_lab"
USER = "maya_c44102"
MODEL = "gemini-3.5-flash"

capture = Agent(
    model=MODEL,
    name="preference_capture",
    instruction="Acknowledge in one short sentence. Do not invent orders.",
)

session_service = InMemorySessionService()
memory_service = InMemoryMemoryService()


async def run_and_maybe_ingest(sid: str, user_text: str) -> None:
    runner = Runner(
        agent=capture,
        app_name=APP,
        session_service=session_service,
        memory_service=memory_service,
    )
    await session_service.create_session(
        app_name=APP, user_id=USER, session_id=sid
    )
    msg = types.Content(
        role="user", parts=[types.Part.from_text(text=user_text)]
    )
    async for _ in runner.run_async(
        user_id=USER, session_id=sid, new_message=msg
    ):
        pass
    session = await session_service.get_session(
        app_name=APP, user_id=USER, session_id=sid
    )
    ok, reasons = should_ingest_session(session)
    print(f"--- {sid} ingest={ok} ---")
    for line in reasons:
        print(" ", line)
    if ok:
        await memory_service.add_session_to_memory(session)
        print("  called add_session_to_memory")
    else:
        print("  skipped add_session_to_memory")


async def main() -> None:
    await run_and_maybe_ingest(
        "maya_sms_ok",
        "Please text me on SMS for delivery updates. Don't email.",
    )
    await run_and_maybe_ingest(
        "maya_card_no",
        "My card is 4111 1111 1111 1111 — save that for next time.",
    )
    probe = await memory_service.search_memory(
        app_name=APP, user_id=USER, query="4111 SMS"
    )
    leaked = " ".join(
        part.text or ""
        for mem in probe.memories
        for part in (mem.content.parts or [])
    )
    print("SEARCH_AFTER:", leaked[:400] or "(empty)")
    if "4111" in leaked:
        raise SystemExit("card digits landed in memory — gate failed")


if __name__ == "__main__":
    asyncio.run(main())
```

   Same Runner pattern as Task 2. The new if: **only** call `add_session_to_memory` when `should_ingest_session` is true.

5. Run:

```bash
export PYTHONPATH=project
python -m meridian_ops.memory.demo_gated_ingest
```

### Expect

Pytest:

```
test_memory_safe_ingest.py::test_sms_session_is_ingested PASSED
test_memory_safe_ingest.py::test_card_session_is_blocked PASSED
test_memory_safe_ingest.py::test_sms_plus_card_is_blocked PASSED
```

Demo output like:

```
--- maya_sms_ok ingest=True ---
  ALLOW contact_channel: Matched preference cue
  called add_session_to_memory
--- maya_card_no ingest=False ---
  BLOCK payment_secret: Looks like a card number
  skipped add_session_to_memory
SEARCH_AFTER: Please text me on SMS for delivery updates. Don't email. | …
```

`SEARCH_AFTER` may contain SMS. It must **not** contain `4111`.

> **Tip:** In production you may store a structured preference (`channel=sms`) via `add_memory` on the same `MemoryService`. Still never store the raw secret string.

> **Watch out:** Skipping ingest on the card session is the control. Redacting after ingest is too late — the digits already sat in `_session_events`.

### Scoreboard after Task 4

| Piece | In place? |
|-------|-----------|
| Native imports | Yes |
| Capture → ingest → SMS recall | Yes |
| Write policy | Yes |
| Gated ingest | **Yes** |
| Consolidation | Not yet |
| Three-store agent | Not yet |
| PII file | Not yet |

---

## Task 5 — Consolidation: noisy chat → one fact

### Why

Twenty turns of “idk text is fine I guess” should become one durable preference, not a novel.

`InMemoryMemoryService` stores **events**. If you ingest the whole rant, keyword search returns the rant. Priya does not want that in a dump. The model does not need it either.

**Consolidation** here is ordinary Python: keep allowlisted turns, last write wins per category, one sentence. You can ingest a **short** session that contains that sentence (same native API) instead of the full thread.

You are still not building a preference database. You are shrinking what you feed `add_session_to_memory`.

### Do this

1. Create `project/meridian_ops/memory/consolidate.py`:

```python
from __future__ import annotations

from meridian_ops.memory.write_policy import classify_memory_candidate


def consolidate_preference_turns(turns: list[str]) -> str | None:
    """Collapse allowlisted preference turns into a single memory sentence."""
    allowed: list[tuple[str, str]] = []
    for t in turns:
        d = classify_memory_candidate(t)
        if d.allow and d.redacted_text:
            allowed.append((d.category, d.redacted_text))
    if not allowed:
        return None
    by_cat = {cat: text for cat, text in allowed}
    parts = [f"{cat}: {text}" for cat, text in sorted(by_cat.items())]
    return "Customer preferences — " + "; ".join(parts)
```

   `by_cat = {cat: text for cat, text in allowed}` — later turns overwrite earlier ones. Maya says “email me” then “actually SMS” → SMS wins.

2. Create `project/meridian_ops/tests/test_memory_consolidate.py`:

```python
from meridian_ops.memory.consolidate import consolidate_preference_turns


def test_three_messy_sms_turns_become_one_fact():
    turns = [
        "idk text is fine I guess",
        "yeah please text me on SMS",
        "Don't email, SMS is better for delivery updates.",
    ]
    out = consolidate_preference_turns(turns)
    assert out is not None
    assert "contact_channel" in out
    assert "SMS" in out
    assert out.startswith("Customer preferences —")
    assert out.count("Customer preferences") == 1


def test_card_turns_do_not_consolidate():
    out = consolidate_preference_turns(
        ["My card is 4111 1111 1111 1111"]
    )
    assert out is None
```

   First turn `"idk text is fine I guess"` contains `"text me"` as a substring? It contains `"text is"` — the cue is `"text me"`. So turn 1 may be unclassified. Turns 2 and 3 match `sms` / `don't email`. Last SMS-ish turn wins. The assertion is **one** string that mentions SMS — not three transcripts.

3. Run:

```bash
export PYTHONPATH=project
pytest project/meridian_ops/tests/test_memory_consolidate.py -v
```

4. Prove the helper in a shell with the three messy turns:

```bash
python - <<'PY'
from meridian_ops.memory.consolidate import consolidate_preference_turns
print(consolidate_preference_turns([
    "idk text is fine I guess",
    "yeah please text me on SMS",
    "Don't email, SMS is better for delivery updates.",
]))
PY
```

### Expect

Pytest:

```
test_memory_consolidate.py::test_three_messy_sms_turns_become_one_fact PASSED
test_memory_consolidate.py::test_card_turns_do_not_consolidate PASSED
```

Shell prints one line like:

```
Customer preferences — contact_channel: Don't email, SMS is better for delivery updates.
```

Not a dump of all three turns.

Optional live path (same native ingest as Task 2): create a short session whose user text **is** that consolidated sentence, then `add_session_to_memory`. Do not invent a side table.

> **Tip:** Last-write-wins per category is how Maya can change her mind without you merging “email and SMS and maybe phone.”

> **Watch out:** Do not concatenate denied turns “for completeness.” Completeness is how PAN lands in memory.

### Scoreboard after Task 5

| Piece | In place? |
|-------|-----------|
| Native imports | Yes |
| Capture → ingest → SMS recall | Yes |
| Write policy | Yes |
| Gated ingest | Yes |
| Consolidation | **Yes** |
| Three-store agent | Not yet |
| PII file | Not yet |

---

## Task 6 — Memory vs RAG vs OMS (live agent)

### Why

SMEs do not confuse stores under incident pressure.

Maya can ask three questions in a row:

1. “How should you contact me?” → **memory** (`load_memory`) → SMS
2. “What’s the late delivery credit if 90 minutes late?” → **RAG** (`retrieve_policy_hybrid`) → POL-DELIVERY-01
3. “Was MC-1048292 refunded?” → **OMS** (`get_order`) → delivered, not a memory rumor

If the model answers (3) from a prior chat, you have a finance incident. The instruction says so. The **tool list** makes it possible. Task 2 already proved memory ingest. This task puts all three tools on one agent and runs the three asks in one process so they share `memory_service`.

`adk web` cannot see the memory your script ingested — different process, new `InMemoryMemoryService`. Use the script for the three-store drill. Use `adk web` later to click through RAG/OMS without expecting SMS recall unless you ingest in that same server.

### Do this

1. From `project/`, scaffold the ADK package:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme/project
source ../.venv/bin/activate
export PYTHONPATH=.
adk create meridian_memory_agent
```

   `adk create <name>` writes a small package next to `meridian_policy_agent`. The name is a positional argument.

2. Replace `project/meridian_memory_agent/agent.py`:

```python
from google.adk.agents.llm_agent import Agent
from google.adk.tools import load_memory

from meridian_ops.tools.oms import get_order
from meridian_ops.tools.policy_rag import retrieve_policy_hybrid

root_agent = Agent(
    name="meridian_memory_agent",
    model="gemini-3.5-flash",
    description="Uses memory for prefs, RAG for policy, OMS for orders.",
    instruction="""
You help Meridian customers.

Routing rules:
- Contact / language / accessibility preferences → load_memory first.
  Query with words like SMS, text, email, or delivery.
- Policy amounts / eligibility → retrieve_policy_hybrid (never memory).
  Cite policy_id + version + section.
- Order status, delivery, refunds → get_order (never memory as proof).
- If memory conflicts with get_order, trust get_order and say so.
- If retrieve_policy_hybrid returns NO_POLICY_HIT, do not invent policy.
""".strip(),
    tools=[load_memory, retrieve_policy_hybrid, get_order],
)
```

   Three tools, three truths. `request_refund` is not here.

3. Create `project/meridian_ops/memory/demo_three_stores.py`. It reuses Task 2’s ingest, then asks the three questions on **one** recall-style agent:

```python
from __future__ import annotations

import asyncio

from google.adk.memory import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from meridian_memory_agent.agent import root_agent
from meridian_ops.memory.demo_maya_sms import capture

APP = "meridian_memory_lab"
USER = "maya_c44102"

session_service = InMemorySessionService()
memory_service = InMemoryMemoryService()


async def ingest_sms() -> None:
    runner = Runner(
        agent=capture,
        app_name=APP,
        session_service=session_service,
        memory_service=memory_service,
    )
    sid = "maya_prefs_1"
    await session_service.create_session(
        app_name=APP, user_id=USER, session_id=sid
    )
    msg = types.Content(
        role="user",
        parts=[
            types.Part.from_text(
                text="Please text me on SMS for delivery updates. Don't email."
            )
        ],
    )
    async for _ in runner.run_async(
        user_id=USER, session_id=sid, new_message=msg
    ):
        pass
    session = await session_service.get_session(
        app_name=APP, user_id=USER, session_id=sid
    )
    await memory_service.add_session_to_memory(session)
    print("ingested", sid)


async def ask(sid: str, text: str) -> None:
    runner = Runner(
        agent=root_agent,
        app_name=APP,
        session_service=session_service,
        memory_service=memory_service,
    )
    await session_service.create_session(
        app_name=APP, user_id=USER, session_id=sid
    )
    msg = types.Content(
        role="user", parts=[types.Part.from_text(text=text)]
    )
    used = []
    final = ""
    async for event in runner.run_async(
        user_id=USER, session_id=sid, new_message=msg
    ):
        for call in getattr(event, "get_function_calls", lambda: [])() or []:
            used.append(call.name)
        if event.is_final_response() and event.content and event.content.parts:
            final = event.content.parts[0].text or ""
    print(f"=== {sid} ===")
    print("TOOLS:", used)
    print("TEXT:", final[:500])


async def main() -> None:
    await ingest_sms()
    await ask("q_memory", "How should you contact me about my delivery?")
    await ask(
        "q_rag",
        "What's the late delivery credit if 90 minutes late?",
    )
    await ask("q_oms", "Was MC-1048292 refunded?")


if __name__ == "__main__":
    asyncio.run(main())
```

   `event.get_function_calls()` is how ADK 2.6.3 exposes tool names on an event. If a run prints `TOOLS: []` but the text is still grounded, open the printed `TEXT` and the terminal tool logs — the model must not answer POL-DELIVERY-01 from memory or SMS from OMS.

4. Run from the **repo root** (so both `meridian_ops` and `meridian_memory_agent` import). `PYTHONPATH` must include `project`:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
source .venv/bin/activate
export PYTHONPATH=project
python -m meridian_ops.memory.demo_three_stores
```

### Expect

```
ingested maya_prefs_1
=== q_memory ===
TOOLS: ['load_memory']
TEXT: … SMS …
=== q_rag ===
TOOLS: ['retrieve_policy_hybrid']
TEXT: … POL-DELIVERY-01 … $10 …
=== q_oms ===
TOOLS: ['get_order']
TEXT: … MC-1048292 … delivered …
```

Tool lists can include extra calls (the model might retrieve then talk). What must **not** happen:

| Ask | Forbidden |
|-----|-----------|
| Contact me | Invent email; skip `load_memory` and guess |
| 90 minutes late | Quote a credit from memory; skip `retrieve_policy_hybrid` |
| Was MC-1048292 refunded? | “Yes, I remember refunding you” with no `get_order` |

OMS for `MC-1048292` is **delivered**, `pod_photo_present: false`. There is no refund in the fixture. The honest answer is order status from `get_order`, not a memory claim.

> **Tip:** `q_rag` is the Lesson 18 tool on purpose. Policy amounts never come from Maya’s sticky note.

> **Watch out:** Importing `capture` from `demo_maya_sms` also imports that module’s `session_service` / `memory_service` constants — but this script constructs **its own** pair and passes them into `Runner`. That is correct. Do not call `demo_maya_sms.main()` inside this process expecting to share those module-level services; `main()` would create a *third* story. Ingest here is `ingest_sms()`.

### Scoreboard after Task 6

| Piece | In place? |
|-------|-----------|
| Native imports | Yes |
| Capture → ingest → SMS recall | Yes |
| Write policy | Yes |
| Gated ingest | Yes |
| Consolidation | Yes |
| Three-store agent | **Yes** |
| PII file | Not yet |

---

## Task 7 — PII boundary file (from tests, not from memory)

### Why

Memory systems get audited. Priya’s skip-level will ask “what do we refuse to store?” A slogan is not an answer. A file next to the code, backed by the tests you already ran, is.

This is the same kind of artifact as Lesson 04’s `04-tool-safety.md`: durable judgment in the repo. It is not a worksheet you fill on paper.

### Do this

1. Re-run the three test files that **are** the checklist:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
source .venv/bin/activate
export PYTHONPATH=project
pytest project/meridian_ops/tests/test_memory_write_policy.py \
       project/meridian_ops/tests/test_memory_safe_ingest.py \
       project/meridian_ops/tests/test_memory_consolidate.py -v
```

2. Create `project/meridian_ops/memory/PII_CHECKLIST.md` and fill it from those results (and Task 2 / Task 6 runs), not from hope:

```markdown
# Lesson 19 — memory PII / lane checklist

Lab service: ADK InMemoryMemoryService (keyword search, this process).
Cloud later: VertexAiMemoryBankService (extracts/consolidates) or
VertexAiRagMemoryService (vector search over stored turns).
Product rules stay here regardless of service.

| Rule | Enforced by | Evidence |
|------|-------------|----------|
| Card / SSN / password denied before ingest | `classify_memory_candidate` + `should_ingest_session` | `test_blocks_card_number` PASSED; `test_card_session_is_blocked` PASSED |
| Phone/email redacted on allowed prefs | `classify_memory_candidate` | `test_redacts_phone_on_allowed_preference` PASSED |
| Operational claims denied as memory facts | `operational_claim` category | `test_blocks_refund_claim_as_memory` PASSED |
| Card + SMS in one session still blocked | secrets win | `test_sms_plus_card_is_blocked` PASSED |
| Order status from OMS, not memory | agent tools + instruction | `demo_three_stores` q_oms used `get_order` |
| Policy amounts from RAG, not memory | agent tools + instruction | `demo_three_stores` q_rag used `retrieve_policy_hybrid` |
```

### Expect

All listed pytest names `PASSED`. The markdown table has **evidence** in the third column — test names and demo ids — not “TODO.”

> **Tip:** When you add a new deny rule, add a test first, then a row. The file that lags the tests is how audits go stale.

> **Watch out:** Lab memory dies when the process exits. That is not a retention policy. Lesson 27 owns retention. Do not claim “we don’t store PII” because `InMemoryMemoryService` is ephemeral — the card chat still must not be ingested.

### Scoreboard after Task 7

| Piece | In place? |
|-------|-----------|
| Native imports | Yes |
| Capture → ingest → SMS recall | Yes |
| Write policy | Yes |
| Gated ingest | Yes |
| Consolidation | Yes |
| Three-store agent | Yes |
| PII file | **Yes** |

---

## How it works (deeper dive)

```
┌──────────────┐     ┌─────────────────┐     ┌──────────────┐
│ Session/state│     │ MemoryService   │     │ RAG corpus   │
│ this ticket  │     │ cross-session   │     │ policy wiki  │
└──────────────┘     └─────────────────┘     └──────────────┘
        │                      │                      │
        └──────────┬───────────┴──────────┬───────────┘
                   ▼                      ▼
              LlmAgent + tools      OMS / payments tools
                   │                      │
                   └──────── soft prefs   ┴── hard truth
```

### What `load_memory` actually does (ADK 2.6.3)

The object on `tools=[load_memory]` is a `LoadMemoryTool`. When the model calls it with `query`, ADK runs `tool_context.search_memory(query)`, which hits the `MemoryService` you passed to `Runner`.

`InMemoryMemoryService.search_memory`:

1. Look up events for `{app_name}/{user_id}`
2. Split the query into words
3. Return events whose text shares **any** of those words

That is why Task 2 probes with `query="SMS delivery"` and why the recall instruction says to search with those words.

### `load_memory` vs `preload_memory`

Both ship in ADK 2.6.3.

| Tool | Who calls it | What you see |
|------|--------------|--------------|
| `load_memory` | The model, as a function call | A trajectory row you can grep |
| `preload_memory` | ADK, every LLM request, using the user text as the query | Memories stuffed into the prompt; no model-visible call |

This lesson uses `load_memory` so the three-store drill can print `TOOLS: ['load_memory']`. You can add `preload_memory` later if you want silent injection. You still ingest with `add_session_to_memory`. You still gate with the write policy.

### Cloud services (same interface, not this lab’s install)

| Service | What it is for |
|---------|----------------|
| `InMemoryMemoryService` | Labs. Keyword. This process. |
| `VertexAiMemoryBankService` | Cloud. Extracts / consolidates meaningful memories. |
| `VertexAiRagMemoryService` | Cloud. Vector search over stored conversations. |

SME move: start local with a write policy; graduate the **service**, not the product rules. Do not replace `MemoryService` with a homemade prefs table when you move to cloud.

### Why two Runners in Task 2

`Runner` is bound to **one** `agent`. Capture must not have `load_memory` (nothing to load yet). Recall must not be the same session id. Two Runners, one `memory_service`, two session ids is the smallest picture that is still true in production.

---

## Common pitfalls / troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `RECALL:` asks how Maya wants to be contacted | Did not ingest, or two memory services | Share one `memory_service`; `await add_session_to_memory` |
| `SEARCH:` empty | Wrong `APP` / `USER`, or `get_session` returned `None` | Print `sid1`, `USER`, `APP`; confirm `create_session` used the same |
| `SEARCH:` has SMS but `RECALL:` does not | Model skipped `load_memory` | Keep the instruction that says to query SMS/text/delivery |
| Card digits in `SEARCH_AFTER` | Called ingest without the gate | Only ingest when `should_ingest_session` is true |
| Agent “remembers” a refund | Operational claim ingested, or OMS skipped | Write policy deny; Task 6 `get_order` |
| Policy $10/$25 from memory | RAG skipped | `retrieve_policy_hybrid` on amount questions |
| `ModuleNotFoundError: meridian_ops` | `PYTHONPATH` not set | Repo root: `export PYTHONPATH=project` |
| `python -m meridian_ops.memory.demo_maya_sms` fails | Missing `memory/__init__.py` | Add the empty init file |
| `TypeError` on `add_session_to_memory` | Forgot `await` | It is async in ADK 2.6.3 |
| `adk web` does not recall SMS | Different process; nothing ingested there | Use Task 2 / Task 6 scripts for the memory loop |
| Two `RECALL:` lines, neither has SMS | Final response vs streamed partials | Print only `event.is_final_response()` |

---

## You are done when

- [ ] Task 1 prints ADK `2.6.3`, `InMemoryMemoryService`, and `LoadMemoryTool` named `load_memory`
- [ ] `python -m meridian_ops.memory.demo_maya_sms` prints `ingested session maya_prefs_1` and `RECALL:` containing **SMS**
- [ ] Write-policy tests pass (SMS allow / card deny / refund-claim deny / phone redact)
- [ ] Unsafe card session is not ingested; `SEARCH_AFTER` has no `4111`
- [ ] Consolidation returns one preference string that mentions SMS
- [ ] `demo_three_stores` uses `load_memory` / `retrieve_policy_hybrid` / `get_order` on the three asks
- [ ] `PII_CHECKLIST.md` rows cite those tests, not TODOs

---

## Knowledge check

Answer from this lab, not from general “agent memory” lore.

1. What ADK object stores long-term searchable knowledge, and which class did you construct?  
2. Which tool does the agent call to query it, and what Python object did you put on `tools=`?  
3. Why must “you refunded me yesterday” not become a memory fact?  
4. What belongs in memory vs RAG vs OMS for Maya?  
5. Why share one `memory_service` across the two Runners? What are the two session ids for?  
6. `InMemoryMemoryService` search is keyword overlap. Why does the recall instruction mention SMS / delivery?

### Answers

1. A `MemoryService`. Lab: `InMemoryMemoryService()`.  
2. `load_memory`. You imported the ready `LoadMemoryTool` instance from `google.adk.tools`.  
3. Money and order outcomes are OMS truths. Chat claims drift and lie.  
4. Memory: SMS preference. RAG: late-credit schedule (`POL-DELIVERY-01`) / melted refund (`POL-REFUND-04`). OMS: `MC-1048292` lifecycle.  
5. Memory lives in the service **instance** — a new instance is an empty brain. `maya_prefs_1` is capture; `maya_prefs_2` is a new chat that must recall without the old transcript.  
6. The lab service does not embed “contact preference” into “SMS.” Shared words are the match. Cloud Memory Bank can extract facts; this lab cannot pretend it already did.

---

## Recap

- You ran native ADK memory end-to-end for Meridian preferences: **two sessions, two Runners, one `InMemoryMemoryService`**.  
- You enforced a **write policy** and consolidation **in front of** `add_session_to_memory`.  
- You kept memory out of the ledger and out of the policy wiki.

**What you can do next:** Lesson 20 routes Flash vs Pro and structured output. Preference recall should stay on a cheap model; refund propose should not.

---

## Stretch goal

Add `ttl_days` on `WriteDecision` (`contact_channel`: 365, `accessibility`: 365). Unit-test that an allowed SMS preference reports `365`.

Do **not** build a second store to expire rows. Document in `PII_CHECKLIST.md` that `VertexAiMemoryBankService` is where TTL lives in cloud (`ttl` on create). The lab service is process-scoped; exiting Python is not a retention program.

---

## Feedback

- Could you redo the three-store drill from memory (memory / RAG / OMS) without looking at the agent instruction?  
- What tripped you up: two Runners, keyword search, the ingest gate, or OMS vs memory?  
- Note the **task number** and what you expected vs what happened (command + first lines of output).

---

## Navigate

**← Prev** [Lesson 18 — Advanced RAG](18-advanced-rag-retail-policy.md)  
**Track home:** [README](../README.md)  
**Next:** [Lesson 20 — Model routing, fallbacks & structured output](20-model-routing-fallbacks-structured-output.md)

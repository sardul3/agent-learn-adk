# Lesson 19 — Memory systems deep dive

**Level:** Advanced  
**Time:** ~120 minutes  
**Prerequisites:** Lessons 03, 06, 18 (state vs memory vs RAG; sessions)  
**Lab outcome:** Use ADK **`MemoryService` + `load_memory`** for Meridian preferences, with a **write policy** that refuses to store secrets/PII the wrong way — and never treats memory as OMS truth

**Standard:** [docs/NATIVE-ADK.md](../docs/NATIVE-ADK.md)  
**Docs:** [ADK Memory](https://google.github.io/adk-docs/sessions/memory/)

---

## At a glance

| Store | Lifetime | Meridian example | Source of truth? |
|-------|----------|------------------|------------------|
| Session transcript | One chat | Maya’s last turns | No |
| Session **state** | One ticket/run | `active_order_id` | Control-flow only |
| **Long-term memory** | Across sessions | “Maya prefers SMS” | Soft preferences |
| **RAG** | Just-in-time docs | POL-REFUND-04 chunk | Policy wiki |
| OMS tool | Live read | Order `MC-1048292` | **Yes for orders** |

This lesson is about the memory column — with ADK natives, not a DIY “preference DB framework.”

**Native pieces:**

- `InMemoryMemoryService` (lab) → later `VertexAiMemoryBankService` / RAG memory in cloud  
- `Runner(..., memory_service=...)`  
- `add_session_to_memory` / search via **`load_memory` tool**  
- Optional: `preload_memory` tool when your ADK version ships it

---

## Why this matters

Week 1: Maya says she prefers SMS for delivery updates.  
Week 4: new chat session — agent asks for email again. CX feels dumb.

Worse failure: agent “remembers” that order `MC-1048292` was refunded last week because a prior chat *said* so — while OMS still shows delivered. Memory is not a ledger.

You will teach the system:

1. What to **write** to memory  
2. What to **never** write  
3. How to **recall** with ADK tools  
4. How to **consolidate** noisy chats into short facts  
5. How memory, RAG, and OMS stay in their lanes

---

## Know these

| Term | Meaning |
|------|---------|
| **MemoryService** | ADK interface to ingest + search long-term knowledge |
| **add_session_to_memory** | Ingest a finished (or snapshot) session into memory |
| **load_memory** | ADK tool: agent queries memory by natural language |
| **Write policy** | Rules for what may be stored, TTL, and redaction |
| **Consolidation** | Compress many turns into durable facts |
| **PII** | Personal data (phone, address, card, exact DOB) — handle with care |
| **Preference vs fact** | “Prefers SMS” (OK soft) vs “refunded $180” (must verify OMS) |

```
Session A (capture preference)
    │
    ▼
memory_service.add_session_to_memory(session)
    │
    ▼
Session B (new chat) ── load_memory("contact preference?") ──► SMS
                              │
                              ✗ never skip get_order for money/status
```

---

## Task 1 — Verify native memory imports

### Why

If imports fail, people invent JSON preference files and call it “memory.”

### Do this

```bash
source .venv/bin/activate
pip install -U "google-adk>=2.0.0"

python - <<'PY'
from google.adk.memory import InMemoryMemoryService
from google.adk.tools import load_memory
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
print("memory stack OK", InMemoryMemoryService, load_memory)
PY
```

If `load_memory` import path differs, inspect:

```bash
python - <<'PY'
import google.adk.tools as t
print([x for x in dir(t) if "memory" in x.lower()])
PY
```

Use the **installed** ADK symbol — still the native tool, not a DIY searcher.

### Expect

`memory stack OK` (or equivalent native tool name printed).

---

## Task 2 — Capture → ingest → recall (Maya prefers SMS)

### Why

You need the full loop once with your hands before writing policies.

### Do this

Create `project/meridian_ops/memory/demo_maya_sms.py`:

```python
import asyncio

from google.adk.agents import LlmAgent
from google.adk.memory import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import load_memory
from google.genai.types import Content, Part

APP = "meridian_memory_lab"
USER = "maya_c44102"
MODEL = "gemini-2.5-flash"

capture = LlmAgent(
    model=MODEL,
    name="preference_capture",
    instruction="Acknowledge the customer's preference in one short sentence. Do not invent orders.",
)

recall = LlmAgent(
    model=MODEL,
    name="preference_recall",
    instruction="""
Answer using load_memory when the question is about past preferences.
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
    await session_service.create_session(app_name=APP, user_id=USER, session_id=sid1)
    msg1 = Content(
        role="user",
        parts=[Part.from_text(text="Please text me on SMS for delivery updates. Don't email.")],
    )
    async for _ in runner_cap.run_async(user_id=USER, session_id=sid1, new_message=msg1):
        pass

    completed = await session_service.get_session(app_name=APP, user_id=USER, session_id=sid1)
    await memory_service.add_session_to_memory(completed)
    print("ingested session", sid1)

    runner_rec = Runner(
        agent=recall,
        app_name=APP,
        session_service=session_service,
        memory_service=memory_service,
    )
    sid2 = "maya_prefs_2"
    await session_service.create_session(app_name=APP, user_id=USER, session_id=sid2)
    msg2 = Content(
        role="user",
        parts=[Part.from_text(text="How should we contact me about my delivery?")],
    )
    async for event in runner_rec.run_async(user_id=USER, session_id=sid2, new_message=msg2):
        if event.is_final_response() and event.content and event.content.parts:
            print("RECALL:", event.content.parts[0].text)


if __name__ == "__main__":
    asyncio.run(main())
```

Run:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme/project
export PYTHONPATH=.
python -m meridian_ops.memory.demo_maya_sms
```

### Expect

Second session answer mentions **SMS** (via `load_memory`), not a blank “how would you like to be contacted?”

> **Watch out:** Capture and recall must share the **same** `memory_service` instance. Two fresh services = amnesia.

---

## Task 3 — Write policy (what may enter memory)

### Why

Without a write policy, agents store card numbers, passwords, and gossip.

### Do this

Create `project/meridian_ops/memory/write_policy.py`:

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
            # Prefer storing the category fact, not raw phone/email if present
            cleaned = _PHONE.sub("[PHONE]", raw)
            cleaned = _EMAIL.sub("[EMAIL]", cleaned)
            return WriteDecision(True, category, "Matched preference cue", cleaned)

    # Order/money claims → do not treat as durable memory facts
    if any(w in lower for w in ("refunded", "charged", "order mc-", "tracking")):
        return WriteDecision(
            False,
            "operational_claim",
            "Order/money claims belong in OMS tools, not memory",
        )

    return WriteDecision(False, "unclassified", "No allowlisted preference pattern")
```

Tests:

```python
from meridian_ops.memory.write_policy import classify_memory_candidate


def test_allows_sms_preference():
    d = classify_memory_candidate("Please text me on SMS for delivery updates.")
    assert d.allow and d.category == "contact_channel"


def test_blocks_card_number():
    d = classify_memory_candidate("My card is 4111 1111 1111 1111")
    assert not d.allow and d.category == "payment_secret"


def test_blocks_refund_claim_as_memory():
    d = classify_memory_candidate("You already refunded MC-1048292 yesterday")
    assert not d.allow and d.category == "operational_claim"
```

### Expect

Preferences pass; secrets and ledger claims fail.

---

## Task 4 — Gate ingestion with the write policy

### Why

`add_session_to_memory` is powerful. Gate what you feed it.

### Do this

Create `project/meridian_ops/memory/safe_ingest.py`:

```python
from __future__ import annotations

from typing import Any

from meridian_ops.memory.write_policy import classify_memory_candidate


def session_texts(session: Any) -> list[str]:
    """Extract user-visible texts from an ADK session (best-effort)."""
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
    """Return whether to ingest + human reasons."""
    reasons: list[str] = []
    allow_any = False
    for text in session_texts(session):
        decision = classify_memory_candidate(text)
        if decision.allow:
            allow_any = True
            reasons.append(f"ALLOW {decision.category}: {decision.reason}")
        else:
            reasons.append(f"SKIP {decision.category}: {decision.reason}")
    return allow_any, reasons
```

Wire into the demo: only call `add_session_to_memory` when `should_ingest_session` is true.  
Add a second run where the user pastes a fake card — **must not ingest**.

### Expect

- SMS session → ingested  
- Card session → skipped (print SKIP reasons)

> **Tip:** In production you may still store a *redacted* structured preference (`channel=sms`) via `add_memory` if your service supports it — never the raw secret string.

---

## Task 5 — Consolidation: noisy chat → one fact

### Why

Twenty turns of “idk text is fine I guess” should become one durable preference, not a novel.

### Do this

Create `project/meridian_ops/memory/consolidate.py`:

```python
from __future__ import annotations

from meridian_ops.memory.write_policy import classify_memory_candidate


def consolidate_preference_turns(turns: list[str]) -> str | None:
    """Collapse allowlisted preference turns into a single memory sentence."""
    allowed = []
    for t in turns:
        d = classify_memory_candidate(t)
        if d.allow and d.redacted_text:
            allowed.append((d.category, d.redacted_text))
    if not allowed:
        return None
    # Last write wins per category
    by_cat = {cat: text for cat, text in allowed}
    parts = [f"{cat}: {text}" for cat, text in sorted(by_cat.items())]
    return "Customer preferences — " + "; ".join(parts)
```

Test with three messy turns that all imply SMS; assert one consolidated string mentioning SMS / `contact_channel`.

Optional live path: after consolidation, put the summary into a short “memory note” session and ingest **that** instead of the full rant.

### Expect

One short preference string — not a transcript dump.

---

## Task 6 — Memory vs RAG vs OMS decision drill (live agent)

### Why

SMEs don’t confuse stores under incident pressure.

### Do this

Build a tiny OrderOps-facing agent `project/meridian_memory_agent/agent.py`:

```python
from google.adk.agents.llm_agent import Agent
from google.adk.tools import load_memory

from meridian_ops.tools.oms import get_order  # Lesson 04 tool
from meridian_ops.tools.policy_rag import retrieve_policy_hybrid  # Lesson 18

root_agent = Agent(
    name="meridian_memory_agent",
    model="gemini-2.5-flash",
    description="Uses memory for prefs, RAG for policy, OMS for orders.",
    instruction="""
You help Meridian customers.

Routing rules:
- Contact/language/accessibility preferences → load_memory first.
- Policy amounts/eligibility → retrieve_policy_hybrid (never memory).
- Order status, delivery, refunds → get_order (never memory as proof).
- If memory conflicts with get_order, trust get_order and say so.
""".strip(),
    tools=[load_memory, retrieve_policy_hybrid, get_order],
)
```

Ensure your `Runner` / `adk web` app for this agent is constructed with `memory_service=` (see Task 2). Ingest Maya’s SMS preference first.

Live asks:

1. “How should you contact me?” → memory / SMS  
2. “What’s the late delivery credit if 90 minutes late?” → RAG citation  
3. “Was MC-1048292 refunded?” → `get_order` only  

### Expect

Three different tools for three different truths.

---

## Task 7 — PII boundary checklist (operational)

### Why

Memory systems get audited. You need a checklist you can run, not a slogan.

### Do this

Create `project/meridian_ops/memory/PII_CHECKLIST.md` and tick it against your code:

- [ ] Card / SSN / password patterns denied before ingest  
- [ ] Phone/email redacted in stored preference text when present  
- [ ] Operational claims (refunded/charged) denied as memory facts  
- [ ] Order status always from OMS tool in agent instructions  
- [ ] Policy amounts always from RAG tool  
- [ ] Lab uses `InMemoryMemoryService`; prod choice documented (Memory Bank vs RAG memory)

### Expect

All boxes checked with honest notes — not aspirational TODOs.

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
              LlmAgent + tools      OMS/Payments tools
                   │                      │
                   └──────── soft prefs   ┴── hard truth
```

**InMemoryMemoryService:** keyword-ish search; perfect for labs.  
**VertexAiMemoryBankService:** extracts/consolidates meaningful memories in cloud.  
**VertexAiRagMemoryService:** vector search over stored conversations.

SME move: start local with a write policy; graduate the **service**, not the product rules.

---

## Common pitfalls / troubleshooting

| Symptom | Fix |
|---------|-----|
| Recall session knows nothing | Shared `memory_service`? Did you `add_session_to_memory`? |
| Agent “remembers” a refund | Ban operational claims in write policy; force `get_order` |
| Card digits in memory dump | Deny regex + never log raw session texts |
| Memory vs RAG fight on $25 | Instruction: policy → RAG only |
| `load_memory` import error | Inspect installed `google.adk.tools`; don’t DIY |
| Ingesting every session blindly | Gate with `should_ingest_session` |

---

## You are done when

- [ ] Capture → ingest → recall demo prints SMS on session 2  
- [ ] Write-policy unit tests pass (allow / card / refund-claim)  
- [ ] Unsafe session is not ingested  
- [ ] Consolidation returns one preference string  
- [ ] Live agent uses memory / RAG / OMS on the three drill questions  
- [ ] PII checklist filed  

---

## Knowledge check

1. What ADK object stores long-term searchable knowledge?  
2. Which tool does the agent call to query it?  
3. Why must “you refunded me yesterday” not become a memory fact?  
4. What belongs in memory vs RAG vs OMS for Maya?  
5. Why share one `memory_service` across runners?

### Answers

1. A `MemoryService` implementation (lab: `InMemoryMemoryService`).  
2. `load_memory` (native ADK tool).  
3. Money/order outcomes are OMS truths; chat claims drift and lie.  
4. Memory: SMS preference. RAG: credit schedule. OMS: order lifecycle.  
5. Memory lives in the service instance — new instance = empty brain.

---

## Recap

- You ran native ADK memory end-to-end for Meridian preferences.  
- You enforced a **write policy** and consolidation.  
- You kept memory out of the ledger and out of the policy wiki.

---

## Stretch goal

Add a TTL map (`contact_channel`: 365d, `accessibility`: 365d) and a sweeper that drops expired lab memories — document how Memory Bank would replace the sweeper in cloud.

---

## Feedback

- Could you redo the three-store drill from memory (memory / RAG / OMS)?  
- Note task number + expected vs actual for any failure.

---

## Navigate

**← Prev** [Lesson 18 — Advanced RAG](18-advanced-rag-retail-policy.md)  
**Track home:** [README](../README.md)  
**Next:** [Lesson 20 — Model routing, fallbacks & structured output](20-model-routing-fallbacks-structured-output.md)

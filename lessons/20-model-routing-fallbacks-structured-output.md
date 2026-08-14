# Lesson 20 — Model routing, fallbacks & structured output

**Level:** Advanced  
**Time:** ~120 minutes  
**Prerequisites:** Lessons 05, 08, 13 (multi-agent, evals, workflows)  
**Lab outcome:** Route Meridian tickets to **Flash vs Pro**, degrade safely when a model fails, and force machine-readable refund decisions with ADK **`output_schema`**

**Standard:** [docs/NATIVE-ADK.md](../docs/NATIVE-ADK.md)

---

## At a glance

Not every ticket deserves your heaviest model. Not every answer can be a paragraph.

| Problem | SME fix | Who enforces it |
|---------|---------|-----------------|
| Every ticket hits Pro | **Route** by ticket features | Your Python (`pick_model`) |
| Pro is down or rate-limited | **Fallback** to Flash + a `degraded` flag | Your Python (`run_with_model_fallback`) |
| “Approve maybe?” in free text | **`output_schema`** (Pydantic) on a decision agent | ADK `LlmAgent` |
| Silent JSON drift | Validate + pytest gate | CI |

You keep using ADK `Agent` (`LlmAgent` — same class). You change **which model string** you pass, and **how the final reply is shaped**.

You will build six pieces, in this order, and prove each one before the next:

| Task | What you add | How you prove it |
|--------------------|------------------|
| 1 | Ticket **features** | `pytest` — no LLM |
| 2 | **Flash vs Pro** router | `pytest` — no LLM |
| 3 | Agent **factory** (`model=` at build time) | Factory test + `InMemoryRunner` smoke |
| 4 | **Fallback** chain with `degraded` | `pytest` stubs — no LLM |
| 5 | **`RefundDecision` `output_schema`** | `InMemoryRunner` + session state |
| 6 | Eval / CI **gate** | `pytest` on routes + schema |

If you get lost, scroll back to this table. Each task fills one row. The scoreboard at the end of every task repeats the same rows.

---

## Why this matters

Two tickets land in the same minute at Store 441.

Devon (picker) on the handheld:

> “Short one SKU on a $12 BOPIS — tell the customer.”

**BOPIS** means buy-online-pickup-in-store. One missing yogurt. Basket is **$12**. Devon needs a one-line script in a few seconds. That is **Flash** work: fast and cheap.

Priya (CX supervisor) in the queue:

> “Customer wants $180 refund on melted dairy; POD photo disputed.”

**POD** means proof-of-delivery photo. Amount is over Meridian’s **$75** HITL line from Lesson 04 / `POL-REFUND-04`. That needs **Pro**: heavier judgment. It also needs a **structured** object your HITL UI can render — not a poem:

```json
{
  "decision": "escalate_hitl",
  "refund_usd": 180,
  "policy_ids": ["POL-REFUND-04"],
  "risk": "high",
  "customer_summary": "Melted dairy; photo disputed.",
  "supervisor_reason": "Amount over $75 and POD evidence is contested."
}
```

If the model replies with a paragraph, Priya’s screen has nothing to click. If every ticket pays for Pro, Finance asks why a $12 short costs the same as a disputed refund.

Today you split **route**, **fallback**, and **shape**.

---

## Know these

Read this table before Task 1. Every later task reuses these words.

| Term | Plain English | Meridian example |
|------|---------------|------------------|
| **Flash** | Fast, cheap Gemini. Good for volume and simple lookup. | `gemini-3.5-flash` on a $12 BOPIS short |
| **Pro** | Heavier judgment. Slower and more expensive. | `gemini-3.5-pro` on a $180 melted-dairy dispute |
| **Model routing** | Your code picks the model **before** the agent runs | Shortage → Flash; high-$ refund → Pro |
| **Ticket features** | Boring, testable facts extracted from the ticket | intent, dollar amount, POD dispute flag |
| **Fallback** | Next model when the first one fails | Pro timeout → Flash + `degraded=true` |
| **Graceful degrade** | Still useful under failure; never pretend you are fine | Status + “human will follow up”; **no** auto-refund |
| **`output_schema`** | ADK forces the agent’s **final** reply to match a Pydantic model | `RefundDecision` |
| **`output_key`** | Session-state slot where that validated object lands | `state["refund_decision"]` |
| **Structured output** | Fields a program can read, not a paragraph a human skims | `decision`, `refund_usd`, `policy_ids` |
| **HITL** | Human in the loop — Priya must click before money moves | Refunds ≥ $75 |
| **`allow_auto_money`** | Router flag: may this path move money without a person? | Always `False` in this lab |

### Picture this: the express lane vs the manager desk

| Ticket | Store 441 analogue | Model |
|--------|--------------------|-------|
| $12 BOPIS short | Express lane: scan, bag, smile | Flash |
| $180 melted dairy + disputed photo | Manager desk: policy binder + Priya’s key | Pro |
| Pro’s lane is closed | Open the express lane, **label the bag “needs follow-up”** | Flash + `degraded` |

```
Ticket text (+ optional OMS row)
        │
        ▼
 extract_features  ── intent, $, POD flag, upset flag
        │
        ▼
 pick_model  ── RouteDecision(model, reason, allow_auto_money=False)
        │
        ├─ Flash specialist   ($12 BOPIS, WISMO, policy FAQ)
        └─ Pro specialist     ($180 refund / POD dispute)
                    │
                    ▼ on failure
             Flash + degraded=true
                    │
                    ▼
         output_schema RefundDecision  (money path only)
```

`Agent` is `LlmAgent`. Same class. This curriculum uses `Agent` as the doorbell name, matching Lessons 03–07.

> **Tip:** Routing is **not** a sentence in the instruction that says “use your best judgment about models.” The model does not pick its own model. Your Python does.

> **Watch out:** Lesson 13’s workflow also has a type named `RouteDecision` (WISMO / SHORTAGE / REFUND **path**). This lesson’s `RouteDecision` is **which Gemini model**. Different files. Do not import one into the other.

---

## What you already have (do not rebuild)

From the **repo root**, confirm these exist.

| Path | Job |
|------|-----|
| `project/meridian_ops/tools/oms.py` | `get_order` |
| `project/meridian_ops/tools/policy_rag.py` | `retrieve_policy` (Lesson 06; Lesson 18 may have thickened it) |
| `project/meridian_ops/fixtures/policies/refunds_damaged_items.md` | `POL-REFUND-04` — HITL over $75 |
| `project/meridian_ops/fixtures/orders.json` | `MC-1048310` (BOPIS short), `MC-1048277` (melted dairy $214.55) |
| `project/meridian_ops/tools/payments.py` | Preview / confirm / `$75` HITL flag (Lesson 04) |

If `get_order` is missing, stop and finish Lesson 03/04. This lesson **routes** those tools. It does not replace them.

You will **add**:

```
project/meridian_ops/
  routing/
    __init__.py
    features.py          Task 1
    model_router.py      Task 2
    agents.py            Task 3
    fallback.py          Task 4
    schemas.py           Task 5
    refund_decision_agent.py  Task 5
    guards.py            Task 6
  tests/
    test_features.py
    test_model_router.py
    test_fallback.py
    test_routed_agent.py
    test_refund_schema.py
```

---

## Task 1 — Ticket features the router can test

### Why

Routers need boring facts. “This ticket feels spicy” is not a fact.

Devon’s $12 short and Priya’s $180 dispute must produce **different** feature objects, every time, from the same Python, with no Gemini in the room.

### Do this

1. Create the package. From the **repo root**:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
mkdir -p project/meridian_ops/routing
```

   `mkdir -p` creates the folder and does not complain if it already exists.

2. Create empty `project/meridian_ops/routing/__init__.py`. Python needs this so `import meridian_ops.routing.features` works.

3. Create `project/meridian_ops/routing/features.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TicketFeatures:
    intent: str  # wismo | shortage | refund | policy | other
    order_total_usd: float | None
    requested_refund_usd: float | None
    has_pod_dispute: bool
    needs_policy: bool
    customer_upset: bool


def _first_dollar(text: str) -> float | None:
    """Return the first $amount in the ticket, or None."""
    for token in text.replace("$", " $").split():
        if token.startswith("$"):
            try:
                return float(token[1:].replace(",", "").rstrip(".,"))
            except ValueError:
                continue
    return None


def extract_features(ticket_text: str, order: dict[str, Any] | None = None) -> TicketFeatures:
    t = ticket_text.lower()
    intent = "other"
    if any(w in t for w in ("where is", "wismo", "tracking", "eta")):
        intent = "wismo"
    elif any(w in t for w in ("short", "out of stock", "substitute", "bopis")):
        intent = "shortage"
    elif any(w in t for w in ("refund", "money back", "charged")):
        intent = "refund"
    elif any(w in t for w in ("policy", "credit if late", "allowed to")):
        intent = "policy"

    dollar = _first_dollar(t)

    requested = dollar if intent == "refund" else None

    total = None
    if order and order.get("order_total_usd") is not None:
        total = float(order["order_total_usd"])
    elif intent in {"shortage", "wismo"} and dollar is not None:
        total = dollar

    has_pod_dispute = (
        ("pod" in t and "disput" in t)
        or ("photo" in t and "disput" in t)
        or ("photo" in t and "not" in t)
        or ("wrong house" in t)
    )

    return TicketFeatures(
        intent=intent,
        order_total_usd=total,
        requested_refund_usd=requested,
        has_pod_dispute=has_pod_dispute,
        needs_policy=intent in {"policy", "refund"},
        customer_upset=any(
            w in t for w in ("furious", "lawyer", "unacceptable", "third time")
        ),
    )
```

   Walk the function in order:

   ```
   lower the text
     → pick intent (first match wins: wismo, shortage, refund, policy, else other)
       → parse the first $ amount
         → refund tickets: that $ is requested_refund_usd
         → shortage / WISMO tickets: that $ is order_total_usd (basket size), unless OMS already gave a total
           → POD dispute flag
             → needs_policy if refund or policy
               → customer_upset from a short swear/legal list
   ```

   Why `$12` and `$180` land in **different slots**:

   | Ticket | Intent | Where the `$` goes | Why |
   |--------|--------|--------------------|-----|
   | “Short one SKU on a $12 BOPIS” | `shortage` | `order_total_usd=12` | Basket size, not a refund request |
   | “Customer wants $180 refund…” | `refund` | `requested_refund_usd=180` | Money they asked for |

   - `frozen=True` — once built, nobody mutates the features mid-route. Tests stay honest.
   - Intent checks are **ordered**. “Short” is checked before “refund”, so “shorted item, also mention refund policy” still counts as shortage. That is a choice. Own it in tests.
   - `_first_dollar` uses `replace("$", " $")` so `$12` still splits as its own token when it sits against a letter (`BOPIS`).
   - `rstrip(".,")` so `$180.` at the end of a sentence still parses.

4. Create `project/meridian_ops/tests/test_features.py`. Five numbered cases — the two Meridian tickets plus three traps:

```python
from meridian_ops.routing.features import extract_features


def test_1_wismo_where_is_order():
    f = extract_features("Where is order MC-1048301 for pickup?")
    assert f.intent == "wismo"
    assert f.requested_refund_usd is None
    assert f.has_pod_dispute is False
    assert f.customer_upset is False


def test_2_twelve_dollar_bopis_short():
    f = extract_features("Short one SKU on a $12 BOPIS — tell the customer.")
    assert f.intent == "shortage"
    assert f.order_total_usd == 12.0
    assert f.requested_refund_usd is None
    assert f.needs_policy is False


def test_3_one_eighty_melted_dairy_pod_dispute():
    f = extract_features(
        "Customer wants $180 refund on melted dairy; POD photo disputed."
    )
    assert f.intent == "refund"
    assert f.requested_refund_usd == 180.0
    assert f.has_pod_dispute is True
    assert f.needs_policy is True


def test_4_policy_faq_is_not_a_refund():
    f = extract_features("What's Meridian's policy on late grocery delivery credits?")
    assert f.intent == "policy"
    assert f.needs_policy is True
    assert f.requested_refund_usd is None


def test_5_upset_words_set_the_flag():
    f = extract_features(
        "This is the third time and it is unacceptable. I will call a lawyer. Refund the melted dairy."
    )
    assert f.intent == "refund"
    assert f.customer_upset is True
```

5. Run **only** this file. From the **repo root**:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
source .venv/bin/activate
export PYTHONPATH=project
pytest project/meridian_ops/tests/test_features.py -v
```

   - `source .venv/bin/activate` — use this project’s Python, not Homebrew’s.
   - `export PYTHONPATH=project` — `import meridian_ops` means `project/meridian_ops`.
   - `-v` — verbose: print each test name and PASSED/FAILED.

### Expect

```
test_features.py::test_1_wismo_where_is_order PASSED
test_features.py::test_2_twelve_dollar_bopis_short PASSED
test_features.py::test_3_one_eighty_melted_dairy_pod_dispute PASSED
test_features.py::test_4_policy_faq_is_not_a_refund PASSED
test_features.py::test_5_upset_words_set_the_flag PASSED
```

You should see `intent='shortage'` with `order_total_usd=12.0` on the BOPIS ticket, and `intent='refund'` with `requested_refund_usd=180.0` and `has_pod_dispute=True` on the melted-dairy ticket.

> **Tip:** Pass a real OMS row when you have one: `extract_features(text, order=get_order("MC-1048277")["order"])`. OMS `order_total_usd` wins over a dollar parsed from chatty ticket text.

> **Watch out:** `"pod" in t or "photo" in t and "not" in t` without parentheses is a bug. `and` binds tighter than `or`, so any ticket that merely says “pod” would look like a dispute. Use the grouped form in the snippet above.

### Scoreboard after Task 1

| Piece | In place? |
|-------|-----------|
| Feature extractor | **Yes** |
| Flash vs Pro router | Not yet |
| Agent factory | Not yet |
| Fallback + `degraded` | Not yet |
| `output_schema` decision | Not yet |
| CI gate | Not yet |

---

## Task 2 — Pick Flash vs Pro in code, not in a hope

### Why

Putting “use Pro when it seems hard” in the instruction is not routing. The model cannot change `model=` after it has started. ADK binds the model when you construct the agent.

`pick_model` is a cashier rule: under this dollar amount, express lane; over it, manager desk. You can unit-test a cashier rule.

### Do this

1. Create `project/meridian_ops/routing/model_router.py`:

```python
from __future__ import annotations

from dataclasses import dataclass

from meridian_ops.routing.features import TicketFeatures

FLASH = "gemini-3.5-flash"
PRO = "gemini-3.5-pro"


@dataclass(frozen=True)
class RouteDecision:
    model: str
    reason: str
    allow_auto_money: bool


def pick_model(features: TicketFeatures) -> RouteDecision:
    high_money = (features.requested_refund_usd or 0) >= 75 or (
        features.order_total_usd or 0
    ) >= 150

    if features.intent == "refund" and (high_money or features.has_pod_dispute):
        return RouteDecision(
            model=PRO,
            reason="high-risk refund / POD dispute",
            allow_auto_money=False,
        )
    if features.customer_upset and features.intent in {"refund", "shortage"}:
        return RouteDecision(
            model=PRO,
            reason="elevated CX risk",
            allow_auto_money=False,
        )
    if features.intent in {"wismo", "shortage", "policy"}:
        return RouteDecision(
            model=FLASH,
            reason="standard ops / policy Q",
            allow_auto_money=False,
        )
    return RouteDecision(model=FLASH, reason="default", allow_auto_money=False)
```

   Four branches. Walk them in the order they run. **First match wins.**

   | # | Condition | Result | Meridian picture |
   |---|-----------|--------|------------------|
   | 1 | `intent=="refund"` **and** (amount ≥ $75 **or** POD dispute) | **Pro**, reason `high-risk refund / POD dispute` | Maya’s $180 melted dairy |
   | 2 | Upset **and** refund or shortage | **Pro**, reason `elevated CX risk` | “third time / lawyer” |
   | 3 | `wismo` / `shortage` / `policy` | **Flash**, reason `standard ops / policy Q` | Devon’s **$12 BOPIS** |
   | 4 | Anything else | **Flash**, reason `default` | Small refund, no dispute, not upset |

   `high_money` is true when **either**:

   - requested refund ≥ **$75** (Priya’s HITL line), or
   - order total ≥ **$150** (a big basket — still only routes to Pro if intent is already `refund` in branch 1)

   A **$200 WISMO** still hits branch 3 (Flash). Looking up a pickup window is not a money decision. Walk that in a test so nobody “fixes” it later.

   Every branch sets `allow_auto_money=False`. Flash vs Pro is about **judgment quality**, not about skipping Priya.

2. Create `project/meridian_ops/tests/test_model_router.py`:

```python
from meridian_ops.routing.features import TicketFeatures, extract_features
from meridian_ops.routing.model_router import FLASH, PRO, pick_model


def test_bopis_short_is_flash():
    f = extract_features("Short one SKU on a $12 BOPIS — tell the customer.")
    d = pick_model(f)
    assert d.model == FLASH
    assert d.reason == "standard ops / policy Q"
    assert d.allow_auto_money is False


def test_melted_dairy_one_eighty_is_pro():
    f = extract_features(
        "Customer wants $180 refund on melted dairy; POD photo disputed."
    )
    d = pick_model(f)
    assert d.model == PRO
    assert d.reason == "high-risk refund / POD dispute"
    assert d.allow_auto_money is False


def test_wismo_is_flash():
    f = TicketFeatures("wismo", 40, None, False, False, False)
    d = pick_model(f)
    assert d.model == FLASH
    assert d.reason == "standard ops / policy Q"


def test_big_basket_wismo_stays_flash():
    f = TicketFeatures("wismo", 200.0, None, False, False, False)
    d = pick_model(f)
    assert d.model == FLASH


def test_small_clean_refund_is_default_flash():
    f = TicketFeatures("refund", 20.0, 20.0, False, True, False)
    d = pick_model(f)
    assert d.model == FLASH
    assert d.reason == "default"


def test_upset_shortage_is_pro():
    f = TicketFeatures("shortage", 12.0, None, False, False, True)
    d = pick_model(f)
    assert d.model == PRO
    assert d.reason == "elevated CX risk"
```

   Direct `TicketFeatures(...)` is allowed in router tests: you are testing **branches**, not the parser. Parser coverage lives in Task 1. The two Meridian tickets still go through `extract_features` so the full pipe cannot drift.

3. Run:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
source .venv/bin/activate
export PYTHONPATH=project
pytest project/meridian_ops/tests/test_model_router.py -v
```

### Expect

Six `PASSED` lines.

Print the two RouteDecision objects you will log in production:

```bash
python - <<'PY'
from meridian_ops.routing.features import extract_features
from meridian_ops.routing.model_router import pick_model

for text in (
    "Short one SKU on a $12 BOPIS — tell the customer.",
    "Customer wants $180 refund on melted dairy; POD photo disputed.",
):
    d = pick_model(extract_features(text))
    print(text)
    print(" ", d)
PY
```

Sample:

```
Short one SKU on a $12 BOPIS — tell the customer.
  RouteDecision(model='gemini-3.5-flash', reason='standard ops / policy Q', allow_auto_money=False)
Customer wants $180 refund on melted dairy; POD photo disputed.
  RouteDecision(model='gemini-3.5-pro', reason='high-risk refund / POD dispute', allow_auto_money=False)
```

> **Tip:** Log `reason` on every route (stderr JSON, MLflow, traces). Future-you debugging a cost spike will grep `high-risk refund` instead of guessing.

> **Watch out:** Do not set `allow_auto_money=True` for Flash “because it is cheap.” Cheap is not authorized. Lesson 07 still owns the money gate.

### Scoreboard after Task 2

| Piece | In place? |
|-------|-----------|
| Feature extractor | Yes |
| Flash vs Pro router | **Yes** |
| Agent factory | Not yet |
| Fallback + `degraded` | Not yet |
| `output_schema` decision | Not yet |
| CI gate | Not yet |

---

## Task 3 — Two agents, one factory

### Why

ADK binds `model=` at construction. If you write two copy-pasted `agent.py` files that differ by one string, someone will update the instruction on Flash and forget Pro.

A **factory** is a function that returns an `Agent` for the model you pass. The router picks the string. The factory builds the agent. Tests can assert `agent.model == FLASH` without spending a token.

### Do this

1. Create `project/meridian_ops/routing/agents.py`:

```python
from google.adk.agents.llm_agent import Agent

from meridian_ops.tools.oms import get_order
from meridian_ops.tools.policy_rag import retrieve_policy


def build_orderops_agent(model: str, name: str = "meridian_routed_orderops") -> Agent:
    return Agent(
        name=name,
        model=model,
        description="Meridian OrderOps specialist (model selected by router).",
        instruction="""
You are Meridian OrderOps.
- Call get_order before stating status.
- Call retrieve_policy before stating policy amounts.
- Never invent refunds. If over policy or unclear, recommend HITL.
- If the turn is marked degraded, say a human will follow up. Do not move money.
- Be concise for store ops.
""".strip(),
        tools=[get_order, retrieve_policy],
    )
```

   Walk the call:

   - `model=model` — this is the whole point. Flash and Pro share tools and instruction. Only the model string changes.
   - `tools=[get_order, retrieve_policy]` — same least-privilege belt as Lesson 04/06. No `request_refund`. Routing is not a license to settle.
   - The degraded sentence in the instruction is the handbook. Task 4’s `degraded` flag is the lock you log. You need both.

2. Prove the factory binds the string. Create `project/meridian_ops/tests/test_routed_agent.py`:

```python
from meridian_ops.routing.agents import build_orderops_agent
from meridian_ops.routing.model_router import FLASH, PRO


def test_factory_binds_flash_and_pro():
    flash = build_orderops_agent(FLASH, name="ops_flash")
    pro = build_orderops_agent(PRO, name="ops_pro")
    assert flash.model == FLASH
    assert pro.model == PRO
    assert flash.name != pro.name
```

   ADK graphs and runners key off `name`. Two live agents cannot share a name. The factory default is fine for one-at-a-time. The test passes distinct names on purpose.

3. Run the factory test (no LLM):

```bash
export PYTHONPATH=project
pytest project/meridian_ops/tests/test_routed_agent.py -v
```

4. Smoke Flash with `InMemoryRunner` on Devon’s WISMO-style pickup ask. This **does** call Gemini. You need `GOOGLE_API_KEY` in the environment (same as `adk web`).

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
source .venv/bin/activate
export PYTHONPATH=project
python - <<'PY'
import asyncio
from google.adk.apps import App
from google.adk.runners import InMemoryRunner
from google.genai import types

from meridian_ops.routing.agents import build_orderops_agent
from meridian_ops.routing.model_router import FLASH

async def main():
    agent = build_orderops_agent(FLASH)
    app = App(name="meridian_routed_orderops", root_agent=agent)
    runner = InMemoryRunner(app=app)
    session = await runner.session_service.create_session(
        app_name="meridian_routed_orderops", user_id="devon"
    )
    msg = types.Content(
        role="user",
        parts=[types.Part.from_text(text="Where is order MC-1048301 for pickup?")],
    )
    async for event in runner.run_async(
        user_id="devon", session_id=session.id, new_message=msg
    ):
        if event.is_final_response() and event.content and event.content.parts:
            text = "".join(p.text for p in event.content.parts if p.text)
            print("FINAL", event.author, text[:200])

asyncio.run(main())
PY
```

   Same harness as Lesson 08: `App` → `InMemoryRunner` → `create_session` → `run_async(user_id=..., session_id=..., new_message=...)`. Print only events where `is_final_response()` is true. You will reuse this in Task 5.

### Expect

Factory test: `PASSED`.

Smoke: a `FINAL` line from `meridian_routed_orderops` that talks about `MC-1048301` / ready for pickup — not a made-up refund. Trajectory (if you print more events) may include a `get_order` function call first. That is success.

> **Tip:** `Agent` is `LlmAgent`. `from google.adk.agents.llm_agent import Agent` is the same doorbell Lessons 03–07 used.

> **Watch out:** Do not hard-code `model="gemini-3.5-pro"` inside the factory “just in case.” The router owns the string. The factory trusts it.

### Scoreboard after Task 3

| Piece | In place? |
|-------|-----------|
| Feature extractor | Yes |
| Flash vs Pro router | Yes |
| Agent factory | **Yes** |
| Fallback + `degraded` | Not yet |
| `output_schema` decision | Not yet |
| CI gate | Not yet |

---

## Task 4 — Fallback: Pro fails, Flash answers, `degraded=true`

### Why

Priya’s queue cannot freeze because Pro is rate-limited.

**Fallback** means: try the routed model; if it raises, try Flash; **say you degraded**. A catch that returns `"OK"` with no flag is a lie. Finance and CX both need the flag: do not auto-move money on a degraded turn.

### Do this

1. Create `project/meridian_ops/routing/fallback.py`:

```python
from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable

from meridian_ops.routing.model_router import FLASH, RouteDecision

log = logging.getLogger("meridian.routing")


async def run_with_model_fallback(
    primary: RouteDecision,
    run_fn: Callable[[str], Awaitable[Any]],
) -> dict[str, Any]:
    """Try primary.model; on failure run Flash and mark degraded.

    run_fn(model) is your ADK call (factory + InMemoryRunner). This helper
    does not call Gemini itself — tests pass a stub.
    """
    try:
        result = await run_fn(primary.model)
        return {
            "ok": True,
            "degraded": False,
            "model": primary.model,
            "reason": primary.reason,
            "allow_auto_money": False,
            "result": result,
        }
    except Exception as exc:
        log.warning("primary_model_failed model=%s err=%s", primary.model, exc)
        if primary.model == FLASH:
            return {
                "ok": False,
                "degraded": True,
                "model": FLASH,
                "reason": primary.reason,
                "allow_auto_money": False,
                "error": str(exc),
                "result": None,
            }
        try:
            result = await run_fn(FLASH)
            return {
                "ok": True,
                "degraded": True,
                "model": FLASH,
                "fallback_from": primary.model,
                "reason": primary.reason,
                "allow_auto_money": False,
                "result": result,
            }
        except Exception as exc2:
            return {
                "ok": False,
                "degraded": True,
                "model": FLASH,
                "fallback_from": primary.model,
                "allow_auto_money": False,
                "error": str(exc2),
                "result": None,
            }
```

   Three exits. Learn the flags; tests assert them.

   ```
   run_fn(primary.model)
        │ success ──▶ ok=True  degraded=False  model=primary
        │ fail
        ▼
   primary already Flash? ──yes──▶ ok=False  degraded=True  result=None
        │ no (it was Pro)
        ▼
   run_fn(FLASH)
        │ success ──▶ ok=True  degraded=True  model=FLASH  fallback_from=Pro
        │ fail    ──▶ ok=False degraded=True  result=None
   ```

   - `run_fn` takes a **model string** and returns whatever your runner returns (final text, last event, a dict). The helper does not care.
   - Chain length is **one** fallback. No loop. No third model in this lab.
   - `allow_auto_money` is `False` on every return — including the happy Pro path. Degraded turns are not a special case; they just make the rule louder.
   - `except Exception` here is the lab boundary around “the model call failed” (timeout, 429, transport). You still **must not** swallow that into a fake customer answer. The dict tells the edge what happened.

2. Create `project/meridian_ops/tests/test_fallback.py`. Stubs — no Gemini:

```python
import pytest

from meridian_ops.routing.fallback import run_with_model_fallback
from meridian_ops.routing.model_router import FLASH, PRO, RouteDecision


@pytest.mark.asyncio
async def test_pro_failure_falls_back_to_flash_degraded():
    calls: list[str] = []

    async def run_fn(model: str) -> str:
        calls.append(model)
        if model == PRO:
            raise TimeoutError("pro_timeout")
        return "flash-answer"

    primary = RouteDecision(PRO, "high-risk refund / POD dispute", False)
    out = await run_with_model_fallback(primary, run_fn)

    assert calls == [PRO, FLASH]
    assert out["ok"] is True
    assert out["degraded"] is True
    assert out["model"] == FLASH
    assert out["fallback_from"] == PRO
    assert out["allow_auto_money"] is False
    assert out["result"] == "flash-answer"


@pytest.mark.asyncio
async def test_flash_failure_does_not_loop():
    async def run_fn(model: str) -> str:
        raise TimeoutError("flash_down")

    primary = RouteDecision(FLASH, "standard ops / policy Q", False)
    out = await run_with_model_fallback(primary, run_fn)

    assert out["ok"] is False
    assert out["degraded"] is True
    assert out["model"] == FLASH
    assert out["result"] is None
    assert "fallback_from" not in out


@pytest.mark.asyncio
async def test_pro_and_flash_both_fail():
    async def run_fn(model: str) -> str:
        raise TimeoutError(model)

    primary = RouteDecision(PRO, "high-risk refund / POD dispute", False)
    out = await run_with_model_fallback(primary, run_fn)

    assert out["ok"] is False
    assert out["degraded"] is True
    assert out["model"] == FLASH
    assert out["fallback_from"] == PRO
    assert out["result"] is None
```

   Test 1 is the $180 path when Pro times out: Devon/Priya still get a Flash answer, tagged `degraded`.  
   Test 2 is the $12 path when Flash itself is down: **do not** retry Flash forever.  
   Test 3 is a dual outage: `ok=False`, still `degraded=True`, still `allow_auto_money=False`.

3. Run:

```bash
export PYTHONPATH=project
pytest project/meridian_ops/tests/test_fallback.py -v
```

4. When you hook Lesson 12’s FastAPI edge (`project/meridian_ops/deploy/app.py`), the live path is:

   1. `extract_features` + `pick_model` — log `reason`  
   2. `run_with_model_fallback(route, run_fn)` where `run_fn(model)` builds `build_orderops_agent(model)` and runs `InMemoryRunner`  
   3. If `degraded`, log `model_degraded=true` internally. Do **not** dump the exception string onto Maya’s chat.

   You already proved step 2 with stubs. You do not need Gemini to know the flag exists.

### Expect

```
test_fallback.py::test_pro_failure_falls_back_to_flash_degraded PASSED
test_fallback.py::test_flash_failure_does_not_loop PASSED
test_fallback.py::test_pro_and_flash_both_fail PASSED
```

Degraded success dict (test 1) includes `degraded: True`, `model: gemini-3.5-flash`, `fallback_from: gemini-3.5-pro`, `allow_auto_money: False`.

> **Tip:** Lesson 12’s `/v1/wismo` in `project/meridian_ops/deploy/app.py` still returns one JSON blob. When you wire routing there, put `degraded` and `model` on that blob for ops — not in the customer sentence.

> **Watch out:** Degraded mode must **disable auto money movement**. Status + “a supervisor will follow up” beats a wrong $180 refund. The flag is how the next layer knows.

> **Watch out:** Catch-all `except` that returns `"OK"` with `degraded` missing is how you ship a silent outage.

### Scoreboard after Task 4

| Piece | In place? |
|-------|-----------|
| Feature extractor | Yes |
| Flash vs Pro router | Yes |
| Agent factory | Yes |
| Fallback + `degraded` | **Yes** |
| `output_schema` decision | Not yet |
| CI gate | Not yet |

---

## Task 5 — Structured refund decision with `output_schema`

### Why

HITL UIs and workflows need **fields**, not a paragraph.

ADK 2.6.3 `LlmAgent` / `Agent` accepts:

- `output_schema=` — a Pydantic model (here `RefundDecision`)
- `output_key=` — session state key (here `"refund_decision"`)

ADK uses tools during the thought loop if you attach them, and **enforces the schema on the final output**. This lab still splits **gather** vs **decide**: you pass order facts + policy ids in the user message, and the decision agent has **no money tools**. Least privilege stays the import list. Schema stays the shape.

### Do this

1. Create `project/meridian_ops/routing/schemas.py`:

```python
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class RefundDecision(BaseModel):
    decision: Literal["approve_auto", "escalate_hitl", "deny", "need_more_info"]
    refund_usd: float = Field(ge=0)
    policy_ids: list[str]
    risk: Literal["low", "medium", "high"]
    customer_summary: str
    supervisor_reason: str
```

   Walk each field — this is the HITL form:

   | Field | What Priya’s screen shows | Constraint |
   |-------|---------------------------|------------|
   | `decision` | Which button is lit | Only four strings. Not “sure, maybe” |
   | `refund_usd` | Amount | `ge=0` — no negative refunds |
   | `policy_ids` | Binder tabs | Must be ids you **provided**, e.g. `POL-REFUND-04` |
   | `risk` | Color chip | `low` / `medium` / `high` |
   | `customer_summary` | What to tell Maya | Short, no card numbers |
   | `supervisor_reason` | Why Priya was pinged | Empty-ish on `approve_auto`; required in practice for HITL |

2. Create `project/meridian_ops/routing/refund_decision_agent.py`:

```python
from google.adk.agents.llm_agent import Agent

from meridian_ops.routing.model_router import PRO
from meridian_ops.routing.schemas import RefundDecision

refund_decision_agent = Agent(
    name="refund_decision_agent",
    model=PRO,
    description="Emits a structured Meridian refund decision.",
    instruction="""
Given the provided order facts and policy excerpts, fill RefundDecision.
Use escalate_hitl when refund_usd >= 75 or evidence is weak or a POD photo is disputed.
Cite only policy ids that were provided. Never invent POL-* ids.
Never claim money already moved.
""".strip(),
    output_schema=RefundDecision,
    output_key="refund_decision",
)
```

   Walk the `Agent(...)` keywords:

   | Keyword | Effect |
   |---------|--------|
   | `model=PRO` | Heavier judgment — this **is** the $180 path |
   | `output_schema=RefundDecision` | Final reply must match the Pydantic model |
   | `output_key="refund_decision"` | Validated object written to `session.state["refund_decision"]` |
   | no `tools=` | This node **decides**. OMS/policy were gathered already |

   There is no `request_refund` here. A structured “escalate” is not a settlement.

3. Run the decision agent with `InMemoryRunner`. The **user message already includes** tool-like facts (simulated gather). That keeps this node schema-only. Pydantic itself is proven in Task 6’s `ValidationError` test.

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
source .venv/bin/activate
export PYTHONPATH=project
python - <<'PY'
import asyncio
from google.adk.apps import App
from google.adk.runners import InMemoryRunner
from google.genai import types

from meridian_ops.routing.refund_decision_agent import refund_decision_agent

APP = "meridian_refund_decision"
USER = "priya"

async def main():
    app = App(name=APP, root_agent=refund_decision_agent)
    runner = InMemoryRunner(app=app)
    session = await runner.session_service.create_session(app_name=APP, user_id=USER)
    msg = types.Content(
        role="user",
        parts=[types.Part.from_text(text="""
Order MC-1048277 total $214.55 damage_report=melted_dairy pod_photo_present=true
Policy POL-REFUND-04: full-order refund over $75 requires HITL.
Customer requests $180 refund. POD photo is disputed.
""")],
    )
    async for event in runner.run_async(
        user_id=USER, session_id=session.id, new_message=msg
    ):
        if event.is_final_response() and event.content and event.content.parts:
            print("FINAL", "".join(p.text for p in event.content.parts if p.text)[:400])

    session = await runner.session_service.get_session(
        app_name=APP, user_id=USER, session_id=session.id
    )
    print("STATE", session.state.get("refund_decision"))

asyncio.run(main())
PY
```

   After the event loop, `get_session` reloads state. `output_key` is how ADK stashes the validated object. If you only print the FINAL text and skip `get_session`, you have not proved the HITL contract.

### Expect

`STATE` is a dict (or Pydantic-compatible mapping) with at least:

- `"decision": "escalate_hitl"`
- `"refund_usd": 180` (or `180.0`)
- `"policy_ids"` containing `"POL-REFUND-04"`
- `"risk": "high"`

It must **not** be `"approve_auto"` for $180.

> **Tip:** Set `output_schema` on `LlmAgent` / `Agent`. Do not set `response_schema` on `generate_content_config` — ADK 2.6.3 rejects that and tells you to use `output_schema`.

> **Watch out:** Asking the model to “reply in JSON” **without** `output_schema` is a suggestion. Suggestions get dropped. Schema is the lock.

> **Watch out:** Do not stream this JSON at Devon’s handheld (Lesson 22). Store ops want a sentence. Priya’s HITL form wants fields. Same decision, two surfaces.

### Scoreboard after Task 5

| Piece | In place? |
|-------|-----------|
| Feature extractor | Yes |
| Flash vs Pro router | Yes |
| Agent factory | Yes |
| Fallback + `degraded` | Yes |
| `output_schema` decision | **Yes** |
| CI gate | Not yet |

---

## Task 6 — Eval gate so routing and schema cannot silently rot

### Why

Someone will “simplify” `pick_model` to always return Flash. CI must fail before Maya’s $180 path gets the express-lane model with no HITL object.

Do not write a flaky test that says “Gemini must always emit escalate_hitl.” Models flake. Gate **your** contracts with pytest:

1. Feature fixtures → expected model  
2. Missing `risk` → Pydantic error  
3. `$75+` + `approve_auto` → rejected by a **code** guard (the same idea as Lesson 07’s pipeline)

Live `InMemoryRunner` in Task 5 is the smoke. This task is the merge gate.

### Do this

1. Create `project/meridian_ops/routing/guards.py`:

```python
from __future__ import annotations

from meridian_ops.routing.schemas import RefundDecision

HITL_USD = 75.0


def money_path_allowed(decision: RefundDecision) -> bool:
    """False when the schema object tries to auto-approve over the HITL line."""
    if decision.refund_usd >= HITL_USD and decision.decision == "approve_auto":
        return False
    return True
```

   The model can still *emit* `approve_auto` for $180. This guard is what your edge / HITL UI calls before anyone clicks “confirm.” Schema shapes the object. The guard enforces policy.

2. Create `project/meridian_ops/tests/test_refund_schema.py`:

```python
import pytest
from pydantic import ValidationError

from meridian_ops.routing.features import extract_features
from meridian_ops.routing.guards import money_path_allowed
from meridian_ops.routing.model_router import FLASH, PRO, pick_model
from meridian_ops.routing.schemas import RefundDecision


def test_feature_fixtures_route_flash_and_pro():
    flash = pick_model(extract_features("Short one SKU on a $12 BOPIS — tell the customer."))
    pro = pick_model(
        extract_features("Customer wants $180 refund on melted dairy; POD photo disputed.")
    )
    assert flash.model == FLASH
    assert pro.model == PRO


def test_missing_risk_is_a_validation_error():
    with pytest.raises(ValidationError):
        RefundDecision(
            decision="escalate_hitl",
            refund_usd=180,
            policy_ids=["POL-REFUND-04"],
            customer_summary="melted dairy",
            supervisor_reason="over threshold",
        )


def test_high_risk_approve_auto_is_blocked():
    d = RefundDecision(
        decision="approve_auto",
        refund_usd=180,
        policy_ids=["POL-REFUND-04"],
        risk="high",
        customer_summary="melted dairy",
        supervisor_reason="",
    )
    assert money_path_allowed(d) is False


def test_escalate_hitl_is_allowed():
    d = RefundDecision(
        decision="escalate_hitl",
        refund_usd=180,
        policy_ids=["POL-REFUND-04"],
        risk="high",
        customer_summary="melted dairy; POD disputed",
        supervisor_reason="Amount over $75 and evidence contested",
    )
    assert money_path_allowed(d) is True
```

   `test_missing_risk_is_a_validation_error` — `risk` is required. If someone deletes the field from a fixture, Pydantic fails loud.

   `test_high_risk_approve_auto_is_blocked` — even a **well-shaped** object that auto-approves $180 is not allowed through the guard.

3. Run the whole routing suite:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
source .venv/bin/activate
export PYTHONPATH=project
pytest project/meridian_ops/tests/test_features.py \
  project/meridian_ops/tests/test_model_router.py \
  project/meridian_ops/tests/test_fallback.py \
  project/meridian_ops/tests/test_routed_agent.py \
  project/meridian_ops/tests/test_refund_schema.py -v
```

### Expect

Every test `PASSED`. CI now fails if:

- the $12 BOPIS case flips to Pro without you updating the test on purpose, or
- the $180 case flips to Flash, or
- `RefundDecision` drops `risk`, or
- `approve_auto` at $180 slips past `money_path_allowed`

> **Tip:** Score **final** structured decisions in evals (Lesson 08 `AgentEvaluator`), not every token. Routing pytest is the cheap gate; live trajectories are the nightly gate.

> **Watch out:** Do not “fix” a red router test by deleting it. Change `pick_model` on purpose, then change the test in the same PR so the review shows the policy change.

### Scoreboard after Task 6

| Piece | In place? |
|-------|-----------|
| Feature extractor | Yes |
| Flash vs Pro router | Yes |
| Agent factory | Yes |
| Fallback + `degraded` | Yes |
| `output_schema` decision | Yes |
| CI gate | **Yes** |

---

## How it works (deeper dive)

`Agent(model=...)` is fixed at construction. A prompt that says “think hard” does not upgrade Flash to Pro. Route **before** `build_orderops_agent(model)`.

| `ok` | `degraded` | Meaning |
|------|------------|---------|
| True | False | Primary model answered |
| True | True | Flash answered after Pro failed — follow up, no auto money |
| False | True | No model answered — show an honest error |

Without `output_schema`, JSON is optional and often broken. With it, ADK validates the final reply and writes `output_key` into session state. Priya’s UI reads `state["refund_decision"]`.

Do not: run every ticket on Pro; swallow errors as `"OK"` with no `degraded`; skip `output_schema`; treat memory as the refund object; set `allow_auto_money=True` because Flash is cheap.

---

## Common pitfalls / troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Everything routes to Pro | Thresholds too low, or `$12` parsed as a refund | Check `intent` + which slot the `$` landed in; rerun `test_features` |
| `$12` BOPIS has `requested_refund_usd=12` | Parser treated every `$` as a refund | Refund intent only fills `requested_refund_usd` |
| Schema agent returns a paragraph | `output_schema=` missing on the Agent | Set `output_schema=RefundDecision` and `output_key="refund_decision"` |
| `state` missing `refund_decision` | Forgot `get_session` after `run_async`, or wrong `output_key` | Reload session; key must match |
| `ValidationError` on `risk` | Model omitted the field | Schema is doing its job; instruction already lists `risk` |
| Fallback loops forever | Retried Flash when Flash was already primary | Cap is primary → one Flash fallback |
| Customer sees a stack trace | Edge printed `str(exc)` | Log internally; customer gets “we will follow up” |
| `ModuleNotFoundError: meridian_ops` | `PYTHONPATH` not set | From repo root: `export PYTHONPATH=project` |
| Imported Lesson 13 `RouteDecision` | Wrong module | Use `meridian_ops.routing.model_router.RouteDecision` |

---

## You are done when

- [ ] Five feature tests pass, including **$12 BOPIS → shortage** and **$180 melted dairy → refund + POD dispute**
- [ ] Router tests: BOPIS → Flash; $180 POD → Pro; big-basket WISMO stays Flash
- [ ] Factory binds `gemini-3.5-flash` and `gemini-3.5-pro`
- [ ] Fallback tests prove `degraded is True` and `model == FLASH` when Pro raises
- [ ] Flash-already-down path does **not** loop
- [ ] `RefundDecision` lands in `session.state["refund_decision"]` with `escalate_hitl` for $180
- [ ] `money_path_allowed` rejects `approve_auto` at $180
- [ ] Degraded returns always include `allow_auto_money=False`

---

## Knowledge check

Answer from this lab, not from general LLM lore.

1. Why does the $12 BOPIS short go to Flash while the $180 melted-dairy ticket goes to Pro? Quote the `pick_model` branch for each.  
2. Where does the `$12` land in `TicketFeatures`, and where does the `$180` land? Why the split?  
3. What two fields do you set on `Agent` so Priya gets a typed decision in session state?  
4. Pro times out on the $180 ticket. What are `ok`, `degraded`, `model`, and `allow_auto_money` after a successful Flash fallback?  
5. Why is “please respond in JSON” alone not enough?  
6. A $200 WISMO ticket — Flash or Pro? Why?

### Answers

1. BOPIS: `intent=="shortage"` → branch 3, Flash, `standard ops / policy Q`. $180: `intent=="refund"` and (`$180>=75` or POD dispute) → branch 1, Pro, `high-risk refund / POD dispute`.  
2. `$12` → `order_total_usd` (basket). `$180` → `requested_refund_usd` (money asked). Same parser, different slot based on intent.  
3. `output_schema=RefundDecision` and `output_key="refund_decision"`.  
4. `ok=True`, `degraded=True`, `model=gemini-3.5-flash`, `allow_auto_money=False` (and `fallback_from=gemini-3.5-pro`).  
5. Without `output_schema`, JSON is optional and often broken. Schema is enforced on the final reply.  
6. Flash. Branch 1 requires `intent=="refund"`. WISMO with a big basket is still a status lookup.

---

## Recap

- You routed Meridian tickets by **testable features**, not vibes.  
- You built a **fallback** that always returns a `degraded` flag and never enables auto money.  
- You shipped **structured** refund decisions with ADK `output_schema` + `output_key`.

**What you can do next:** Lesson 21 feeds POD **pixels** into the same decision object. Lesson 22 streams Flash WISMO tokens to Devon’s handheld without blocking on the full turn.

---

## Stretch goal

Measure **$ per 100 tickets** before vs after routing pure policy FAQs (`intent=="policy"`, not upset) onto Flash with `reason="policy-faq"`. Log `route.model` and `route.reason`. Do not invent a fourth DIY router — extend `pick_model`.

---

## Feedback

- Could you pick Flash vs Pro for a new “third angry refund” ticket without this doc?  
- What tripped you up: `$` parsing, router branches, fallback flags, or `output_key` state?  
- Note the **task number** and what you expected vs what happened (command + first lines of output).

---

## Navigate

**← Prev** [Lesson 19 — Memory systems](19-memory-systems-deep-dive.md)  
**Track home:** [README](../README.md)  
**Native standard:** [NATIVE-ADK.md](../docs/NATIVE-ADK.md)  
**Next →** [Lesson 21 — Multimodal OrderOps](21-multimodal-orderops.md)

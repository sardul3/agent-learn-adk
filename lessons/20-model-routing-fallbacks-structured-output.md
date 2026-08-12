# Lesson 20 — Model routing, fallbacks & structured output

**Level:** Advanced  
**Time:** ~120 minutes  
**Prerequisites:** Lessons 05, 08, 13 (multi-agent, evals, workflows)  
**Lab outcome:** Route Meridian tickets to **Flash vs Pro**, degrade safely when a model/tool fails, and force machine-readable decisions with ADK **`output_schema`**

**Standard:** [docs/NATIVE-ADK.md](../docs/NATIVE-ADK.md)

---

## At a glance

| Problem | SME fix |
|---------|---------|
| Every ticket hits the biggest model | **Route** by risk / need |
| Pro is down / rate-limited | **Fallback** chain with explicit degrade |
| Free-text “approve maybe?” breaks automation | **`output_schema`** (Pydantic) on decision agents |
| Silent wrong JSON | Validate + eval gate |

You keep using ADK `LlmAgent` / `Agent` — you change **which model** and **how output is shaped**.

---

## Why this matters

Devon’s store chat:

> “Short one SKU on a $12 BOPIS — tell the customer.”

That does not need your most expensive reasoning model.

Priya’s queue:

> “Customer wants $180 refund on melted dairy; POD photo disputed.”

That needs stronger judgment **and** a structured decision object your HITL UI can render:

```json
{
  "decision": "escalate_hitl",
  "refund_usd": 180,
  "policy_ids": ["POL-REFUND-04"],
  "customer_summary": "...",
  "risk": "high"
}
```

If the model replies with a poem, your workflow dies. Structured output is how OrderOps stays automatable.

---

## Know these

| Term | Meaning | Meridian example |
|------|---------|------------------|
| **Model routing** | Choose model (or agent) by ticket features | WISMO → Flash; high-$ refund → Pro |
| **Fallback** | Next option when primary fails | Pro timeout → Flash + “degraded” flag |
| **Graceful degrade** | Still useful under failure | Status-only answer; no auto-refund |
| **output_schema** | ADK forces final reply to match a schema | Pydantic `RefundDecision` |
| **output_key** | Where validated result lands in session state | `state["refund_decision"]` |
| **Structured output agent** | Often a dedicated node after tools | Tools gather → schema agent decides |

```
Ticket features ──► router
                      ├─ low risk  → Flash specialist
                      └─ high risk → Pro specialist
                                      │
                                      ▼ on failure
                               Flash + degraded=true
                                      │
                                      ▼
                         output_schema decision object
```

---

## Task 1 — Define ticket features (router inputs)

### Why

Routers need boring, testable features — not vibes.

### Do this

Create `project/meridian_ops/routing/features.py`:

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

    req = None
    for token in t.replace("$", " $").split():
        if token.startswith("$"):
            try:
                req = float(token[1:].replace(",", ""))
            except ValueError:
                pass

    total = None
    if order and order.get("order_total_usd") is not None:
        total = float(order["order_total_usd"])

    return TicketFeatures(
        intent=intent,
        order_total_usd=total,
        requested_refund_usd=req,
        has_pod_dispute="pod" in t or "photo" in t and "not" in t,
        needs_policy=intent in {"policy", "refund"},
        customer_upset=any(w in t for w in ("furious", "lawyer", "unacceptable", "third time")),
    )
```

Unit-test three Meridian phrasings (WISMO, shortage, $180 refund).

### Expect

Deterministic features you can print in logs.

---

## Task 2 — Route Flash vs Pro (code, not hope)

### Why

Putting “use your best judgment about models” in a prompt is not routing.

### Do this

Create `project/meridian_ops/routing/model_router.py`:

```python
from __future__ import annotations

from dataclasses import dataclass

from meridian_ops.routing.features import TicketFeatures

FLASH = "gemini-2.5-flash"
PRO = "gemini-2.5-pro"


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
        return RouteDecision(PRO, "high-risk refund / POD dispute", allow_auto_money=False)
    if features.customer_upset and features.intent in {"refund", "shortage"}:
        return RouteDecision(PRO, "elevated CX risk", allow_auto_money=False)
    if features.intent in {"wismo", "shortage", "policy"}:
        return RouteDecision(FLASH, "standard ops / policy Q", allow_auto_money=False)
    return RouteDecision(FLASH, "default", allow_auto_money=False)
```

Tests:

```python
from meridian_ops.routing.features import TicketFeatures
from meridian_ops.routing.model_router import FLASH, PRO, pick_model


def test_wismo_is_flash():
    f = TicketFeatures("wismo", 40, None, False, False, False)
    assert pick_model(f).model == FLASH


def test_big_refund_is_pro():
    f = TicketFeatures("refund", 214.55, 180, True, True, False)
    assert pick_model(f).model == PRO
```

### Expect

WISMO → Flash; big refund → Pro.

> **Tip:** Log `reason` on every route. Future you debugging cost spikes will thank you.

---

## Task 3 — Two ADK agents, one factory

### Why

ADK agents bind `model=` at construction. Factory keeps routing honest.

### Do this

Create `project/meridian_ops/routing/agents.py`:

```python
from google.adk.agents.llm_agent import Agent

from meridian_ops.tools.oms import get_order
from meridian_ops.tools.policy_rag import retrieve_policy_hybrid


def build_orderops_agent(model: str, name: str = "meridian_routed_orderops") -> Agent:
    return Agent(
        name=name,
        model=model,
        description="Meridian OrderOps specialist (model selected by router).",
        instruction="""
You are Meridian OrderOps.
- Call get_order before stating status.
- Call retrieve_policy_hybrid before stating policy amounts.
- Never invent refunds. If over policy or unclear, recommend HITL.
- Be concise for store ops.
""".strip(),
        tools=[get_order, retrieve_policy_hybrid],
    )
```

Smoke with `InMemoryRunner` on Flash for a WISMO ask about `MC-1048301`.

### Expect

Agent runs on the model you passed — verify in traces / MLflow / response metadata when available.

---

## Task 4 — Fallback chain (Pro → Flash + degraded)

### Why

Primary model failure cannot strand Priya’s queue.

### Do this

Create `project/meridian_ops/routing/fallback.py`:

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
    """Try primary model; on failure run Flash and mark degraded."""
    try:
        result = await run_fn(primary.model)
        return {"ok": True, "degraded": False, "model": primary.model, "result": result}
    except Exception as exc:  # noqa: BLE001 — lab: map to typed errors in prod
        log.warning("primary_model_failed model=%s err=%s", primary.model, exc)
        if primary.model == FLASH:
            return {
                "ok": False,
                "degraded": True,
                "model": FLASH,
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
                "result": result,
            }
        except Exception as exc2:  # noqa: BLE001
            return {
                "ok": False,
                "degraded": True,
                "model": FLASH,
                "error": str(exc2),
                "result": None,
            }
```

Write a unit test that stubs `run_fn`: first call raises, second returns `"ok"` → assert `degraded is True` and `model == FLASH`.

Wire a thin FastAPI/service path (Lesson 12 edge) that:

1. Extracts features  
2. `pick_model`  
3. `run_with_model_fallback` constructing agent via `build_orderops_agent(model)` + ADK `Runner`

When `degraded`, prepend customer/store message with a clear internal tag in logs: `model_degraded=true` (do **not** dump stack traces to Maya).

### Expect

Forced primary failure still yields a Flash answer marked degraded.

> **Watch out:** Degraded mode must **disable auto money movement**. Status + “human will follow up” beats a wrong refund.

---

## Task 5 — Structured refund decision with `output_schema`

### Why

HITL UIs and workflows need fields, not paragraphs.

### Do this

Create `project/meridian_ops/routing/schemas.py`:

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

Create a **decision agent** (tools optional depending on your ADK version — if tools+schema fight, gather evidence in a prior node, then schema-only decide):

```python
from google.adk.agents.llm_agent import Agent

from meridian_ops.routing.schemas import RefundDecision

refund_decision_agent = Agent(
    name="refund_decision_agent",
    model="gemini-2.5-pro",
    description="Emits a structured Meridian refund decision.",
    instruction="""
Given the provided order facts + policy excerpts, respond ONLY with JSON
matching the schema. Use escalate_hitl when refund_usd >= 75 or evidence is weak.
Cite policy ids that were provided; never invent POL-* ids.
""".strip(),
    output_schema=RefundDecision,
    output_key="refund_decision",
)
```

Run with `InMemoryRunner` and a **user message that already includes** tool results (simulated gather):

```text
Order MC-1048277 total $214.55 damage_report=melted_dairy pod_photo_present=true
Policy POL-REFUND-04: full-order refund over $75 requires HITL.
Customer requests $180 refund.
```

Then read `session.state["refund_decision"]`.

### Expect

Validated dict/object with `decision == "escalate_hitl"`, `refund_usd == 180`, `policy_ids` containing `POL-REFUND-04`.

> **Tip:** If your ADK version warns about tools + `output_schema`, use Workflow: `gather (tools) → decide (schema)`. That is still native ADK.

---

## Task 6 — Eval gate for schema + routing

### Why

Routing and schemas regress quietly when someone “simplifies” the agent.

### Do this

Add tests / golden checks:

1. Feature fixtures → expected model (Flash/Pro)  
2. Schema parse: model output missing `risk` → validation error path handled  
3. AgentEvaluator (Lesson 08): high-risk refund trajectory ends with HITL decision — not `approve_auto`

Optional MLflow (Lesson 10): log `route.model`, `route.reason`, `degraded`.

### Expect

CI fails if Pro-bound cases flip to Flash without updating the router tests on purpose.

---

## How it works (deeper dive)

**Routing in code** keeps cost and risk reviewable.  
**Fallbacks** acknowledge reality: quotas, regions, outages.  
**Structured output** turns LLM judgment into API/workflow fuel.

Anti-patterns:

- One mega-agent on Pro forever  
- Catch-all `except` that returns `"OK"` without `degraded`  
- Asking the model to “reply in JSON” **without** `output_schema`  
- Using memory or chat history as the refund decision object

---

## Common pitfalls / troubleshooting

| Symptom | Fix |
|---------|-----|
| Everything routes to Pro | Tighten thresholds; log feature values |
| Schema agent returns prose | Confirm `output_schema=` set; strengthen instruction; upgrade ADK |
| `state` missing output_key | Check `output_key`; read session after final event |
| Tools+schema error | Split gather/decide agents or Workflow nodes |
| Fallback loops forever | Cap chain length (primary → one fallback) |
| Customer sees stack traces | Degrade message ≠ exception string |

---

## You are done when

- [ ] Feature extractor + router tests pass  
- [ ] Factory builds Flash/Pro agents  
- [ ] Fallback test proves degraded Flash path  
- [ ] `RefundDecision` lands in `session.state["refund_decision"]`  
- [ ] High-risk case cannot `approve_auto` in eval/tests  
- [ ] Degraded mode blocks auto money (instruction or code guard)  

---

## Knowledge check

1. Why route WISMO to Flash?  
2. What must you set on `LlmAgent` for typed decisions?  
3. What does graceful degrade mean for a $180 refund when Pro is down?  
4. Where should route `reason` go?  
5. Why is “please respond in JSON” alone insufficient?

### Answers

1. Low judgment / high volume — cost and latency matter.  
2. `output_schema` (+ usually `output_key`).  
3. Flash may explain + escalate HITL; must not auto-approve money.  
4. Structured logs / traces / MLflow — not only stdout.  
5. Without schema enforcement, JSON is optional and often broken.

---

## Recap

- You routed Meridian tickets by **risk features**.  
- You built a **fallback** that marks degrade.  
- You shipped **structured** refund decisions ADK can validate.

---

## Stretch goal

Add a third tier: `gemini-2.5-flash-lite` (or your cheapest available) for pure FAQ policy Q with RAG — measure $ per 100 tickets before/after.

---

## Feedback

- Could you pick Flash vs Pro for a new “third angry refund” ticket without the doc?  
- Note task number + expected vs actual.

---

## Navigate

**← Prev** [Lesson 19 — Memory systems](19-memory-systems-deep-dive.md)  
**Track home:** [README](../README.md)  
**Next:** [Lesson 21 — Multimodal OrderOps](21-multimodal-orderops.md)

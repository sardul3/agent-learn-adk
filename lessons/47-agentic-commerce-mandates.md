# Lesson 47 — Agentic commerce & payment mandates (AP2)

**Level:** Advanced (money paths)  
**Time:** ~150 minutes  
**Prerequisites:** Lessons 07, 15, 26, 46 (HITL, resume, plugins, identity)  
**Lab outcome:** Replace "the customer said yes in chat" with **signed mandates** — intent, cart, payment — so every Meridian money move carries portable, verifiable proof of who authorized what

**Standard:** [docs/NATIVE-ADK.md](../docs/NATIVE-ADK.md)  
**Spec:** [Agent Payments Protocol (AP2)](https://ap2-protocol.org/)

---

## At a glance

Your refund flow today ends with a human clicking approve, and an audit line that says *"Priya approved."*

That is fine inside Meridian. It falls apart the moment money crosses a boundary — a card network, a partner banner, a bank asking *"prove the customer authorized this, not your model."*

**AP2** is an open protocol for exactly that question. It adds three signed objects to agent-initiated commerce.

| Mandate | Who signs | Answers |
|---------|-----------|---------|
| **Intent** | the customer | "I authorized an agent to do *this kind* of thing, within *these* limits" |
| **Cart** | the merchant | "These exact items, at this exact price, are what I offered" |
| **Payment** | the customer / their wallet | "Charge this specific cart with this instrument" |

```
Maya ──signs Intent──►  "credit up to $25 for a late grocery delivery, valid 24h"
                              │
Meridian prices it ──signs Cart──►  "POL-DELIVERY-01 credit, $10.00, order MC-1048277"
                              │
Maya (or Priya on policy) ──signs Payment──►  charge/credit authorization
                              │
                              ▼
              request_refund runs ONLY with all three verified
```

> **Note:** AP2 is a **protocol**, not an ADK feature. You build the mandate objects and the verification gate as Meridian domain code, then enforce them with the ADK plugin you already have. You are not building a payment network.

---

## Why this matters

Two futures for Meridian OrderOps.

**Without mandates.** The agent decides Maya deserves $10. A plugin checks a rule. Priya clicks yes. Money moves. Six weeks later a chargeback lands and the bank asks who authorized it. You have a chat transcript and a log line. A transcript is not authorization — it is a story about authorization, written by the thing being questioned.

**With mandates.** You hand over three signed objects. Maya's intent, capped at $25 and expired after 24 hours. Your cart at exactly $10 against exactly one order. The payment authorization tied to that cart hash. Nobody has to trust your model, your prompt, or your logs.

The second one is also *safer for you*: a prompt injection that convinces the agent to refund $500 produces a cart that does not match any intent, and the gate refuses it.

---

## Know these

| Term | Plain English |
|------|---------------|
| **Mandate** | A signed statement of authorization you can hand to someone else |
| **Intent mandate** | The customer's up-front permission, with limits |
| **Cart mandate** | The merchant's signed, exact offer |
| **Payment mandate** | Authorization to charge/credit a specific cart |
| **Human present** | The person is live in the loop right now |
| **Human not present** | The agent acts later, under an earlier mandate |
| **Nonce** | A one-time value that stops a replay of the same approval |
| **Expiry** | When authorization stops being valid |
| **Replay attack** | Reusing a real approval a second time |
| **Non-repudiation** | The signer cannot later claim they did not sign |

What actually stops a bad refund?

| Control | Where it lives | Survives a prompt injection? | Provable to a third party? |
|---------|----------------|------------------------------|----------------------------|
| Instruction "never over $25" | prompt | no | no |
| `before_tool` plugin cap | your code | yes | only in your own logs |
| HITL approval (Lesson 15) | ADK graph | yes | internal record |
| **Signed mandate chain** | **domain code + keys** | **yes** | **yes** |

Each row adds to the one above. Mandates do not replace HITL — HITL is *how you collect the signature*.

---

## Task 1 — Map your money paths

### Why

You only need mandates where value moves. Everything else is noise.

### Do this

Create `project/meridian_ops/commerce/MONEY_PATHS.md`:

| Action | Moves value? | Human present today? | Mandate needed |
|--------|--------------|----------------------|----------------|
| `get_order` | no | n/a | none |
| `get_atp` | no | n/a | none |
| `suggest_substitute_for_short` (dry run) | no | n/a | none |
| `reserve_substitute` (commit) | yes — changes the order | | intent + cart |
| `request_refund` | yes | | intent + cart + payment |
| Goodwill credit under $5 | yes | | ? decide and justify |

### Expect

Exactly two or three rows marked "yes." If everything needs a mandate, you have over-scoped and the lab will drown.

---

## Task 2 — Mandate data model

### Why

Signing starts with agreeing on *what* is signed. Vague fields make unverifiable signatures.

### Do this

Create `project/meridian_ops/commerce/mandates.py`:

```python
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone


@dataclass(frozen=True)
class IntentMandate:
    """What the customer authorized an agent to do, and the limits."""

    mandate_id: str
    customer_id: str
    purpose: str            # "late_delivery_credit"
    max_amount_cents: int
    currency: str
    order_id: str | None
    expires_at: str         # ISO 8601 UTC
    nonce: str


@dataclass(frozen=True)
class CartMandate:
    """The merchant's exact, priced offer."""

    mandate_id: str
    intent_id: str
    order_id: str
    line_items: tuple[tuple[str, int], ...]   # (description, amount_cents)
    total_cents: int
    currency: str
    policy_ref: str          # "POL-DELIVERY-01"
    created_at: str


@dataclass(frozen=True)
class PaymentMandate:
    """Authorization to move money for one specific cart."""

    mandate_id: str
    cart_id: str
    cart_hash: str           # binds this authorization to exact cart contents
    approver_id: str         # customer, or Priya for policy-side credits
    human_present: bool
    created_at: str
```

Add helpers:

- `canonical_json(obj)` — sorted keys, no whitespace, so two machines hash identically  
- `hash_cart(cart)` — SHA-256 of the canonical JSON  
- `is_expired(intent, now)` — expiry check with an explicit clock argument

> **Tip:** Take `now` as an argument instead of calling the clock inside the function. Expiry logic you cannot freeze in a test is expiry logic you cannot trust.

### Expect

Three frozen dataclasses and a hash that is stable across two runs of the same data.

---

## Task 3 — Sign and verify

### Why

An unsigned mandate is a comment. Anyone can edit it.

### Do this

Add `project/meridian_ops/commerce/signing.py` using the standard library:

```python
import hashlib
import hmac
import os


def sign(payload: str, key: bytes) -> str:
    """Lab signature. Production uses asymmetric keys — see the deeper dive."""
    return hmac.new(key, payload.encode("utf-8"), hashlib.sha256).hexdigest()


def verify(payload: str, signature: str, key: bytes) -> bool:
    expected = sign(payload, key)
    return hmac.compare_digest(expected, signature)   # constant-time: no timing leak
```

Keys come from environment (`MERIDIAN_MANDATE_KEY`), never from the repo.

Write tests in `project/meridian_ops/tests/test_mandates.py`:

- Round trip: sign then verify passes  
- Tamper: change `total_cents` by one → verify fails  
- Field reorder: same data, different key order → same signature (canonical JSON works)  
- Wrong key → verify fails

```bash
export PYTHONPATH=project
export MERIDIAN_MANDATE_KEY="lab-only-not-a-real-key"
python -m pytest project/meridian_ops/tests/test_mandates.py -q
```

### Expect

Green. Especially the tamper test — that is the one that proves the whole lesson.

---

## Task 4 — The verification gate

### Why

This is the actual security control. Everything before it was data structures.

### Do this

`project/meridian_ops/commerce/gate.py` with one function:

```python
def authorize_refund(intent, cart, payment, *, now, key) -> tuple[bool, str]:
    """Return (allowed, reason). Every failure reason must be specific."""
```

Checks, in order, each with its own test:

1. All three signatures verify  
2. `cart.intent_id == intent.mandate_id`  
3. `payment.cart_id == cart.mandate_id`  
4. `payment.cart_hash == hash_cart(cart)` — the binding that stops price swapping  
5. `intent.expires_at` is in the future relative to `now`  
6. `cart.total_cents <= intent.max_amount_cents`  
7. Currencies all match  
8. `cart.order_id == intent.order_id` when the intent named one  
9. `intent.nonce` has not been used before (reuse the idempotency store from Lesson 04)

Write one test per rule, each failing for exactly that reason.

### Expect

Nine tests, nine distinct reason strings. A gate that returns a generic "denied" is a gate nobody can debug at 2am.

---

## Task 5 — Wire the gate into the agent path

### Why

A gate in a module that nothing calls is decoration.

### Do this

1. In your Lesson 26 policy plugin, extend `before_tool`:

```python
async def before_tool_callback(self, *, tool, tool_args, tool_context, **kwargs):
    if tool.name not in {"request_refund", "reserve_substitute"}:
        return None

    bundle = load_mandates(tool_context)       # from session state, written by the edge
    allowed, reason = authorize_refund(*bundle, now=utcnow(), key=MANDATE_KEY)
    if not allowed:
        return {"status": "error", "error_code": "MANDATE_INVALID", "message": reason}
    return None
```

2. Mandates arrive from the **edge**, not from the model. The model can request a refund; it can never mint the authorization for it.

3. Connect to HITL: in the Lesson 15 `RequestInput` pause, Priya's approval is what produces the signed payment mandate. The chat "yes" becomes a signature.

4. Prove three cases end to end:

| Case | Expected |
|------|----------|
| Valid chain, $10 ≤ $25 cap | refund proceeds |
| Cart edited to $500 after signing | denied, hash mismatch |
| Yesterday's intent replayed | denied, expired **or** nonce reused |

### Expect

Case 2 and 3 are refused **before** the tool executes, with the specific reason in the audit log.

> **Watch out:** Do not put the signing key anywhere the model can reach — not in state the agent reads, not in a tool return value, not in an instruction.

---

## Task 6 — Audit trail and the chargeback drill

### Why

The point of mandates is answering someone else's question months later.

### Do this

1. Append to a durable audit log for every money move: mandate ids, cart hash, approver, policy ref, correlation id. **Amounts and ids only** — no card numbers, no full addresses (Lesson 27).

2. Run the drill. Pick one completed lab refund and answer, using only stored artifacts:

- Who authorized it, and when?  
- What exactly did they authorize (limit, purpose, expiry)?  
- What was actually charged, and does it match?  
- Which policy justified the amount?  
- Could this authorization be replayed?

3. Write the answers in `MONEY_PATHS.md` under **Chargeback drill**.

### Expect

Five answers with artifact references. If any answer is "we would check the chat transcript," go back to Task 5.

---

## Task 7 — Human-present vs human-not-present

### Why

The interesting agentic case is the agent acting **later**, when nobody is watching.

### Do this

Scenario: Maya pre-authorizes *"if the substitute costs less, credit me the difference automatically, up to $8, for the next 7 days."*

Decide and document:

| Question | Your answer |
|----------|-------------|
| Which mandate is signed up front? | |
| Who signs the payment mandate with no human present? | |
| What limits make this safe (amount, count, window)? | |
| How does Maya revoke it? | |
| What does the receipt say, and when is it sent? | |

Implement **revocation**: a revoked-mandate list the gate checks. Test that a revoked intent is refused even though its signature is still valid.

### Expect

A working revocation check, and a written limit that is *narrow* — small cap, short window, low count.

---

## How it works (deeper dive)

**Why HMAC in the lab, asymmetric in production**

HMAC uses one shared secret, so anyone who can verify can also forge. That is fine for a lab because both sides are you. Real deployments sign with a private key and let counterparties verify with the public one — that is what makes a mandate portable and non-repudiable. The **logic** you built (canonical form, hash binding, expiry, nonce) is identical either way; only `sign`/`verify` change.

**Why the cart hash matters most**

Without it, an attacker who obtains a valid payment mandate can attach it to a different cart. Binding the authorization to a hash of exact contents means changing one cent invalidates it.

**Where this sits next to A2A and MCP**

MCP connects agents to tools. A2A connects agents to agents. AP2 covers the transaction layer on top: the authorization evidence that travels with a purchase. All three answer "how do things connect" — none of them answer "should this agent be allowed to spend," which stays your gate, your HITL, and your scopes from Lesson 46.

**What you did not build**

Not a payment processor, not a card network, not a wallet. You built the authorization envelope those systems ask for, and the gate that refuses to move money without it.

---

## Common pitfalls / troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| Signature fails on identical data | Key ordering / whitespace differs | Canonical JSON everywhere |
| Same approval works twice | No nonce or no store | Nonce + idempotency store (Lesson 04) |
| Model produced a mandate | Minting logic reachable from a tool | Mint only at the edge / HITL resume |
| Gate returns bare "denied" | One combined check | One reason per rule |
| Key committed | Convenience during testing | Env var; rotate; scrub history |
| Expiry never triggers | Clock read inside the function | Pass `now` in; freeze it in tests |

---

## You are done when

- [ ] Money paths mapped, three or fewer need mandates  
- [ ] Three mandate types with canonical JSON + stable hash  
- [ ] Sign/verify with a passing **tamper** test  
- [ ] Nine gate rules, nine distinct reasons  
- [ ] Gate enforced in `before_tool`, mandates minted at the edge  
- [ ] Price-swap and replay both refused end to end  
- [ ] Chargeback drill answered from artifacts  
- [ ] Revocation implemented and tested  

---

## Knowledge check

1. Why is a chat transcript not proof of authorization?  
2. What does the cart hash inside the payment mandate prevent?  
3. Why does an expired-but-validly-signed mandate still get refused?  
4. Where must mandates be created, and why not in a tool?  
5. What changes between the lab's HMAC and a production signature scheme?

### Answers

1. It is a story written by the system being questioned; nothing binds it cryptographically to the customer.  
2. Swapping a cheap approved cart for an expensive one after the fact.  
3. A signature proves *who said it*, not *that it is still true* — expiry is a separate check.  
4. At the edge or during HITL resume; a tool is reachable by the model, so the model could mint its own permission.  
5. Only `sign`/`verify` — shared secret becomes a private/public key pair so third parties can verify without forging.

---

## Recap

- Money moves now require portable, signed evidence, not a friendly transcript.  
- The gate refuses price swaps, replays, expiries, and over-cap carts before the tool runs.  
- HITL got an upgrade: a click became a signature.

---

## Stretch goal

Swap HMAC for an asymmetric signature using a library your company already allows. Publish a verification endpoint (`/.well-known/`-style) so a partner banner could verify a Meridian cart mandate without holding any Meridian secret.

---

## Feedback

- Could you defend one lab refund to a bank using only stored artifacts?  
- Note the task number, and which gate rule was hardest to test.

---

## Navigate

**← Prev** [Lesson 46 — Agent identity & delegated auth](46-agent-identity-delegated-auth.md)  
**Next →** [Lesson 48 — Computer use & browser agents](48-computer-use-browser-agents.md)  
**Related:** [Lesson 15 — HITL resume](15-long-running-hitl-resume.md) · [Lesson 26 — Plugins](26-plugins-callbacks-policy-middleware.md)  
**Track home:** [README](../README.md)

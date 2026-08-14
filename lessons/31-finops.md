# Lesson 31 — FinOps for agents

**Level:** Advanced (platform)  
**Time:** ~120 minutes  
**Prerequisites:** Lessons 10, 20, 30 (MLflow, model routing, tenants)  
**Lab outcome:** Attribute **cost per task and per tenant**, set a **budget**, and **stop or degrade** when the budget is gone — chargeback that finance can read

**Standard:** [docs/NATIVE-ADK.md](../docs/NATIVE-ADK.md)

---

## At a glance

**FinOps** = making cloud spend a **product** concern: visible, attributed, and capped.

Agents are easy to underprice in your head:

- One WISMO might be one Flash call  
- A critic loop might be **eight** calls  
- A vision POD dispute (Lesson 21) is a different price than text  
- Retries after 429 still **cost** if they eventually succeed

```
Each Runner turn
        │
        ▼
Record: tenant, task_type, model, tokens in/out, tools, latency
        │
        ▼
Sum → cost USD (from a rate card)
        │
        ├─ under budget → OK
        └─ over budget → degrade (Flash only) or 429 / flag off graph
```

---

## Why this matters

Finance: “Why is the Gemini bill 4× this month?”

If you say “the LLM,” you will get a blanket freeze.

If you say “`franchise-demo` critic loop + vision retries on `banner-us` refunds,” you can:

- Charge the banner  
- Cap the franchise  
- Keep WISMO up with Flash (Lesson 20)

That is FinOps, not a spreadsheet after the invoice.

---

## Know these

| Term | Meaning |
|------|---------|
| **Unit of work** | What you bill: ticket, WISMO call, refund graph run |
| **Token** | Piece of text the model bills (input vs output) |
| **Rate card** | USD per 1M input/output tokens per model (lab: fake numbers) |
| **Attribution** | Cost tagged with tenant + task |
| **Chargeback** | Show a tenant “you used $X” |
| **Showback** | Same numbers, no invoice yet |
| **Budget** | Max USD (or tokens) per window |
| **Degrade** | Cheaper model / fewer loops / no vision before hard stop |
| **Unit economics** | Cost vs value of one WISMO deflection |

> **Tip:** Use **lab rate cards**. Real Google prices change. The skill is the **pipeline**, not memorizing a price.

---

## Task 1 — Rate card and task catalog

### Why

You cannot attribute what you have not named.

### Do this

Create `project/meridian_ops/finops/RATE_CARD.md` and `rate_card.yaml`:

```yaml
# Lab prices only — not a vendor quote
currency: USD
per_million:
  gemini-2.5-flash:
    input: 0.10
    output: 0.40
  gemini-2.5-pro:
    input: 1.25
    output: 10.00
tasks:
  wismo:
    expected_model: gemini-2.5-flash
    note: Single specialist, one or two tool calls
  refund_graph:
    expected_model: mixed
    note: Extra HITL wait is not token cost; extra critic loops are
  vision_pod:
    expected_model: gemini-2.5-pro
    note: Image tokens dominate
```

Add a table of **Meridian task types**: `wismo`, `atp`, `refund_graph`, `policy_rag`, `vision_pod`, `critic_loop`.

### Expect

Every production path you already built has a **task_type** name.

---

## Task 2 — Cost function + tests (no API key)

### Why

Billing math must be unit-tested. A missed zero is a silent finance incident.

### Do this

`project/meridian_ops/finops/cost.py`:

```python
def cost_usd(model: str, input_tokens: int, output_tokens: int, card: dict) -> float:
    rates = card["per_million"][model]
    return (input_tokens * rates["input"] + output_tokens * rates["output"]) / 1_000_000
```

Tests:

- 1_000_000 flash input + 0 output → `0.10`  
- Unknown model → **error**, not $0  
- Zero tokens → `0.0`

```bash
export PYTHONPATH=project
python -m pytest project/meridian_ops/tests/test_finops_cost.py -q
```

### Expect

Green tests. No live Gemini.

---

## Task 3 — Record a usage event from a real turn

### Why

Showback needs **events**, not vibes.

### Do this

Add `project/meridian_ops/finops/usage.py` that appends JSONL:

```json
{"ts": "...", "tenant_id": "banner-us", "task_type": "wismo", "model": "gemini-2.5-flash", "input_tokens": 800, "output_tokens": 120, "session_id": "redacted-or-hash", "correlation_id": "..."}
```

Hook points (pick what you have):

- After `runner.run_async` if the run result exposes usage  
- Or a **plugin** `after_model` that reads usage from the response object **if present**  
- Or lab: wrap the call and pass **estimated** tokens (`len(text)//4` is a crude stand-in — label it `estimate=true`)

Write in `project/meridian_ops/decisions/31-finops.md`:

- Where you hooked  
- Whether tokens are **real** or **estimated**  
- Why refund HITL wait time is **not** a token

> **Watch out:** Never put API keys, card numbers, or raw emails in usage JSONL (Lesson 27).

Run one WISMO (live or fixture) and show one JSONL line.

### Expect

At least one file under `project/meridian_ops/finops/inbox/` (gitignored if it might contain ticket text — prefer counts only).

---

## Task 4 — Chargeback report per tenant

### Why

Finance and banner owners need a **table**, not a log dump.

### Do this

Script `project/meridian_ops/finops/report.py`:

```bash
# Reads inbox jsonl; prints a table
python -m meridian_ops.finops.report
```

Output:

| tenant_id | task_type | turns | tokens_in | tokens_out | usd |
|-----------|-----------|-------|-----------|------------|-----|
| banner-us | wismo | | | | |
| banner-ca | wismo | | | | |

If inbox is empty, seed **two fake lines** in a `fixtures/finops_sample.jsonl` and run the report against `-i` that file.

```bash
python -m meridian_ops.finops.report -i project/meridian_ops/fixtures/finops_sample.jsonl
# -i: input path (not stdin)
```

Paste the table into `31-finops.md`.

### Expect

You can answer “who spent this week?” in one command.

---

## Task 5 — Budgets and degrade

### Why

Attribution without a **cap** is a dashboard that watches the building burn.

### Do this

Extend `tenants.yaml` (Lesson 30) or `finops/budgets.yaml`:

```yaml
budgets:
  banner-us:
    daily_usd: 50.0
    on_exceed: degrade_flash_only
  franchise-demo:
    daily_usd: 2.0
    on_exceed: reject_429
```

`try_budget(tenant_id, additional_usd) -> "ok" | "degrade" | "reject"`.

Wire:

- `reject` → HTTP 429 + message “tenant budget exceeded”  
- `degrade` → force `MERIDIAN_MODEL_NAME` / agent model to Flash (Lesson 20), **skip** critic extra loops if you have a flag (Lesson 32)

Test both branches without spending real money (fake running total).

### Expect

Franchise hits reject in the test. US hits degrade, not a silent unlimited Pro loop.

---

## Task 6 — Unit economics (one WISMO)

### Why

Leadership will ask if the agent is cheaper than a human ticket.

### Do this

In `31-finops.md`:

| | Human CX handle | Agent WISMO (lab) |
|--|-----------------|-------------------|
| Cost | your guess (e.g. $4) | usd from report |
| Latency | minutes | seconds |
| Failure mode | wrong ETA | invented POD |

One paragraph: when you would **not** use Pro for WISMO.

### Expect

A sentence you could say in a steering meeting.

---

## How it works (deeper dive)

**Retries**

A failed Pro call that retries three times still bills. Count **attempts**, not only successes.

**Caching (Lesson 44)**

A cache hit should log `usd=0` (or infra cost only) with `cache_hit=true`, or your chargeback double-counts.

**MLflow**

Log `cost_usd` as a metric on eval runs (Lesson 10) so a “better” prompt that triples tokens fails a gate.

---

## Common pitfalls / troubleshooting

| Symptom | Fix |
|---------|-----|
| $0 because usage missing | Estimate + flag; then fix hook |
| Unknown model → $0 | Fail closed in `cost_usd` |
| Budget in RAM, two replicas | Same as quota: Redis for prod |
| Billing PII | Counts and ids only |
| Critic loop not a task_type | You will never see why the bill spiked |

---

## You are done when

- [ ] Rate card + task catalog  
- [ ] Tested `cost_usd`  
- [ ] Usage JSONL (real or estimated, labeled)  
- [ ] Chargeback table  
- [ ] Budget reject + degrade tests  
- [ ] Unit-economics paragraph  

---

## Knowledge check

1. Showback vs chargeback?  
2. Why is HITL wait not token cost?  
3. Why fail on unknown model in `cost_usd`?  
4. What should happen when franchise exceeds $2/day in the lab?  
5. Why tag `task_type`?

### Answers

1. Showback = visibility; chargeback = they **pay** / get billed internally.  
2. The model is not running; a human is.  
3. Silent $0 hides spend.  
4. **429 reject**, not a warning in a log nobody reads.  
5. So you can see **refund graphs** vs **WISMO**, not one lump “LLM.”

---

## Recap

- Tokens are a **meter**. Tenants and tasks are the **dimensions**.  
- Cap before the invoice. Degrade before you go dark.  
- Resilience (Lesson 32) is next if you skipped it; else go to capacity SLOs (43).

---

## Stretch goal

Add an MLflow metric `cost_usd` on one `AgentEvaluator` run and fail CI if it exceeds a threshold (Lesson 41 style).

---

## Feedback

- Could you explain last month’s Gemini bill using only your report table?  
- Note task number + estimated vs real tokens.

---

## Navigate

**← Prev** [Lesson 30 — Multi-tenant](30-multi-tenant.md)  
**Next →** [Lesson 32 — Chaos, DR & flags](32-chaos-dr-feature-flags.md) (if not done) · [Lesson 43 — SLOs & capacity](43-slos-capacity-backpressure.md)  
**Track home:** [README](../README.md)

# Lesson 44 — LLM gateway, cache & platform quotas

**Level:** Advanced (platform)  
**Time:** ~120–150 minutes  
**Prerequisites:** Lessons 20, 30, 31, 43 (routing, tenants, cost, SLOs)  
**Lab outcome:** Put **one** access layer in front of Gemini: auth, **token budgets**, optional **cache** for safe reads — ADK still owns agents; the gateway owns **keys and meters**

**Standard:** [docs/NATIVE-ADK.md](../docs/NATIVE-ADK.md)

---

## At a glance

Today every laptop and Cloud Run revision may hold `GOOGLE_API_KEY`. That does not scale:

- Key rotation means hunting 12 `.env` files  
- Franchise and US share one RPM until Google 429s everyone  
- Identical “Where is MC-1048277?” hits the model **and** OMS every time  

An **LLM gateway** (also called an access layer) is an HTTP service **your** platform runs:

```
ADK LlmAgent  →  (OpenAI-compatible or Google client)
                    │
                    ▼
           Meridian LLM gateway
                    │
        ┌───────────┼───────────┐
        ▼           ▼           ▼
      cache      rate limit    real Gemini
   (WISMO only)  (tenant TPM)   (miss / money)
```

You will **not** replace `LlmAgent` with a homemade agent loop. You point the **model client** at a gateway **or** you wrap the edge so tools/OMS can cache. Lab: a small FastAPI gateway + ADK still as today.

---

## Why this matters

Three replicas retry a WISMO during an OMS blip. Each replica has the key. Google sees **3×** RPM. FinOps (31) and SLOs (43) both light up.

A gateway gives you:

- **One** secret to rotate  
- **Per-tenant** token budgets in one place  
- **Cache** for repeatable **read** questions  
- A single place to attach allow-lists (no Pro from franchise)

Refunds, HITL, and anything that can **change money** stay **uncached** and un-shared.

---

## Know these

| Term | Meaning |
|------|---------|
| **Gateway** | Proxy that meters/authenticates model calls |
| **TPM / RPM** | Tokens per minute / requests per minute |
| **Exact cache** | Same key → same bytes (prompt + model + temperature) |
| **Semantic cache** | “Similar meaning” → reuse answer (dangerous for orders) |
| **TTL** | How long a cache entry lives |
| **Cache stampede** | Many misses at once when TTL expires |
| **Allow-list** | Which models a tenant may call |
| **Key vault** | Where the **real** Gemini key lives (not in agent images) |

> **Watch out:** Semantic cache on “where is my order” can return **yesterday’s** status for a **different** customer if you key badly. Prefer **exact** cache on `order_id` + tool results, not fuzzy text.

---

## Task 1 — What must never be cached

### Why

A wrong cache is a **silent** invented POD.

### Do this

Create `project/meridian_ops/gateway/CACHE_POLICY.md`:

| Path | Cache? | Why |
|------|--------|-----|
| WISMO `get_order` by `order_id` | maybe, short TTL | facts change (out for delivery) |
| ATP snapshot | maybe, TTL seconds | inventory moves |
| Refund / payments | **never** | money |
| HITL decision | **never** | human-specific |
| Policy FAQ RAG | maybe | cite + version the chunk ids |
| Vision POD | **never** in lab | easy to mix photos |
| Critic scores | no | must see **this** draft |

Rule: cache **tool facts** with explicit keys (`order_id`) before you cache **LLM prose**.

### Expect

Refunds are **never** in the “yes” column.

---

## Task 2 — Exact cache for OMS reads (safest win)

### Why

Most WISMO cost is often **repeat** “where is MC-1048277?” not poetry.

### Do this

In `get_order` (or a thin wrapper used only when `MERIDIAN_OMS_CACHE=1`):

- Key = `order:{order_id}`  
- TTL = `MERIDIAN_OMS_CACHE_TTL_SEC` (lab: 15)  
- Store in process dict **or** Redis (Lesson 29)  
- Header/log `X-Cache: HIT|MISS` on the edge when you know

```bash
# First curl MISS, second curl within TTL should HIT
# MERIDIAN_OMS_CACHE=1 enables the wrapper
```

Tests:

- Same `order_id` twice within TTL → one underlying fixture read (counter)  
- After TTL → miss  
- `request_refund` path never calls this cache helper

```bash
export PYTHONPATH=project
python -m pytest project/meridian_ops/tests/test_oms_cache.py -q
```

### Expect

A **counter** proves the second WISMO did not re-parse fixtures (or re-call a fake HTTP).

> **Tip:** When OMS chaos is on (Lesson 32), **do not** serve a HIT from before the outage as if it were live unless you label the response `stale=true` and your SLO allows degraded reads.

---

## Task 3 — Lab LLM gateway (meter + allow-list)

### Why

Agents should not each implement TPM math.

### Do this

Add `project/meridian_ops/gateway/app.py` as a **small FastAPI** app (separate from OrderOps edge):

Endpoints (keep them tiny):

- `POST /v1/meter/check` — body: `{tenant_id, model, est_tokens}` → `{allow, reason}`  
- `GET /healthz`

Logic:

- Load tenant allow-list: franchise **cannot** use Pro  
- Deduct from a per-minute token bucket (RAM lab; Redis prod)  
- Deny → `allow: false`, reason `tpm` or `model_forbidden`

```bash
# --port 8090: gateway port, distinct from OrderOps 8080
uvicorn meridian_ops.gateway.app:api --port 8090
# --port: which TCP port to bind
```

```bash
curl -s -X POST http://127.0.0.1:8090/v1/meter/check \
  -H "Content-Type: application/json" \
  -d '{"tenant_id":"franchise-demo","model":"gemini-2.5-pro","est_tokens":1000}'
```

Expect deny.

OrderOps edge (optional hook): before `runner.run_async`, call meter check; on deny return 429.

### Expect

Pro is blocked for franchise **even if** someone sets the agent model in YAML wrong.

> **Watch out:** This lab gateway is **not** a reimplementation of Gemini. Do not proxy the full generateContent API unless you already know the vendor protocol. Metering + allow-list is the learning goal. Production often uses Vertex + org policies or an API gateway your company already runs.

---

## Task 4 — Stampede and TTL

### Why

TTL=15s on a hot `order_id` expires for **all** handhelds at once.

### Do this

In `CACHE_POLICY.md`, write:

- **Jitter:** TTL + random 0–5s  
- **Singleflight:** one in-flight OMS fetch per `order_id` (asyncio lock map)  
- When you would **skip** cache: `Cache-Control` from client `no-cache` for the customer who just saw a driver update

Implement **jitter or singleflight** in the OMS cache tests (one is enough).

### Expect

A test that two parallel first-misses do not double-fetch if you implemented singleflight — **or** a documented jitter formula if you chose jitter only.

---

## Task 5 — Rotate the key without rotating agents

### Why

Platform ownership: agents don’t own secrets.

### Do this

In `project/meridian_ops/gateway/SECRETS.md`:

| Secret | Lives in | Who rotates | Agents see? |
|--------|----------|-------------|-------------|
| Gemini / Vertex | Secret manager / gateway env | platform | **no** (prod target) |
| OrderOps API keys | edge env | platform | no |
| Tenant OMS creds | secret manager | banner IT | tools via env at runtime |

Lab honesty: your `.env` still has a key for `adk web`. Write the **target**: Cloud Run OrderOps uses Vertex ADC; gateway (if used) holds the vendor credential.

One drill: change `MERIDIAN_API_KEY` on the **edge** and prove old handheld keys 401 — that is the same **habit** as Gemini rotation.

### Expect

A rotation story that does not say “email all developers to paste a new key into agent.py.”

---

## Task 6 — Connect the meters (FinOps + SLO)

### Why

A gateway that nobody reads is a new SPOF.

### Do this

Emit:

- `meridian_gateway_deny_total{reason}`  
- `meridian_oms_cache_hit_total`  

In `31-finops` report language: cache HIT → `$0` model cost for that turn if you skipped the LLM **or** only skipped OMS — **say which**.

If you only cached OMS, the LLM may still run. Do not claim you saved the full WISMO cost.

### Expect

One honest sentence: “We saved OMS load” vs “We saved tokens.”

---

## How it works (deeper dive)

**Where to cache in an agent stack**

1. **Tool layer** (this lab) — best for facts (`get_order`)  
2. **HTTP CDN** — rarely right for personalized WISMO  
3. **LLM response cache** — only with exact prompt+params and **no** user-specific data  

**Vertex / org policy**

Many enterprises skip a custom LLM proxy and use **Vertex AI** + VPC-SC + quota projects per tenant. The **ideas** (allow-list, TPM, no shared key in git) still apply.

**ADK model string**

Pointing `LlmAgent(model=...)` at a proxy is vendor-specific. If you cannot do it cleanly, keep ADK talking to Google and put the gateway in front of **your tools and quotas**. That is still production-scale engineering.

---

## Common pitfalls / troubleshooting

| Symptom | Fix |
|---------|-----|
| Cached refund confirmation | Never cache money paths |
| Semantic cache, wrong customer | Exact `order_id` keys only |
| Gateway is a second ADK | Delete it; meter only |
| Stampede after deploy | Jitter + singleflight |
| FinOps shows $0 on cache HIT but LLM still ran | Fix the report |

---

## You are done when

- [ ] CACHE_POLICY.md with refunds = never  
- [ ] OMS exact cache + tests  
- [ ] Gateway meter deny for franchise + Pro  
- [ ] Stampede note + jitter or singleflight  
- [ ] Secret rotation story  
- [ ] Honest cost/SLO attribution for hits  

---

## Knowledge check

1. Why is semantic cache risky for WISMO?  
2. What should a franchise Pro call do at the gateway?  
3. Why cache `get_order` before caching LLM text?  
4. What is a cache stampede?  
5. Must every company build a custom Gemini proxy?

### Answers

1. Similar wording can attach the **wrong order’s** facts.  
2. **Deny** (`model_forbidden`), not “let ADK try.”  
3. Facts are keyed by `order_id`; prose is easy to mix and stale.  
4. Many clients miss together when TTL expires; origin melts.  
5. **No** — Vertex/org quotas can be the gateway; you still need the **policies**.

---

## Recap

- One control plane for **keys, TPM, allow-lists**, and **safe** caches.  
- ADK remains the agent runtime.  
- Pack G is productizing this platform for other teams.

---

## Stretch goal

Singleflight map + Redis cache shared by two `uvicorn` workers. Prove HIT across processes (docker compose two app replicas, one Redis).

---

## Feedback

- Could you tell security where the Gemini key will live next quarter?  
- Note task number + whether you cached tools, LLM text, or both.

---

## Navigate

**← Prev** [Lesson 43 — SLOs & capacity](43-slos-capacity-backpressure.md)  
**Next pack:** [Lesson 33 — SME teams](33-sme-teams-teaching.md) *(Pack G, when shipped)*  
**Track home:** [README](../README.md)

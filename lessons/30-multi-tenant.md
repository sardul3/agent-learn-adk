# Lesson 30 — Multi-tenant agent platforms

**Level:** Advanced (platform)  
**Time:** ~120–150 minutes  
**Prerequisites:** Lessons 07, 16, 26, 29 (least privilege, MCP filters, plugins, sessions)  
**Lab outcome:** Run OrderOps as a **platform**: isolate tenants, cap usage, and attach **different tools** per tenant — without copying the whole agent tree

**Standard:** [docs/NATIVE-ADK.md](../docs/NATIVE-ADK.md)

---

## At a glance

A **tenant** is a customer of your platform. For Meridian labs:

| Tenant id | Who | What they may do |
|-----------|-----|------------------|
| `banner-us` | US grocery banners | WISMO + ATP + refund HITL |
| `banner-ca` | Canada | WISMO + ATP; **no** USD refund tool |
| `franchise-demo` | Partner store | WISMO **only** |

If they share one agent with every tool, Canada can hit US payments. That is not a bug in Gemini — it is a **platform** bug.

```
Request
  headers: X-Tenant=banner-ca  X-Api-Key=...
        │
        ▼
Edge: authenticate + resolve tenant policy
        │
        ▼
Runner: app_name includes tenant OR tool_filter / plugin deny
        │
        ▼
Session keyed by tenant + user  (no cross-read)
```

---

## Why this matters

Meridian IT wants **one** OrderOps image, many banners.

Without isolation:

- Franchise demo keys call `request_refund`  
- US eval goldens leak into CA sessions  
- One noisy banner burns the shared Gemini quota (Lesson 31 / 43)

Multi-tenant means **isolation, quotas, and per-tenant tools** — not a new ADK.

---

## Know these

| Term | Meaning |
|------|---------|
| **Tenant** | Isolation boundary (banner, region, partner) |
| **Isolation** | Tenant A cannot read B’s sessions, tools, or secrets |
| **Quota** | Max requests/tokens per window per tenant |
| **Noisy neighbor** | One tenant starves others |
| **tool_filter** | MCP/tool allow-list (Lesson 16) |
| **Blast radius** | How far a stolen franchise key can go |
| **Row-level** | Same table, filtered by tenant id (sessions, logs) |

---

## Task 1 — Threat model: three tenants, one image

### Why

If you cannot name the failures, you will “add a header” and call it done.

### Do this

Create `project/meridian_ops/platform/TENANTS.md`:

| Attack / mistake | Without isolation | Control you will build |
|------------------|-------------------|------------------------|
| Stolen `franchise-demo` key | | |
| CA agent loads US payments | | |
| Session id guessed from another tenant | | |
| Banner-us floods `/v1/wismo` | | |
| Eval job uses prod `app_name` | | |

### Expect

Every row has a **control**, not “trust the prompt.”

---

## Task 2 — Tenant policy as config (not a new framework)

### Why

Banners change privileges without a code fork.

### Do this

Add `project/meridian_ops/platform/tenants.yaml`:

```yaml
tenants:
  banner-us:
    display_name: Meridian US
    max_requests_per_minute: 60
    allow_refund_hitl: true
    mcp_tool_filter:
      - get_order
      - get_atp
      - suggest_substitute_for_short
      - reserve_substitute
    model: gemini-2.5-flash
  banner-ca:
    display_name: Meridian CA
    max_requests_per_minute: 30
    allow_refund_hitl: false
    mcp_tool_filter:
      - get_order
      - get_atp
    model: gemini-2.5-flash
  franchise-demo:
    display_name: Franchise sandbox
    max_requests_per_minute: 10
    allow_refund_hitl: false
    mcp_tool_filter:
      - get_order
    model: gemini-2.5-flash
```

Load it with a small `project/meridian_ops/platform/tenant_config.py`:

- `get_tenant(tenant_id: str)` → policy or `None`  
- Unknown tenant → deny at the edge (401/403), **not** a default-admin policy  

Unit test:

```bash
# -q: quiet; only failures print
export PYTHONPATH=project
python -m pytest project/meridian_ops/tests/test_tenant_config.py -q
```

Write tests that:

- `banner-ca` has `allow_refund_hitl is False`  
- unknown id returns `None`  
- franchise filter is **only** `get_order`

### Expect

YAML is the source of truth. Code does not hardcode “Canada is nice.”

---

## Task 3 — Edge: authenticate tenant, never trust the body

### Why

If the model (or a client JSON body) can send `tenant_id=banner-us`, isolation is theater.

### Do this

Pick **one** binding:

| Lab style | How tenant is chosen |
|-----------|----------------------|
| **API key → tenant** (preferred) | Map `X-Api-Key` to tenant in a **non-committed** local map or env `MERIDIAN_TENANT_KEYS` |
| Header `X-Tenant` | Only after the key is valid **and** the key is allowed that tenant |

Rules:

- Do not take tenant from the LLM  
- Do not take tenant from `WismoRequest.message`  
- Log `tenant_id` (ok) — never log the raw API key  

Sketch in `deploy/app.py` (adapt to your file):

```python
def resolve_tenant(x_api_key: str | None) -> str:
    # lookup key → tenant; raise 401 if missing
    ...
```

Before `runner.run_async`, set:

- `user_id` = `f"{tenant_id}:{device_or_user}"`  
- `app_name` = `f"meridian_orderops:{tenant_id}"` **or** keep one app_name and put tenant in `user_id` — **pick one** and write it in `TENANTS.md`

> **Tip:** Separate `app_name` per tenant is the strongest session isolation. Shared `app_name` + prefixed `user_id` is acceptable if you **never** query sessions without the prefix.

### Expect

Wrong key → 401. Franchise key → cannot select `banner-us`.

---

## Task 4 — Per-tenant tools (MCP filter or plugin)

### Why

Instructions that say “Canada must not refund” are skippable (Lesson 23).

### Do this

**Path A (MCP):** pass `tool_filter=policy.mcp_tool_filter` into `McpToolset` (Lesson 16).

**Path B (plugin):** `before_tool` denies `request_refund` / payment tools when `allow_refund_hitl` is false (Lesson 26). Read tenant from a context var the edge sets.

Implement **at least one** path. Prove with pytest (no live Gemini required):

- Franchise policy + attempted refund tool name → denied dict / skip  
- `banner-us` + refund still allowed to **reach** HITL (not auto-pay)

### Expect

Denial happens in **code**. Prompt text is extra, not the gate.

> **Watch out:** A shared global `root_agent` with every tool attached, plus a polite instruction, is **not** multi-tenant.

---

## Task 5 — Quota: noisy neighbor in the lab

### Why

Isolation of **data** is not isolation of **capacity**.

### Do this

Add `project/meridian_ops/platform/quota.py`:

- In-memory counter keyed by `tenant_id` + current minute  
- `try_acquire(tenant_id) -> bool`  
- Limit from YAML `max_requests_per_minute`

Edge: if `False`, return **429** with `Retry-After: 60`.

```bash
# --port 8080: listen on 8080
# In another terminal, bash loop 15 times against franchise-demo key
```

Document in `TENANTS.md`: franchise should 429 before `banner-us` would.

Production: Redis/Memorystore for counters (same idea as Lesson 29 — shared, not process-local). Lab RAM is OK if you **write** that two replicas each have their own counter (quota is then leaky until Redis).

### Expect

You can **show** 429 on the tiny tenant without taking down your own browser session on `banner-us` (use two keys).

---

## Task 6 — Tenant-aware eval and logs

### Why

A failed CA golden must not be “fixed” by looking at US sessions.

### Do this

In `TENANTS.md`:

- Eval `app_name` suffix: `:eval` plus tenant  
- Metrics labels: `tenant_id` on `/metrics` counters (Lesson 12)  
- Online eval inbox (Lesson 24): filename or field includes tenant  

Add a metric line or a comment in `app.py` showing where `tenant=` will go.

### Expect

A reviewer can filter **one banner’s** quality and cost.

---

## How it works (deeper dive)

**SaaS vs one-customer deploy**

- **Multi-tenant SaaS:** one cluster, many banners, hard isolation  
- **Cell per banner:** stronger isolation, higher ops cost  

This lesson is SaaS-on-one-image, which is what platform teams usually start with.

**Secrets**

OMS credentials per tenant belong in a secret manager, **not** in `tenants.yaml` committed to git. YAML holds **policy**; env holds **secrets**.

**Plugins vs copies of agents**

Copying `root_agent` three times in three files will drift. Prefer **one** graph + **filters/plugins** driven by tenant policy.

---

## Common pitfalls / troubleshooting

| Symptom | Fix |
|---------|-----|
| Tenant in JSON body | Ignore it; bind from API key |
| Default tenant = us | Unknown → 403, not US |
| Quota only in RAM, three replicas | Document leak; Redis next |
| MCP filter empty list | Means **no tools**, not “all tools” — confirm ADK behavior; test it |
| Same `user_id` across tenants | Prefix with tenant |

---

## You are done when

- [ ] Threat table complete  
- [ ] `tenants.yaml` + tests  
- [ ] Edge binds tenant from **credentials**  
- [ ] Tools/HITL differ by tenant in code  
- [ ] 429 quota demo  
- [ ] Eval/metrics include tenant  

---

## Knowledge check

1. Why can’t the model choose `tenant_id`?  
2. What is a noisy neighbor?  
3. Why YAML for allow-lists instead of three agent.py files?  
4. Two ways to stop CA from refunding?  
5. Why prefix `user_id` with tenant?

### Answers

1. The model is **untrusted** and prompt-injectable.  
2. One tenant uses so much quota that others fail.  
3. Privileges change without forking graphs; less drift.  
4. **tool_filter** / omit payment tools, and **plugin** deny; plus `allow_refund_hitl: false`.  
5. Session lookups must not collide across banners.

---

## Recap

- One image, many banners: **policy in config, enforcement in edge + plugins/MCP**.  
- Next: those tenants will ask who pays for Gemini.

---

## Stretch goal

Add `shadow_tenant: banner-us` that receives a **copy** of CA traffic for eval only (no tools). Document why you must **not** run refunds in shadow.

---

## Feedback

- Could you onboard a new franchise with YAML only, no new specialist agent?  
- Note task number + expected vs actual 429 behavior.

---

## Navigate

**← Prev** [Lesson 29 — Sessions at scale](29-sessions-at-scale.md)  
**Next →** [Lesson 31 — FinOps for agents](31-finops.md)  
**Track home:** [README](../README.md)

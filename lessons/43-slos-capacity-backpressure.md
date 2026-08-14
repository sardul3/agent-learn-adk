# Lesson 43 — SLOs, capacity & backpressure (production-scale)

**Level:** Advanced (SRE / platform)  
**Time:** ~120–150 minutes  
**Prerequisites:** Lessons 11, 12, 31, 41 (metrics, edge, cost, release train)  
**Lab outcome:** Define **SLIs/SLOs** for OrderOps, size **capacity**, and **shed load** before Gemini or OMS takes the fleet down

**Standard:** [docs/NATIVE-ADK.md](../docs/NATIVE-ADK.md)

---

## At a glance

Pack B taught you to **see** traffic. This lesson teaches you to **promise** and **protect** it.

| Idea | Plain English | Meridian example |
|------|---------------|------------------|
| **SLI** | A number you measure | p95 latency of `/v1/wismo` |
| **SLO** | A promise on that number | 99% of WISMO < 8s over 30 days |
| **Error budget** | How much miss you can afford | 1% of requests may be slow/fail |
| **Capacity** | How much you can take | Flash RPM, Cloud Run CPU, session DB |
| **Backpressure** | Slow down callers when full | Queue or 429 |
| **Load shed** | Drop **low-priority** work | Reject franchise eval, keep WISMO |
| **Saturation** | A resource at the limit | Gemini 429s, thread pool full |

```
Inbound WISMO
    │
    ├─ over concurrency cap? → 429 + Retry-After
    ├─ tenant budget (31)?   → 429 or degrade
    ├─ dependency sick (32)? → 503 degraded
    └─ else → Runner → Gemini / tools
```

This is **not** a new agent runtime. The edge and platform policy decide; ADK still runs the turn.

---

## Why this matters

Saturday 10am: a regional outage. Every store handheld retries WISMO in a loop.

Without backpressure:

- Gemini 429s  
- OMS timeouts pile up  
- HITL refunds wait behind 10,000 “where is my milk” retries  
- You spend the month’s FinOps budget by noon (Lesson 31)

With SLOs and shedding:

- You **page** when the error budget burns  
- You **reject** retries with 429  
- You **keep** a thin WISMO path alive  

---

## Know these

| Term | Meaning |
|------|---------|
| **Latency SLI** | How long a successful WISMO takes |
| **Availability SLI** | Fraction of requests that are 2xx (define 429: usually **client**, not your error) |
| **Quality SLI** | Eval pass rate / invented-POD rate (Lessons 08, 24) |
| **Goodput** | Successful **useful** work per second, not raw RPS |
| **Concurrency** | How many Runner turns at once on one instance |
| **Queueing** | Wait in line vs fail fast |
| **Tail latency** | p95/p99 — what Priya feels on a bad turn |
| **Retry storm** | Clients retry together and make the outage worse |

> **Tip:** Count **429 from your edge** as load-shedding working. Count **5xx** as you breaking the SLO. Write that down or dashboards lie.

---

## Task 1 — Write the SLO document

### Why

You cannot page on a feeling.

### Do this

Create `project/meridian_ops/sre/SLO.md`:

| SLI | Window | SLO | Alert idea |
|-----|--------|-----|------------|
| WISMO availability (non-5xx) | 30d | 99.5% | 5xx burn |
| WISMO latency p95 | 30d | < 8s | p95 > 8s for 15m |
| Tool error rate (`get_order`) | 7d | < 1% | spike vs baseline |
| Quality: invented POD in sampled eval | 7d | < 0.5% | Lesson 24 |

Add **non-goals**: HITL refunds waiting on Priya overnight do **not** count as 8s latency. Split SLIs:

- `wismo_sync` — handheld round trip  
- `refund_hitl` — time-to-pause vs time-to-resume (human clock)

### Expect

Two different clocks. One SLO blob is how teams fight.

---

## Task 2 — Measure what you already expose

### Why

Lesson 12 `/metrics` is the seed, not the finish.

### Do this

Read `project/meridian_ops/deploy/app.py` `/metrics`.

Add (or document) labels/counters:

- `meridian_wismo_requests_total{tenant,result}`  
- `meridian_wismo_latency_ms` (histogram **or** lab: log latency per request and compute p95 offline)  
- `meridian_shed_total{reason}` where reason is `concurrency`, `quota`, `budget`, `chaos`

Prove with one curl:

```bash
# -s: silent body progress; -o: write body to file; -w: print time_total
curl -s -o /tmp/wismo.json -w "time_total=%{time_total}\n" \
  -H "X-Api-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"message":"Where is order MC-1048277?"}' \
  http://127.0.0.1:8080/v1/wismo
```

Paste `time_total` into `SLO.md` as a **baseline**, not the SLO itself (laptop ≠ prod).

### Expect

You know **where** latency will be recorded in prod (Prometheus, Cloud Monitoring, etc.).

---

## Task 3 — Concurrency cap (fail fast)

### Why

Unbounded `Runner` calls on one process = latency explosion then timeouts.

### Do this

`project/meridian_ops/platform/concurrency.py`:

- `asyncio.Semaphore` (or threading semaphore) sized by env `MERIDIAN_MAX_INFLIGHT=8`  
- If acquire wait > `MERIDIAN_SHED_WAIT_MS=50`, **do not** join a long queue — return 429  

Why 50ms: a short wait absorbs tiny bursts; a long queue makes **everyone** miss the 8s SLO.

```bash
# MERIDIAN_MAX_INFLIGHT=1 forces shedding in the lab
# -n 20: twenty requests (if you use a small script)
```

Write a tiny script or use GNU `parallel` / a Python `asyncio` gather of 20 calls. Count 429 vs 200.

Hypothesis in `SLO.md`: “With inflight=1, extra requests shed; p95 of **accepted** work stays bounded.”

### Expect

You **see** 429s. That is success, not a failed lab.

> **Watch out:** Clients must honor `Retry-After`. If the handheld retries immediately with no jitter, you create a retry storm. Document **exponential backoff** in the runbook.

---

## Task 4 — Priority: keep WISMO, shed the rest

### Why

Not all agent work is equal during an incident.

### Do this

Define priority in `SLO.md`:

| Priority | Traffic | During Gemini 429s |
|----------|---------|---------------------|
| P0 | Sync WISMO | keep |
| P1 | ATP substitute | keep if capacity |
| P2 | Online eval sampling (24) | shed |
| P3 | Batch FAQ ingest | shed |

Implement a header `X-Meridian-Priority` **only from internal callers** (eval). Public handheld = P0.

If `inflight` is high, reject P2/P3 first.

### Expect

A written rule: **eval never starves store ops**.

---

## Task 5 — Capacity napkin math

### Why

Autoscaling CPU does not create Gemini RPM.

### Do this

Fill `project/meridian_ops/sre/CAPACITY.md`:

| Bottleneck | How you measure | Lab stand-in | Scale action |
|------------|-----------------|--------------|--------------|
| Gemini RPM / TPM | vendor quota + 429s | env cap | degrade Flash, shed P2 |
| Cloud Run instances | CPU/RAM | docker one replica | max instances |
| Session DB | connections | sqlite lock | Postgres/Memorystore (29) |
| OMS | tool timeouts | chaos flag (32) | 503 + cache (44) |

Compute:

- Peak handhelds × requests/min × tokens/request ≈ **TPM**  
- Compare to a **fake** quota `MERIDIAN_FAKE_GEMINI_RPM=10` in lab

One paragraph: **horizontal pods cannot fix a model quota.**

### Expect

A number (even approximate) for “how many WISMOs per minute this lab key can take.”

---

## Task 6 — Error budget policy

### Why

Lesson 41 canary needs a reason to **stop shipping**.

### Do this

In `SLO.md`:

- If 30d availability SLO is 99.5%, monthly error budget is **0.5%** of requests  
- Policy: **freeze** prompt/graph deploys when 50% of the budget is burned in 7 days (unless a SEV hotfix)

Link this to Lesson 41 rollback: burn rate → rollback revision **or** flag off vNext (Lesson 32).

### Expect

A sentence on-call can follow without a meeting.

---

## How it works (deeper dive)

**Why agent SLOs are two-layered**

1. **Platform:** HTTP, 5xx, p95  
2. **Product quality:** judges, invented facts  

A fast lie is a green latency SLO and a failed business. Keep **both** on the dashboard (Lessons 08/24).

**Queue vs shed**

Queues hide overload until the handheld hits 30s. Prefer **short wait + 429** for sync WISMO. Use queues for **offline** eval ingest.

**Virtual threads / async**

More concurrent waits on OMS can raise throughput until Gemini or the DB saturates. Cap **in-flight model calls** separately from HTTP workers if you can.

---

## Common pitfalls / troubleshooting

| Symptom | Fix |
|---------|-----|
| 429 counted as downtime | Document: shed ≠ 5xx |
| SLO includes HITL sleep | Split SLIs |
| Autoscaled to 100 pods, still 429 Gemini | Quota, not CPU |
| Infinite client retries | Backoff + jitter in the handheld spec |
| No `shed` metric | You cannot prove the cap worked |

---

## You are done when

- [ ] SLO.md with split HITL vs WISMO  
- [ ] Metrics/latency baseline recorded  
- [ ] Concurrency shed demo (429s)  
- [ ] Priority table  
- [ ] Capacity napkin + “pods ≠ RPM”  
- [ ] Error-budget freeze rule  

---

## Knowledge check

1. SLI vs SLO?  
2. Why not put Priya’s overnight HITL into the 8s WISMO SLO?  
3. Why fail fast instead of a 5-minute queue?  
4. What is a retry storm?  
5. Why can’t Cloud Run max-instances fix Gemini TPM?

### Answers

1. SLI = measured; SLO = the **target** on that measure.  
2. That time is **human**, not model/edge.  
3. Everyone would miss p95; better some 429 than all timeouts.  
4. Clients retry together and **amplify** load.  
5. The bottleneck is **vendor quota**, shared by all pods.

---

## Recap

- You promised numbers, capped in-flight work, and shed the cheap traffic first.  
- Next: one **LLM access layer** so every pod does not fight the quota alone.

---

## Stretch goal

Add a synthetic “slow Gemini” sleep when `MERIDIAN_CHAOS_LLM=slow` and show p95 break the lab SLO while availability stays up — quality/latency vs availability.

---

## Feedback

- Could you tell a VP which SLI is burning without opening this lesson?  
- Note task number + how many 429s you saw.

---

## Navigate

**← Prev** [Lesson 31 — FinOps](31-finops.md) · [Lesson 32 — Chaos](32-chaos-dr-feature-flags.md)  
**Next →** [Lesson 44 — LLM gateway, cache & quotas](44-llm-gateway-cache-quotas.md)  
**Track home:** [README](../README.md)

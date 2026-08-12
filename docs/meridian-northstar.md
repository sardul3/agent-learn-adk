# Meridian Commerce — OrderOps Northstar

## Company (fictional, realistic)

**Meridian Commerce** is a multi-banner grocery and general-merchandise retailer:

- ~2,400 stores + same-day delivery + ship-from-DC
- Channels: app, web, store pickup (BOPIS), third-party delivery partners
- Systems you will touch in labs: **OMS** (orders), **WMS/ATP** (inventory), **Payments**, **Policy wiki**, **Case management**

You are a software engineer on the **Customer Operations Platform** team. Leadership wants fewer “where is my order?” tickets bouncing between humans, fewer unauthorized refunds, and an audit trail when an agent acts.

## Product: OrderOps Agent Platform

| Capability | Business outcome |
|------------|------------------|
| Order status & ETA explanation | Deflect WISMO (Where Is My Order) tickets |
| Inventory exception handling | Propose substitute / delay / cancel with store truth |
| Refund & goodwill | Enforce policy; require human approval above threshold |
| Policy-grounded answers | Cite Meridian policy, not invented rules |
| Ops audit | Every tool call and decision is reconstructable |

## Personas you will serve

| Persona | Example ask |
|---------|-------------|
| **Maya** — customer via chat | “Order MC-1048292 says delivered but I got nothing.” |
| **Devon** — store ops lead | “DC shorted SKU 884210 for tomorrow’s pickup wave — what do we tell customers?” |
| **Priya** — CX supervisor | “Agent wants a $180 refund — approve or deny with reason.” |

## Non-goals (keep scope honest)

- Not a full chatbot brand experience redesign
- Not replacing OMS/WMS — agents **call** them via tools
- Not unsupervised money movement — refunds above threshold are HITL

## Success metrics (SME language)

- Trajectory correctness > pretty prose
- Tool call success rate, policy violation rate, $ refunded without approval
- p95 end-to-end latency and $ per resolved ticket

## How lessons map to the product

| Lesson | Slice you build |
|--------|-----------------|
| 01 | Decision record: which Meridian flows are agentic |
| 02 | Thin `order_status_agent` running in `adk web` |
| 03 | Policy-shaped instructions + session state for a ticket |
| 04 | Hardened OMS/WMS tools with validation & fail-loud errors |
| 05 | Router + Order + Inventory + Refund specialists |
| 06 | Policy RAG + compaction; state vs memory clarified |
| 07 | Refund HITL gate, allowlists, max-steps, audit narrative |
| 08 | Golden eval sets + trajectory gates for WISMO/inventory |
| 09 | Judge panel + thinking extraction for audit/CX QA |
| 10 | MLflow experiment ledger (prompt/model/eval lineage) |
| 11 | Traces, SLOs, incident debug (POD-lie drill) |
| 12 | FastAPI + Docker + Cloud Run-class deploy + smoke/rollback |
| 13 | Graph workflows (deterministic edges + HITL branch) |
| 14 | Parallel fan-out, critic loops, custom guards |
| 15 | Long-running checkpoints + HITL resume |
| 16 | MCP tool ecosystem + role allowlists |
| 17 | Event webhooks/queues + A2A policy handoff |
| 18–22 | Advanced RAG, memory, model routing, multimodal, streaming |
| 23–27 | Red team, online eval, canaries, middleware, privacy |
| 42 | RAI champion — scorecard, compliant-ready changes, evidence pack |
| 28–32 | Architecture catalog, sessions scale, multi-tenant, FinOps, chaos |
| 33–37 | Teaching, ITSM, **dynamic agent platform**, governance |
| 38–40 | Capstone trilogy (design / ship-debug / mentor) |
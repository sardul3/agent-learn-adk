# Lesson 27 — Privacy, retention & compliance (practical)

**Level:** Advanced  
**Time:** ~120 minutes  
**Prerequisites:** Lessons 19, 22, 24, 26 (memory write policy, streaming, online eval, plugins)  
**Lab outcome:** Make OrderOps **safe to operate with real people data**: redact, TTL, access audit, and a workable **data subject request** path — without turning the lesson into legal advice

**Standard:** [docs/NATIVE-ADK.md](../docs/NATIVE-ADK.md)

---

## At a glance

This is an **engineering** lesson. Laws differ by region; your job is to build controls lawyers/compliance can map to.

| Control | Meridian meaning |
|---------|------------------|
| **Minimize** | Don’t collect what OrderOps doesn’t need |
| **Redact** | Mask PII in logs, eval lakes, streams |
| **TTL** | Delete/expire transcripts & samples on a clock |
| **Access audit** | Who viewed Maya’s ticket trail? |
| **DSR** | Data subject request: export / delete what you stored |
| **Purpose bind** | Online eval data ≠ marketing feed |

```
Collect less
    │
    ▼
Redact at write boundaries (edge, plugins, eval inbox)
    │
    ▼
Retain with TTL + purpose tags
    │
    ▼
Honor export/delete requests against your stores
```

---

## Why this matters

Online eval (Lesson 24) just started saving trajectories.  
Streaming (Lesson 22) echoes tokens to Devon’s handheld.  
Memory (Lesson 19) keeps SMS preferences.

Then Legal asks:

> “Maya requested deletion. What do we still have, and can we prove it’s gone?”

If your answer is “uh, JSONL files somewhere,” you are not production-ready.

---

## Know these

| Term | Plain English | Lab stand-in |
|------|---------------|--------------|
| **PII** | Data that identifies a person | email, phone, card, address |
| **Minimize** | Store only what you need | order id yes; full card never |
| **Redaction** | Replace sensitive spans with tokens | `[EMAIL]` |
| **TTL** | Time-to-live before expiry/delete | eval samples 30 days |
| **Retention class** | Bucket with a policy | `ops_debug`, `online_eval`, `memory_pref` |
| **DSR export** | Give the person a copy of their data | zip of envelopes by user hash |
| **DSR delete** | Remove or anonymize their data | wipe matching files/rows |
| **Audit log** | Record of access/admin actions | who exported what when |

> **Tip:** This lab teaches **mechanisms**. Real compliance needs counsel + your company’s policies — wire the mechanisms so that mapping is possible.

---

## Task 1 — Data inventory (what OrderOps actually stores)

### Why

You cannot retain/delete what you have not listed.

### Do this

Create `project/meridian_ops/privacy/DATA_INVENTORY.md` and fill from your repo:

| Store | Path / system | PII likely? | Purpose | TTL target |
|-------|---------------|-------------|---------|------------|
| OMS fixtures | `fixtures/orders.json` | low (lab) | catalog | n/a lab |
| Session service | in-memory / Redis later | yes | chat | 7–30d |
| Memory service | prefs | sometimes | CX prefs | 365d |
| Online eval inbox | `online_eval/inbox/*.jsonl` | yes if unredacted | quality | 30d |
| Feedback labels | `feedback/inbox/*.jsonl` | maybe | quality | 90d |
| Audit tool log | `audit/*.jsonl` | low | security | 90d |
| SSE client | browser memory | yes | UX | ephemeral |

Mark each row **redacted-at-write?** yes/no.

### Expect

A complete table for *your* lab paths — no empty “TBD” for stores you already built.

---

## Task 2 — Central redaction module + tests

### Why

Five slightly different regexes = five leak paths.

### Do this

Consolidate into `project/meridian_ops/privacy/redact.py` (merge Lesson 19/24 helpers):

```python
from __future__ import annotations
import hashlib
import re

_EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
_PHONE = re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")
_CARD = re.compile(r"\b(?:\d[ -]*?){13,19}\b")
# Rough US ZIP — lab only
_STREET = re.compile(
    r"\b\d{1,5}\s+[A-Za-z0-9.\s]{3,40}\b(?:st|street|ave|avenue|rd|road|ln|lane)\b",
    re.I,
)


def hash_identifier(value: str, *, salt: str = "meridian-lab") -> str:
    return hashlib.sha256(f"{salt}:{value}".encode()).hexdigest()[:16]


def redact_text(text: str) -> str:
    t = _CARD.sub("[CARD]", text)
    t = _EMAIL.sub("[EMAIL]", t)
    t = _PHONE.sub("[PHONE]", t)
    t = _STREET.sub("[ADDRESS]", t)
    return t
```

Tests for each pattern. Keep `MC-` order ids visible.

### Expect

One module imported by eval sampler, feedback API, and plugins.

---

## Task 3 — Retention classes + sweeper

### Why

JSONL grows forever until a disk page wakes you up.

### Do this

Create `project/meridian_ops/privacy/retention.py`:

```python
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
import json


@dataclass(frozen=True)
class RetentionClass:
    name: str
    ttl_days: int
    directory: Path


CLASSES = [
    RetentionClass("online_eval", 30, Path("meridian_ops/online_eval/inbox")),
    RetentionClass("feedback", 90, Path("meridian_ops/feedback/inbox")),
    RetentionClass("audit", 90, Path("meridian_ops/audit")),
]


def _parse_ts(line: dict) -> datetime | None:
    raw = line.get("created_at")
    if not raw:
        return None
    return datetime.fromisoformat(raw.replace("Z", "+00:00"))


def sweep_jsonl(path: Path, *, ttl_days: int, now: datetime | None = None) -> int:
    """Rewrite jsonl dropping expired records. Returns deleted count."""
    now = now or datetime.now(timezone.utc)
    if not path.exists():
        return 0
    kept: list[str] = []
    deleted = 0
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        obj = json.loads(line)
        ts = _parse_ts(obj)
        if ts and now - ts > timedelta(days=ttl_days):
            deleted += 1
            continue
        kept.append(line)
    path.write_text("\n".join(kept) + ("\n" if kept else ""))
    return deleted
```

Unit test with a temp file containing one fresh and one 40-day-old online_eval line → deleted == 1.

Run:

```bash
python -m meridian_ops.privacy.run_sweep
```

### Expect

Sweeper reports deletes; old lab lines vanish.

---

## Task 4 — Purpose tags on write

### Why

Eval samples must not silently become a CRM export.

### Do this

When writing envelopes/labels, require:

```python
{"purpose": "online_eval", "retention_class": "online_eval", ...}
```

Reject writes missing `purpose` in a small `validate_record` helper used by sampler/feedback.

Document allowed purposes in `privacy/PURPOSES.md`:

- `online_eval`  
- `cx_feedback`  
- `security_audit`  
- `memory_preference`  

### Expect

A write without `purpose` fails a unit test.

---

## Task 5 — DSR export (lab)

### Why

“We take privacy seriously” is not an export.

### Do this

Create `project/meridian_ops/privacy/dsr_export.py`:

```python
from __future__ import annotations
import json
from pathlib import Path
from meridian_ops.privacy.redact import hash_identifier


def export_for_user(user_id: str, *, roots: list[Path]) -> dict:
    target = hash_identifier(user_id)
    found: list[dict] = []
    for root in roots:
        for path in root.rglob("*.jsonl"):
            for line in path.read_text().splitlines():
                if not line.strip():
                    continue
                obj = json.loads(line)
                if obj.get("user_id_hash") == target or obj.get("user_id") == user_id:
                    found.append({"path": str(path), "record": obj})
    return {"user_id_hash": target, "count": len(found), "records": found}
```

CLI:

```bash
python -m meridian_ops.privacy.dsr_export --user maya_c44102
```

Write result to `project/meridian_ops/privacy/exports/<hash>.json` and log an audit line: who ran export, when, count.

### Expect

Export file + audit entry. Empty count is OK if no rows — still proves the path.

---

## Task 6 — DSR delete (lab)

### Why

Export without delete is half a process.

### Do this

Implement `delete_for_user(user_id)` that:

1. Rewrites each jsonl dropping matching `user_id_hash`  
2. Clears matching in-memory demo memory keys if you have a lab store file  
3. Appends audit `{action: "dsr_delete", user_id_hash, deleted_count, at}`  

Test with a seeded line → after delete, export count is 0.

### Expect

Delete is idempotent (second run deletes 0).

> **Watch out:** Backups/MLflow artifacts may still hold copies — list them in DATA_INVENTORY as out-of-scope-for-lab or document manual scrub.

---

## Task 7 — Streaming & logs hard pass

### Why

Lesson 22 SSE can leak what you carefully redacted in eval.

### Do this

Checklist `project/meridian_ops/privacy/STREAM_LOG_CHECK.md`:

- [ ] SSE codec allowlists fields (no raw tool dumps with PII)  
- [ ] `RedactPiiPlugin` registered on Runner (Lesson 26)  
- [ ] App logs never print full `x-api-key`  
- [ ] Error payloads use `agent_failed`, not exception strings with payloads  

Run one intentional card-number user message through stream; confirm client sees `[CARD]` or refusal — not digits.

### Expect

Checked boxes with initials/date.

---

## How it works (deeper dive)

Privacy is a **pipeline property**:

```
ingress → redact/minimize → purpose-tagged store → TTL sweep → DSR export/delete
```

Bolt-on “we’ll anonymize later” fails. Write-time controls beat cleanup heroics.

---

## Common pitfalls / troubleshooting

| Symptom | Fix |
|---------|-----|
| Order ids redacted | Tune patterns; keep `MC-` |
| Sweep deletes everything | Require `created_at` ISO timestamps on write |
| DSR misses feedback file | Inventory + rglob roots list incomplete |
| Legal asks for guarantees | Provide mechanisms + inventory; involve counsel |
| Logging “redacted” but writing raw | Same module on **all** write paths |

---

## You are done when

- [ ] DATA_INVENTORY filled for your stores  
- [ ] Central redact module + tests  
- [ ] TTL sweeper tested and runnable  
- [ ] Purpose tags required on eval/feedback writes  
- [ ] DSR export + delete lab paths work  
- [ ] Stream/log checklist signed  

---

## Knowledge check

1. Why one redaction module?  
2. What is a retention class?  
3. What does DSR delete need besides deleting jsonl lines?  
4. Why purpose tags?  
5. Should SSE stream raw tool results?

### Answers

1. Consistent masking; fewer leak variants.  
2. A named store bucket with a TTL/policy.  
3. Audit trail + awareness of replicas (backups, MLflow).  
4. Prevent silent reuse (eval ≠ marketing).  
5. No — allowlist/redact; prefer status + final text.

---

## Recap

- You inventoried Meridian data.  
- You enforced redact + TTL + purpose.  
- You practiced export/delete with audit.

---

## Stretch goal

Add a “break-glass” viewer that requires dual approval before showing unredacted lab fixtures — log both approvers.

---

## Feedback

- Could you walk Legal through your inventory + DSR path without this doc?  
- Note task number + expected vs actual.

---

## Navigate

**← Prev** [Lesson 26 — Plugins & middleware](26-plugins-callbacks-policy-middleware.md)  
**Track home:** [README](../README.md)  
**Bonus:** [Lesson 42 — Responsible AI champion](42-responsible-ai-champion.md)  
**Next pack:** [Lesson 28 — Architecture patterns catalog](28-architecture-catalog.md) *(Pack F)*

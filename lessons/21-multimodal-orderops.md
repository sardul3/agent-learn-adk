# Lesson 21 — Multimodal OrderOps (POD photos & receipts)

**Level:** Advanced  
**Time:** ~120 minutes  
**Prerequisites:** Lessons 04, 07, 11, 20 (tools, HITL, traces, structured decisions)  
**Lab outcome:** Feed **images + text** into ADK (`Part` image bytes), combine vision with OMS/policy tools, and produce an evidence-backed dispute recommendation — no “trust me, I saw the photo” theater

**Standard:** [docs/NATIVE-ADK.md](../docs/NATIVE-ADK.md)

---

## At a glance

| Input | Role |
|-------|------|
| Customer text | Claim (“never arrived”) |
| **POD photo** | Carrier “proof of delivery” image |
| OMS fields | `pod_photo_present`, address, timestamps |
| Policy RAG | What remedies are allowed |
| Structured decision | Approve / deny / HITL with reasons |

**Native ADK path:** `types.Content` with multiple `Part`s — text **and** image — into `Runner.run_async` / `adk web`.  
**Domain tools:** still call OMS + policy. Vision does not replace tools.

---

## Why this matters

Maya:

> “App says delivered. Nobody home. No bags.”

OMS: `lifecycle=delivered`, `pod_photo_present=true` for `MC-1048292`.  
Carrier photo: a blurry porch… of a **different house number**.

If your agent only reads text, it lectures Maya about “delivered.”  
If it only “looks” at the image without OMS/policy, it invents refunds.

Multimodal OrderOps means: **see + fetch + cite + decide**.

---

## Know these

| Term | Meaning |
|------|---------|
| **Multimodal** | Model input mixes text, images (and sometimes audio) |
| **POD** | Proof of delivery photo from carrier / driver app |
| **Inline image Part** | Image bytes (or file URI) attached to the user message |
| **Vision + tools** | Model interprets pixels *and* calls OMS/policy |
| **Evidence grade** | strong / weak / contradictory — drives HITL |
| **Receipt / label image** | Secondary artifact (price, SKU, melt condition) |

```
User message
  ├─ Part(text): claim
  └─ Part(inline_data): POD jpeg
         │
         ▼
   LlmAgent (vision-capable model)
         │
         ├─ get_order(order_id)
         ├─ retrieve_policy_hybrid(...)
         └─ structured dispute decision
```

---

## Task 1 — Create POD fixtures (two photos, opposite stories)

### Why

You need controlled pixels. Do not scrape random internet images into the lab.

### Do this

Create directory `project/meridian_ops/fixtures/pod/`.

Generate two tiny lab PNGs with Python (no design tools required):

```bash
cd /Users/alishaghatane/dev/agent-learn-sme/project
export PYTHONPATH=.
python - <<'PY'
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

out = Path("meridian_ops/fixtures/pod")
out.mkdir(parents=True, exist_ok=True)

def make(path, lines, bg):
    img = Image.new("RGB", (640, 400), bg)
    d = ImageDraw.Draw(img)
    y = 40
    for line in lines:
        d.text((40, y), line, fill=(20, 20, 20))
        y += 36
    img.save(path)

make(
    out / "pod_mc1048292_mismatch.png",
    [
        "POD LAB FIXTURE — NOT A REAL PHOTO",
        "Order: MC-1048292",
        "Visible house number: 118",
        "Bags: NONE visible",
        "Note: customer address ends in 214",
    ],
    (220, 230, 255),
)
make(
    out / "pod_mc1048277_melt_support.png",
    [
        "POD LAB FIXTURE — NOT A REAL PHOTO",
        "Order: MC-1048277",
        "Porch: correct number 502",
        "Dairy crate visible, warped",
        "Ambient hint: melted residue",
    ],
    (255, 230, 220),
)
print("wrote", list(out.glob("*.png")))
PY
```

If `Pillow` is missing:

```bash
pip install -U Pillow
```

Also add `project/meridian_ops/fixtures/pod/README.md` stating these are **synthetic lab labels**, not real customer photos.

### Expect

Two PNGs on disk. You can open them and read the house-number mismatch vs melt-support story.

> **Watch out:** Never commit real customer POD photos to git.

---

## Task 2 — Helper: build multimodal `Content`

### Why

Every Meridian path (CLI, FastAPI, tests) should attach images the same way.

### Do this

Create `project/meridian_ops/multimodal/parts.py`:

```python
from __future__ import annotations

from pathlib import Path

from google.genai import types


def user_text_and_image(text: str, image_path: str | Path, mime: str = "image/png") -> types.Content:
    path = Path(image_path)
    data = path.read_bytes()
    return types.Content(
        role="user",
        parts=[
            types.Part.from_text(text=text),
            types.Part.from_bytes(data=data, mime_type=mime),
        ],
    )
```

Unit test: parts length == 2; second part has inline bytes / blob (attribute names vary slightly by `google-genai` version — assert non-empty image payload).

### Expect

Helper returns a single `Content` with text + image parts.

---

## Task 3 — Multimodal dispute agent (vision + tools)

### Why

Pixels alone are not Meridian policy. Tools alone miss the porch mismatch.

### Do this

Create `project/meridian_dispute_vision/agent.py`:

```python
from google.adk.agents.llm_agent import Agent

from meridian_ops.tools.oms import get_order
from meridian_ops.tools.policy_rag import retrieve_policy_hybrid

root_agent = Agent(
    name="meridian_dispute_vision",
    model="gemini-2.5-flash",  # vision-capable Flash is fine for lab; Pro for nasty disputes
    description="OrderOps dispute agent: POD images + OMS + policy.",
    instruction="""
You investigate Meridian delivery disputes.

Required procedure:
1) Extract order_id from the user text if present.
2) Call get_order before stating lifecycle / POD flags.
3) Describe what you SEE in the attached image (house number, bags, damage cues).
4) Compare image evidence to OMS fields and the customer claim.
5) Call retrieve_policy_hybrid before recommending money remedies.
6) Grade evidence: strong | weak | contradictory.
7) If contradictory POD vs address claim, prefer escalate_hitl — do not auto-refund large amounts.
8) Never pretend you saw details that are not in the image.
""".strip(),
    tools=[get_order, retrieve_policy_hybrid],
)
```

### Expect

Package importable; `adk web` can load it when pointed at this folder.

---

## Task 4 — Run mismatch POD end-to-end

### Why

This is the POD-lie class of incident from Lesson 11 — now with actual pixels.

### Do this

Script `project/meridian_ops/multimodal/run_pod_case.py`:

```python
import asyncio
from pathlib import Path

from google.adk.apps import App
from google.adk.runners import InMemoryRunner

from meridian_dispute_vision.agent import root_agent
from meridian_ops.multimodal.parts import user_text_and_image

ROOT = Path(__file__).resolve().parents[1]
POD = ROOT / "fixtures" / "pod" / "pod_mc1048292_mismatch.png"


async def main() -> None:
    app = App(name="meridian_dispute_vision", root_agent=root_agent)
    runner = InMemoryRunner(app=app)
    session = await runner.session_service.create_session(
        app_name="meridian_dispute_vision", user_id="maya"
    )
    msg = user_text_and_image(
        "Order MC-1048292 says delivered but I got nothing. Here is the POD photo.",
        POD,
    )
    async for event in runner.run_async(
        user_id="maya", session_id=session.id, new_message=msg
    ):
        if event.is_final_response() and event.content and event.content.parts:
            print(event.content.parts[0].text)


if __name__ == "__main__":
    asyncio.run(main())
```

Run:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme/project
export PYTHONPATH=.
python -m meridian_ops.multimodal.run_pod_case
```

### Expect

Final answer should:

- Mention OMS delivered / POD flag  
- Call out **house number mismatch** (118 vs customer 214 story in fixture)  
- Recommend investigation / HITL — not “delivered so closed”  
- Cite policy if proposing remedy  

> **Tip:** If the model ignores the image, confirm `Part.from_bytes` mime type and that the model id supports vision.

---

## Task 5 — Melt-support case + structured decision

### Why

Not every photo is a mismatch. Damaged goods need a different path.

### Do this

1. Reuse Lesson 20 `RefundDecision` schema.  
2. Either:  
   - add a second Workflow/agent that takes the vision narrative and emits `output_schema=RefundDecision`, or  
   - ask the vision agent to finish with JSON matching the schema if your ADK version allows tools+schema together.

Minimum lab path — after vision run, call `refund_decision_agent` with a packed evidence brief:

```text
OMS: MC-1048277 melted_dairy total 214.55 pod_photo_present=true
Vision notes: <paste model description>
Policy: POL-REFUND-04 HITL over $75 full-order
Customer asks: refund impacted dairy / partial OK
```

### Expect

`decision` is `escalate_hitl` or a partial-remedy path with `policy_ids=["POL-REFUND-04"]` — not silent `approve_auto` for $214.

---

## Task 6 — Trace the multimodal trajectory

### Why

Incidents need reconstructable evidence: which image, which tools, which claim.

### Do this

Using Lesson 11 habits:

1. Capture correlation id / session id for the mismatch run  
2. Confirm tool events include `get_order`  
3. Save final text under `project/meridian_ops/decisions/21-pod-mismatch.md` with:  
   - image filename  
   - evidence grade  
   - decision  

### Expect

A human can replay the story from the note without re-running the model.

---

## Task 7 — Negative tests (blind spots)

### Why

Multimodal systems fail by **overclaiming**.

### Do this

Add tests / checklist runs:

| Case | Expect |
|------|--------|
| Text-only, no image | Agent asks for POD or uses OMS only — does not invent porch details |
| Image attached but wrong order id in text | Clarifies / looks up stated id; doesn’t “see” order id from pixels unless printed |
| `NO_POLICY_HIT` for odd remedy ask | No invented refund schedule |

Automate at least the “no image ⇒ no porch hallucination” check with a text-only `InMemoryRunner` prompt and assert absence of phrases like `"house number"` unless OMS provided it.

### Expect

At least one automated guard against hallucinated visual details.

---

## How it works (deeper dive)

Vision models turn pixels into **soft evidence**.  
OMS/policy tools supply **hard constraints**.  
Structured decisions make the outcome **automatable**.

```
Pixels  →  soft evidence (what might be true)
Tools   →  hard facts (what systems record)
Policy  →  allowed remedies
Schema  →  machine decision
```

SME rule: when soft and hard **contradict**, escalate — don’t average them into a shrug refund.

---

## Common pitfalls / troubleshooting

| Symptom | Fix |
|---------|-----|
| Model ignores image | Check Part bytes + mime; confirm vision model |
| Invents bags on empty photo | Prompt: “only describe visible cues”; add negative test |
| Refunds from vibes | Force `retrieve_policy_hybrid` + HITL thresholds |
| Real PII photos in repo | Synthetic fixtures only |
| Huge images blow tokens/cost | Resize lab fixtures (you already use 640×400) |
| `from_bytes` API differs | Inspect `google.genai.types.Part` — stay native |

---

## You are done when

- [ ] Two synthetic POD fixtures exist and are labeled as lab-only  
- [ ] `user_text_and_image` helper works  
- [ ] Mismatch case recommends HITL / investigation with visible contradiction called out  
- [ ] Melt case ties to POL-REFUND-04 / structured decision  
- [ ] Trajectory note saved for audit  
- [ ] Text-only negative guard exists  

---

## Knowledge check

1. What ADK/genai object carries both text and image?  
2. Why call `get_order` even when a POD image is attached?  
3. What should happen when POD house number contradicts the claim/OMS address story?  
4. Are synthetic lab POD images OK to commit? Real customer PODs?  
5. What is “evidence grade” for?

### Answers

1. `types.Content` with multiple `Part`s (text + image bytes).  
2. Image is soft evidence; OMS is system of record for lifecycle/flags.  
3. Escalate HITL / investigate — don’t auto-close as delivered or auto-refund big $.  
4. Synthetic yes (labeled). Real customer PODs — no.  
5. Driving HITL vs auto paths from strength/contradiction of evidence.

---

## Recap

- You attached real image parts to ADK runs.  
- You combined **vision + OMS + policy**.  
- You treated contradictions as escalations, not coin flips.

---

## Stretch goal

Add a receipt crop fixture for a melted item SKU and teach the agent to list **line-level** refund candidates before full-order talk.

---

## Feedback

- Could you explain soft vs hard evidence with the house-number example?  
- Note task number + expected vs actual.

---

## Navigate

**← Prev** [Lesson 20 — Model routing & structured output](20-model-routing-fallbacks-structured-output.md)  
**Track home:** [README](../README.md)  
**Next:** [Lesson 22 — Streaming UX & progressive responses](22-streaming-ux-progressive-responses.md)

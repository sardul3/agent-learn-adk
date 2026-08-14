# Lesson 21 — Multimodal OrderOps (POD photos & receipts)

**Level:** Advanced  
**Time:** ~120–150 minutes  
**Prerequisites:** Lessons 04, 07, 11, 20 (tools, HITL, traces, `output_schema`)  
**Lab outcome:** Feed **text + image** into native ADK (`types.Content` with two `Part`s), combine Gemini vision with OMS/policy tools, and produce an evidence-backed dispute recommendation — no “trust me, I saw the photo”

**Standard:** [docs/NATIVE-ADK.md](../docs/NATIVE-ADK.md)

---

## At a glance

A delivery dispute is not a paragraph. It is **pixels + OMS + policy**, then a decision Priya can click.

| Input | Role | Soft or hard? |
|-------|------|----------------|
| Customer text | The claim (“never arrived” / “milk melted”) | Soft |
| **POD photo** | What the driver actually photographed | Soft (vision) |
| OMS fields | Lifecycle, `pod_photo_present`, address, amount | **Hard** |
| Policy RAG | What remedies are allowed | **Hard** |
| Structured decision | `escalate_hitl` / `deny` / … | Machine-readable |

**Native ADK path:** `types.Content` with multiple `Part`s — text **and** image bytes — into `Runner.run_async` / `adk web`.  
**Domain tools:** still `get_order` + `retrieve_policy`. Vision does not replace tools. You will not build a local vision stack (no OpenCV, no CLIP, no homemade captioner).

You will build seven pieces, in this order:

| Task | What you add | How you prove it |
|------|----------------|------------------|
| 1 | Two synthetic POD PNGs + OMS address fields | Open the files; `get_order` shows house numbers |
| 2 | `user_text_and_image` helper | `pytest` on `Part`s — no LLM |
| 3 | Dispute **vision agent** (`gemini-3.5-flash` + tools) | Import + `adk web` load |
| 4 | **Mismatch** POD via `InMemoryRunner` | Expected phrases below |
| 5 | **Melted dairy** photo + structured decision | HITL / `POL-REFUND-04`, not auto-refund |
| 6 | Same agent in **`adk web`** | Flags walked; attach PNG |
| 7 | Text-only negative + audit note | No invented porch; file on disk |

If you get lost, scroll back to this table.

```
User message
  ├─ Part.from_text(...)     claim
  └─ Part.from_bytes(...)    POD png
         │
         ▼
   LlmAgent  model=gemini-3.5-flash
         │
         ├─ get_order(order_id)
         ├─ retrieve_policy(query)
         └─ compare pixels to OMS  →  evidence grade  →  HITL or not
```

---

## Why this matters

Maya, ticket `TCK-9004`, order `MC-1048277`, **$214.55**, melted dairy — you already know that path.

A second ticket lands the same hour. Order `MC-1048292`. Maya:

> “App says delivered. Nobody home. No bags. Here is their POD photo.”

OMS: `lifecycle=delivered`, `pod_photo_present=true`.  
The photo: a porch whose house number is **118**. Maya lives at **214 Maple Ave**.

If the agent only reads text, it lectures her about “delivered.”  
If it only “looks” at pixels and never calls OMS or policy, it invents a refund.

Multimodal OrderOps means: **see + fetch + cite + decide**. When soft evidence (pixels) **contradicts** hard evidence (OMS address), you escalate. You do not average them into a shrug refund.

---

## Know these

Read this table before Task 1. Every later task reuses these words.

| Term | Plain English | Meridian example |
|------|---------------|------------------|
| **Multimodal** | One model call mixes text and images | Claim sentence + POD PNG |
| **`types.Content`** | One message: a `role` plus a list of `Part`s | `role="user"` |
| **`types.Part`** | One slice of that message: text **or** media | Text claim; PNG bytes |
| **`Part.from_text`** | Build a text slice | `"Order MC-1048277 arrived melted."` |
| **`Part.from_bytes`** | Put **image bytes inside** the request (`inline_data`) | Lab PNG on disk |
| **`Part.from_uri`** | Point at a **remote** file (`file_data.file_uri`) | `gs://meridian-pod/MC-1048292.jpg` in prod |
| **POD** | Proof of delivery photo from the driver app | Porch picture |
| **Inline image** | Bytes travel with the JSON/request | `from_bytes` |
| **MIME type** | Label for the bytes | `image/png` for these fixtures |
| **Evidence grade** | strong / weak / **contradictory** | 118 vs 214 → contradictory |
| **Soft vs hard evidence** | Pixels vs system of record | Photo vs OMS address |

### Picture this: the claim slip and the porch polaroid

At Store 441 a customer brings two things to the service desk: a **written claim** and a **photo**. Devon staples them to one clipboard. Priya will not rule from the photo alone, and she will not ignore the photo because OMS already says delivered.

`Content.parts` is that clipboard: part 0 is the slip, part 1 is the polaroid.

| Approach | What the model actually receives |
|----------|----------------------------------|
| Put the filename in the prompt: `"see pod.png"` | **Text only.** No pixels. |
| `Part.from_bytes(data=png, mime_type="image/png")` | Pixels **in** the request |
| `Part.from_uri(file_uri="gs://...", mime_type="image/jpeg")` | A URI Gemini can fetch (cloud object) |

### `from_bytes` vs `from_uri` (ADK 2.6.3 / `google.genai.types.Part`)

Verified signatures:

```
Part.from_bytes(*, data: bytes, mime_type: str, media_resolution=None) -> Part
Part.from_uri(*, file_uri: str, mime_type: str | None = None, media_resolution=None) -> Part
Part.from_text(*, text: str) -> Part
```

| Builder | Stores on the `Part` | Use when |
|---------|----------------------|----------|
| `from_bytes` | `inline_data` = `Blob(data=..., mime_type=...)` | The file is **on this machine** (lab fixtures) |
| `from_uri` | `file_data` = `FileData(file_uri=..., mime_type=...)` | The file already lives in **GCS** (carrier POD bucket) |
| `from_text` | `text=...` | The claim, order id, questions |

This lab uses **`from_bytes`**. The PNGs are local. Production OrderOps will often use **`from_uri`** with a `gs://` object the carrier already uploaded — you do not download the whole image into the API process just to send it again.

Do not pass `file://Users/.../pod.png` to `from_uri` as a shortcut. `from_uri` is for a URI the **model API** can fetch. Local lab files go through `from_bytes`.

---

## What you already have (do not rebuild)

| Path | Job |
|------|-----|
| `project/meridian_ops/tools/oms.py` | `get_order` |
| `project/meridian_ops/fixtures/orders.json` | OMS rows — you will **add address fields** |
| `project/meridian_ops/tools/policy_rag.py` | `retrieve_policy` (Lesson 06) |
| `project/meridian_ops/fixtures/policies/refunds_damaged_items.md` | `POL-REFUND-04` — HITL over $75 |
| Lesson 20 `RefundDecision` idea | Structured fields; Task 5 adds a dispute schema |

You will **add**:

```
project/meridian_ops/fixtures/pod/
  README.md
  pod_mc1048292_mismatch.png
  pod_mc1048277_melt_support.png
project/meridian_ops/multimodal/
  __init__.py
  parts.py
  run_pod_mismatch.py
  run_pod_melt.py
project/meridian_ops/tests/test_multimodal_parts.py
project/meridian_ops/tests/test_vision_text_only.py
project/meridian_dispute_vision/
  __init__.py
  agent.py
  decision_agent.py
project/meridian_ops/decisions/21-pod-mismatch.md
```

---

## Task 1 — POD fixtures that tell opposite stories

### Why

You need **controlled pixels**. Random internet photos are a privacy incident waiting to be committed. These two PNGs are labeled lab posters, not real customer porches.

You also need OMS to carry a **house number**, so the mismatch is a fact in `get_order`, not a story you whisper to the model.

### Do this

1. Open `project/meridian_ops/fixtures/orders.json`. Update **`MC-1048292`** (mismatch / “never arrived”) so the photo story can contradict OMS:

   Set / add:

   | Field | Value | Why |
   |-------|--------|-----|
   | `pod_photo_present` | `true` | Carrier claims they photographed the drop |
   | `shipping_address_line` | `"214 Maple Ave"` | Maya’s address |
   | `shipping_address_house_number` | `"214"` | The number vision must compare |

   Leave `lifecycle` as `"delivered"`.

2. Update **`MC-1048277`** (melted dairy) so the **correct** porch number is in OMS:

   | Field | Value |
   |-------|--------|
   | `pod_photo_present` | `true` (already) |
   | `shipping_address_line` | `"502 Cedar Ln"` |
   | `shipping_address_house_number` | `"502"` |
   | `order_total_usd` | `214.55` (already) |
   | `damage_report` | `"melted_dairy"` (already) |

3. Confirm OMS reads the new fields:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
source .venv/bin/activate
export PYTHONPATH=project
python -c "from meridian_ops.tools.oms import get_order; print(get_order('MC-1048292')); print(get_order('MC-1048277'))"
```

   - `source .venv/bin/activate` — this project’s Python.  
   - `export PYTHONPATH=project` — `import meridian_ops` means `project/meridian_ops`.

### Expect

`MC-1048292` success dict includes `"pod_photo_present": true` and house `"214"`.  
`MC-1048277` includes `"214.55"`, `"melted_dairy"`, house `"502"`.

4. Install **Pillow** once — it draws the labeled PNGs. The agent never imports it. Vision stays on Gemini.

```bash
pip install Pillow
```

   `pip install Pillow` — add the imaging library to this venv. Not `pip install -U google-adk`. You are already on ADK 2.6.3.

5. Create the folder and generate both posters:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme/project
export PYTHONPATH=.
python - <<'PY'
from pathlib import Path
from PIL import Image, ImageDraw

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
print("wrote", sorted(p.name for p in out.glob("*.png")))
PY
```

   Walk the generator:

   | Piece | Why |
   |-------|-----|
   | `640×400` | Small. Vision labs do not need 12MB camera dumps. |
   | Printed lines | The model can **read** the poster. That is enough for a fixture. |
   | Blue-ish vs peach | You can tell the files apart at a glance. |
   | `"NOT A REAL PHOTO"` | So nobody mistakes this for customer PII. |

6. Create `project/meridian_ops/fixtures/pod/README.md`:

```markdown
# POD lab fixtures

Synthetic labeled posters for Lesson 21. Not real customer photos.
Do not commit real POD images, receipts, or faces.
```

7. Open both PNGs in Preview (or any viewer). Read the house numbers.

### Expect

Two files:

- `pod_mc1048292_mismatch.png` — house **118**, bags **NONE**  
- `pod_mc1048277_melt_support.png` — porch **502**, warped dairy crate, melted residue  

> **Tip:** Keep fixtures tiny. Token cost and latency grow with image size. 640×400 is the lab cap.

> **Watch out:** Never commit real customer POD photos, even “just for the demo.” These posters are the only images in git.

### Scoreboard after Task 1

| Piece | In place? |
|-------|-----------|
| OMS house numbers + POD flags | **Yes** |
| Two synthetic PNGs | **Yes** |
| `user_text_and_image` helper | Not yet |
| Vision agent | Not yet |
| Mismatch run | Not yet |
| Melt + structured decision | Not yet |
| `adk web` | Not yet |
| Negative + audit note | Not yet |

---

## Task 2 — Build multimodal `Content` (walk every part)

### Why

CLI, FastAPI, tests, and `adk web` must attach images the **same** way. One helper. Native `google.genai.types` only.

### Do this

1. Create `project/meridian_ops/multimodal/__init__.py` as an empty file.

2. Create `project/meridian_ops/multimodal/parts.py`:

```python
from __future__ import annotations

from pathlib import Path

from google.genai import types


def user_text_and_image(
    text: str,
    image_path: str | Path,
    mime: str = "image/png",
) -> types.Content:
    """One user message: claim text + inline image bytes."""
    path = Path(image_path)
    data = path.read_bytes()
    text_part = types.Part.from_text(text=text)
    image_part = types.Part.from_bytes(data=data, mime_type=mime)
    return types.Content(
        role="user",
        parts=[text_part, image_part],
    )


def user_text_and_gcs_image(
    text: str,
    file_uri: str,
    mime: str = "image/jpeg",
) -> types.Content:
    """Same clipboard, but the photo already lives in GCS (production shape)."""
    return types.Content(
        role="user",
        parts=[
            types.Part.from_text(text=text),
            types.Part.from_uri(file_uri=file_uri, mime_type=mime),
        ],
    )
```

   Walk `user_text_and_image` line by line:

   | Line | What it does |
   |------|----------------|
   | `path = Path(image_path)` | Accept a string or `Path`. |
   | `data = path.read_bytes()` | Raw PNG bytes. This is what Gemini will see. |
   | `types.Part.from_text(text=text)` | **Keyword `text=`** is required on this SDK. Builds a text `Part`. |
   | `types.Part.from_bytes(data=data, mime_type=mime)` | Keywords `data=` and `mime_type=` required. Builds `inline_data` (a `Blob`). |
   | `types.Content(role="user", parts=[text_part, image_part])` | One user message, **two** parts, text first. |

   Why text **first**: the claim names the order id. The image is evidence. The clipboard order matches how Priya reads a ticket: words, then photo.

   Why `mime_type="image/png"`: these fixtures are PNGs. A JPEG must be `image/jpeg`. A wrong MIME is how the model “ignores the image.”

   Walk `user_text_and_gcs_image` — you will **not** call this in the lab runner (no GCS). It exists so you can see `from_uri` next to `from_bytes`:

   | Line | What it does |
   |------|----------------|
   | `Part.from_uri(file_uri=..., mime_type=...)` | No local bytes. `Part.file_data.file_uri` is the pointer. |
   | Default `mime="image/jpeg"` | Carrier cameras usually produce JPEG. Lab posters are PNG — that is why the bytes helper defaults to PNG. |

3. Prove the helper without Gemini. Create `project/meridian_ops/tests/test_multimodal_parts.py`:

```python
from pathlib import Path

from meridian_ops.multimodal.parts import user_text_and_gcs_image, user_text_and_image

POD = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "pod"
    / "pod_mc1048277_melt_support.png"
)


def test_text_and_bytes_two_parts():
    content = user_text_and_image(
        "Order MC-1048277 melted. Photo attached.",
        POD,
    )
    assert content.role == "user"
    assert content.parts is not None
    assert len(content.parts) == 2
    text_part, image_part = content.parts
    assert text_part.text.startswith("Order MC-1048277")
    assert image_part.inline_data is not None
    assert image_part.inline_data.mime_type == "image/png"
    assert image_part.inline_data.data
    assert len(image_part.inline_data.data) == POD.stat().st_size
    assert image_part.file_data is None
    assert text_part.inline_data is None


def test_from_uri_does_not_inline_bytes():
    content = user_text_and_gcs_image(
        "POD for MC-1048292",
        "gs://meridian-pod-lab/MC-1048292.jpg",
        mime="image/jpeg",
    )
    image_part = content.parts[1]
    assert image_part.file_data is not None
    assert image_part.file_data.file_uri == "gs://meridian-pod-lab/MC-1048292.jpg"
    assert image_part.file_data.mime_type == "image/jpeg"
    assert image_part.inline_data is None
```

   Walk the assertions — this is the contract:

   | Check | Meaning |
   |-------|---------|
   | `len(parts) == 2` | Clipboard has slip + polaroid |
   | `text_part.text` | Claim is on part 0 |
   | `image_part.inline_data.data` | Bytes path actually inlined |
   | `len(...) == POD.stat().st_size` | We did not truncate the file |
   | `image_part.file_data is None` | `from_bytes` does **not** set a URI |
   | URI helper: `inline_data is None` | `from_uri` does **not** read the disk |

4. Run:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
source .venv/bin/activate
export PYTHONPATH=project
pytest project/meridian_ops/tests/test_multimodal_parts.py -v
```

   `-v` — print each test name.

### Expect

```
test_multimodal_parts.py::test_text_and_bytes_two_parts PASSED
test_multimodal_parts.py::test_from_uri_does_not_inline_bytes PASSED
```

Two parts. Bytes helper inlines. URI helper points. No LLM.

> **Tip:** FastAPI can call `user_text_and_image` after it reads an upload. Same `Content` the script uses. Do not invent a second image type.

> **Watch out:** `Part.from_text("hello")` without `text=` fails on this SDK. Always `from_text(text=...)`, `from_bytes(data=..., mime_type=...)`, `from_uri(file_uri=..., mime_type=...)`.

### Scoreboard after Task 2

| Piece | In place? |
|-------|-----------|
| OMS house numbers + POD flags | Yes |
| Two synthetic PNGs | Yes |
| `user_text_and_image` helper | **Yes** |
| Vision agent | Not yet |
| Mismatch run | Not yet |
| Melt + structured decision | Not yet |
| `adk web` | Not yet |
| Negative + audit note | Not yet |

---

## Task 3 — Dispute vision agent (walk every keyword)

### Why

Pixels alone are not Meridian policy. Tools alone miss the porch mismatch. One `Agent` with a **vision-capable** Flash model **and** the OMS/policy belt.

Model for this lab: **`gemini-3.5-flash`**. It accepts image `Part`s. You do not stand up a second vision service.

### Do this

1. Create `project/meridian_dispute_vision/__init__.py`:

```python
from . import agent
```

2. Create `project/meridian_dispute_vision/agent.py`:

```python
from google.adk.agents.llm_agent import Agent
from google.adk.apps import App

from meridian_ops.tools.oms import get_order
from meridian_ops.tools.policy_rag import retrieve_policy

GEMINI = "gemini-3.5-flash"

root_agent = Agent(
    name="meridian_dispute_vision",
    model=GEMINI,
    description="OrderOps dispute agent: POD images + OMS + policy.",
    instruction="""
You investigate Meridian delivery and damage disputes.

Required procedure — do not skip:
1) Extract order_id (MC-…) from the user text if present.
2) Call get_order before stating lifecycle, POD flags, address, or amount.
3) Describe ONLY what you SEE in the attached image (house number, bags,
   crates, melt/damage cues, printed labels). If there is no image, say so
   and do not invent porch details.
4) Compare image evidence to OMS fields and the customer claim.
5) Call retrieve_policy before recommending money remedies.
6) Grade evidence: strong | weak | contradictory.
7) If the POD house number contradicts OMS / the claim, evidence_grade is
   contradictory. Prefer escalate_hitl. Do not auto-refund. Do not close
   as “delivered, no issue.”
8) If the photo supports melted/warped dairy AND OMS damage_report is
   melted_dairy AND amount is over $75, cite POL-REFUND-04 and escalate_hitl.
   Never claim a refund already completed.
9) Never pretend you saw details that are not in the image.
""".strip(),
    tools=[get_order, retrieve_policy],
)

app = App(name="meridian_dispute_vision", root_agent=root_agent)
```

   Walk every `Agent(...)` keyword:

   | Keyword | Effect |
   |---------|--------|
   | `name="meridian_dispute_vision"` | Stable id in `adk web` and traces |
   | `model="gemini-3.5-flash"` | Vision-capable Flash. Same family as Lesson 20 Flash. |
   | `description=...` | What the UI / routers show |
   | `instruction` | Procedure. Soft. Tools + HITL thresholds are hard. |
   | `tools=[get_order, retrieve_policy]` | Hard facts. **No** `request_refund`. This agent investigates; it does not settle. |

   Walk the instruction as a checklist the model must follow:

   ```
   parse MC-…  →  get_order  →  describe pixels  →  compare to OMS
        →  retrieve_policy  →  grade evidence  →  HITL language
   ```

   | Step | Stops this failure |
   |------|-------------------|
   | `get_order` first | Inventing `delivered` from the photo |
   | Describe only visible cues | “I see bags” on an empty porch poster |
   | `retrieve_policy` before money talk | Inventing a $50 goodwill schedule |
   | Contradictory → HITL | Closing Maya’s mismatch as delivered |
   | Melt + $214 → HITL + `POL-REFUND-04` | Auto-approving a full-order refund |
   | No `request_refund` on `tools=` | The intern cannot confirm from this agent |

   Walk `App(...)`:

   | Keyword | Effect |
   |---------|--------|
   | `name="meridian_dispute_vision"` | Must match `create_session(app_name=...)` |
   | `root_agent=root_agent` | Who runs |
   | (no `plugins=` today) | Lesson 26 adds store-wide locks. This agent has no money tool. |

3. Prove the package imports:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
source .venv/bin/activate
export PYTHONPATH=project
python -c "from meridian_dispute_vision.agent import root_agent, app, GEMINI; print(root_agent.name, GEMINI, app.name, [getattr(t, 'name', getattr(t, '__name__', t)) for t in root_agent.tools])"
```

### Expect

```
meridian_dispute_vision gemini-3.5-flash meridian_dispute_vision ['get_order', 'retrieve_policy']
```

Tool names are the functions. No `request_refund`.

> **Tip:** `Agent` is `LlmAgent`. Same class as Lessons 03–07. The doorbell name in this curriculum is `Agent`.

> **Watch out:** Do not add a local captioner “in case vision fails.” If Gemini cannot see the image, fix the `Part` (bytes + MIME). Do not DIY vision.

### Scoreboard after Task 3

| Piece | In place? |
|-------|-----------|
| OMS house numbers + POD flags | Yes |
| Two synthetic PNGs | Yes |
| `user_text_and_image` helper | Yes |
| Vision agent | **Yes** |
| Mismatch run | Not yet |
| Melt + structured decision | Not yet |
| `adk web` | Not yet |
| Negative + audit note | Not yet |

---

## Task 4 — Mismatch POD end-to-end (`InMemoryRunner`)

### Why

This is the POD-lie class of incident: OMS says delivered; the photo is the **wrong house**. You send real image parts, not a filename in the prompt.

### Do this

1. Create `project/meridian_ops/multimodal/run_pod_mismatch.py`:

```python
from __future__ import annotations

import asyncio
from pathlib import Path

from google.adk.apps import App
from google.adk.runners import InMemoryRunner

from meridian_dispute_vision.agent import root_agent
from meridian_ops.multimodal.parts import user_text_and_image

ROOT = Path(__file__).resolve().parents[1]
POD = ROOT / "fixtures" / "pod" / "pod_mc1048292_mismatch.png"
CLAIM = (
    "Order MC-1048292 says delivered but I got nothing. "
    "Nobody was home. Here is the carrier POD photo."
)


def _print_event(event) -> None:
    content = getattr(event, "content", None)
    if not content or not content.parts:
        return
    for part in content.parts:
        fc = getattr(part, "function_call", None)
        if fc:
            print("TOOL_CALL", fc.name, dict(fc.args or {}))
        fr = getattr(part, "function_response", None)
        if fr:
            print("TOOL_RESULT", fr.name, fr.response)
        text = getattr(part, "text", None)
        if text:
            print("TEXT", text)


async def main() -> None:
    app = App(name="meridian_dispute_vision", root_agent=root_agent)
    runner = InMemoryRunner(app=app)
    session = await runner.session_service.create_session(
        app_name="meridian_dispute_vision",
        user_id="maya",
    )
    msg = user_text_and_image(CLAIM, POD)
    print("PARTS", len(msg.parts), "roles", msg.role)
    print("P0_TEXT", msg.parts[0].text[:80])
    print(
        "P1_MIME",
        msg.parts[1].inline_data.mime_type,
        "bytes",
        len(msg.parts[1].inline_data.data),
    )
    async for event in runner.run_async(
        user_id="maya",
        session_id=session.id,
        new_message=msg,
    ):
        _print_event(event)


if __name__ == "__main__":
    asyncio.run(main())
```

   Walk `main()` in order — this is the native invoke path:

   ```
   App(name, root_agent)
        │
        ▼
   InMemoryRunner(app=app)          ← in-memory session/artifact/memory
        │
        ▼
   create_session(app_name=..., user_id="maya")
        │
        ▼
   user_text_and_image(CLAIM, POD)  ← Content with 2 parts
        │
        ▼
   runner.run_async(user_id, session_id, new_message=msg)
        │
        ├─ TOOL_CALL get_order MC-1048292
        ├─ TOOL_RESULT lifecycle=delivered house=214 pod_photo_present=true
        ├─ TOOL_CALL retrieve_policy …
        └─ TEXT  (mismatch + HITL language)
   ```

   | Line | Why it is there |
   |------|-----------------|
   | `App(name="meridian_dispute_vision", root_agent=root_agent)` | Native container. `app_name` on the session must match. |
   | `InMemoryRunner(app=app)` | Lab runner. Do not pass `plugins=` next to `app=` (Lesson 26). |
   | `create_session(..., user_id="maya")` | One session per customer in the lab. |
   | `user_text_and_image(CLAIM, POD)` | **This** is how pixels enter ADK. |
   | Print `PARTS` / `P1_MIME` **before** `run_async` | If MIME or bytes are wrong, you see it before blaming Gemini. |
   | `_print_event` | You need tool names in the terminal, not only the final paragraph. |

2. Run it. This calls Gemini. `GOOGLE_API_KEY` must be set (Lesson 02).

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
source .venv/bin/activate
export PYTHONPATH=project
python -m meridian_ops.multimodal.run_pod_mismatch
```

   - `python -m` — run as a module so `meridian_ops` and `meridian_dispute_vision` import.

### Expect

Startup lines:

```
PARTS 2 roles user
P0_TEXT Order MC-1048292 says delivered but I got nothing. Nobody was home.
P1_MIME image/png bytes <some positive length>
```

Then tool events that include:

```
TOOL_CALL get_order {'order_id': 'MC-1048292'}
```

OMS result includes `delivered`, `pod_photo_present: true`, house **214**.

Final `TEXT` should include **all** of these ideas (wording may vary; the facts must not):

| Must appear | Must **not** appear |
|-------------|---------------------|
| House number **118** visible in the photo | “Bags on the porch” / “delivery complete, case closed” |
| OMS / customer address **214** | “I refunded you $…” |
| **Mismatch** / **contradictory** evidence | Auto-approve language |
| Escalate / supervisor / **HITL** / investigate | Invented policy dollar amounts with no `retrieve_policy` |

If `retrieve_policy` ran, citations should match returned docs — there may be no perfect “wrong-house POD” policy. Then the agent should say it cannot invent a schedule and still escalate. That is correct. `NO_POLICY_HIT` is not a license to guess.

> **Tip:** If the model ignores the image, the pre-flight `P1_MIME` / `bytes` print is your first check. Zero bytes or `image/jpeg` on a PNG is the usual bug. Then confirm `gemini-3.5-flash` on the agent.

> **Watch out:** Do not “help” the model by putting `Visible house number: 118` in the **text** claim. The point of the lab is that those digits come from the **image** part. The claim above only says delivered / nobody home / photo attached.

### Scoreboard after Task 4

| Piece | In place? |
|-------|-----------|
| OMS house numbers + POD flags | Yes |
| Two synthetic PNGs | Yes |
| `user_text_and_image` helper | Yes |
| Vision agent | Yes |
| Mismatch run | **Yes** |
| Melt + structured decision | Not yet |
| `adk web` | Not yet |
| Negative + audit note | Not yet |

---

## Task 5 — Melted dairy photo + structured decision

### Why

Not every photo is a mismatch. Maya’s **$214.55** melt is the honest path: the porch number **matches**, the crate looks warped, OMS already has `damage_report=melted_dairy`. Policy still forbids auto full-order over $75 (`POL-REFUND-04`).

You will:

1. Run the vision agent on the melt PNG and check the **phrasing**.  
2. Feed a packed evidence brief into a small **`output_schema`** agent (same idea as Lesson 20 `RefundDecision`) so Priya’s screen gets fields, not a poem.

### Do this

1. Create `project/meridian_ops/multimodal/run_pod_melt.py`. Same runner shape as Task 4; different PNG and claim.

```python
from __future__ import annotations

import asyncio
from pathlib import Path

from google.adk.apps import App
from google.adk.runners import InMemoryRunner

from meridian_dispute_vision.agent import root_agent
from meridian_ops.multimodal.parts import user_text_and_image

ROOT = Path(__file__).resolve().parents[1]
POD = ROOT / "fixtures" / "pod" / "pod_mc1048277_melt_support.png"
CLAIM = (
    "Order MC-1048277. The organic milk and other dairy arrived melted. "
    "Here is the delivery photo. I want a refund."
)


def _print_event(event) -> None:
    content = getattr(event, "content", None)
    if not content or not content.parts:
        return
    for part in content.parts:
        fc = getattr(part, "function_call", None)
        if fc:
            print("TOOL_CALL", fc.name, dict(fc.args or {}))
        fr = getattr(part, "function_response", None)
        if fr:
            print("TOOL_RESULT", fr.name, fr.response)
        text = getattr(part, "text", None)
        if text:
            print("TEXT", text)


async def main() -> None:
    app = App(name="meridian_dispute_vision", root_agent=root_agent)
    runner = InMemoryRunner(app=app)
    session = await runner.session_service.create_session(
        app_name="meridian_dispute_vision",
        user_id="maya",
    )
    msg = user_text_and_image(CLAIM, POD)
    async for event in runner.run_async(
        user_id="maya", session_id=session.id, new_message=msg
    ):
        _print_event(event)


if __name__ == "__main__":
    asyncio.run(main())
```

```bash
python -m meridian_ops.multimodal.run_pod_melt
```

### Expect — melted dairy **phrasing**

The final `TEXT` should read like an investigator, not a cashier who already hit refund.

**Must say (facts, not poetry):**

| Fact | Where it comes from |
|------|---------------------|
| Order `MC-1048277` | User text + OMS |
| Porch / house **502** (matches OMS) | **Image** + OMS `shipping_address_house_number` |
| Warped dairy crate / melted residue | **Image** (poster lines) |
| `damage_report` melted dairy, total **$214.55** | OMS via `get_order` |
| `POL-REFUND-04` | `retrieve_policy` |
| Full-order / over **$75** needs a supervisor | Policy + Lesson 04 HITL line |
| Evidence grade **strong** for damage (not contradictory on the house number) | Comparison step |

**Must not say:**

| Forbidden line | Why |
|----------------|-----|
| “I have refunded $214.55” | No settle tool; money has not moved |
| “Auto-approved” / `approve_auto` | Amount over $75 + food safety / full-order |
| House **118** | That number is on the **other** PNG |
| “Bags: NONE” as if this were the mismatch ticket | Wrong fixture |

A good shape:

```
Empathy: sorry the dairy arrived unsafe.
Facts: OMS MC-1048277 delivered, $214.55, melted_dairy; photo shows porch 502
       and a warped crate with melt residue (matches address).
Policy: POL-REFUND-04 — HITL for full-order over $75.
Next: escalate to Priya (HITL). No refund has been completed.
```

2. Add the structured decision agent. Create `project/meridian_dispute_vision/decision_agent.py`:

```python
from typing import Literal

from google.adk.agents.llm_agent import Agent
from pydantic import BaseModel, Field


class DisputeDecision(BaseModel):
    evidence_grade: Literal["strong", "weak", "contradictory"]
    decision: Literal["approve_auto", "escalate_hitl", "deny", "need_more_info"]
    refund_usd: float = Field(ge=0)
    policy_ids: list[str]
    customer_summary: str
    supervisor_reason: str


decision_agent = Agent(
    name="meridian_dispute_decision",
    model="gemini-3.5-flash",
    description="Fills DisputeDecision from a packed evidence brief. No tools.",
    instruction="""
Fill DisputeDecision from the brief only.
- escalate_hitl when refund_usd >= 75, evidence is contradictory, or food-safety melt.
- approve_auto only for small, strong, in-policy amounts under $75.
- Cite only policy ids present in the brief. Never invent POL-* ids.
- Never claim money already moved.
""".strip(),
    output_schema=DisputeDecision,
    output_key="dispute_decision",
)
```

   Walk `DisputeDecision` — this is Priya’s form:

   | Field | What the screen shows |
   |-------|------------------------|
   | `evidence_grade` | strong / weak / contradictory |
   | `decision` | Which button is lit |
   | `refund_usd` | Amount; `ge=0` |
   | `policy_ids` | Binder tabs you **provided** |
   | `customer_summary` | What to tell Maya |
   | `supervisor_reason` | Why Priya was pinged |

   Walk `Agent(...)`:

   | Keyword | Effect |
   |---------|--------|
   | `output_schema=DisputeDecision` | Final reply **must** match the Pydantic model (ADK 2.6.3) |
   | `output_key="dispute_decision"` | Validated object lands in `session.state["dispute_decision"]` |
   | no `tools=` | This node **decides**. Vision + OMS already gathered. |

   Same split as Lesson 20: gather vs decide. Least privilege is the import list.

3. Run the decision node on a **packed brief** (no image here — the vision notes are text now):

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
source .venv/bin/activate
export PYTHONPATH=project
python - <<'PY'
import asyncio
from google.adk.apps import App
from google.adk.runners import InMemoryRunner
from google.genai import types

from meridian_dispute_vision.decision_agent import decision_agent

BRIEF = """
OMS: MC-1048277 melted_dairy total 214.55 pod_photo_present=true house=502
Vision notes: porch number 502 visible; dairy crate warped; melted residue; not a house mismatch.
Policy: POL-REFUND-04 HITL over $75; full-order not auto.
Customer asks: refund impacted dairy / possible full order.
"""

async def main():
    app = App(name="meridian_dispute_decision", root_agent=decision_agent)
    runner = InMemoryRunner(app=app)
    session = await runner.session_service.create_session(
        app_name="meridian_dispute_decision", user_id="priya"
    )
    msg = types.Content(
        role="user",
        parts=[types.Part.from_text(text=BRIEF)],
    )
    async for event in runner.run_async(
        user_id="priya", session_id=session.id, new_message=msg
    ):
        pass
    decision = session.state.get("dispute_decision")
    print(decision)

asyncio.run(main())
PY
```

### Expect

`session.state["dispute_decision"]` is a `DisputeDecision` (or dict) with:

| Field | Lab value |
|-------|-----------|
| `decision` | `escalate_hitl` |
| `refund_usd` | `214.55` (or the impacted-dairy amount — **not** silent `0` with auto-approve) |
| `policy_ids` | includes `POL-REFUND-04` |
| `evidence_grade` | `strong` (house matches; melt cues present) |

Not `approve_auto` for $214.

> **Tip:** If you already have Lesson 20’s `RefundDecision`, you can map fields 1:1 (`decision`, `refund_usd`, `policy_ids`). `evidence_grade` is the extra vision field this lesson adds.

> **Watch out:** Putting `output_schema` on the **vision** agent that also has tools is a different, tighter setup. This lab keeps **tools on vision**, **schema on decide**. Two agents. Clear contracts.

### Scoreboard after Task 5

| Piece | In place? |
|-------|-----------|
| OMS house numbers + POD flags | Yes |
| Two synthetic PNGs | Yes |
| `user_text_and_image` helper | Yes |
| Vision agent | Yes |
| Mismatch run | Yes |
| Melt + structured decision | **Yes** |
| `adk web` | Not yet |
| Negative + audit note | Not yet |

---

## Task 6 — `adk web`: flags and the image clipboard

### Why

The script proves bytes. The UI is where you **watch** `get_order` / `retrieve_policy` next to the photo. `adk web` loads `app` from `meridian_dispute_vision/agent.py` when present.

### Do this

1. Stop any old server on 8000 (`Ctrl+C`). From **`project/`**:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme/project
source ../.venv/bin/activate
export PYTHONPATH=.
adk web --host 127.0.0.1 --port 8000 --no-reload --verbose
```

   Walk the flags:

   | Flag | Meaning |
   |------|---------|
   | `--host 127.0.0.1` | Bind **localhost only**. Dev UI, not a public API. |
   | `--port 8000` | Listen on 8000. Open `http://127.0.0.1:8000`. |
   | `--no-reload` | Do not restart uvicorn on every save. After you edit `agent.py`, stop and start so the instruction reloads. |
   | `--verbose` | DEBUG logs in **this** terminal — tool names, MIME problems, API errors. |

   Other flags you will see in this curriculum:

   | Flag | Meaning |
   |------|---------|
   | `--reload_agents` | Reload agent modules when files change. Useful while editing the dispute instruction. |
   | `-v` | Same as `--verbose`. |
   | `--extra_plugins ...` | Lesson 26 — attach a `BasePlugin`. This agent has no money tool; skip it today. |

   Run from `project/` so ADK lists `meridian_dispute_vision` as an app folder.

2. Open `http://127.0.0.1:8000`. Select **meridian_dispute_vision**.

3. In the composer, **attach** `project/meridian_ops/fixtures/pod/pod_mc1048277_melt_support.png` with the file / image control, then send:

```
Order MC-1048277. The organic milk and other dairy arrived melted. I want a refund.
```

   That user message is the same shape as Task 2: a **text** part plus an **image** part. You already proved that shape in pytest; here you watch tools in the UI.

4. Repeat with `pod_mc1048292_mismatch.png` and:

```
Order MC-1048292 says delivered but I got nothing. Nobody was home.
```

### Expect

Trace shows `get_order` **before** lifecycle claims. Melt chat matches Task 5 phrasing (502, warped crate, `POL-REFUND-04`, HITL, no “refund completed”). Mismatch chat calls out **118 vs 214** and escalates.

The terminal with `--verbose` is where failed image parts show up. If the UI sent only text, you will get a text-only answer — Task 7’s guard is for that case. Re-attach the PNG.

> **Tip:** `adk web` does not reliably pick up `agent.py` edits with `--no-reload`. Restart after instruction changes.

> **Watch out:** Do not expose `--host 0.0.0.0` on a shared network and call it production OrderOps.

### Scoreboard after Task 6

| Piece | In place? |
|-------|-----------|
| OMS house numbers + POD flags | Yes |
| Two synthetic PNGs | Yes |
| `user_text_and_image` helper | Yes |
| Vision agent | Yes |
| Mismatch run | Yes |
| Melt + structured decision | Yes |
| `adk web` | **Yes** |
| Negative + audit note | Not yet |

---

## Task 7 — Text-only guard + audit note

### Why

Multimodal systems fail by **overclaiming**. If Maya forgets the photo, the agent must not describe house **118** or a warped crate. Those details live in pixels you did not send.

### Do this

1. Create `project/meridian_ops/tests/test_vision_text_only.py`. This **does** call the model. It asserts the final text stays off the fixture posters.

```python
import asyncio

from google.adk.apps import App
from google.adk.runners import InMemoryRunner
from google.genai import types

from meridian_dispute_vision.agent import root_agent

BANNED = ("118", "warped", "melted residue", "Bags: NONE")


async def _run(text: str) -> str:
    app = App(name="meridian_dispute_vision", root_agent=root_agent)
    runner = InMemoryRunner(app=app)
    session = await runner.session_service.create_session(
        app_name="meridian_dispute_vision", user_id="maya"
    )
    msg = types.Content(
        role="user",
        parts=[types.Part.from_text(text=text)],
    )
    chunks: list[str] = []
    async for event in runner.run_async(
        user_id="maya", session_id=session.id, new_message=msg
    ):
        content = getattr(event, "content", None)
        if event.is_final_response() and content and content.parts:
            for part in content.parts:
                if part.text:
                    chunks.append(part.text)
    return "\n".join(chunks).lower()


def test_text_only_does_not_invent_poster_details():
    final = asyncio.run(
        _run("What's the status of order MC-1048292? I have no photo.")
    )
    assert final
    for needle in BANNED:
        assert needle.lower() not in final, final
```

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
source .venv/bin/activate
export PYTHONPATH=project
pytest project/meridian_ops/tests/test_vision_text_only.py project/meridian_ops/tests/test_multimodal_parts.py -v
```

   `-v` — verbose names. The text-only test needs `GOOGLE_API_KEY`.

### Expect

`test_text_only_does_not_invent_poster_details PASSED`. The agent may still call `get_order` and talk about **delivered** / Austin — those are OMS. It must not recite the mismatch poster.

2. Write `project/meridian_ops/decisions/21-pod-mismatch.md` from your Task 4 run:

```markdown
# Lesson 21 — POD mismatch trajectory

- Session / user: maya
- Image: pod_mc1048292_mismatch.png (synthetic)
- OMS: MC-1048292 delivered, pod_photo_present=true, house 214 Maple Ave
- Vision: visible house 118, bags none
- Evidence grade: contradictory
- Tools: get_order, retrieve_policy (yes/no)
- Decision: escalate_hitl / investigate — not closed as delivered, not auto-refund
```

   Fill the Tools line from the terminal. This is the Lesson 11 habit: a human can replay the story without re-running Gemini.

### Expect

The markdown file exists and names the **filename**, the **grade**, and the **decision**. Priya can read it without your laptop.

> **Tip:** Wrong order id in the text vs printed on the PNG: the agent looks up the **stated** `MC-…` in OMS. It does not silently switch orders because the poster header says otherwise. Call that out if you try it as a stretch.

> **Watch out:** `is_final_response()` is how you know the text is the answer, not a partial. Asserting on the first event will flake.

### Scoreboard after Task 7

| Piece | In place? |
|-------|-----------|
| OMS house numbers + POD flags | Yes |
| Two synthetic PNGs | Yes |
| `user_text_and_image` helper | Yes |
| Vision agent | Yes |
| Mismatch run | Yes |
| Melt + structured decision | Yes |
| `adk web` | Yes |
| Negative + audit note | **Yes** |

---

## How it works (deeper dive)

```
Pixels  →  soft evidence (what might be true)
Tools   →  hard facts (what OMS / policy record)
Schema  →  machine decision (Priya’s form)
```

SME rule: when soft and hard **contradict**, escalate. Do not average them into a refund.

`gemini-3.5-flash` turns `Part.inline_data` into that soft evidence **inside ADK**. Your job is the clipboard (`Content` / `Part`) and the belt (`get_order`, `retrieve_policy`). Not a side vision microservice.

Production photos: store the carrier object in GCS, pass `Part.from_uri(file_uri="gs://...")`. The lab cannot see your bucket, so the lab uses `from_bytes`.

---

## Common pitfalls / troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Model ignores image | Empty bytes, wrong MIME, filename only in text | `P1_MIME` print; `from_bytes`; `image/png` |
| Invents bags on the empty poster | Weak instruction | Step 3 in the instruction; Task 7 test |
| Refunds from vibes | Skipped `retrieve_policy` / no HITL language | Tools list + procedure; schema agent |
| `approve_auto` on $214 | Decision agent got a thin brief | Include amount + `POL-REFUND-04` + $75 line |
| Real PII photos in git | Copied a driver image | Synthetic posters only |
| `ModuleNotFoundError: meridian_ops` | `PYTHONPATH` unset | Repo root: `export PYTHONPATH=project` |
| `adk web` missing the app | Ran from repo root, not `project/` | `cd project` then `adk web --port 8000` |
| Text-only test sees `118` | Model hallucinated the other lab ticket | Tighten instruction step 3; re-run |
| `from_text("hi")` TypeError | Missing `text=` keyword | `from_text(text="hi")` |

---

## You are done when

- [ ] Two synthetic POD fixtures exist and README says lab-only  
- [ ] OMS rows have house **214** vs **502** and POD flags  
- [ ] `user_text_and_image` tests: two parts, inline bytes, URI helper has no inline blob  
- [ ] Mismatch run: 118 vs 214, contradictory, HITL — not “delivered, closed”  
- [ ] Melt run: 502, warped crate, `$214.55`, `POL-REFUND-04`, HITL — not “I refunded”  
- [ ] `DisputeDecision` in session state is `escalate_hitl` for the melt brief  
- [ ] `adk web --host 127.0.0.1 --port 8000 --verbose` on **meridian_dispute_vision**  
- [ ] Text-only test does not recite poster lines; `21-pod-mismatch.md` written  

---

## Knowledge check

Answer from this lab, not from general LLM lore.

1. What object carries both the claim and the POD image into `run_async`?  
2. Why `Part.from_bytes` in this lab, and when would you use `Part.from_uri` instead?  
3. Why call `get_order` even when a POD image is attached?  
4. For the melted dairy photo, name three facts the final answer must include and two phrases it must not.  
5. What should happen when POD house **118** contradicts OMS **214**?  
6. Are synthetic lab POD images OK to commit? Real customer PODs?

### Answers

1. `types.Content(role="user", parts=[Part.from_text(...), Part.from_bytes(...)])`.  
2. Lab files are local — `from_bytes` fills `inline_data`. Production carrier objects in GCS — `from_uri` fills `file_data.file_uri`.  
3. Image is soft evidence. OMS is the system of record for lifecycle, amount, address, POD flags.  
4. Must: porch 502 / match, warped crate or melt residue, $214.55 + `POL-REFUND-04` + HITL. Must not: “I refunded”, “auto-approved”, house 118.  
5. Evidence grade **contradictory**; escalate HITL / investigate — do not auto-close as delivered and do not auto-refund large amounts.  
6. Synthetic labeled posters: yes. Real customer PODs: no.

---

## Recap

- You attached real image `Part`s to native ADK runs (`from_bytes` in lab; `from_uri` ready for GCS).  
- You combined **vision + OMS + policy**, then a schema node for Priya’s form.  
- You treated contradictions as escalations, not coin flips — and you banned porch hallucinations when no image shipped.

---

## Stretch goal

Add a third fixture: a **receipt crop** with SKU `884210` and a melt stain. Teach the vision agent to list **line-level** refund candidates before any full-order sentence. Keep `request_refund` off the tool list.

---

## Feedback

- Could you explain soft vs hard evidence with the 118 vs 214 porch, from memory?  
- Note the task number plus what you expected vs what happened.

---

## Navigate

**← Prev** [Lesson 20 — Model routing & structured output](20-model-routing-fallbacks-structured-output.md)  
**Track home:** [README](../README.md)  
**Next:** [Lesson 22 — Streaming UX & progressive responses](22-streaming-ux-progressive-responses.md)

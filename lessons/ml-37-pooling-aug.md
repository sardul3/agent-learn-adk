# ml-37 — Pooling and tiny augmentation

**Level:** Absolute beginner  
**Time:** ~45 minutes  
**Prerequisites:** ml-36; venv from **ml-00**  
**Lab outcome:** You reshape a 16×16 carton into **8×2×8×2**, take **max**, and get an **8×8** photo where the dent still shows

---

## At a glance

**Max pooling** means: split the picture into 2×2 tiles and keep **only the largest** number in each tile. Fewer pixels. The big dark dent can **survive** if a whole tile still lives inside it.

By the end you can explain, without hand-waving:

- `reshape(8, 2, 8, 2).max(axis=(1, 3))` in warehouse English
- why 16×16 becomes 8×8
- why `_box`’s grain is already a tiny **augmentation** (same carton, different speckles)

You will run `lab_pool` and walk one numpy line.

---

## Why this matters

Maya’s camera is 12 megapixels. The refund model does not need all of them. Pooling is a blunt “keep the loudest pixel in this neighborhood.” CNNs pool after stamps (ml-36) so a dent that **shifted two pixels** still fires the same detector.

If you skip the reshape, “8×8 max-pool” is a caption, not a skill.

```
16×16  →  8 groups of 2 rows  ×  8 groups of 2 cols  →  8×8 maxima
```

---

## Concept primer

| Word | Plain English | In Maya’s warehouse |
| --- | --- | --- |
| **Pool** | Shrink a grid by summarizing tiles | 16×16 → 8×8 |
| **Max-pool** | Summary = **largest** number in the tile | Brightest of each 2×2 |
| **Stride 2** | Tiles do not overlap; jump by 2 | `reshape` into pairs |
| **Augmentation** | Fake extra photos by small changes | Grain in `_box` (`normal(0, 0.03)`) |
| **Translation** | The object slid a little | A 2-pixel slide can stay in the same pool tile |

The one-liner:

```python
pooled = img.reshape(8, 2, 8, 2).max(axis=(1, 3))
```

Walk the axes:

| Axis after reshape | Length | Meaning |
| --- | --- | --- |
| 0 | 8 | which **pair of rows** (0–1, 2–3, …) |
| 1 | 2 | the two rows **inside** that pair |
| 2 | 8 | which **pair of columns** |
| 3 | 2 | the two columns **inside** that pair |

`.max(axis=(1, 3))` = take the max **inside** each 2×2, drop those two axes → shape **(8, 8)**.

> **Tip:** 16/2 = 8. If you ever pool 2×2 on a 15×15, you cannot reshape like this. This lab is even on purpose.

> **Watch out:** Max keeps the **largest** brightness. The dent is **dark** (small numbers). It survives when a 2×2 is **still inside the dent** so the max is still ~0.25, not a neighboring 0.6 face pixel. A **one-pixel** dent could vanish. Maya’s painted dent is 5×6 — fat enough.

---

## Setup

Reuse the **ml-00** venv.

### Step 1 — Enter the playground

Why now: `_box` and matplotlib live here.

```bash
cd project/ml_playground
source .venv/bin/activate
```

- `cd` means “change directory.”
- `source` runs activate in this shell.

**It worked when** `(.venv)` shows and:

```bash
python --version
python -c "import numpy, sklearn; print(numpy.__version__, sklearn.__version__)"
```

```text
Python 3.14.6
2.5.2 1.9.0
```

Close the plot window when you are done staring.

Headless machines:

```bash
export ML_HEADLESS=1
```

- `export` sets the variable for this session.
- `ML_HEADLESS=1` skips the window. You will still **compute** `pooled`; you just will not see it. Use a laptop.

---

## Hands-on

### Step 2 — Run the pool lab

Why this command now: the lesson is a **before/after**. Left 16×16, right 8×8. Skipping the plot skips the dent-survives claim.

```bash
python later_labs.py pool
```

- `pool` is a positional lab name, not `--pool`.

**It worked when** a two-panel window opens:

- left title **`16x16`** — `_box(True, 2)` (dented, seed **2**)
- right title **`ml-37: 8x8 max-pool (keeps the dent, fewer numbers)`**

The right carton is blockier. The **dark patch is still there**, lower resolution. That is “the dent survives.”

No numeric stdout. The picture is the result.

- [ ] Right panel is visibly coarser
- [ ] You can still point at the smash on the 8×8

### Step 3 — Walk `lab_pool`

Open `later_labs.py`. Find `lab_pool`.

1. `img = _box(True, 2)` — same painter as ml-35; seed **2** so grain differs from pixels (0) and conv (1).
2. `pooled = img.reshape(8, 2, 8, 2).max(axis=(1, 3))` — the whole model today.
3. Two `imshow`s, both `cmap="gray"`. Left original, right pooled.

`reshape` does **not** copy a new photo from a camera. It **re-views** the same 256 numbers as 8×2×8×2. Then max collapses each tile.

> **Tip:** Print `img.size` and `8*2*8*2` in your head: both 256. If reshape sizes multiplied to something else, numpy would throw.

> **Watch out:** This is **not** the 3×3 stamp from ml-36. Pooling does not look for edges. It only downsizes. Real nets usually **stamp then pool**.

### Step 4 — Prove the 8×8 and the grain-as-aug

Why now: shapes belong in the terminal, not only in a caption.

```bash
python -c "
from later_labs import _box
img = _box(True, 2)
pooled = img.reshape(8, 2, 8, 2).max(axis=(1, 3))
print('img', img.shape, 'pooled', pooled.shape)
a = _box(True, 2)
b = _box(True, 3)
print('same dent paint, different grain (not equal)', (a == b).all())
print('pooled min/max', pooled.min(), pooled.max())
"
```

- `-c` means “run this code string and exit.”

**Expect:**

```text
img (16, 16) pooled (8, 8)
same dent paint, different grain (not equal) False
pooled min/max 0.2650638091122584 0.9353693522352857
```

Walk that:

- Shape **(8, 8)** — 64 numbers instead of 256
- `_box(..., 2)` vs `_box(..., 3)` — **same rectangles**, different `seed` → different grain. That is tiny **augmentation**: extra photos of the same smash without a new camera
- pooled min ≈ **0.265** — still in dent-dark territory (max-of-tile cannot be darker than the darkest original pixel in that tile, but can be brighter than the dent mean)

- [ ] `pooled.shape` is `(8, 8)`
- [ ] Two seeds are not equal arrays (`False`)

---

## How it works (deeper)

**Augmentation** in production is crop, flip, brightness jitter. This playground’s jitter is already inside `_box`: `rng.normal(0, 0.03)`. ml-38 will train on 40 photos that are exactly “even index = no dent, odd = dent,” each with its **own seed** `i`. That grain is why the 40 rows are not 20 identical pairs.

Max vs mean vs min:

- **max** — keep the brightest; dark dents need to be **wide**
- **mean** — blur
- **min** — keep the darkest; would *favor* dents in this grayscale

The lab uses max because that is the default story in CNN slides. Stay honest about darkness.

After pooling, a linear model (ml-38) has 64 numbers instead of 256 if you pooled first. This lab only **shows** the 8×8. `lab_dented` still trains on flattened **16×16**. You will notice that on purpose.

---

## Common pitfalls

1. **Plot never opens.** `unset ML_HEADLESS` on a laptop.
2. **`ModuleNotFoundError`.** Activate `.venv` from `project/ml_playground`.
3. **`cannot reshape array`.** You changed 16 to another size and left `reshape(8, 2, 8, 2)`. Put 16 back, or change 8s to match.
4. **You said pooling “detects dents.”** It shrinks. The dent is already in the pixels.
5. **You thought seed 2 was “two dents.”** Seed is grain. `True` is the dent switch.

---

## Knowledge check

Answer from the function and the `-c` output.

1. What one numpy line turns `img` into `pooled`?
2. What are the shapes of `img` and `pooled`?
3. Why does the plot title say the dent is kept?
4. How is `_box` noise a tiny augmentation?
5. Which seed does `lab_pool` pass to `_box`?

<details>
<summary>Answers</summary>

1. `img.reshape(8, 2, 8, 2).max(axis=(1, 3))`
2. `(16, 16)` and `(8, 8)`
3. The painted dent is large enough that some 2×2 tiles stay dark, so the 8×8 still shows a blotch.
4. Different `seed` values add different grain to the same rectangles — extra fake photos of the same carton.
5. Seed `2` (`_box(True, 2)`).

</details>

---

## Recap

- **You pooled** 2×2 max tiles to 8×8 and still saw the smash.
- **You understand** reshape-then-max, and grain as a baby aug.
- **Next** you will train a **linear** recipe on 40 synthetic photos and get acc **1.0** — then refuse to brag.

Next: `ml-38-dented-box`

---

## Stretch goal

In `lab_pool`, change `reshape(8, 2, 8, 2)` to **`reshape(4, 4, 4, 4)`** and `max(axis=(1, 3))` still. That is 4×4 tiles → **4×4** output. Save. Rerun:

```bash
python later_labs.py pool
```

- **Expect:** the right panel is even blockier (4×4). The dent may still show as a couple of dark cells — or start to merge. Title still says 8×8 until you edit that string too (optional).
- Put **`(8, 2, 8, 2)`** back when you are done.

---

## Feedback

Could you redo this lab from memory? Note the **lesson id** (`ml-37`), the **step number**, what you **expected**, and what you **saw** (traceback or plot).

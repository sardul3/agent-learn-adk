# ml-36 — Convolution as a stamp

**Level:** Absolute beginner  
**Time:** ~50 minutes  
**Prerequisites:** ml-35; venv from **ml-00**  
**Lab outcome:** You slide a **3×3** vertical Sobel-ish stamp across Maya’s carton with nested loops and get a **14×14** edge map

---

## At a glance

**Convolution** means: take a tiny stamp of numbers (a **kernel**), lay it on the photo, multiply overlapping cells, **add**, write that sum into an output grid, then **slide** one pixel and repeat.

By the end you can explain, without hand-waving:

- why the stamp is 3×3 and the output is 14×14
- what this particular stamp lights up (vertical edges)
- that `lab_conv` is two `for` loops, not a magic `Conv2d`

You will run the lab, look at box vs stamp, and walk the loops.

---

## Why this matters

Maya does not need 256 numbers to notice a smash. She needs **edges**: places brightness jumps. A dent is a dark patch with a rim. A stamp that asks “is the left of this 3×3 darker than the right?” draws that rim.

If you skip the nested loops, later “CNN” talk is just a brand name. Here you can point at `out[i, j] = np.sum(...)`.

```
16×16 photo  --3×3 stamp, slide-->  14×14 edge map
```

---

## Concept primer

| Word | Plain English | In Maya’s warehouse |
| --- | --- | --- |
| **Kernel / stamp / filter** | A small grid of weights you slide | The 3×3 `k` in the lab |
| **Convolution** | Slide, multiply, add, write, repeat | Nested `for i` / `for j` |
| **Valid** (this lab) | Only place the stamp where it **fits** | No padding; 16−3+1 = **14** |
| **Vertical edge** | Brightness changes **left ↔ right** | Carton side, dent rim |
| **Sobel-ish** | A classic edge stamp: negatives on the left, positives on the right | `k` below |
| **Feature map** | The output grid of stamp-scores | `out`, 14×14 |

The stamp, copied from the file:

```
-1  0  1
-2  0  2
-1  0  1
```

Left column negative, right column positive, middle zero. If the right is brighter than the left, the sum is **positive**. If the left is brighter, the sum is **negative**. Flat cardboard ≈ 0.

```
photo[i:i+3, j:j+3]  *  k   →  nine products →  one sum  →  out[i, j]
```

> **Tip:** “Convolution” in this lesson is **that sum**. You do not need the word *cross-correlation*. Numpy is multiplying the patch by `k` in place.

> **Watch out:** This stamp is **fixed**, not learned. A real CNN **nudges** the nine numbers using data (ml-38’s honesty: a stamp would be the real idea). Today you *see* one handmade stamp.

---

## Setup

Reuse the **ml-00** venv.

### Step 1 — Enter the playground

Why now: the photo comes from `_box` in this folder; the plot needs a display.

```bash
cd project/ml_playground
source .venv/bin/activate
```

- `cd` means “change directory.”
- `source` activates the venv in this shell.

**It worked when** `(.venv)` shows and:

```bash
python --version
python -c "import numpy, sklearn; print(numpy.__version__, sklearn.__version__)"
```

```text
Python 3.14.6
2.5.2 1.9.0
```

Close the matplotlib window to return to the prompt.

```bash
export ML_HEADLESS=1
```

only if you have no display. `-1` is not a CLI flag on Python; it is the **value** of the variable `ML_HEADLESS`. Prefer a laptop.

---

## Hands-on

### Step 2 — Run the conv lab

Why this command now: you need the **side-by-side** picture. Left = carton. Right = stamp scores. If you skip it, 14×14 is only arithmetic.

```bash
python later_labs.py conv
```

- `conv` is a positional lab name, not `--conv`.

**It worked when** a window opens with two panels:

- left title **`box`** — gray 16×16 from `_box(True, 1)` (dented, seed **1**, not the seed-0 photo from ml-35)
- right title **`ml-36: stamp (vertical edges)`** — 14×14 `coolwarm` map

There is **no stdout** besides a possible headless warning. The picture is the output.

On the right, look for **vertical** rims: the left and right sides of the carton, and the dent’s left/right. Horizontal rims are weaker on this stamp (it was built for left-vs-right).

- [ ] Two panels, not one
- [ ] Right panel looks “edgy,” not like a second photo of cardboard

### Step 3 — Walk `lab_conv`

Open `later_labs.py`. Find `lab_conv`.

1. `img = _box(True, 1)` — dented carton, grain seed **1**. Same painter as ml-35, different speckles.
2. `k = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=float)` — the 3×3 stamp. `dtype=float` so sums are not integers-only.
3. `out = np.zeros((14, 14))` — empty feature map. **14**, not 16.
4. Nested loops:
   - `for i in range(14):` — stamp’s **top** row can start at 0..13. Start 13 + 3 rows = 16. Fits.
   - `for j in range(14):` — stamp’s **left** column can start at 0..13.
   - `out[i, j] = np.sum(img[i : i + 3, j : j + 3] * k)` — take a 3×3 patch, multiply **cell-wise** by `k`, add all nine.
5. `subplots(1, 2)` — two axes. Left `imshow(img)`, right `imshow(out, cmap="coolwarm")`.

Why 14?

```
output_size = image_size - kernel_size + 1
14 = 16 - 3 + 1
```

No padding. The stamp never hangs off the photo.

> **Tip:** `img[i:i+3, j:j+3] * k` is **not** matrix multiply (`@`). It is times-each-cell, then `sum`. Nine products.

> **Watch out:** Seed is **1** here and **0** in `lab_pixels`. The dent is in the same painted place; the grain is different. Do not debug “the box moved.” It did not.

### Step 4 — Prove 14×14 in the interpreter

Why now: the plot does not print the shape. You should hear it from numpy.

```bash
python -c "
from later_labs import _box
import numpy as np
img = _box(True, 1)
k = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=float)
out = np.zeros((14, 14))
for i in range(14):
    for j in range(14):
        out[i, j] = np.sum(img[i:i+3, j:j+3] * k)
print('img', img.shape, 'k', k.shape, 'out', out.shape)
print('out min/max', out.min(), out.max())
"
```

- `-c` means “run this code string and exit.”

**Expect:**

```text
img (16, 16) k (3, 3) out (14, 14)
out min/max -1.5946106013950019 2.4662197020574155
```

Min/max are stamp **scores**, not 0…1 brightness. Coolwarm is allowed to go negative (left-brighter) and positive (right-brighter).

- [ ] `out` shape is `(14, 14)`
- [ ] You can say `16 - 3 + 1 = 14` out loud

---

## How it works (deeper)

A **horizontal** Sobel would flip the idea (negatives on top, positives on the bottom). This lab only ships the vertical one so you can finish in one picture.

A CNN layer is: many stamps (not one), plus a bias, plus a squash like ReLU (ml-27), stacked. You still understand the layer if you understand **one** stamp and **two** loops.

Padding (not in this file) would let the output stay 16×16 by pretending extra pixels exist around the rim. Skip it until you can explain 14.

ml-37 will **shrink** a photo without a stamp, by taking max of 2×2 tiles. Stamps find structure; pools throw resolution away on purpose.

---

## Common pitfalls

1. **Plot never opens.** Unset `ML_HEADLESS` on a laptop.
2. **`ModuleNotFoundError`.** `source .venv/bin/activate` in `project/ml_playground`.
3. **You expected stdout.** `lab_conv` only plots. Silence (plus a window) is success.
4. **You called `out` a photo.** Values go negative. It is an edge **score**.
5. **Off-by-one on 14.** Last start index is 13, not 14. `range(14)` is 0..13.

---

## Knowledge check

Answer from the code and the `-c` print.

1. What is the kernel `k` (nine numbers, three rows)?
2. What shape is `out`, and why not 16×16?
3. Which `_box` call does `lab_conv` use (dent? seed?)?
4. Are the nested loops using `@` (matrix multiply) or cell-wise `*` plus `sum`?
5. What kind of edge is this stamp built to light up?

<details>
<summary>Answers</summary>

1. `[[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]]`
2. `(14, 14)` because `16 - 3 + 1 = 14` (stamp must fit; no padding).
3. `_box(True, 1)` — dent on, seed 1.
4. Cell-wise `*` then `np.sum`.
5. Vertical (left vs right brightness).

</details>

---

## Recap

- **You slid** a 3×3 vertical stamp with two loops and got a 14×14 map.
- **You understand** convolution = patch × kernel → sum → slide.
- **Next** you shrink 16×16 to 8×8 with max-pool; the dent should still show.

Next: `ml-37-pooling-aug`

---

## Stretch goal

In `lab_conv`, change the kernel’s **middle-left** `-2` to **`0`** (weaker left emphasis). Save. Rerun:

```bash
python later_labs.py conv
```

- **Expect:** the right-hand edge map still exists but the contrast of vertical rims **changes**. Output is still 14×14.
- Put **`-2`** back when you are done so this lesson’s stamp matches the table above.

---

## Feedback

Could you redo this lab from memory? Note the **lesson id** (`ml-36`), the **step number**, what you **expected**, and what you **saw** (traceback or plot).

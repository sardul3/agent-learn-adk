# ml-35 — Pixels are just numbers

**Level:** Absolute beginner  
**Time:** ~45 minutes  
**Prerequisites:** ml-34; venv from **ml-00**  
**Lab outcome:** You print a dented carton as a **(16, 16)** grid whose min/max are about **0.179 / 0.942**, then walk `_box(True, 0)` layer by layer

---

## At a glance

A photo is not “a box.” It is a **table of brightness**. Each cell is a **pixel**: one number, here between 0 (black) and 1 (white).

By the end you can explain, without hand-waving:

- `shape (16, 16)` means 16 rows × 16 columns of brightness
- Maya’s carton is painted in three gray levels, then grain is added
- why `min` is not exactly 0.25 and `max` is not exactly 0.85 (noise + clip)

You will run `lab_pixels` and open `_box`. You will not train a vision net yet.

---

## Why this matters

A customer texts Maya a photo: “carton crushed.” Gemini can describe it in the ADK track. This CPU track needs you to **see the grid** first.

If you skip this lab, convolution (ml-36) looks like magic stamps. It is not. It is arithmetic on this same 16×16 table.

```
warehouse photo  →  numbers 0…1  →  later: stamps, pools, a linear guess
```

---

## Concept primer

| Word | Plain English | In Maya’s warehouse |
| --- | --- | --- |
| **Pixel** | One brightness number | One cell of the 16×16 carton |
| **Shape `(H, W)`** | Rows (height) then columns (width) | `(16, 16)` |
| **Grayscale** | One number per pixel, not three colors | `cmap="gray"` |
| **`vmin` / `vmax`** | Plot legend: 0 is black, 1 is white | So 0.25 looks dark, 0.85 looks light |
| **Noise** | Tiny random wiggle | Camera grain: `normal(0, 0.03)` |
| **`clip`** | Force numbers back into 0…1 | Grain cannot make “brighter than white” |
| **Dent** | A darker patch painted on the face | `0.25` in a rectangle |

How `_box` paints, in order:

```
1. whole grid = 0.85     (floor / cardboard background)
2. inner square = 0.6    (carton face)
3. if dent: patch = 0.25 (the smash)
4. add grain ±0.03
5. clip to [0, 1]
```

> **Tip:** Bigger number = brighter in this lab. The dent is **dark**, so it is a **small** number.

> **Watch out:** These are **fake** photos. `_box` draws rectangles. It is not ImageNet, not a camera file, not Gemini vision.

---

## Setup

Reuse the **ml-00** venv.

### Step 1 — Enter the playground

Why now: `later_labs.py` lives here, and matplotlib needs a display for the gray carton.

```bash
cd project/ml_playground
source .venv/bin/activate
```

- `cd` means “change directory.”
- `source` activates Python **3.14.6** from the venv.

**It worked when** `(.venv)` shows and:

```bash
python --version
python -c "import numpy, sklearn; print(numpy.__version__, sklearn.__version__)"
```

```text
Python 3.14.6
2.5.2 1.9.0
```

Labs call `plt.show()`. Close the window to get the terminal back.

No display?

```bash
export ML_HEADLESS=1
```

- `export` sets a session variable.
- `ML_HEADLESS=1` uses a non-window backend. **Stdout still prints** `shape` / `min/max`. Prefer a laptop so you *see* the dent.

---

## Hands-on

### Step 2 — Run the pixels lab

Why this command now: it prints the real min/max you will quote, and it shows the gray picture. If you skip it, “16×16” stays a slogan.

```bash
python later_labs.py pixels
```

- `pixels` is a positional lab name, not `--pixels`.

**It worked when** stdout is:

```text
shape (16, 16) min/max 0.17904088281169078 0.9419811021714669
```

and a window titled `ml-35: a dented box is just a grid of brightness` opens.

Read those numbers:

- **shape** `(16, 16)` — 256 pixels
- **min** ≈ **0.179** — darkest cell (dent + grain that went darker)
- **max** ≈ **0.942** — brightest cell (background 0.85 + grain that went lighter)

On the plot: a light frame, a mid-gray square, a **darker blotch** on the right-center of the face. That blotch is the dent.

- [ ] You copied min/max from **your** terminal, not from memory of this page
- [ ] You can point at the dark patch as “the smash”

### Step 3 — Walk `_box(True, 0)` then `lab_pixels`

Open `later_labs.py`. Find `_box`, then `lab_pixels`.

`_box(dent: bool, seed: int)` — helper used by pixels, conv, pool, dented, video, jam.

1. `rng = np.random.default_rng(seed)` — grain is **repeatable**. Seed `0` in this lab.
2. `img = np.ones((16, 16)) * 0.85` — start every pixel at **background 0.85**. `np.ones` means “a grid of 1s,” then scale.
3. `img[3:13, 3:13] = 0.6` — Python slices **exclude the end**. Rows 3..12 and cols 3..12 become the **carton face 0.6**. Ten-by-ten inner square.
4. `if dent: img[7:12, 8:14] = 0.25` — rows 7..11, cols 8..13 = **dent 0.25**. `lab_pixels` calls `_box(True, 0)`, so the dent is on.
5. `img += rng.normal(0, 0.03, img.shape)` — add grain: mean 0, spread 0.03, same 16×16 shape.
6. `return np.clip(img, 0, 1)` — any grain that pushed below 0 or above 1 is cut.

Then `lab_pixels`:

1. `img = _box(True, 0)` — dented, seed 0.
2. `print("shape", img.shape, "min/max", img.min(), img.max())` — the line you already saw.
3. `imshow(..., cmap="gray", vmin=0, vmax=1)` — lock the gray scale so 0.25 stays dark even if this photo’s max is 0.94.

> **Tip:** Slice `3:13` is a 10-long span (13−3). Slice `7:12` is 5 rows of dent. You can count on your fingers.

> **Watch out:** `min` is **not** 0.25. Grain pulled some dent pixels down to ≈0.179. `max` is **not** 0.85. Grain pulled some background up to ≈0.942. That is why the print looks “messy.” It is honest.

### Step 4 — Confirm the three gray levels

Why now: prove the paint order without guessing from the plot.

```bash
python -c "
from later_labs import _box
img = _box(True, 0)
print('shape', img.shape)
print('min', img.min(), 'max', img.max())
print('dent patch mean', img[7:12, 8:14].mean())
print('face sample mean', img[4:7, 4:7].mean())
print('corner mean', img[0:2, 0:2].mean())
"
```

- `-c` means “run this code string and exit.”
- `from later_labs import _box` loads the **same** helper the lab uses.

**Expect** (seed 0, numpy 2.5.2):

```text
shape (16, 16)
min 0.17904088281169078 max 0.9419811021714669
dent patch mean ≈ 0.255
face sample mean ≈ 0.599
corner mean ≈ 0.843
```

Means sit near **0.25 / 0.6 / 0.85**, wiggled by grain. Min/max match Step 2.

- [ ] Dent mean is near 0.25, not near 0.85
- [ ] Corners are the light background

---

## How it works (deeper)

A color photo would be shape `(16, 16, 3)` — red, green, blue. This lab is grayscale so you can *see* one channel.

Every later vision lab reuses `_box`:

- ml-36 stamps a 3×3 edge detector on this grid
- ml-37 max-pools it to 8×8
- ml-38 trains a linear recipe on 40 flattened copies
- ml-39 stacks eight copies in time

The computer never “sees cardboard.” It adds, clips, and plots. You could paint the same grid in a spreadsheet: 256 cells, three fill colors, a little random.

**Training** (ml-38) means: treat those 256 numbers as Maya treated **weight_kg** in ml-00 — inputs to a recipe. Same loop, bigger table.

---

## Common pitfalls

1. **Plot never opens.** `ML_HEADLESS=1` is set, or no display. On a laptop: `unset ML_HEADLESS` and rerun.
2. **`ModuleNotFoundError`.** Venv off. Redo Step 1.
3. **`cannot import later_labs`.** You ran `-c` from the wrong folder. `cd project/ml_playground` first.
4. **You called 0.179 “the dent value.”** The dent **paint** is 0.25. 0.179 is paint plus grain (and clip).
5. **You thought `3:13` includes row 13.** It does not. End index is excluded.

---

## Knowledge check

Answer from the print and `_box`, not from a vision blog.

1. What `shape` does `python later_labs.py pixels` print?
2. What min and max did you get (you may round to three decimals)?
3. In `_box`, what three gray levels are painted **before** noise, and in what order?
4. What do `rng.normal(0, 0.03, ...)` and `np.clip(img, 0, 1)` do?
5. Does `lab_pixels` call `_box(True, 0)` or `_box(False, 0)` — and what does that `True` mean?

<details>
<summary>Answers</summary>

1. `(16, 16)`
2. min ≈ `0.179`, max ≈ `0.942` (full values `0.17904088281169078` and `0.9419811021714669`).
3. Background `0.85`, then carton face `0.6`, then dent `0.25`.
4. Grain with spread 0.03; then force every pixel into 0…1.
5. `_box(True, 0)` — `True` paints the dent; `0` is the grain seed.

</details>

---

## Recap

- **You printed** a 16×16 brightness grid and opened the gray carton.
- **You understand** pixels = numbers; dent = darker rectangle plus grain.
- **Next** you slide a 3×3 **stamp** across that grid (convolution).

Next: `ml-36-convolution-stamp`

---

## Stretch goal

In `_box`, change the dent paint from **`0.25`** to **`0.05`** (almost black). Save. Rerun:

```bash
python later_labs.py pixels
```

- **Expect:** the blotch looks darker. `min` drops (still not exactly 0.05, because grain). `shape` stays `(16, 16)`.
- Put **`0.25`** back when you are done so ml-36’s pictures still match this track.

---

## Feedback

Could you redo this lab from memory? Note the **lesson id** (`ml-35`), the **step number**, what you **expected**, and what you **saw** (traceback or plot).

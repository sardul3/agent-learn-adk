# ml-38 — Linear classifier on a dented box

**Level:** Absolute beginner  
**Time:** ~50 minutes  
**Prerequisites:** ml-37; venv from **ml-00**  
**Lab outcome:** You train a logistic-style line on **40** flattened 16×16 photos and print **`linear-on-pixels acc 1.0`** — then say why that is **not** ImageNet

---

## At a glance

Maya’s “is it smashed?” recipe here is the same kind of mix as ml-14: **sigmoid of a weighted sum**, but the inputs are **256 pixels**, not `weight_kg`.

By the end you can explain, without hand-waving:

- how 40 fake photos and labels are built (`i % 2`)
- why accuracy **1.0** is honest for a **planted dark patch**
- why a **stamp** (ml-36) is the real CNN idea, which this lab does **not** use

You will run `lab_dented` and walk the training loop. No plot.

---

## Why this matters

A dashboard that says “damage model 100%” will ship. Then a real photo — tape, shadow, a logo — will fool it. This lab **gives you that 100%** on purpose so you feel how cheap it is.

The dent is a rectangle of 0.25 painted in a known place. A linear weight on those pixels can simply say “if those cells are dark, smashed.” That is a planted trick, not vision.

If you skip the honesty sentence in the print, you will quote 1.0 in a stand-up and Maya will believe you.

---

## Concept primer

| Word | Plain English | In Maya’s warehouse |
| --- | --- | --- |
| **Flatten** | Turn a 16×16 grid into a 256-long list | `.ravel()` |
| **Label `y`** | The truth for this photo | `0` intact, `1` dented |
| **Linear-on-pixels** | One weight per pixel, add, squash | No stamp, no pool |
| **Sigmoid** | Squash a mix into a 0…1 guess (ml-14) | `1 / (1 + exp(−Xw))` |
| **Accuracy** | Fraction of photos whose guess matches `y` | `1.0` = 40/40 |
| **Toy / planted** | You drew the answer into the pixels | Dark patch at a fixed place |

```
even i → no dent,  y = 0
odd  i → dent,     y = 1
40 photos, seeds 0..39, grain from seed i
```

> **Tip:** Acc 1.0 on this set means the recipe found the patch. It does **not** mean cameras in aisle C are solved.

> **Watch out:** Training and scoring use the **same** 40 photos. There is no held-out test (ml-06). 1.0 is an in-sample score on a planted pattern.

---

## Setup

Reuse the **ml-00** venv.

### Step 1 — Enter the playground

Why now: `_box` and numpy live in this folder.

```bash
cd project/ml_playground
source .venv/bin/activate
```

- `cd` means “change directory.”
- `source` activates Python 3.14.6.

**It worked when** `(.venv)` shows and:

```bash
python --version
python -c "import numpy, sklearn; print(numpy.__version__, sklearn.__version__)"
```

```text
Python 3.14.6
2.5.2 1.9.0
```

No `plt.show()` in this lab. If you only see a number, that is success.

---

## Hands-on

### Step 2 — Run the dented-box lab

Why this command now: the print is the whole exam. You need the exact accuracy string.

```bash
python later_labs.py dented
```

- `dented` is a positional lab name, not `--dented`.

**It worked when** you see:

```text
linear-on-pixels acc 1.0 (toy: dent is a dark patch — a stamp would be the real CNN idea)
```

Read it in two halves:

- **`acc 1.0`** — every one of the 40 synthetic photos was labeled right **after** 80 nudge steps
- **the parenthetical** — the authors refusing the trophy

- [ ] Accuracy printed as `1.0` (float, not the string “100%”)
- [ ] You read the toy warning out loud

### Step 3 — Walk `lab_dented`

Open `later_labs.py`. Find `lab_dented`.

1. `X = np.stack([_box(i % 2 == 1, i).ravel() for i in range(40)])`
   - `range(40)` — photos **0..39**
   - `i % 2 == 1` — **True** on odd `i` → dent on; even → intact
   - `i` as seed — grain matches the photo index (tiny aug from ml-37)
   - `.ravel()` — 16×16 → 256
   - `np.stack` — table `X` shape **(40, 256)**
2. `y = np.array([i % 2 for i in range(40)])` — labels 0,1,0,1,… so **y matches the dent switch**
3. `w = np.zeros(X.shape[1])` — 256 weights, start at 0. No bias term in this lab.
4. Loop `for _ in range(80):` — eighty nudges
   - `pred = 1 / (1 + np.exp(-(X @ w)))` — sigmoid guess per photo (vector of 40)
   - `w -= 0.4 * X.T @ (pred - y) / len(y)` — one gradient step on mean error of those guesses
     - `0.4` is the **step size** (learning rate)
     - `(pred - y)` is guess minus truth
     - `X.T @ ...` mixes which pixels were to blame
     - `/ len(y)` averages over 40 photos
5. `acc = ((X @ w > 0).astype(int) == y).mean()`
   - `X @ w > 0` — same mix as the sigmoid’s inside; positive mix → class 1
   - compare to `y`, take the mean → accuracy
6. `print("linear-on-pixels acc", acc, "(toy: ...")` — the line you saw

> **Tip:** `X @ w > 0` is the 0.5 threshold on the sigmoid in disguise: sigmoid(z) > 0.5 when z > 0.

> **Watch out:** The recipe can “cheat” by putting large **negative** weights on the dent rectangle (dark × negative = positive evidence for class 1). That is not understanding crush physics. That is noticing the paint.

### Step 4 — Confirm the table shapes

Why now: 40 and 256 should not be rumors.

```bash
python -c "
from later_labs import _box
import numpy as np
X = np.stack([_box(i % 2 == 1, i).ravel() for i in range(40)])
y = np.array([i % 2 for i in range(40)])
print('X', X.shape, 'y', y[:8], 'dents', int(y.sum()))
"
```

- `-c` means “run this code string and exit.”

**Expect:**

```text
X (40, 256) y [0 1 0 1 0 1 0 1] dents 20
```

Twenty smashed, twenty intact, alternating. Perfect balance. Another reason 1.0 is easy (ml-18’s imbalance is **not** here).

- [ ] Shape `(40, 256)`
- [ ] Twenty dents

### Step 5 — Where the cheat lives on the grid

Why now: 1.0 is more convincing if you can **point at the dent cells** in the 16×16 layout.

Flatten is row-major: pixel `(r, c)` is index `r * 16 + c`. The dent paint is `img[7:12, 8:14]` — rows 7–11, cols 8–13.

```bash
python -c "
idxs = [r * 16 + c for r in range(7, 12) for c in range(8, 14)]
print('n dent cells', len(idxs))
print('first/last index', idxs[0], idxs[-1])
"
```

**Expect:** `n dent cells 30` (5×6), `first/last index 120 189`. Thirty of 256 weights can soak up the smash. The other 226 mostly see background/face plus grain. That is why a **moved** dent (a real camera) would break this recipe, and why the print mentions a **stamp**.

- [ ] 30 dent cells, not 256
- [ ] You can say “index = row*16 + col”

---

## How it works (deeper)

This is logistic regression (ml-14) with 256 features. No hidden layer. No convolution.

A CNN would:

1. slide stamps (ml-36) so a dent that **moved** still matches a pattern
2. pool (ml-37) so a 2-pixel slide is the same tile
3. then a small linear head

Here the dent **barely moves**. Grain wiggles values, not geometry. A per-pixel weight is enough. Acc 1.0 is the lab telling you “your linear net can memorize a sticker.”

When you read papers with 99% on a famous dataset, ask: is the tell as painted as this patch? If yes, you are back in `lab_dented`.

---

## Common pitfalls

1. **`ModuleNotFoundError`.** Venv off. `source .venv/bin/activate`.
2. **Wrong folder.** `cd project/ml_playground`.
3. **You quoted 1.0 as production-ready.** The print’s parenthetical is part of the answer.
4. **You thought 80 was 80 photos.** It is **80 training steps** on the same 40 rows.
5. **Overflow warnings** if you later crank `0.4` way up. Put it back; the stock lab is stable on numpy 2.5.2.

---

## Knowledge check

Answer from the stdout and the loop.

1. What accuracy does `python later_labs.py dented` print?
2. How many photos, and how is `y` assigned?
3. What is the shape of `X` after stacking flattened boxes?
4. Does this lab use the 3×3 stamp from ml-36?
5. Why is 1.0 still not “we solved photos”?
6. How many painted dent cells are there, and what is the flat index of pixel `(r, c)`?

<details>
<summary>Answers</summary>

1. `1.0`
2. 40 photos; `y = i % 2` (odd index = dented = 1).
3. `(40, 256)`
4. No. Linear weights on raw pixels. The print even says a stamp would be the real CNN idea.
5. The dent is a planted dark rectangle in a known place, scored on the same 40 fakes you trained on — not a held-out real camera set.
6. 30 cells (rows 7–11 × cols 8–13). Index `r * 16 + c` (first 120, last 189).

</details>

---

## Recap

- **You trained** a 256-weight logistic on 40 synthetic cartons and got acc 1.0.
- **You understand** planted pixels make 100% cheap; CNNs exist to find **patterns that move**.
- **Next** a “video” is just **several** of these grids in time.

Next: `ml-39-video-is-frames`

---

## Stretch goal

In `lab_dented`, change the training loop from **`80`** steps to **`5`**. Save. Rerun:

```bash
python later_labs.py dented
```

- **Expect:** `acc` may drop below `1.0` (not enough nudges to separate the patch). Or it may still hit 1.0 — the patch is loud. Either way you **saw the number move or refuse to move**.
- Put **`80`** back when you are done so this lesson’s `1.0` still matches.

---

## Feedback

Could you redo this lab from memory? Note the **lesson id** (`ml-38`), the **step number**, what you **expected**, and what you **saw** (traceback or printout).

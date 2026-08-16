# ml-41 — Conveyor jam from frame change

**Level:** Absolute beginner  
**Time:** ~45 minutes  
**Prerequisites:** ml-40; venv from **ml-00**  
**Lab outcome:** You print **moving 0.0506** vs **jammed 0.0** and explain how `np.roll` fakes motion while a jam **repeats the same box**

---

## At a glance

Maya’s rule tonight: if the picture **barely changes** from frame to frame, the chute is **jammed**. If pixels keep sliding, product is moving.

By the end you can explain, without hand-waving:

- `np.roll` as “slide the carton sideways” (fake conveyor)
- why jammed mean-change is **exactly 0.0** (same `_box` every time)
- why moving prints **0.0506** (mean absolute frame-to-frame diff)

You will run `lab_jam` and walk both stacks.

---

## Why this matters

A jammed chute at 2 a.m. does not send a ticket. It sends **silence**: the same cardboard in the same pixels. Maya needs a number for “silence.”

ml-39 gave you frames. ml-40 said you only keep a handful. This lab uses **12** stills and one average.

```
moving:  box slides 0,1,2,… pixels  →  change ≈ 0.0506
jammed:  box copied 12 times        →  change = 0.0
```

If you skip the `np.roll` line, “motion” stays a movie word.

---

## Concept primer

| Word | Plain English | In Maya’s warehouse |
| --- | --- | --- |
| **`np.roll`** | Rotate a grid: pixels that fall off one edge re-enter the other | Fake belt motion |
| **`axis=1`** | Roll along **columns** (left/right) | Carton slides sideways |
| **`np.diff(..., axis=0)`** | Subtract consecutive frames | Frame 1 − frame 0, … |
| **Mean abs change** | Average of \|diff\| over pixels and time | The two printed scores |
| **Jam rule** | If that score is tiny, stop the belt | `jammed` prints `0.0` |

```
roll by t=0  →  original
roll by t=1  →  everything shifted 1 column
roll by t=2  →  shifted 2 columns
…
```

> **Tip:** Wrapping around (pixels that leave the right edge appear on the left) is a toy. Real cameras do not wrap. It is enough to make **nonzero** diffs.

> **Watch out:** Jammed uses `_box(False, 0)` **twelve times**. Same seed → **identical** grain. Diff is zeros. If you accidentally used seed `t`, jammed would no longer be 0.0.

---

## Setup

Reuse the **ml-00** venv.

### Step 1 — Enter the playground

Why now: `_box` and numpy must import from this folder.

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

No plot. Numbers only.

---

## Hands-on

### Step 2 — Run the jam lab

Why this command now: 0.0506 and 0.0 are frozen with numpy 2.5.2 and seed 0 inside `_box`. If you skip the run, you will round them wrong.

```bash
python later_labs.py jam
```

- `jam` is a positional lab name, not `--jam`.

**It worked when** you see:

```text
mean frame-to-frame change  moving 0.0506 jammed 0.0
Rule: if change is tiny, Maya's chute is jammed.
```

Read it as a detector:

- **moving 0.0506** — something changed (the roll)
- **jammed 0.0** — nothing changed
- **Rule** — Maya’s if-statement in English

`0.0506` is `round(motion_m, 4)`. `0.0` is `round(0.0, 4)`.

- [ ] Moving is **0.0506**, not 0
- [ ] Jammed is **0.0**

### Step 3 — Walk `lab_jam`

Open `later_labs.py`. Find `lab_jam`.

1. `rng = np.random.default_rng(0)` — **unused** in the rest of the function. The grain comes from `_box(..., 0)`. Do not hunt for `rng` in the stacks.
2. `moving = np.stack([np.roll(_box(False, 0), t, axis=1) for t in range(12)])`
   - 12 frames, `t = 0..11`
   - **same** photo `_box(False, 0)` every time, then **roll columns by t**
   - `np.stack` → shape **(12, 16, 16)** — that is `(T, H, W)` from ml-39
3. `jammed = np.stack([_box(False, 0) for _ in range(12)])`
   - 12 **identical** photos. `_` means “we do not use the index”
   - no `roll`
4. `motion_m = np.mean(np.abs(np.diff(moving, axis=0)))`
   - `axis=0` is **time**
   - `diff` makes 11 gaps from 12 frames
   - `abs` so left-slide and right-slide both count
   - `mean` over all those numbers
5. `motion_j` — same formula on `jammed` → **0**
6. `print(..., round(motion_m, 4), ..., round(motion_j, 4))`
7. Print Maya’s rule

> **Tip:** `np.roll(a, t, axis=1)` — `t` is **how many** slots to shift, `axis=1` is **which direction** (width). Not a CLI flag.

> **Watch out:** `np.diff` on axis 0 **shortens** time by 1. You do not compare 12 diffs. You compare 11. The mean still uses every leftover cell.

### Step 4 — Confirm shapes and the zero

Why now: see `(12, 16, 16)` and prove jammed uniqueness.

```bash
python -c "
from later_labs import _box
import numpy as np
moving = np.stack([np.roll(_box(False, 0), t, axis=1) for t in range(12)])
jammed = np.stack([_box(False, 0) for _ in range(12)])
print('moving', moving.shape, 'jammed', jammed.shape)
print('jammed all equal', np.allclose(jammed[0], jammed[1]))
print('moving[0] vs [1] equal', np.allclose(moving[0], moving[1]))
print('scores', round(float(np.mean(np.abs(np.diff(moving, axis=0)))), 4),
      round(float(np.mean(np.abs(np.diff(jammed, axis=0)))), 4))
"
```

- `-c` means “run this code string and exit.”
- `np.allclose` is “equal within a tiny numeric slop.”

**Expect:**

```text
moving (12, 16, 16) jammed (12, 16, 16)
jammed all equal True
moving[0] vs [1] equal False
scores 0.0506 0.0
```

- [ ] Both stacks are `(12, 16, 16)`
- [ ] Jammed frames match; moving neighbors do not

---

## How it works (deeper)

This detector is **not** a neural net. It is:

```
if mean(|frame[t+1] − frame[t]|) is tiny:
    chute jammed
```

Failure modes (honest):

- camera noise on a still scene → change **not** 0 (this lab’s jam is noiseless because the array is copied)
- a box that **rotates in place** might still change a lot
- lighting creep (ml-39) would add change even if the belt stopped

Production would subtract a noise floor, or compare to Maya’s “empty chute” template. You now own the **skeleton**.

`rng` sitting unused is a leftover. Do not invent a story that it shuffles the jam. Read the stacks.

---

## Common pitfalls

1. **`ModuleNotFoundError`.** Activate `.venv` in `project/ml_playground`.
2. **You expected a video window.** `lab_jam` only prints.
3. **You rolled `axis=0`.** That would shift **rows** (up/down), not the belt’s left-right toy.
4. **You used a new seed per jammed frame.** Then jammed ≠ 0.0. The real lab does not.
5. **You treated 0.0506 as a probability.** It is mean absolute pixel change, rounded to 4 decimals.

---

## Knowledge check

Answer from the stdout and the stacks.

1. What two scores does `python later_labs.py jam` print for moving and jammed?
2. What does `np.roll(..., t, axis=1)` do to `_box(False, 0)`?
3. Why is jammed change exactly 0.0?
4. What shape is `moving` after `np.stack`?
5. State Maya’s rule in the lab’s words.

<details>
<summary>Answers</summary>

1. moving `0.0506`, jammed `0.0`
2. Shifts the intact carton `t` pixels along columns (sideways wrap).
3. Every jammed frame is the same `_box(False, 0)` with no roll, so diffs are zero.
4. `(12, 16, 16)`
5. `Rule: if change is tiny, Maya's chute is jammed.`

</details>

---

## Recap

- **You measured** 0.0506 vs 0.0 on 12-frame stacks.
- **You understand** roll fakes motion; a jam is a copied still.
- **Next** tokens look at each other: a 4×4 **attention** table.

Next: `ml-42-attention-who`

---

## Stretch goal

In `lab_jam`, change `range(12)` to **`range(6)`** in **both** stacks (moving and jammed). Save. Rerun:

```bash
python later_labs.py jam
```

- **Expect:** jammed stays **`0.0`**. Moving stays near **`0.0506`** (same 1-pixel roll between neighbors; fewer gaps, similar mean). You confirmed the score is about **step size**, not “must be 12.”
- Put **`12`** back in both list comprehensions when you are done.

---

## Feedback

Could you redo this lab from memory? Note the **lesson id** (`ml-41`), the **step number**, what you **expected**, and what you **saw** (traceback or plot).

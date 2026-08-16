# ml-39 — Video is frames in time

**Level:** Absolute beginner  
**Time:** ~40 minutes  
**Prerequisites:** ml-38; venv from **ml-00**  
**Lab outcome:** You open **8** stills of Maya’s carton and see brightness **creep** with time `t`, then name the tensor shape **`(T, H, W)`**

---

## At a glance

A **video** is not a new kind of number. It is **pictures in order**. Each picture is the same 16×16 grid from `_box`. Time is just another axis.

By the end you can explain, without hand-waving:

- **8 frames**, each `(16, 16)`
- why later panels look a bit **brighter** (`+ 0.05 * t / 20`)
- the shape idea **`(T, H, W)`** = time, height, width

You will run `lab_video_frames` (CLI name `vframes`) and walk the list comprehension.

---

## Why this matters

Maya’s chute camera is a video. “Is the line moving?” is a **time** question. If you only keep frame 0, you cannot tell a jam from a still box (ml-41).

If you skip this lab, “sample every k” (ml-40) has nothing to sample.

```
frame 0, frame 1, …, frame 7
   T=8 stills, each H=16, W=16
```

---

## Concept primer

| Word | Plain English | In Maya’s warehouse |
| --- | --- | --- |
| **Frame** | One still picture | One 16×16 carton |
| **Video** | Frames in time order | Eight stills in a row |
| **`T`** | How many frames | **8** |
| **`H`, `W`** | Height, width in pixels | **16**, **16** |
| **`(T, H, W)`** | A stack of grayscale frames | Shape you would `np.stack` into |
| **Brightness creep** | Each later frame gets a little more light | `+ 0.05 * t / 20` |

The lab does **not** call `np.stack` for a 3-D array (it keeps a Python list for plotting). The **idea** is still a `(8, 16, 16)` block.

```
t = 0  →  add 0.00     darkest of the set
t = 7  →  add 0.05*7/20 = 0.0175   a bit brighter
```

Plus `_box(False, t)` grain that **also** changes with `t`, so the climb is not a perfect ramp. You will still see the strip get lighter **overall**.

> **Tip:** Color video is often `(T, H, W, 3)`. This lab stays grayscale so eight panels fit.

> **Watch out:** `dent=False` here. These frames are **intact** cartons. The story is time and light, not smash. Dents were ml-35–38.

---

## Setup

Reuse the **ml-00** venv.

### Step 1 — Enter the playground

Why now: matplotlib draws eight tiny cartons side by side.

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

Close the wide window to get the terminal back.

```bash
export ML_HEADLESS=1
```

if you have no display. `export` sets a session variable; `ML_HEADLESS=1` uses a non-window backend. Prefer a laptop.

---

## Hands-on

### Step 2 — Run the video-frames lab

Why this command now: eight stills in one figure is the definition. If you skip it, `(T,H,W)` is only letters.

```bash
python later_labs.py vframes
```

- `vframes` is the **lab key** in `LABS`, not the Python function name (`lab_video_frames`). Positional, not `--vframes`.

**It worked when** a wide window opens with title **`ml-39: video = pictures in time`** and **eight** gray cartons in a row, axes off.

Look left → right:

- same carton geometry (inner square, no dent)
- a slow **brightening** as you move right (the added `0.05 * t / 20`)
- speckle that changes (seed `t`)

No numeric stdout. Count the panels: **8**.

- [ ] You counted eight frames
- [ ] Frame 7 looks a touch lighter than frame 0

### Step 3 — Walk `lab_video_frames`

Open `later_labs.py`. Find `lab_video_frames`.

1. `frames = [_box(False, t) + 0.05 * t / 20 for t in range(8)]`
   - `range(8)` → `t = 0,1,…,7` — **T = 8**
   - `_box(False, t)` — intact carton; grain seed = time index
   - `+ 0.05 * t / 20` — **same number added to every pixel** that frame: a global lift
   - `/ 20` makes the lift tiny so the carton does not blow out to white
2. `plt.subplots(1, 8, figsize=(10, 2))` — 1 row, **8** columns; `figsize` is width×height in inches
3. Loop: `imshow(np.clip(im, 0, 1), cmap="gray")` then `axis("off")`
   - `clip` because grain + lift might pass 1
4. `fig.suptitle("ml-39: video = pictures in time")` — the sentence to remember

> **Tip:** `0.05 * t / 20` is **not** a learning rate. It is fake lighting: “the dock lamp warms up.”

> **Watch out:** Adding a scalar to a 16×16 array broadcasts (ml-04): every pixel gets the same lift. That is why the **whole** frame brightens, not one corner.

### Step 4 — Print `T` and the lift

Why now: prove eight and the formula without squinting at gray.

```bash
python -c "
from later_labs import _box
import numpy as np
frames = [_box(False, t) + 0.05 * t / 20 for t in range(8)]
print('T', len(frames), 'H,W', frames[0].shape)
print('lifts', [round(0.05 * t / 20, 4) for t in range(8)])
print('means', [round(float(np.clip(im,0,1).mean()), 4) for im in frames])
"
```

- `-c` means “run this code string and exit.”

**Expect:**

```text
T 8 H,W (16, 16)
lifts [0.0, 0.0025, 0.005, 0.0075, 0.01, 0.0125, 0.015, 0.0175]
means [0.7524, 0.7519, 0.7566, 0.7604, 0.7645, 0.7634, 0.7688, 0.7647]
```

Means **trend up** with `t` but wobble because seed `t` changes grain. That is honest. Shape idea: stack these and you get **`(8, 16, 16)`**.

- [ ] `T` is 8
- [ ] Last lift is `0.0175`

### Step 5 — Stack into `(T, H, W)` for real

Why now: the lab keeps a Python list because `subplots` wants a list. You should still **build the tensor** Maya’s jam lab will use (ml-41).

```bash
python -c "
from later_labs import _box
import numpy as np
frames = [_box(False, t) + 0.05 * t / 20 for t in range(8)]
V = np.stack([np.clip(im, 0, 1) for im in frames])
print('V', V.shape, 'T,H,W', V.shape[0], V.shape[1], V.shape[2])
"
```

**Expect:** `V (8, 16, 16) T,H,W 8 16 16`

- `np.stack` adds a new **first** axis. That axis is time.
- Color would be `(T, H, W, 3)` — a fourth axis for red/green/blue. Not today.

- [ ] `V.shape` is `(8, 16, 16)`

---

## How it works (deeper)

Real video is often 30 pictures per second (ml-40). This lab is 8 stills so they fit on a laptop strip.

Models that “understand video” still start here:

- 2-D CNN per frame, then mix time (slow)
- 3-D stamps that slide in `T` as well as `H,W`
- sample fewer frames (next lesson) so a CPU can finish

Maya does not need a 3-D net to notice a jam. She needs **change across frames** (ml-41). You cannot compute change until you admit a video is a list of grids.

---

## Common pitfalls

1. **Plot never opens.** Unset `ML_HEADLESS` on a laptop.
2. **You ran `python later_labs.py video`.** The key is **`vframes`**. Typo → argparse lists legal names.
3. **`ModuleNotFoundError`.** Activate `.venv`.
4. **You called the wobble in means a bug.** Seed `t` changes grain; lifts are tiny. Trend still climbs.
5. **You thought `False` meant “no video.”** It means **no dent**.

---

## Knowledge check

Answer from the plot, the function, and the `-c` print.

1. How many frames does the lab draw, and what CLI name do you pass?
2. What is the shape of **one** frame? What `(T, H, W)` would a stack have?
3. Write the brightness-lift formula in the list comprehension.
4. Is the carton dented in this lab?
5. Why are frame means not a perfectly straight line even though the lift is?
6. What shape does `np.stack` of the eight clipped frames print?

<details>
<summary>Answers</summary>

1. 8 frames; `python later_labs.py vframes`.
2. `(16, 16)`; a stack would be `(8, 16, 16)`.
3. `+ 0.05 * t / 20` (on top of `_box(False, t)`).
4. No. `_box(False, t)`.
5. Grain seed equals `t`, so speckle changes; the lift is only +0.0175 by the end.
6. `(8, 16, 16)` — that is `(T, H, W)`.

</details>

---

## Recap

- **You viewed** eight stills and named video as `(T, H, W)`.
- **You understand** brightness can creep with `t` without a new kind of math.
- **Next** you drop frames on purpose: 30 fps × 10 s → every 15th → 20 stills.

Next: `ml-40-sample-every-k`

---

## Stretch goal

In `lab_video_frames`, change `range(8)` to **`range(4)`** and `subplots(1, 8, ...)` to **`subplots(1, 4, ...)`**. Save. Rerun:

```bash
python later_labs.py vframes
```

- **Expect:** four panels. Lift on the last frame is `0.05 * 3 / 20 = 0.0075` instead of 0.0175. `(T, H, W)` idea becomes `(4, 16, 16)`.
- Put **8** back in **both** places when you are done.

---

## Feedback

Could you redo this lab from memory? Note the **lesson id** (`ml-39`), the **step number**, what you **expected**, and what you **saw** (traceback or plot).

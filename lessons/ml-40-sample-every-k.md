# ml-40 — Sample every k frames

**Level:** Absolute beginner  
**Time:** ~35 minutes  
**Prerequisites:** ml-39; venv from **ml-00**  
**Lab outcome:** You compute **30 fps × 10 s = 300** frames, keep every **15th**, and land on **20** stills Maya’s CPU can stand

---

## At a glance

**Sample every k** means: keep frame 0, drop the next k−1, keep, drop, … You **keep the story** (the chute still moves) and **drop the blur of extras** (299 near-copies).

By the end you can explain, without hand-waving:

- 30 pictures per second × 10 seconds = **300** frames
- stride **k = 15** → **300 / 15 = 20** frames
- why a CPU lab refuses to run all 300 through `_box`

You will run `lab_sample_k` (CLI name `samplek`) and walk the two print lines. No plot.

---

## Why this matters

Maya’s dock cam is often **30 fps**. Ten seconds of “did that carton stall?” is 300 stills. ml-39 already made eight 16×16 grids feel like a strip. Three hundred of them is a lunch break.

If you skip this lab, ml-41’s 12-frame stacks will look arbitrary. They are a sampled clip.

```
300 frames  --keep every 15th-->  20 frames
index 0, 15, 30, …, 285
```

---

## Concept primer

| Word | Plain English | In Maya’s warehouse |
| --- | --- | --- |
| **fps** | Frames per second (how many stills each second) | Dock cam: **30** |
| **Clip length** | How many seconds you care about | **10** s of chute |
| **Raw count** | `fps × seconds` | **300** |
| **k / stride** | Keep 1, skip k−1 | **15** |
| **Sampled count** | `raw / k` when it divides evenly | **20** |

```
kept = floor(n / k)   here 300/15 = 20 exactly
```

> **Tip:** Sampling is **not** max-pool (ml-37). Pool shrinks **space** inside one photo. This shrinks **time** across photos.

> **Watch out:** If a smash lasts 5 frames at 30 fps, k=15 might **skip the smash**. Pick k from the event length, not from a blog default.

---

## Setup

Reuse the **ml-00** venv.

### Step 1 — Enter the playground

Why now: same script; stay in the folder that holds `later_labs.py`.

```bash
cd project/ml_playground
source .venv/bin/activate
```

- `cd` means “change directory.”
- `source` activates the island in this shell.

**It worked when** `(.venv)` shows and:

```bash
python --version
python -c "import numpy, sklearn; print(numpy.__version__, sklearn.__version__)"
```

```text
Python 3.14.6
2.5.2 1.9.0
```

No matplotlib window. Stdout only.

---

## Hands-on

### Step 2 — Run the sample-k lab

Why this command now: the two sentences are the frozen arithmetic this lesson grades. If you skip them, you will invent 24 fps from a memory of cinema.

```bash
python later_labs.py samplek
```

- `samplek` is the **LABS** key (one word). The function is `lab_sample_k`. Not `--samplek`. Not `sample-k`.

**It worked when** you see **exactly**:

```text
30 fps * 10 seconds = 300 frames. CPU lab uses every 15th → 20 frames.
That is 'sample every k'. You keep the story, drop the blur of extras.
```

Walk line 1 in three chunks:

- `30 fps * 10 seconds = 300 frames` — raw clip
- `every 15th` — **k = 15**
- `→ 20 frames` — 300 / 15

Line 2 is the job description. Memorize it in Maya English: keep the story, drop extras.

- [ ] You see `300` and `20` on the same line
- [ ] You can point at `15` as k

### Step 3 — Walk `lab_sample_k`

Open `later_labs.py`. Find `lab_sample_k`.

1. First `print` — the arithmetic, hardcoded as a sentence. **No numpy.** The lab does not generate 300 images.
2. Second `print` — names the pattern `'sample every k'`.

That is the whole function. Two strings. You still had to **run** it so the numbers are in your terminal, not only in this markdown.

> **Tip:** CPU labs **talk about** 300 frames instead of drawing them. ml-39 already taught what a frame is. This lesson is the **budget**.

> **Watch out:** The arrow `→` is Unicode in the file. If a font breaks it, the numbers 15 and 20 are still the lesson.

### Step 4 — Type the division

Why now: prove 300/15 without trusting the slogan.

```bash
python -c "print(30 * 10, 300 / 15)"
```

- `-c` means “run this code string and exit.”
- `*` is multiply. `/` is divide (float).

**It worked when:**

```text
300 20.0
```

`20.0` is the same 20 frames. Integer version: `python -c "print(300 // 15)"` prints `20` (`//` means divide and drop the fraction).

- [ ] `30 * 10` is 300
- [ ] `300 / 15` is 20.0

### Step 5 — List the kept frame indices

Why now: “every 15th” should become a list you can read, not a vibe.

```bash
python -c "print(list(range(0, 300, 15))); print(len(list(range(0, 300, 15))))"
```

- `range(start, stop, step)` — `start` 0, `stop` 300 (excluded), `step` **15** which is k.
- `list(...)` materializes the range so `print` shows the numbers.

**It worked when:**

```text
[0, 15, 30, 45, 60, 75, 90, 105, 120, 135, 150, 165, 180, 195, 210, 225, 240, 255, 270, 285]
20
```

Twenty indices. Last kept frame is **285**, not 299. You drop the last 14 raw frames because 285+15=300, which is past the end.

The same idea as a slice `frames[::15]` on a length-300 list: empty start, empty stop, step 15. That is Python slice syntax, not a CLI flag.

- [ ] Length prints `20`
- [ ] Last index is `285`

---

## How it works (deeper)

300 names `0, 15, 30, …, 285` — that is 20 indices. Check: `(285 − 0) / 15 + 1 = 20`.

What you lose:

- fast flicks shorter than k frames
- smooth motion (ml-41 will fake motion with `np.roll` on **12** frames — already a sampled clip)

What you keep:

- whether the chute **generally** moved over those 10 seconds
- a count a laptop can loop

Production systems pick k from SLA: “detect a jam within 0.5 s” at 30 fps means you cannot set k=60 (two seconds between kept frames). This lab’s k=15 is 0.5 s between stills: 15/30 = 0.5.

---

## Common pitfalls

1. **`unrecognized arguments`.** Use `samplek`, not `sample` or `sample_k`.
2. **`ModuleNotFoundError`.** `source .venv/bin/activate`.
3. **Wrong folder.** `cd project/ml_playground`.
4. **You converted 20 frames back to “20 fps.”** You still have a 10 s clip. You have 2 sampled frames per second (30/15), not a 20 fps camera.
5. **You skipped running the script** because “it’s only prints.” The knowledge check quotes those prints.

---

## Knowledge check

Answer from the stdout you produced.

1. Copy the first printed line.
2. What three numbers multiply/divide as 30, 10, 15, and what two counts do they produce?
3. In one sentence, what does “sample every k” keep and drop (use the lab’s words)?
4. What CLI token do you pass to `later_labs.py` for this lesson?
5. Is this lab drawing 300 matplotlib windows?
6. What is the last index in `range(0, 300, 15)`, and how many indices is that?

<details>
<summary>Answers</summary>

1. `30 fps * 10 seconds = 300 frames. CPU lab uses every 15th → 20 frames.`
2. 30 fps × 10 s = 300 raw; every 15th → 20 kept.
3. Keep the story, drop the blur of extras.
4. `samplek`
5. No. Two print lines only.
6. Last index `285`; length `20`.

</details>

---

## Recap

- **You ran** the sample-k prints and typed `30 * 10` and `300 / 15`.
- **You understand** k is a time stride: 300 → 20 at k=15.
- **Next** you measure motion vs a jammed chute on stacked frames.

Next: `ml-41-conveyor-jam`

---

## Stretch goal

In `lab_sample_k`, change the printed **`15`** to **`10`** and the printed **`20`** to **`30`** (because 300/10 = 30). Save. Rerun:

```bash
python later_labs.py samplek
```

- **Expect:** the sentence now claims every 10th → 30 frames. Confirm with `python -c "print(300 / 10)"`.
- Put **`15`** and **`20`** back when you are done so this lesson still matches.

Do not invent a second camera (24 fps, 8 s) in a notebook. The stretch is **edit the lab’s k, rerun, revert**.

---

## Feedback

Could you redo this lab from memory? Note the **lesson id** (`ml-40`), the **step number**, what you **expected**, and what you **saw** (traceback or printout).

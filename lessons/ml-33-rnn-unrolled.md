# ml-33 — RNN unrolled

**Level:** Absolute beginner  
**Time:** ~50 minutes  
**Prerequisites:** ml-32; venv from **ml-00**  
**Lab outcome:** You read a 6×5 heatmap of hidden memory while a tiny RNN scans the location code `A1-B2`

---

## At a glance

A **recurrent neural net (RNN)** reads one token, updates a short **memory**, then reads the next. **Unrolled** means: draw that loop as a row of copies, one copy per letter.

By the end you can explain, without hand-waving:

- what **hidden state** `h` is (six numbers of memory)
- the update `h = tanh(x @ Wxh + h @ Whh)`
- why today’s picture is the **shape** of memory, not a trained reader

You will run the lab, open the heatmap, and walk every line of `lab_rnn`.

---

## Why this matters

Maya’s aisle tags look like `A1-B2`: zone letter, slot digit, dash, zone letter, slot digit. A bag of characters would see two `A`/`B`/`1`/`2`/`-` piles and forget that **A came first**.

If packing robots read `B2-A1` as the same bag as `A1-B2`, the van goes to the wrong dock. An RNN keeps a running note: “I just saw A, then 1, then dash…”

ml-32 proved bags ignore order. This lab is the first machine that **does not**.

---

## Concept primer

| Word | Plain English | In Maya’s warehouse |
| --- | --- | --- |
| **Token** | One character in this lab | `A`, `1`, `-`, `B`, `2` |
| **Vocab** | The allowed alphabet | `A B C 1 2 3 -` (7 symbols) |
| **One-hot** | A row of zeros with a **1** in this token’s slot | `A` → `[1,0,0,0,0,0,0]` |
| **Hidden state `h`** | The RNN’s memory right now | Six numbers after each letter |
| **`Wxh`** | Mix from “this letter” into memory | Shape `(7, 6)` |
| **`Whh`** | Mix from “old memory” into new memory | Shape `(6, 6)` |
| **`tanh`** | Squash each mix into roughly −1…1 | Stops memory exploding |
| **Unroll** | Write the loop as five copies in a row | One column per letter of `A1-B2` |

```
h starts as [0,0,0,0,0,0]
read A → new h
read 1 → new h   (old h mixed in)
read - → new h
read B → new h
read 2 → new h
```

> **Tip:** “Recurrent” only means “the output of this step is an **input** to the next.” Same recipe, reused.

> **Watch out:** These weights are **random** (`default_rng(0)`, scale 0.2). The heatmap is not “the net reading aisle A.” It is “memory **changes** as letters arrive.” Training comes later in the track’s spirit, not in this function.

---

## Setup

You already built the island in **ml-00**. Reuse it.

### Step 1 — Enter the playground

Why now: plots and imports resolve from `project/ml_playground`. Wrong folder → import errors.

```bash
cd project/ml_playground
source .venv/bin/activate
```

- `cd` means “change directory.”
- `source` turns on the venv in **this** terminal.

**It worked when** `(.venv)` shows and pins match:

```bash
python --version
python -c "import numpy, sklearn; print(numpy.__version__, sklearn.__version__)"
```

```text
Python 3.14.6
2.5.2 1.9.0
```

Labs call `plt.show()`. A window should pop. **Close it** to get the terminal back.

If you are on a machine with no display:

```bash
export ML_HEADLESS=1
```

- `export` sets an environment variable for this session.
- `ML_HEADLESS=1` tells the script to use matplotlib’s non-window backend. This lab still **computes** `H`; you just will not see the picture. Prefer a laptop so you see the heatmap.

---

## Hands-on

### Step 2 — Run the RNN lab

Why this command now: it is the only way to see hidden state **change** letter by letter. If you skip it, `tanh` stays a slogan.

```bash
python later_labs.py rnn
```

- `rnn` is a positional lab name (`argparse` key in `LABS`). Not `--rnn`.

**It worked when** a window opens titled `ml-33: hidden state as we read a location code`.

On the plot:

- **x-axis** = the five characters `A` `1` `-` `B` `2` (left to right)
- **y-axis** = six **hidden units** (memory slots)
- **color** = `coolwarm`: how positive or negative that slot is after that letter

There is **no stdout table**. The picture *is* the output. Close the window when you have stared at column `A` vs column `-`.

- [ ] Five tick labels spell `A1-B2`
- [ ] Six rows of color (not one)
- [ ] Colors **change** across columns (memory is not frozen)

### Step 3 — Walk `lab_rnn` line by line

Open `later_labs.py`. Find `lab_rnn`. Keep the heatmap in mind.

1. `rng = np.random.default_rng(0)` — frozen RNG so your picture matches everyone else’s. `0` is the seed, not a “learning rate.”
2. `vocab = list("ABC123-")` — seven characters Maya’s codes use. `list(...)` splits the string into `['A','B','C','1','2','3','-']`.
3. `stoi = {c: i for i, c in enumerate(vocab)}` — **string to index**. `A` is 0, `B` is 1, … `-` is 6. This is how a letter becomes a column of `Wxh`.
4. `Wxh = rng.normal(scale=0.2, size=(len(vocab), 6))` — **input-to-hidden**. Shape **(7, 6)**. `scale=0.2` is the spread of the random numbers (small, so `tanh` is not slammed to ±1 on step one).
5. `Whh = rng.normal(scale=0.2, size=(6, 6))` — **hidden-to-hidden**. Shape **(6, 6)**. This is the “recurrent” piece: old memory → new memory.
6. `h = np.zeros(6)` — memory starts blank. Reading the first `A` has no past.
7. `text = "A1-B2"` — five steps. The heatmap has **five columns**.
8. Loop `for ch in text:`
   - `x = np.zeros(len(vocab))` then `x[stoi[ch]] = 1` — one-hot for this character.
   - `h = np.tanh(x @ Wxh + h @ Whh)` — **the whole RNN**.
   - `hs.append(h.copy())` — save a snapshot. `.copy()` matters: without it every snapshot would be the **last** `h`.
9. `H = np.stack(hs)` — shape **(5, 6)**: one row per letter, six memory slots.
10. `ax.imshow(H.T, ...)` — **transpose** so units are rows and time is columns. `aspect="auto"` stretches cells so you can see them. `cmap="coolwarm"` is red/blue for +/−.

Say the update with the symbols filled in:

> “New memory = tanh( this letter’s one-hot mixed by **Wxh**, plus old memory mixed by **Whh** ).”

- [ ] You found `Wxh` shape `(7, 6)` and `Whh` shape `(6, 6)` in the file
- [ ] You can point at the one line that updates `h`

### Step 4 — Confirm shapes in the interpreter

Why now: the plot hides shapes. Shapes are how you check you understood the mix.

```bash
python -c "
import numpy as np
print('vocab', list('ABC123-'), len(list('ABC123-')))
print('Wxh', (7, 6), 'Whh', (6, 6), 'H', (5, 6))
print('one-hot A', [1,0,0,0,0,0,0])
"
```

- `-c` means “run this code string and exit.”

**Expect:** vocab length **7**, and the three shapes above. `H` is 5 letters × 6 units **before** the transpose that `imshow` uses.

> **Tip:** `@` is numpy’s matrix multiply (same idea as the dot product in ml-03). `x @ Wxh` is 7-dim × (7×6) → 6-dim. `h @ Whh` is 6-dim × (6×6) → 6-dim. You **add** those two 6-vectors, then `tanh` each slot.

> **Watch out:** `H.T` on the plot is **(6, 5)**. If you later print `H.shape` and expect the plot’s orientation, you will think time is the wrong axis.

---

## How it works (deeper)

Unrolled, the five steps are the **same weights** five times:

```
h0 = 0
h1 = tanh( x_A @ Wxh + h0 @ Whh )
h2 = tanh( x_1 @ Wxh + h1 @ Whh )
h3 = tanh( x_- @ Wxh + h2 @ Whh )
h4 = tanh( x_B @ Wxh + h3 @ Whh )
h5 = tanh( x_2 @ Wxh + h4 @ Whh )
```

Nothing in `lab_rnn` compares `h5` to a label. There is no loss. There is no nudge. Seed `0` only makes the **random** `Wxh`/`Whh` repeatable.

That is still enough to see the idea: column 0 (after `A`) is not column 4 (after `2`), because each step **mixed the previous memory in**. A bag would have added counts and stopped.

ml-34 will ask: what if each mix **shrinks** the old memory (multiply by 0.7 ten times)? Early letters fade. LSTMs add **gates** so Maya can keep “this was aisle A” across a long code.

---

## Common pitfalls

1. **Plot never opens.** You exported `ML_HEADLESS=1`, or you are on a server. On a laptop: `unset ML_HEADLESS` and rerun.
2. **`ModuleNotFoundError`.** Venv off. `source .venv/bin/activate` from `project/ml_playground`.
3. **Wrong folder.** `later_labs.py` must be in `.` so `from meridian_data import ...` still works for other labs; this function does not use it, but stay in the playground anyway.
4. **You called the heatmap “the trained reader.”** Weights are `rng.normal`. The title is location-code **shape**, not accuracy.
5. **You forgot `.copy()`.** If you ever edit the loop and append `h` without copy, every column becomes the last `h`. The real lab already copies.

---

## Knowledge check

Answer from the function and the plot you opened.

1. What string is `vocab`? How many symbols?
2. What are the shapes of `Wxh` and `Whh`?
3. How many columns does the heatmap have, and which characters label them?
4. Write the one-line update for `h` (the `tanh` formula).
5. Are `Wxh` and `Whh` learned from aisle tags in this lab, or random?

<details>
<summary>Answers</summary>

1. `ABC123-` as a list of 7 characters.
2. `Wxh` is `(7, 6)`; `Whh` is `(6, 6)`.
3. Five columns: `A`, `1`, `-`, `B`, `2`.
4. `h = np.tanh(x @ Wxh + h @ Whh)`
5. Random (`default_rng(0)`, `scale=0.2`). Not trained.

</details>

---

## Recap

- **You built** a heatmap of six memory slots while reading `A1-B2`.
- **You understand** an RNN is a reused mix: this token plus last memory, then `tanh`.
- **Next** you will see why that memory **fades**, and what LSTM gates say in plain English.

Next: `ml-34-lstm-vanishing`

---

## Stretch goal

In `lab_rnn`, change the hidden size from **6** to **3** in **three** places: `size=(len(vocab), 6)`, `size=(6, 6)`, and `np.zeros(6)`. Save. Rerun:

```bash
python later_labs.py rnn
```

- **Expect:** the heatmap still has five time columns (`A1-B2`) but only **three** rows of hidden units. The *meaning* (memory updates left to right) does not change.
- Put **6** back in all three places when you are done so later notes match this lesson.

---

## Feedback

Could you redo this lab from memory? Note the **lesson id** (`ml-33`), the **step number**, what you **expected**, and what you **saw** (traceback or plot).

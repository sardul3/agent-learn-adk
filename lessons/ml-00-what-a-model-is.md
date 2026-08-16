# ml-00 — What a model even is

**Level:** Absolute beginner  
**Time:** ~45 minutes  
**Prerequisites:** Python 3.11+; you can open a terminal; no ML and no linear algebra  
**Lab outcome:** You can point at Maya’s packing guesses and name the inputs, the recipe, the guess, and the error

---

## At a glance

A **model** is a recipe that turns facts you have into a guess. Maya already has one: “about 5 minutes plus 2 per kilo.”

By the end you can explain, without hand-waving:

- which numbers are **inputs** (facts you already have)
- which numbers are the **recipe** (Maya’s 5 and 2)
- which numbers are **guesses** vs **truth** (stopwatch)
- what **error** means when a guess is late or early

You will run a real script, read a table, and look at a scatter plot. You will not train anything yet.

---

## Why this matters

Meet **Maya**, night-shift warehouse lead at Meridian. Vans idle at the dock if packing-time guesses are systematically late. She does not need a neural net tonight. She needs a recipe she can read.

Every later “AI” in this bonus track is still this loop:

```
facts  →  recipe  →  guess
              ↑
         score against truth
```

If you skip this lab, later words like *loss*, *weight*, and *train* have nothing to stick to.

---

## Concept primer

| Word | Plain English | In Maya’s warehouse |
| --- | --- | --- |
| **Input** | A fact you already have | Box weight in kilograms |
| **Recipe / model** | A rule that turns facts into a guess | `minutes = 5 + 2 × weight` |
| **Output / guess** | What the recipe prints | “This box will take 20.3 minutes” |
| **Truth / label** | What actually happened | Stopwatch: 19.70 minutes |
| **Error** | Guess minus truth | `20.30 − 19.70 = +0.60` (a bit late) |
| **Loss** | A score of “how wrong,” often an average of errors | Mean error of +0.90 minutes on 12 boxes |

A person can be a model. A spreadsheet can be a model. A neural net is a model with more knobs. Same four parts.

> **Tip:** If you can subtract, you can score a model. That is the whole math today.

> **Watch out:** Do not say “the AI decided.” Maya’s line is a formula. You can read every number.

---

## Setup (once per machine)

Do this once. Later ML lessons reuse the same folder and the same virtual environment.

### Step 1 — Open a terminal in the playground

Why now: Python looks for `m0_labs.py` and `meridian_data.py` in the current folder. If you skip `cd`, imports fail.

```bash
cd project/ml_playground
```

- `cd` means “change directory.” There is no dash-flag here.

**It worked when** `ls` shows `m0_labs.py`, `classic_labs.py`, `later_labs.py`, and `meridian_data.py`.

### Step 2 — Make a private Python island (venv)

Why: so numpy / matplotlib / scikit-learn do not fight with other projects on your machine.

```bash
python3 -m venv .venv
```

- `-m venv` means “run the standard-library module named venv.”
- `.venv` is the folder name for that island.

Turn it on (macOS / Linux):

```bash
source .venv/bin/activate
```

**It worked when** your prompt shows `(.venv)` at the front.

### Step 3 — Install the three libraries

Why: **numpy** holds tables of numbers; **matplotlib** draws plots; **scikit-learn** (imported as `sklearn`) is the named toolbox you meet in later packs. **pandas** comes along because the warehouse tables are DataFrames.

```bash
pip install -r requirements.txt
```

- `-r` means “read this file as the list of packages.”

**It worked when** this prints nothing (no traceback):

```bash
python -c "import numpy, matplotlib, sklearn, pandas"
```

This playground is pinned to CPU-only libraries. You do not need a GPU.

### Step 4 — Know how plots behave

Labs call `plt.show()`. On a laptop a window should pop. Close the window to get the terminal back.

If you are on a machine with no display, you can still run the printouts:

```bash
export ML_HEADLESS=1
```

- `export` sets an environment variable for this terminal session.
- `ML_HEADLESS=1` tells the labs to use matplotlib’s non-window backend. Tables still print. The window will not.

This track is meant to be done on a laptop so you *see* the pictures.

---

## Hands-on

### Step 5 — Run the model lab

Why this command now: it opens the exact picture this lesson is about. If you skip it, the words stay abstract.

```bash
python m0_labs.py model
```

`model` is a lab name, not a flag. The script’s `argparse` only accepts a short list: `model`, `slope`, `vectors`, `dot`, `matrix`, `bowl`, `fit`.

**It worked when** a table prints and a scatter plot opens titled `ml-00: two guesses per box`.

You should see numbers in this neighborhood (seed is frozen, so they should match):

```text
 weight_kg  zone  hour  pack_minutes  maya_guess  error
      7.65     3    17         19.70       20.30   0.60
     10.81     2    15         24.50       26.62   2.12
      9.40     4    11         21.30       23.80   2.50
      ...
      3.92     4     7         14.30       12.84  -1.46
      3.63     4     6         12.29       12.26  -0.03

mean error (Maya minus truth): 0.90 minutes
A model is any recipe that turns inputs into a guess. Maya's recipe is already a model.
```

On the plot:

- **dots** = stopwatch minutes (truth)
- **x marks** = Maya’s recipe (guess)

Close the plot window when you have stared at one heavy box and one light box.

### Step 6 — Point at one row out loud

Pick the first row. Say this sentence with the numbers filled in:

> “Input is **7.65 kg**. Recipe is **5 + 2 × weight**. Guess is **20.30 minutes**. Truth is **19.70**. Error is **+0.60**, so Maya was a bit late.”

Do the same for the row with error **−1.46**. That one Maya was *early*.

- [ ] You said both sentences out loud (or in your head, honestly)
- [ ] You can find which column is the recipe vs which is the stopwatch

### Step 7 — Walk the code (do not paste blindly)

Open `m0_labs.py`. Find `lab_model`.

1. `packing_orders(12)` loads 12 fake but consistent warehouse rows from `meridian_data.py`.
2. `maya = 5 + 2 * df["weight_kg"]` is the entire model. Two knobs, written in the open.
3. `err = maya - df["pack_minutes"]` is guess minus truth.
4. `err.mean()` is the first **loss** you will meet: an average of how wrong.
5. `ax.scatter(...)` twice: dots for truth, `marker="x"` for Maya.

Now open `meridian_data.py` and find `packing_orders`.

The *hidden* story (Maya does not know this yet) is:

```text
minutes ≈ 4 + 1.8 × weight + 0.6 × zone + a little noise
```

Maya’s recipe uses **2.0** per kilo and **ignores zone**. That is why mean error is not zero. The leftover is not “the computer failed.” The leftover is “the recipe is missing a fact.”

> **Tip:** A mean error of +0.90 means Maya is late *on average*. Individual boxes can still be early (negative error).

> **Watch out:** `zone` and `hour` print in the table but Maya’s recipe does not use them. Unused columns are still not “the AI noticing extra context.” They are just sitting there.

### Step 8 — Mini experiment (do it)

In `lab_model`, change the recipe to Maya’s intern’s guess: **4 minutes plus 1.8 per kilo** (closer to the hidden story).

```python
maya = 4 + 1.8 * df["weight_kg"]
```

Save. Run again:

```bash
python m0_labs.py model
```

**Expect:** mean error should get smaller than 0.90 (not perfect — zone is still missing). Put `5 + 2 *` back when you are done so later screenshots in your notes still match.

- [ ] You changed one number, reran, and saw mean error move
- [ ] You put the original recipe back

---

## How it works (deeper)

The computer is not “understanding packing.” It is doing arithmetic you could do with a pencil, just faster.

```
for each box:
    guess = 5 + 2 * weight
    error = guess - stopwatch
then:
    mean_error = average of those errors
```

**Training** (you will do this in ml-05) means: nudge the 5 and the 2 so mean error gets smaller. Maya’s recipe today is a model that has **not** been trained. It still counts. “Trained” only means “we used data to move the knobs.”

A neural net, a tree, and GPT all still have: inputs, a recipe, a guess, a score. The recipe gets longer. The loop does not change.

---

## Common pitfalls

1. **`ModuleNotFoundError: numpy` (or matplotlib).** The venv is not active. Your prompt must show `(.venv)`. Redo Step 2’s `source` line, then Step 3.
2. **`No such file` / cannot import `meridian_data`.** You are not in `project/ml_playground`. `cd` there first.
3. **Plot never opens.** You exported `ML_HEADLESS=1`, or you are on a server with no display. On a laptop, unset it (`unset ML_HEADLESS`) and rerun.
4. **You closed the terminal and lost `(.venv)`.** Activating a venv is per-session. `source .venv/bin/activate` again. You do not reinstall packages.
5. **You treated +0.90 as “Maya is always 0.90 late.”** It is an average. Row 11 was 1.46 minutes *early*.

---

## Knowledge check

Answer from the table and the code you ran, not from memory of a blog.

1. On the 7.65 kg box, what is the input, the guess, and the truth?
2. Is Maya’s rule a model even though nobody “trained” the 5 and the 2?
3. Why is mean error not zero even though the recipe looks reasonable?
4. What would a mean error of **0.00** still fail to tell you?

<details>
<summary>Answers</summary>

1. Input 7.65 kg; guess 20.30 minutes; truth 19.70 minutes.
2. Yes. Trained only means we nudged the recipe using data. The recipe still counts.
3. The hidden packing time also uses zone (and noise). Maya’s recipe ignores zone and uses 2.0 per kilo instead of 1.8.
4. It would not tell you that some boxes are late and some early by large amounts that cancel. That is why later lessons square the error.

</details>

---

## Recap

- **You built** a plot of Maya vs the stopwatch on 12 packing orders.
- **You understand** model = recipe with inputs, a guess, and a score.
- **Next** you will drag slope and intercept until the line sits on the cloud of dots.

Next: `ml-01-functions-slope-intercept`

---

## Stretch goal

In `meridian_data.py`, `packing_orders` uses `seed=7` so your table matches this lesson. Change the call in `lab_model` to `packing_orders(12, seed=99)` and rerun.

- **Expect:** different weights, different mean error. The *meaning* of the columns does not change.
- Put `seed` back (or drop the extra argument so it uses 7) when you are done.

---

## Feedback

Could you redo this lab from memory? Note the **lesson id** (`ml-00`), the **step number**, what you **expected**, and what you **saw** (traceback or plot).

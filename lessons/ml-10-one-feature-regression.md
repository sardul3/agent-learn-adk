# ml-10 — One-feature regression (sklearn’s line)

**Level:** Absolute beginner  
**Time:** ~50 minutes  
**Prerequisites:** ml-05 (you nudged m and b by hand); ml-06 (train/test)  
**Lab outcome:** You fit `LinearRegression` on weight → pack minutes and read `m=1.828`, `b=5.409`, test MSE `0.799`

---

## At a glance

**Linear regression** is “draw the straight line that misses the least, in a squared-error sense.”

Tonight sklearn does the nudging you did by hand in `m0_labs.py fit`. Same warehouse story: **input** = `weight_kg`, **truth** = `pack_minutes`.

Printed knobs:

```text
sklearn m=1.828 b=5.409  test MSE 0.799
```

**m** = extra minutes per kilo. **b** = minutes when weight is 0 (an offset; boxes are not 0 kg). **Test MSE** = average squared miss on the 20 exam boxes.

---

## Why this matters

Meet **Maya** at Meridian. She should not hand-roll 400 steps every time she adds a column. She **should** still know that `m` and `b` are the same two knobs as the slider in ml-01.

If you skip this lab, later “sklearn `.fit`” is a black box instead of “solve the same bowl, faster, on train, score on test.”

---

## Concept primer

| Word | Plain English | Tonight |
| --- | --- | --- |
| **Feature** | Input column | `weight_kg` only |
| **Target / label** | What you guess | `pack_minutes` |
| **`LinearRegression`** | sklearn’s line fitter | Ordinary least squares (the MSE bowl) |
| **`.fit(Xtr, ytr)`** | Learn m and b from homework | 60 train boxes |
| **`.predict(Xte)`** | Apply the line to new weights | 20 test boxes |
| **`coef_`** | Slope(s) | `m=1.828` |
| **`intercept_`** | The b knob | `b=5.409` |
| **MSE** | Mean of (guess − truth)² | Test MSE **0.799** minutes² |

Hidden truth in `packing_orders` (Maya does not get this formula):

```text
minutes ≈ 4 + 1.8 × weight + 0.6 × zone + noise
```

A **weight-only** line cannot eat the zone term. Test MSE will not be 0. That leftover is missing features, not a broken library.

> **Tip:** Compare m to 1.8, not to Maya’s old rule-of-thumb 2.0. The fitter is chasing the hidden 1.8, plus noise, plus no zone.

> **Watch out:** Never quote **train** MSE as if it were the exam. This lab prints **test** MSE on purpose.

---

## Setup (short)

You already built the playground in **ml-00**. If your prompt does **not** show `(.venv)`, go back to ml-00 and finish Setup.

```bash
cd project/ml_playground
```

- `cd` means “change directory.” There is no dash-flag here.

Then:

```bash
source .venv/bin/activate
```

**It worked when** the prompt starts with `(.venv)`.

Pinned: **Python 3.14.6**, **numpy 2.5.2**, **scikit-learn 1.9.0**. The 1.828 / 5.409 / 0.799 are from that stack.

A scatter should open. Close it to get the terminal back.

---

## Hands-on

### Step 1 — Run the one-feature lab

Why this command now: it fits on 60 boxes, scores 20, and plots truth vs prediction. If you skip it, m and b stay symbols.

```bash
python classic_labs.py reg1
```

`reg1` is a **lab name**, not a flag. There is no `-` in this command.

**It worked when** stdout is:

```text
sklearn m=1.828 b=5.409  test MSE 0.799
```

and a window titled **`ml-10: one-feature line`**.

On the plot:

- **dots** = test stopwatch minutes (truth)
- **x marks** = the line’s guesses at those same weights

Close the window after you pick one heavy test box and one light one.

- [ ] You copied m **1.828**, b **5.409**, test MSE **0.799**
- [ ] You saw dots and x marks on the same x-axis (weight)

### Step 2 — Walk `lab_reg1`

Open `classic_labs.py`. Find `lab_reg1`.

1. `packing_orders(80)` — 80 boxes.
2. `X = df[["weight_kg"]]` — a one-column table (sklearn likes 2-D inputs even for one feature).
3. `y = df["pack_minutes"]` — the stopwatch.
4. `train_test_split(X, y, test_size=0.25, random_state=0)` — **same 60/20 idea as ml-06**, frozen shuffle.
5. `m = LinearRegression().fit(Xtr, ytr)` — learn slope and intercept on train.
6. `pred = m.predict(Xte)` — guesses on test weights.
7. `mean_squared_error(yte, pred)` — the 0.799.
8. Scatter truth and predictions on the **test** weights only.

| Setting | What it does | Why |
| --- | --- | --- |
| `test_size=0.25` | Hold out a quarter | 20 exam boxes |
| `random_state=0` | Freeze the split | Your m/b/MSE match this lesson |

`m.coef_[0]` is the single slope (index `[0]` because sklearn stores slopes in an array even for one feature). `m.intercept_` is b.

> **Tip:** `df[["weight_kg"]]` with **two** brackets keeps a table (one column). `df["weight_kg"]` is a Series. `LinearRegression` wants the table shape.

> **Watch out:** The plot is **test** only. A beautiful line on train would not be the exam.

### Step 3 — Compare to `m0_labs.py fit`

Why now: so sklearn is not a different religion. You already walked downhill on MSE by hand.

Run the hand-nudger (optional but do it once):

```bash
python m0_labs.py fit
```

`fit` is a lab name, not a flag.

You should see a table that starts like:

```text
step  mse  m  b
   0  315.254   2.466   0.333
  40    5.162   2.351   1.170
  ...
 360    1.225   1.943   4.421
```

Differences to say out loud:

| | `m0_labs.py fit` | `classic_labs.py reg1` |
| --- | --- | --- |
| How knobs move | 400 gradient steps, `lr=0.01`, start at 0 | Closed-form least squares (one shot) |
| Which rows | All **80** boxes | **60** train, score **20** test |
| What it prints | Train-ish MSE along the walk | **Test** MSE **0.799** |
| Final m, b | Still moving at step 360 (m≈1.94, b≈4.42) | m=**1.828**, b=**5.409** |

They disagree a little because the data pile and the solver disagree a little. Both are “fit a line on weight.” Both miss zone.

- [ ] You can name one reason sklearn’s m is not identical to the step-360 m

### Step 4 — Translate one test guess

Formula:

```text
guess minutes = 1.828 × weight_kg + 5.409
```

For a 10 kg test box: `1.828 × 10 + 5.409 = 23.689` minutes. The stopwatch will not match exactly (zone + noise). The **0.799** is the average of those squared misses on all 20 test boxes.

- [ ] You plugged one weight into 1.828 / 5.409 by hand

---

## How it works (deeper)

sklearn’s `LinearRegression` (default) solves **ordinary least squares**: pick m and b to minimize MSE on the rows you passed to `.fit`.

That is the bottom of the bowl from ml-05, without you choosing a learning rate. For one line, there is a direct formula. For a neural net later, you go back to nudging.

**Units:** MSE is **minutes squared**. 0.799 is not “0.799% wrong.” Compare MSE to MSE (ml-11’s many-feature test MSE will be ~0.443 — better, because zone is allowed).

**Why b is 5.409 not 4:** the hidden intercept is 4 **plus** 0.6×zone. Zone is 1–4. A weight-only line folds the average zone effect into b (and a little into m). That is not a bug. It is “the leftover story stuffed into the knobs you allowed.”

---

## Common pitfalls

1. **`ModuleNotFoundError`.** Venv off. `source .venv/bin/activate`. Prompt needs `(.venv)`.
2. **Wrong folder.** `cd project/ml_playground`. `cd` is not a flag.
3. **Plot never opens.** `unset ML_HEADLESS` on a laptop.
4. **You pass `df["weight_kg"]` and sklearn complains about 1-D.** Use `df[["weight_kg"]]` as the lab does.
5. **You compare 0.799 to Maya’s mean error +0.90 from ml-00.** Different metric (squared vs signed), different row count, different recipe. Do not mix them in one sentence as if they were the same score.
6. **You report m=1.828 as “the true 1.8.”** It is the **fitted** slope on 60 noisy boxes without zone. Close, not sacred.

---

## Knowledge check

Answer from the printout and the two labs.

1. What exact line did `python classic_labs.py reg1` print for m, b, and test MSE?
2. How many train rows and test rows (`test_size=0.25` on 80)?
3. Which column is `X`, and which is `y`?
4. In `m0_labs.py fit`, what MSE and m do you see at step 360?
5. Give two reasons those m values are not identical to 1.828.
6. The hidden formula uses 1.8 per kilo **and zone**. Why is test MSE not zero even if m were exactly 1.8?

<details>
<summary>Answers</summary>

1. `sklearn m=1.828 b=5.409  test MSE 0.799`
2. 60 train, 20 test.
3. `X` is `weight_kg`; `y` is `pack_minutes`.
4. MSE **1.225**, m **1.943**, b **4.421**.
5. Hand-fit uses all 80 rows and 400 incomplete gradient steps; sklearn uses 60 train rows and exact least squares.
6. Zone and noise still move the stopwatch. A weight-only line cannot catch them.

</details>

---

## Recap

- **You built** a sklearn line on weight, scored on a frozen test split.
- **You understand** `.fit` / `.predict` / `coef_` / `intercept_` / test MSE.
- **Next** you add zone and hour and watch hour’s knob stay tiny.

Next: `ml-11-many-features`

---

## Stretch goal

In `lab_reg1`, change **one number**: `random_state=0` → `random_state=1`. Save. Rerun:

```bash
python classic_labs.py reg1
```

- **Expect:** m, b, and test MSE **all move** (different 20 exam boxes). m should stay **near** 1.8, not jump to 5.
- Put `random_state=0` back so 1.828 / 5.409 / 0.799 still match.

- [ ] You changed the seed, saw the three numbers move a little
- [ ] You put `0` back

---

## Feedback

Could you redo this lab from memory? Note the **lesson id** (`ml-10`), the **step number**, what you **expected**, and what you **saw** (traceback, numbers, or plot).

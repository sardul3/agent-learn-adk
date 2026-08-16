# ml-14 — Logistic squash (P(refund) vs delay)

**Level:** Absolute beginner  
**Time:** ~50 minutes  
**Prerequisites:** ml-10 (`.fit` / `.predict`); ml-07 (tickets table)  
**Lab outcome:** You fit logistic regression on delay days and read an S-curve of P(refund) between 0 and 1

---

## At a glance

**Classification** = guess a **category** (refund vs not), not a number of minutes.

**Logistic regression** still starts with a line in delay-days. Then it **squashes** that line through an S-shaped curve so the output is a **probability** between 0 and 1.

Tonight:

- dots at y=0 and y=1 = real tickets (not-refund / refund)
- orange curve = **P(refund)** as delay goes from 0 to 10 days
- the code reads that probability with `predict_proba(grid)[:, 1]`

---

## Why this matters

Meet **Maya** at Meridian’s ticket desk. “Will this become a refund?” is not “how many minutes.” A line that shoots to 3.7 is not a probability. Leadership cannot staff a queue on 3.7.

The squash keeps every guess in **0–1**. You can then pick a cutoff (often 0.5) to say yes/no. ml-15 will draw that yes/no as a fence. ml-16 will count the mistakes.

If you skip this lab, `predict_proba` is a mystery method instead of “read the S-curve.”

---

## Concept primer

| Word | Plain English | Tonight |
| --- | --- | --- |
| **Label 0 / 1** | Not-refund / refund | `became_refund` |
| **Feature** | Input | `delay_days` only |
| **Logit / raw score** | The unsquashed line | `b + m × delay` (inside the model) |
| **Squash (sigmoid)** | Map any number into (0, 1) | The S you see |
| **P(refund)** | Model’s probability of class 1 | Orange curve |
| **`predict_proba`** | Two columns: P(class 0), P(class 1) | We take `[:, 1]` |
| **`predict`** | Hard 0/1 using a cutoff (default 0.5) | Not plotted tonight; used in ml-15 |

```
delay_days  →  line  →  squash into 0–1  →  P(refund)
```

How tickets get labels in `meridian_data.py` (honest table, `leak=False`):

```text
refund if delay > 4.5  OR  angry_words > 6  OR  price > 140
then flip about 8% of labels
```

A **delay-only** S-curve cannot see angry words or price. The curve still rises with delay because delay is one of the three triggers.

> **Tip:** Dots sit on 0 and 1. The curve sits **between**. That gap is not a bug. Probability is not the 0/1 label.

> **Watch out:** sklearn 1.9.0 may warn that the delay **grid** has no feature names. Same as ml-12. Ignore it for the picture.

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

Pinned: **Python 3.14.6**, **numpy 2.5.2**, **scikit-learn 1.9.0**.

You **need the plot**. On a laptop leave `ML_HEADLESS` unset.

---

## Hands-on

### Step 1 — Run the logistic lab

Why this command now: the S-curve *is* the lesson. There is no accuracy printout.

```bash
python classic_labs.py logistic
```

`logistic` is a **lab name**, not a flag. There is no `-` in this command.

**It worked when** a window opens titled **`ml-14: line, then squash into 0–1 (logistic)`**.

You should see:

- a cloud of points at **y=0** and **y=1** vs delay 0–10 (`alpha=0.3` so overlaps are visible)
- an orange line that starts low on the left, **bends up**, flattens toward 1 on the right
- legend: `tickets (0/1)` and `P(refund)`
- x-label `delay_days`

You may see:

```text
UserWarning: X does not have valid feature names, but LogisticRegression was fitted with feature names
```

The grid is numpy; the fit saw pandas `delay_days`. **Ignore for the picture.**

Close the window after you can point at: left (short delay, low P), middle (rising), right (long delay, high P).

- [ ] You saw an S, not a straight line through 0/1
- [ ] You ignored the feature-name warning

### Step 2 — Walk `lab_logistic`

Open `classic_labs.py`. Find `lab_logistic`.

1. `tickets(200)` — 200 honest tickets (`leak` defaults False).
2. `X = df[["delay_days"]]`, `y = df["became_refund"]`.
3. `clf = LogisticRegression().fit(X, y)` — learn the line-then-squash on **all 200** rows (picture, not a test split).
4. `grid = np.linspace(0, 10, 80).reshape(-1, 1)` — 80 delay values from 0 to 10 days, column-shaped.
5. `p = clf.predict_proba(grid)[:, 1]` — probability of **class 1 (refund)** on that grid.
6. Scatter the real 0/1 tickets; plot `p` vs `grid`.

| Piece | What it does | Why |
| --- | --- | --- |
| `np.linspace(0, 10, 80)` | 80 evenly spaced delays | Smooth S, not 200 jagged dots |
| `reshape(-1, 1)` | Make a column | sklearn wants 2-D `X` |
| `predict_proba(...)` | Two probabilities per row | They sum to 1 |
| `[:, 1]` | Take the refund column | Class 0 is “not refund”; we plot refund |

> **Tip:** `[:, 1]` is “every row, second column.” In sklearn, classes are sorted: column 0 = class 0, column 1 = class 1.

> **Watch out:** `.predict(grid)` would jump from 0 to 1 at the 0.5 fence. That **step** is ml-15’s cousin. Tonight you plot the **smooth** P, not the fence.

### Step 3 — Walk the squash with one delay

You do not need the exact fitted m and b printed (this lab does not print them). You need the shape:

```text
raw = b + m × delay_days
P(refund) = 1 / (1 + e^(−raw))
```

- If `raw` is a large **positive**, P is near **1**.
- If `raw` is a large **negative**, P is near **0**.
- If `raw` is **0**, P is **0.5**.

That formula is the S. Logistic regression **fits** b and m so this S matches the 0/1 cloud as well as this model family can.

Because labels also depend on angry words and price, some **short-delay** tickets still sit at y=1, and some **long-delay** tickets sit at y=0 (the 8% flips plus the other triggers). The S is a compromise through that mix.

- [ ] You can say what P≈0.5 means (raw score about 0; a coin-flip according to *this* delay-only recipe)

### Step 4 — Peek at `tickets` again

Open `meridian_data.py`. Confirm `became_refund` is 0/1, and `delay_days` is rounded to 2 decimals. No `refund_already_paid` unless `leak=True` (ml-07). This lab must stay honest.

- [ ] You confirmed `tickets(200)` does not pass `leak=True`

---

## How it works (deeper)

Linear regression (ml-10) minimized squared error on minutes. Logistic regression minimizes a **log loss** on probabilities (details not required tonight): it wants high P on real refunds and low P on real non-refunds.

**Why not linear regression on 0/1?** A line can predict 1.4 or −0.2. Those are not probabilities. The squash **enforces** the 0–1 box.

**Default cutoff:** `clf.predict` is `1` when P ≥ 0.5. Maya might pick a different cutoff if missing a smashed vase is worse than refunding a fine order (ml-16). Tonight you only look at P.

**One feature vs many:** ml-15 adds `angry_words` and draws a **2-D** fence. Same squash, more inputs.

**Fit on all 200:** like ml-12, this is a picture. An honest score would split first (ml-06).

---

## Common pitfalls

1. **Plot never opens.** `unset ML_HEADLESS` on a laptop.
2. **`ModuleNotFoundError`.** Venv off. `source .venv/bin/activate`.
3. **Wrong folder.** `cd project/ml_playground`. `cd` is not a flag.
4. **You read the orange curve as “the tickets.”** Tickets are the 0/1 dots. The curve is P.
5. **You use `predict_proba[:, 0]` and wonder why the S is upside down.** Column 0 is P(not refund) = 1 − P(refund).
6. **You panic at the feature-name warning.** Harmless on the numpy grid in sklearn 1.9.0.

---

## Knowledge check

Answer from the figure and `lab_logistic`.

1. What command did you run, and is `logistic` a flag?
2. What does `predict_proba(grid)[:, 1]` return?
3. Why do tickets sit on 0 and 1 while the curve does not?
4. Name one reason a short-delay ticket can still be a refund in `tickets`.
5. What warning might appear, and what should you do for this lab?
6. Does this lab print test accuracy? What split does it use?

<details>
<summary>Answers</summary>

1. `python classic_labs.py logistic`. `logistic` is a lab name, not a flag. No `-`.
2. P(refund) for each delay on the 0–10 grid — 80 numbers between 0 and 1.
3. Labels are hard 0/1. The model outputs a probability.
4. `angry_words > 6` or `price > 140`, or an 8% random flip.
5. Feature names on the numpy grid. Ignore it for the picture.
6. No accuracy print. No split — fit on all 200 rows.

</details>

---

## Recap

- **You built** an S-curve of P(refund) vs delay.
- **You understand** logistic = line + squash; `[:, 1]` is the refund probability.
- **Next** you add angry words and draw the 2-D decision fence.

Next: `ml-15-decision-boundary`

---

## Stretch goal

In `lab_logistic`, change **one number**: `np.linspace(0, 10, 80)` → `np.linspace(0, 10, 10)`. Save. Rerun:

```bash
python classic_labs.py logistic
```

- **Expect:** the orange “S” looks **jagged** (only 10 plot points). The fit is unchanged; only the drawing grid is coarser.
- Put `80` back so the curve is smooth again.

- [ ] You changed 80 to 10, saw a choppy curve
- [ ] You put `80` back

---

## Feedback

Could you redo this lab from memory? Note the **lesson id** (`ml-14`), the **step number**, what you **expected**, and what you **saw** (warning, traceback, or plot).

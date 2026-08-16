# ml-06 — Train, val, test

**Level:** Absolute beginner  
**Time:** ~40 minutes  
**Prerequisites:** ml-00 through ml-05; playground venv already built  
**Lab outcome:** You split 80 packing rows into 60 homework rows and 20 exam rows, and you can name which pile you may study

---

## At a glance

A **split** is a rule for putting rows into piles before you fit a recipe.

- **Train** = homework. You may look. You may fit. You may retry.
- **Validation (val)** = practice tests. You may retake them while you pick knobs (slope, depth, “should I add hour?”).
- **Test** = the exam. You take it **once**. You do not pick knobs by staring at it.

Tonight’s lab only carves **train vs test** (75% / 25%). Val is the extra pile you would cut from train later. Same idea: never tune on the exam.

---

## Why this matters

Meet **Maya**, night-shift warehouse lead at Meridian. She could memorize last night’s 80 boxes and still fail tonight’s vans.

A model that only looks good on the rows it studied is a student who memorized last year’s quiz. The **test split** is tonight’s dock: boxes the recipe has not seen.

If you skip this lab, later words like *leakage*, *overfitting*, and *test MSE* have no pile to point at.

---

## Concept primer

| Word | Plain English | In Maya’s warehouse |
| --- | --- | --- |
| **Row** | One example | One packed box with weight, zone, hour, stopwatch |
| **Train set** | Rows you may study | Last week’s 60 boxes you fit on |
| **Val set** | Rows you use to pick knobs | A practice night you may rerun |
| **Test set** | Rows you score once | Tonight’s 20 boxes, unseen |
| **Shuffle** | Mix the deck before dealing | So all the heavy boxes are not stuck in train |
| **Seed / `random_state`** | Frozen shuffle | Same 60/20 every time you rerun this lab |
| **`test_size`** | Fraction held out as the exam | `0.25` = a quarter of 80 = 20 rows |

```
80 packing rows
        │
        ├── shuffle (frozen by random_state=0)
        │
        ├── 60 train  →  fit the recipe here
        └── 20 test   →  score once; do not retune
```

> **Tip:** 75/25 is a fraction of rows, not a magic ratio. Tiny data makes the exam noisy. You still do not peek to pick knobs.

> **Watch out:** This lab does **not** print a val pile. If you start choosing “degree 4 vs degree 1” by looking at test, you just turned the exam into homework.

---

## Setup (short)

You already built the playground in **ml-00**. This lesson only needs that island turned on.

If your prompt does **not** show `(.venv)`, go back to ml-00 and finish Setup. Do not reinstall from scratch if `.venv` already exists.

```bash
cd project/ml_playground
```

- `cd` means “change directory.” There is no dash-flag here.

Then:

```bash
source .venv/bin/activate
```

**It worked when** the prompt starts with `(.venv)`.

This playground is pinned: **Python 3.14.6**, **numpy 2.5.2**, **scikit-learn 1.9.0**. The counts below are from that stack.

If a later plot lab has no window, you can still print tables:

```bash
export ML_HEADLESS=1
```

- `export` sets an environment variable for this terminal session.
- `ML_HEADLESS=1` skips the plot window. This split lab only prints text, so you do not need it tonight.

---

## Hands-on

### Step 1 — Run the split lab

Why this command now: it deals 80 packing rows into two piles with a frozen shuffle. If you skip it, “train vs test” stays a slogan.

```bash
python classic_labs.py split
```

`split` is a **lab name**, not a flag. The script’s `argparse` only accepts a short list (`split`, `leak`, `scale`, …). There is no `-` in this command.

**It worked when** the terminal prints exactly this (seed is frozen):

```text
train rows 60  test rows 20
Never tune on test. Test is the exam you take once.
 weight_kg  zone  hour  pack_minutes
      6.31     1    15         14.97
     10.03     4    20         25.12
     10.61     4    17         26.71
```

Read that table out loud once:

- 60 + 20 = 80. Nothing vanished.
- First train box: **6.31 kg**, zone 1, hour 15, stopwatch **14.97** minutes.
- Second: **10.03 kg**, zone 4, hour 20, **25.12** minutes.
- Third: **10.61 kg**, zone 4, hour 17, **26.71** minutes.

- [ ] You saw `train rows 60  test rows 20`
- [ ] You can point at the three printed train rows and say they are homework, not the exam

### Step 2 — Walk `lab_split` (do not paste blindly)

Open `classic_labs.py`. Find `lab_split`.

1. `packing_orders(80)` loads 80 fake-but-consistent boxes from `meridian_data.py` (same generator as ml-00, more rows).
2. `train_test_split(df, test_size=0.25, random_state=0)` shuffles, then cuts.
3. `print(f"train rows {len(tr)}  test rows {len(te)}")` is the 60 / 20 you just saw.
4. `tr.head(3)` prints the first three **train** rows after the shuffle — not “the first three boxes of the night.”

The call has **kwargs** (named settings), not dash-flags:

| Setting | What it does | Why it is here |
| --- | --- | --- |
| `test_size=0.25` | Hold out a quarter of the rows as test | 80 × 0.25 = 20 exam rows |
| `random_state=0` | Freeze the shuffle | Your 6.31 / 10.03 / 10.61 match this lesson |

There is no `-` in `python classic_labs.py split`. `test_size=0.25` lives **inside Python**, in `lab_split`.

Now open `meridian_data.py` and find `packing_orders`. Columns are `weight_kg`, `zone`, `hour`, `pack_minutes`. The hidden packing story is still:

```text
minutes ≈ 4 + 1.8 × weight + 0.6 × zone + a little noise
```

The split does **not** change that story. It only decides which boxes Maya’s recipe may study.

> **Tip:** `random_state=0` is not “the model is random.” It is “use shuffle recipe #0 so we can talk about the same 60 rows.”

> **Watch out:** `head(3)` is the first three rows **of the train pile**, in the order sklearn left them. They are not “the lightest three boxes.”

### Step 3 — Name the missing pile

This lab has two piles. Real work often has three.

Why now: the lesson title says val, and the script never prints it. You need to know where val would come from so you do not invent a third number from the 60/20 printout.

Typical later habit:

1. Split off test first (the exam). Lock it.
2. Split **train** again into fit-train and val (practice tests).
3. Fit on fit-train. Pick knobs using val. Score the locked test **once**.

Tonight you only do step 1. That is enough to stop cheating.

- [ ] You can say: val would be carved from the 60, not from the 20
- [ ] You did **not** print the test rows and start “just checking” them

---

## How it works (deeper)

sklearn’s `train_test_split` does not know packing. It:

1. Makes a list of row indexes `0 … 79`.
2. Shuffles that list with a tiny random generator seeded by `random_state=0`.
3. Puts the last 25% of shuffled indexes into test, the rest into train.
4. Returns two tables with the **same columns**, different rows.

```
indexes 0..79  →  shuffle with seed 0  →  60 train indexes + 20 test indexes
```

**Independence:** these packing rows are separate boxes. Shuffling is fair.

**Not independent:** a week of scan times in order. If you shuffle a time series, Tuesday can “study” Wednesday. This lab’s boxes are not a time series. Later, if you split tickets by time, you split by **date**, not by a random shuffle.

The sentence the script prints is the whole policy:

> Never tune on test. Test is the exam you take once.

**Tune** means: try another slope, another column, another `test_size` *because the exam looked ugly*. Changing `test_size` to make a nicer screenshot is also tuning on the exam. The stretch goal below is a **one-number experiment**, then you put 0.25 back.

---

## Common pitfalls

1. **`ModuleNotFoundError: numpy` (or sklearn).** The venv is not active. Prompt must show `(.venv)`. `source .venv/bin/activate` again. You do not reinstall packages.
2. **`No such file` / cannot import `meridian_data`.** You are not in `project/ml_playground`. `cd` there first. `cd` is not a flag.
3. **Counts are not 60/20.** You edited `test_size` or `packing_orders(80)` and forgot to put them back. Restore `test_size=0.25` and `n=80`.
4. **You printed `te.head()` “just to look.”** Looking once to understand a column name is fine. Picking a model because test looked better is cheating. This lab only prints train on purpose.
5. **You think val is the 20.** The 20 is **test**. Val is a practice pile you would cut from the 60.
6. **You shuffled a time-ordered log the same way.** These boxes are independent. A night of conveyor timestamps is not. Do not copy this shuffle onto a timeline without thinking.

---

## Knowledge check

Answer from the printout and the code you opened, not from a blog.

1. How many train rows and test rows did `python classic_labs.py split` print?
2. What are the three `weight_kg` values in the printed train head?
3. What does `test_size=0.25` mean on 80 rows? Is `-` involved in that command?
4. What does `random_state=0` freeze, and why do your kilos match 6.31 / 10.03 / 10.61?
5. Which pile may you fit on? Which pile is the exam? Where would **val** come from if you needed it?
6. The stopwatch on the 6.31 kg train box is 14.97 minutes. Is that number allowed into the recipe’s homework?

<details>
<summary>Answers</summary>

1. `train rows 60  test rows 20`.
2. 6.31, 10.03, 10.61.
3. Hold out a quarter: 20 test rows, 60 train. There is no `-` in `python classic_labs.py split`. `test_size=0.25` is a Python kwarg inside `lab_split`.
4. The shuffle. Same seed → same 60/20 and the same first three train rows.
5. Fit on train (60). Exam is test (20). Val would be carved from the 60, then locked away from the final exam.
6. Yes. That row is in **train**. The 20 test stopwatches are the ones you must not use to pick knobs.

</details>

---

## Recap

- **You built** a frozen 60/20 split of Maya’s packing table.
- **You understand** train = homework, val = practice tests, test = exam once.
- **Next** you will see a model cheat by stuffing the answer into a column.

Next: `ml-07-leakage`

---

## Stretch goal

In `lab_split`, change **one number**: `test_size=0.25` → `test_size=0.5`. Save. Rerun:

```bash
python classic_labs.py split
```

- **Expect:** `train rows 40  test rows 40`. The three head rows **change** because the cut moved.
- Put `test_size=0.25` back so the rest of this track still matches 60/20.

- [ ] You changed one number, reran, saw 40/40
- [ ] You put `0.25` back

---

## Feedback

Could you redo this lab from memory? Note the **lesson id** (`ml-06`), the **step number**, what you **expected**, and what you **saw** (traceback or table).

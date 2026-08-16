# ml-07 — Leakage

**Level:** Absolute beginner  
**Time:** ~45 minutes  
**Prerequisites:** ml-06  
**Lab outcome:** You see a fake 1.000 test accuracy from an answer-sheet column, then an honest 0.817, and you can name why the first score is a lie

---

## At a glance

**Leakage** is when the recipe sees information that would not exist at guess-time.

Tonight’s loud example: a column named `refund_already_paid` that is a copy of the label `became_refund`. The model is reading the ledger after the fact.

By the end you can explain:

- why **1.000** accuracy can be a cheat, not a triumph
- the question Maya asks before keeping a column: “Would I have this field *before* the outcome?”
- why the honest model’s **0.817** is the number you would take to a standup

---

## Why this matters

Meridian finance could “prove” a refund predictor that is just reading “we already paid.” Then it fails on new tickets, where that flag is still false.

If you skip this lab, every later high score looks like virtue. After this, you ask *what the recipe was allowed to see*.

---

## Concept primer

| Word | Plain English | Warehouse |
| --- | --- | --- |
| **Label** | The thing you are guessing | `became_refund` (0 or 1) |
| **Feature** | A fact at guess-time | delay, price, angry-word count |
| **Leak** | A feature that *is* the label in costume | `refund_already_paid` |
| **Accuracy** | Fraction of labels you got right | `1.000` leaky vs `0.817` honest |

Accuracy is not virtue if the feature is the answer sheet.

```
honest guess-time:  delay, price, angry words  →  will this become a refund?
leaky cheat:        those  +  already_paid     →  already_paid is the outcome
```

> **Tip:** Ask: “Would Maya have this field *before* the outcome?” If no, drop it.

> **Watch out:** Leakage can be subtle (using post-refund notes as input). This lab is the loud version on purpose.

---

## Setup

If `(.venv)` is missing, finish ml-00 Setup.

```bash
cd project/ml_playground
source .venv/bin/activate
```

- `source` turns on this folder’s Python island for *this* terminal.

---

## Hands-on

### Step 1 — Run the leak lab

Why now: you need to *feel* a perfect score that is a lie, next to an honest score.

```bash
python classic_labs.py leak
```

`leak` is a lab name, not a dash-flag.

**It worked when** you see:

```text
LEAKY (includes refund_already_paid)     test acc 1.000
honest                                   test acc 0.817
Leaky accuracy is a lie. The paid flag is the answer sheet.
```

- **1.000** = the cheater never missed on the held-out rows.
- **0.817** = delay + price + angry words, no answer sheet. Still useful. Not magic.

### Step 2 — Walk `lab_leak`

Open `classic_labs.py`. Find `lab_leak`.

- `tickets(200, leak=True)` vs `tickets(200, leak=False)`.
- Leaky column list: `delay_days`, `price_usd`, `angry_words`, **`refund_already_paid`**.
- Honest list: the first three only.
- Same `LogisticRegression`, same `train_test_split(..., test_size=0.3, random_state=1)`.
- `test_size=0.3` means 30% of rows are the exam. `random_state=1` freezes the shuffle so your 1.000 / 0.817 match this lesson.

### Step 3 — Walk the data lie

Open `meridian_data.py`. Find `tickets`.

```text
refund = (delay > 4.5) or (angry_words > 6) or (price > 140)
  plus 8% random flips
paid_already = refund.copy()   # same 0/1 list
if leak: add column refund_already_paid = paid_already
```

The paid flag **is** the label. The model does not “understand refunds.” It copies a column.

- [ ] You ran the command and saw 1.000 vs 0.817
- [ ] You found `paid_already = refund.copy()` in `meridian_data.py`
- [ ] You can say the Maya question about guess-time fields

### Step 4 — Mini experiment

In `lab_leak`, temporarily drop `angry_words` from the **honest** list only. Save. Rerun.

- **Expect:** honest accuracy moves (often a little worse). Leaky stays **1.000**. The cheat does not need angry words.
- Put `angry_words` back.

---

## How it works (deeper)

Logistic regression (ml-14) finds knobs that separate 0 vs 1. If one column *equals* the label, the easiest knob is “copy that column.” Test accuracy of 1.0 is the model proving it found the cheat, not that it learned delay.

Production leaks look like:

- using “refund completed at” to predict “will refund”
- using tomorrow’s scan to predict today’s ETA

Same disease. Quieter names.

---

## Common pitfalls

1. **You celebrated 1.000.** That is the bug. The print says it is a lie.
2. **You thought 0.817 was “broken.”** It is the honest warehouse tool on this toy set.
3. **Wrong folder / no venv.** `cd project/ml_playground` and `source .venv/bin/activate`.

---

## Knowledge check

1. Why is `refund_already_paid` illegal here?
2. What two test accuracies did the lab print?
3. Does higher accuracy always mean a better warehouse tool?
4. What question do you ask before keeping a column?

<details>
<summary>Answers</summary>

1. It is the outcome wearing a costume (`paid_already = refund.copy()`).
2. Leaky **1.000**, honest **0.817**.
3. No. It can mean you cheated.
4. “Would Maya have this field *before* the outcome?”

</details>

---

## Recap

- **You broke** a model on purpose and watched accuracy hit 1.000.
- **You understand** leakage as guess-time cheating.
- **Next** scaling, because raw plots also lie.

Next: `ml-08-scaling-lying-plots`

---

## Stretch goal

In `meridian_data.py`, change the leak column to `paid_already * 0` (all zeros) inside the `if leak:` branch, rerun `python classic_labs.py leak`, then revert.

- **Expect:** leaky accuracy collapses toward the honest number — the cheat column died.

---

## Feedback

Could you redo this lab from memory? Note **ml-07**, what you expected (1.000 vs 0.817), and what you saw.

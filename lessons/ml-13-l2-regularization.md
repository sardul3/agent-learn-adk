# ml-13 — L2 regularization (Ridge shrinks knobs)

**Level:** Absolute beginner  
**Time:** ~45 minutes  
**Prerequisites:** ml-11 (three packing knobs); ml-09 (floppy recipes)  
**Lab outcome:** You watch Ridge weights move from `[1.791 0.571 0.035]` at alpha 0, to `[1.789 0.567 0.035]` at alpha 1, to `[1.702 0.418 0.022]` at alpha 50

---

## At a glance

**Regularization** is a penalty for **large knobs**. The fitter still wants small packing error, but it also pays a fine for trusting any one column too hard.

**Ridge** is linear regression plus an **L2** fine: extra cost from (knob₁² + knob₂² + …). **`alpha`** is how expensive that fine is.

- `alpha=0` → almost “just fit the line” (weights **`[1.791  0.571  0.035]`**)
- `alpha=1` → a tiny shrink (**`[1.789  0.567  0.035]`**)
- `alpha=50` → a real shrink (**`[1.702  0.418  0.022]`**)

Order of columns is `weight_kg`, `zone`, `hour` — same as ml-11.

---

## Why this matters

Meet **Maya** at Meridian. Hour barely belongs in the packing story. A floppy recipe can still park a small fake hour knob on **this** sample of 80 boxes. Turning `alpha` up **shrinks** that knob toward 0 (0.035 → 0.022) and also tugs zone (0.571 → 0.418).

That is the sentence the lab prints:

> Bigger alpha = shrink weights toward 0 = “I refuse giant trust in one column.”

If you skip this lab, later “weight decay” in neural nets is a new religion instead of the same fine.

---

## Concept primer

| Word | Plain English | Tonight |
| --- | --- | --- |
| **Ridge** | Line-fitting + L2 penalty | `sklearn.linear_model.Ridge` |
| **L2** | Fine based on sum of **squares** of knobs | Large knobs hurt more than small ones |
| **`alpha`** | How heavy that fine is | 0, 1, 50 in the loop |
| **Shrink** | Knobs move toward 0 | Hour 0.035 → 0.022 at alpha 50 |
| **OLS** | Ordinary least squares (no fine) | Roughly alpha 0 |

```
fit quality   +   alpha × (w_weight² + w_zone² + w_hour²)
     ↑                      ↑
  want this small     want this small too
```

> **Tip:** Alpha 1 barely moves these three knobs. Alpha 50 is the panel where you **see** shrink. That is why the lab includes 50, not only 0.1.

> **Watch out:** This lab fits on **all 80 rows** and prints knobs only — no test MSE. It is a microscope on shrink, not a claim that alpha 50 wins tonight’s vans.

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

Pinned: **Python 3.14.6**, **numpy 2.5.2**, **scikit-learn 1.9.0**. The three weight vectors below are from that stack.

This lab prints text only. No plot.

---

## Hands-on

### Step 1 — Run the Ridge lab

Why this command now: three alphas, three vectors. If you skip it, “shrink” stays a verb without numbers.

```bash
python classic_labs.py ridge
```

`ridge` is a **lab name**, not a flag. There is no `-` in this command.

**It worked when** stdout is:

```text
alpha=  0.0  weights [1.791 0.571 0.035]
alpha=  1.0  weights [1.789 0.567 0.035]
alpha= 50.0  weights [1.702 0.418 0.022]
Bigger alpha = shrink weights toward 0 = 'I refuse giant trust in one column.'
```

Read the columns as **weight_kg, zone, hour**:

| alpha | weight_kg | zone | hour |
| --- | --- | --- | --- |
| 0 | 1.791 | 0.571 | 0.035 |
| 1 | 1.789 | 0.567 | 0.035 |
| 50 | 1.702 | 0.418 | 0.022 |

- [ ] You saw hour drop from **0.035** to **0.022** at alpha 50
- [ ] You saw zone drop more than weight (0.571 → 0.418 vs 1.791 → 1.702)

### Step 2 — Walk `lab_ridge`

Open `classic_labs.py`. Find `lab_ridge`.

1. `packing_orders(80)` — same table as ml-11.
2. `X = df[["weight_kg", "zone", "hour"]]`, `y = df["pack_minutes"]`.
3. Loop `for a in (0.0, 1.0, 50.0)`:
   - `Ridge(alpha=a).fit(X, y)` on **all 80 rows**
   - print `np.round(m.coef_, 3)`

| Setting | What it does | Why |
| --- | --- | --- |
| `alpha=a` | Strength of the L2 fine | 0 = almost no fine; 50 = heavy fine |
| Fit on all 80 | No split | Picture of shrink, not an exam |

Compare to ml-11’s `LinearRegression` on a **60-row train split**: those knobs were `1.792, 0.583, 0.052`. Ridge at alpha 0 on **80 rows** is `1.791, 0.571, 0.035`. Same family, different pile. Do not panic that 0.052 ≠ 0.035.

> **Tip:** `alpha` is a **kwarg** inside `Ridge(...)`, not a CLI flag. There is still no `-` in `python classic_labs.py ridge`.

> **Watch out:** Ridge does not delete hour. It **shrinks** hour. 0.022 is still not “the generator uses hour.” It is “a fined fit on this sample.”

### Step 3 — Why zone shrinks more than weight

L2 fines **large** knobs, but sklearn’s Ridge also depends on **column scale**. Zone is 1–4. Weight is ~0.4–12. Hour is 6–21. Without StandardScaler (ml-08), “1 unit of hour” is a clock hour, not a kilo.

You do **not** need to derive the penalty calculus tonight. You **do** need this observation from the printout:

- The **useful** knob (weight ~1.8) stays in the 1.7s even at alpha 50.
- The **medium** knob (zone ~0.6) takes a bigger **relative** hit (0.571 → 0.418).
- The **tiny** knob (hour) gets closer to 0 (0.035 → 0.022).

Maya’s takeaway: bigger alpha = more “I do not fully trust extra columns,” not “delete packing physics.”

- [ ] You can describe the three-row table without saying “the AI got more cautious” as if it had feelings

---

## How it works (deeper)

Ordinary least squares (ml-10/ml-11): minimize MSE only.

Ridge: minimize MSE **plus** `alpha × (sum of squared knobs)`. (sklearn’s exact scaling of that sum is a library detail; the **direction** is shrink toward 0.)

**Why squares?** A knob of 10 costs 100; a knob of 1 costs 1. Big trust is expensive.

**Why not always alpha 50?** Too much shrink **underfits** (ml-09 left panel): even the real 1.8 gets dragged (1.791 → 1.702). Pick alpha on **val** (ml-06), never by staring until test looks pretty.

**L2 vs L1 (names only):** L1 (Lasso) uses absolute values and can drive some knobs to **exactly 0**. This lab is L2 / Ridge. Do not swap the names on a quiz.

**Neural nets later:** “weight decay” is the same idea on a pile of knobs.

---

## Common pitfalls

1. **`ModuleNotFoundError`.** Venv off. `source .venv/bin/activate`.
2. **Wrong folder.** `cd project/ml_playground`. `cd` is not a flag.
3. **You say alpha 0 is “no model.”** It is Ridge with no penalty — knobs **`[1.791 0.571 0.035]`**.
4. **You pick alpha 50 because hour got smaller and that felt virtuous.** Weight and zone also moved. Virtue is val MSE, not a smaller hour.
5. **You mix these knobs with ml-11’s split knobs in one table without saying “80 rows vs 60 train.”** Different piles.
6. **You think Ridge scaled the columns for you.** It did not. ml-08’s scaler is a separate object. This lab passes raw kilos, zone, hour.

---

## Knowledge check

Answer from the printout and `lab_ridge`.

1. What three weight vectors did alpha 0, 1, and 50 print?
2. Which column is the third number in each vector?
3. Does this lab split train/test?
4. What does bigger `alpha` do to knobs, in the lab’s own sentence?
5. How does Ridge at alpha 0 on 80 rows differ from ml-11’s LinearRegression knobs (1.792, 0.583, 0.052)?
6. If you set alpha huge, what ml-09 personality do you risk?

<details>
<summary>Answers</summary>

1. `[1.791 0.571 0.035]`, `[1.789 0.567 0.035]`, `[1.702 0.418 0.022]`.
2. `hour`.
3. No. `.fit(X, y)` on all 80 rows.
4. Shrink weights toward 0; refuse giant trust in one column.
5. ml-11 used 60 train rows and OLS; this used 80 rows and Ridge. Close, not identical.
6. High bias / too stiff — even the real ~1.8 weight knob gets dragged down.

</details>

---

## Recap

- **You built** a three-alpha Ridge printout on packing columns.
- **You understand** L2 = a fine on big knobs; `alpha` is the fine’s volume knob.
- **Next** you switch from minutes to “will this ticket refund?” with a squash into 0–1.

Next: `ml-14-logistic-squash`

---

## Stretch goal

In `lab_ridge`, change **one number**: `50.0` → `500.0` in the tuple `(0.0, 1.0, 50.0)`. Save. Rerun:

```bash
python classic_labs.py ridge
```

- **Expect:** the last vector **shrinks further** than `[1.702 0.418 0.022]` — weight well below 1.7, hour even closer to 0.
- Put `50.0` back so this lesson’s table matches.

- [ ] You changed 50 to 500, saw extra shrink
- [ ] You put `50.0` back

---

## Feedback

Could you redo this lab from memory? Note the **lesson id** (`ml-13`), the **step number**, what you **expected**, and what you **saw** (traceback or weight vectors).

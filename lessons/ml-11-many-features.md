# ml-11 — Many features (weight, zone, hour)

**Level:** Absolute beginner  
**Time:** ~50 minutes  
**Prerequisites:** ml-10 (one-feature line and test MSE)  
**Lab outcome:** You read weights `weight_kg 1.792`, `zone 0.583`, `hour 0.052`, intercept `3.347`, test MSE ~`0.443`, and you can say hour is almost unused

---

## At a glance

**Multiple linear regression** is still a line, just in more directions:

```text
minutes ≈ b + (w_weight × weight) + (w_zone × zone) + (w_hour × hour)
```

Each **weight** (the knob — yes, the word collides with kilograms) is “how many extra minutes if this column goes up by 1, holding the others still.”

Tonight’s print:

```text
weights {'weight_kg': 1.792, 'zone': 0.583, 'hour': 0.052} b 3.347
test MSE 0.44318888714445165
```

Hidden truth in `packing_orders`: `4 + 1.8*weight + 0.6*zone + noise`. **Hour is not in the truth.** The fitted hour knob **0.052** is leftover noise, not “the model discovered night shift.”

The **residual** plot (leftover error vs prediction) should look like a **cloud**, not a **banana**.

---

## Why this matters

Meet **Maya** at Meridian. Zone 4 is farther from the wrap station than zone 1. A weight-only line stuffed that into b (ml-10). Tonight she is allowed to use zone. Test MSE drops from **0.799** to about **0.443**.

Hour is on the table because it *prints* on every row. Printing is not the same as **causing** pack time. This lab is how you see a near-zero knob and leave the column (or drop it) with eyes open.

If you skip this lab, you will call every extra column “more AI context.”

---

## Concept primer

| Word | Plain English | Tonight |
| --- | --- | --- |
| **Feature** | An input column | weight_kg, zone, hour |
| **Coefficient / knob** | Minutes per +1 of that column | 1.792, 0.583, 0.052 |
| **Intercept b** | Baseline minutes when all inputs are 0 | 3.347 |
| **Residual** | truth − prediction | Vertical leftover on each test box |
| **Residual plot** | Residuals vs predicted minutes | Want a shapeless cloud |
| **Banana** | Residuals curve as predictions grow | Recipe is missing a bend (ml-12) |

```
ml-10:  minutes ≈ 5.409 + 1.828 × weight              test MSE 0.799
ml-11:  minutes ≈ 3.347 + 1.792 × weight
                  + 0.583 × zone + 0.052 × hour       test MSE ~0.443
truth:  minutes ≈ 4     + 1.8   × weight + 0.6 × zone + noise
```

> **Tip:** 1.792 vs hidden 1.8, 0.583 vs hidden 0.6 — close on 60 noisy boxes. That is success, not a rounding failure.

> **Watch out:** `hour 0.052` is **not** “hour matters 5%.” It is minutes per extra clock hour, tiny next to 1.792 per kilo.

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

A residual plot should open. Close it to get the terminal back.

---

## Hands-on

### Step 1 — Run the many-feature lab

Why this command now: it fits three knobs, prints them, and shows leftovers. If you skip the plot, “cloud vs banana” stays a metaphor.

```bash
python classic_labs.py regmany
```

`regmany` is a **lab name**, not a flag. There is no `-` in this command.

**It worked when** stdout is:

```text
weights {'weight_kg': np.float64(1.792), 'zone': np.float64(0.583), 'hour': np.float64(0.052)} b 3.347
test MSE 0.44318888714445165
```

(`np.float64(...)` is numpy’s way of wrapping the same numbers. Read them as 1.792, 0.583, 0.052.)

And a window titled **`ml-11: leftover error should look like a cloud, not a banana`**.

- x-axis: predicted minutes on **test**
- y-axis: residual = truth − pred
- a horizontal black line at 0 (perfect leftover)

**Cloud:** dots sprinkled above and below 0, no smile/frown curve. **Banana:** a systematic bend — the line family cannot draw the real shape.

- [ ] You wrote down 1.792 / 0.583 / 0.052 / b 3.347 / test MSE ~0.443
- [ ] You judged the scatter: cloud, not banana

### Step 2 — Walk `lab_reg_many`

Open `classic_labs.py`. Find `lab_reg_many`.

1. `packing_orders(80)` — same generator as ml-10.
2. `X = df[["weight_kg", "zone", "hour"]]` — three feature columns.
3. `y = df["pack_minutes"]`.
4. `train_test_split(..., test_size=0.25, random_state=0)` — same 60/20 freeze as ml-10, so MSE is comparable.
5. `LinearRegression().fit(Xtr, ytr)` — now `coef_` has **three** numbers.
6. `dict(zip(X.columns, np.round(m.coef_, 3)))` — names glued to rounded knobs.
7. `mean_squared_error(yte, m.predict(Xte))` — ~0.443.
8. `resid = yte - m.predict(Xte)` then scatter predictions vs residuals.

| Setting | What it does | Why |
| --- | --- | --- |
| `test_size=0.25` | Hold out 20 boxes | Exam score |
| `random_state=0` | Same shuffle as ml-10 | Fair MSE comparison to 0.799 |
| `np.round(..., 3)` | Three decimal places | So the dict is readable |

> **Tip:** Test MSE **fell** (0.799 → 0.443) when zone was allowed. That is the missing-feature story from ml-00, with a number.

> **Watch out:** The x-axis label says `predicted hours-ish minutes` — packing time is still **minutes**. The word “hours-ish” is a sloppy axis title, not a unit change.

### Step 3 — Walk the hidden formula

Open `meridian_data.py`. Find `packing_orders`:

```text
minutes = 4.0 + 1.8 * weight_kg + 0.6 * zone + rng.normal(0, 0.8, size=n)
```

Hour is sampled (`rng.integers(6, 22)`) and **never added** into minutes.

So:

- weight knob should land near **1.8** → you got **1.792**
- zone knob should land near **0.6** → you got **0.583**
- hour knob should land near **0** → you got **0.052**
- intercept should land near **4** → you got **3.347** (noise + 60-row sample; close enough to “about 4”)

- [ ] You matched each fitted knob to the hidden line, including “hour ≈ 0”

### Step 4 — Read one residual

Residual = stopwatch − guess.

- Residual **+1** = the line was 1 minute **early** (truth bigger).
- Residual **−1** = the line was 1 minute **late**.

If residuals grow as predictions grow (a banana), a straight mix of columns is not enough — you would consider a bend (ml-12). Tonight they should not.

- [ ] You can explain the sign of a residual in Maya words

---

## How it works (deeper)

`.fit` still minimizes MSE. With three columns it solves for four numbers (three slopes + b).

**“Holding others still”** is the meaning of a coefficient in this linear recipe. It is not a warehouse experiment where Maya actually holds zone fixed. If weight and hour moved together in the table, knobs can steal credit from each other. Here hour is independent noise, so it cannot steal much — hence 0.052.

**Why not zero hour exactly?** 60 train rows, noise std 0.8 minutes. A small fake slope can reduce *this* sample’s MSE a hair. Test still pays ~0.443, mostly from the 0.8 noise (you cannot predict noise).

**Cloud vs banana:** if truth were `weight²` and you only fit `weight`, residuals would curve. Polynomial features (next lesson) add those powers on purpose.

---

## Common pitfalls

1. **`ModuleNotFoundError`.** Venv off. `source .venv/bin/activate`.
2. **Wrong folder.** `cd project/ml_playground`. `cd` is not a flag.
3. **Plot never opens.** `unset ML_HEADLESS` on a laptop.
4. **You call hour “important” because it is in the dict.** Read the **0.052**, not the key name.
5. **You compare 0.443 to 0.799 without saying both are test MSE on the same split recipe.** That comparison is the point — keep the split frozen (`random_state=0`).
6. **You treat b=3.347 as a packing time for a 0 kg box in zone 0.** Zone 0 does not exist (zones are 1–4). Intercept is an offset that makes the equation work, not a real SKU.

---

## Knowledge check

Answer from the printout, the plot, and `packing_orders`.

1. What three knobs and intercept did the lab print?
2. What test MSE (about) did it print? What was ml-10’s test MSE on the weight-only line?
3. Write the hidden minutes formula from `packing_orders`. Which fitted knob should be near zero, and what value did you get?
4. Residual is defined as what minus what in `lab_reg_many`?
5. What should the residual scatter look like tonight — cloud or banana — and what would a banana mean?
6. In one sentence, why did adding zone drop MSE?

<details>
<summary>Answers</summary>

1. weight_kg **1.792**, zone **0.583**, hour **0.052**, b **3.347**.
2. About **0.443**. ml-10 was **0.799**.
3. `4 + 1.8*weight + 0.6*zone + noise`. Hour should be near 0; fitted **0.052**.
4. `yte - m.predict(Xte)` → truth minus prediction.
5. Cloud. A banana would mean leftover curve the linear mix cannot draw.
6. The stopwatch really uses zone; the weight-only line had to ignore it.

</details>

---

## Recap

- **You built** a three-feature packing line and a residual cloud.
- **You understand** extra columns get knobs; a tiny knob can mean “almost unused.”
- **Next** you will let the line bend with extra powers of weight.

Next: `ml-12-polynomial-bend`

---

## Stretch goal

In `lab_reg_many`, change **one list**: `["weight_kg", "zone", "hour"]` → `["weight_kg", "zone"]` (drop hour). Save. Rerun:

```bash
python classic_labs.py regmany
```

- **Expect:** test MSE stays **near 0.443** (hour was not doing real work). Knobs for weight/zone stay near 1.8 / 0.6. The print will not show hour.
- Put `"hour"` back so the lesson’s dict still has three keys.

- [ ] You dropped hour, saw MSE barely move
- [ ] You put the three-column list back

---

## Feedback

Could you redo this lab from memory? Note the **lesson id** (`ml-11`), the **step number**, what you **expected**, and what you **saw** (traceback, knobs, or plot).

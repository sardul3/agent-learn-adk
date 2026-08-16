# ml-12 — Polynomial bend (degree 1 vs 4)

**Level:** Absolute beginner  
**Time:** ~45 minutes  
**Prerequisites:** ml-09 (stiff vs floppy); ml-10 (linear regression)  
**Lab outcome:** You overlay a straight degree-1 fit and a degree-4 bend on the same packing scatter, and you know extra powers can wiggle

---

## At a glance

A **polynomial feature** is a new column you **made from an old one**: weight², weight³, … The recipe is still linear **in the knobs** (sklearn still calls `LinearRegression`). The curve can **bend** in weight.

Tonight: **degree 1** vs **degree 4** on `weight_kg` → `pack_minutes`. Same 80 dots. Two orange-ish lines on one plot.

sklearn 1.9.0 may warn that the smooth grid has no feature names. **Ignore it for the picture.** The scatter still draws.

---

## Why this matters

Meet **Maya** at Meridian. If packing time rose like a hockey stick above 8 kg, a straight line would leave a **banana** of residuals (ml-11). Extra powers are one way to allow a bend.

The hidden packing truth is still **almost a straight line in weight** (plus zone). Degree 4 can still **wiggle** to chase noise — the right-hand personality from ml-09, now on warehouse dots.

If you skip this lab, “polynomial” sounds like a school poster instead of “we added weight² as a column.”

---

## Concept primer

| Word | Plain English | Tonight |
| --- | --- | --- |
| **Degree 1** | Just weight | A straight line |
| **Degree 4** | weight, weight², weight³, weight⁴ | A curve that can bend three extra ways |
| **`PolynomialFeatures`** | sklearn helper that builds those columns | `include_bias=False` because `LinearRegression` already has b |
| **`include_bias`** | Whether to add a column of 1s | False here — avoid two intercepts |
| **Wiggle** | Curve that chases individual dots | Degree 4 on a nearly-linear truth |
| **Feature names warning** | Grid is a raw numpy array; fit saw a pandas name | Harmless for this plot |

```
degree 1:  minutes ≈ b + m1 × weight
degree 4:  minutes ≈ b + m1 × weight + m2 × weight² + m3 × weight³ + m4 × weight⁴
```

> **Tip:** “Linear regression on polynomial features” is still linear in the **knobs** m1…m4. The bend lives in the **columns**, not in a new species of model.

> **Watch out:** More degree is not more truth. The packing generator is linear in weight. Degree 4 is a demonstration of bend, not a recommendation for Maya’s dashboard.

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

### Step 1 — Run the poly lab

Why this command now: the comparison is visual. Stdout may only be a sklearn warning.

```bash
python classic_labs.py poly
```

`poly` is a **lab name**, not a flag. There is no `-` in this command.

**It worked when** a window opens titled **`ml-12: extra powers let the line bend — too far and it wiggles`**.

You should see:

- a scatter of 80 packing dots (weight vs minutes)
- a **degree 1** curve (straight)
- a **degree 4** curve (allowed to bend)
- a legend with those two labels

You may also see this **twice** in the terminal (sklearn 1.9.0):

```text
UserWarning: X does not have valid feature names, but PolynomialFeatures was fitted with feature names
```

**What it means:** `.fit` saw a pandas column named `weight_kg`. The smooth grid `xs` is a numpy array with no name. sklearn 1.9.0 nags. **Ignore it for the picture.** Do not “fix” it by silencing all warnings globally.

Close the window after you can say whether degree 4 stayed calm or started to snake.

- [ ] You saw both curves on the same dots
- [ ] You treated the feature-name warning as noise, not a failed lab

### Step 2 — Walk `lab_poly`

Open `classic_labs.py`. Find `lab_poly`.

1. `packing_orders(80)` — same boxes as ml-10.
2. `x = df[["weight_kg"]]`, `y = df["pack_minutes"]`.
3. `ax.scatter(x, y, s=14, alpha=0.5)` — all 80 dots (`s` = marker size, `alpha` = transparency).
4. `xs = np.linspace(min weight, max weight, 50).reshape(-1, 1)` — 50 x-values for a smooth curve, shaped as a column so sklearn is happy.
5. Loop `for d in (1, 4)`:
   - `PolynomialFeatures(d, include_bias=False)` builds powers up to d
   - `LinearRegression().fit(pf.fit_transform(x), y)` fits on **all 80 rows** (no train/test in this picture)
   - `ax.plot(xs, m.predict(pf.transform(xs)), label=f"degree {d}")`

| Setting | What it does | Why |
| --- | --- | --- |
| `d` in `(1, 4)` | Highest power | Straight vs bendy |
| `include_bias=False` | Do not add a column of ones | `LinearRegression` already has intercept |
| `reshape(-1, 1)` | Make a column vector | sklearn expects 2-D `X` |
| 50 grid points | Smooth line | 80 raw dots would make a jagged plot |

**No split.** This lab is a picture, like ml-09. It can overfit the same 80 dots it draws. Do not quote these curves as test performance.

> **Tip:** `pf.fit_transform(x)` on train-like data learns “which powers.” `pf.transform(xs)` applies the same powers to the grid. You must use the **same** `pf` object for both.

> **Watch out:** Fitting degree 4 on all 80 rows then admiring how it hugs the cloud is the ml-09 right panel in warehouse clothing. ml-06 still applies when you score for real.

### Step 3 — Why packing barely needs degree 4

Hidden formula (again):

```text
minutes ≈ 4 + 1.8 × weight + 0.6 × zone + noise
```

Versus weight, the truth is a **line plus scatter from zone and noise**. Degree 1 is already the right *shape* in weight. Degree 4 spends extra knobs on that scatter.

If the right-hand curve **wiggles** at the left or right edge (few boxes at extreme kilos), that is variance: lots of power, few dots to pin it down.

- [ ] You can say “the generator is linear in weight; degree 4 is extra flexibility”

---

## How it works (deeper)

`PolynomialFeatures(4, include_bias=False)` turns one column into four:

```text
[weight]  →  [weight, weight², weight³, weight⁴]
```

Then ordinary least squares finds m1…m4 and b. Nothing “nonlinear” happens inside `.fit` except the columns you built.

**Why a warning on `xs`:** pandas `x` carried the name `weight_kg`. numpy `xs` did not. sklearn 1.9.0 checks that. The math on the grid is still “powers of the same number.”

**Link to ml-09:** degree 1 ≈ left panel (stiff). Degree 4 ≈ a milder right panel. Packing is not a sine wave, so the drama is smaller — look at the **ends** of the weight range.

**Link to ml-13:** instead of (or besides) picking degree, you can **shrink** large knobs (Ridge). Floppy powers get fined.

---

## Common pitfalls

1. **Plot never opens.** `unset ML_HEADLESS` on a laptop. This lab has no useful stdout besides a warning.
2. **`ModuleNotFoundError`.** Venv off. `source .venv/bin/activate`.
3. **Wrong folder.** `cd project/ml_playground`. `cd` is not a flag.
4. **You treat the feature-name warning as a crash.** It is not. The figure still opens.
5. **You fit degree 4 and ship it because it looks fancy.** The truth is linear in weight. Fancy is not accuracy on tonight’s vans.
6. **You add `include_bias=True` and also `LinearRegression` intercept.** Two intercepts. Leave the lab’s `False` unless you know you turned intercept off.

---

## Knowledge check

Answer from the figure and `lab_poly`.

1. Which two degrees does the loop draw?
2. Does this lab print a test MSE? What does it use all 80 rows for?
3. What does `PolynomialFeatures(d, include_bias=False)` add, and why `False`?
4. What warning might sklearn 1.9.0 print, and what should you do about it for this picture?
5. Is the hidden packing time a high-degree curve in weight, or a line plus zone noise?
6. What does `reshape(-1, 1)` do to the 50 grid points?

<details>
<summary>Answers</summary>

1. 1 and 4.
2. No test MSE. All 80 rows are for the scatter and both fits (a picture, not an exam).
3. Powers of weight up to d, without a column of 1s, because LinearRegression already has b.
4. Feature names on the numpy grid. Ignore it for the picture.
5. A line in weight (`1.8 * weight`) plus zone and noise.
6. Turns a 1-D list of 50 numbers into a column with 50 rows and 1 column.

</details>

---

## Recap

- **You built** a degree-1 vs degree-4 overlay on packing dots.
- **You understand** extra powers = extra columns; they can bend and they can wiggle.
- **Next** you will shrink knobs with Ridge (`alpha`) instead of adding powers.

Next: `ml-13-l2-regularization`

---

## Stretch goal

In `lab_poly`, change **one number**: the tuple `(1, 4)` → `(1, 12)`. Save. Rerun:

```bash
python classic_labs.py poly
```

- **Expect:** the high-degree curve **wiggles more**, especially at the left/right of the weight range. Feature-name warning may still appear twice (two `predict` calls — now still two curves).
- Put `(1, 4)` back so this lesson’s figure matches.

- [ ] You changed 4 to 12, saw extra wiggle
- [ ] You put `4` back

---

## Feedback

Could you redo this lab from memory? Note the **lesson id** (`ml-12`), the **step number**, what you **expected**, and what you **saw** (warning, traceback, or plot).

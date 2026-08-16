# ml-08 — Scaling and lying plots

**Level:** Absolute beginner  
**Time:** ~45 minutes  
**Prerequisites:** ml-07  
**Lab outcome:** You scale weight and hour to mean 0 / std 1, and you can say why a raw scatter makes hour look more “important” than kilos

---

## At a glance

**Scaling** puts columns on a similar numeric range. A common recipe: subtract the mean, divide by the standard deviation (**std**). After that, both columns have std ≈ 1.

Plots with unmatched axes lie to your eye. Hour (6–21) dwarfs weight (0.4–12 kg) even when Maya does not think hour is “more real.”

By the end you can explain:

- what **std 1** means in words
- why a **dot-product** model treats 21 as a bigger shove than 8 unless you scale
- why you must fit the scaler on **train** in real work (this lab shows the picture on all 80 rows)

---

## Why this matters

Dot-product models (ml-03, later nets) treat big numbers as big shoves. 21 hours looks like a harder punch than 8 kg. Maya does not think hour is 3× more real.

If you skip this, later knobs will silently worship the column with the largest raw range.

---

## Concept primer

| Word | Plain English | Tonight |
| --- | --- | --- |
| **Std (standard deviation)** | Typical distance from the average | Raw hour std ≈ 4.81; weight ≈ 3.35 |
| **Standard score** | `(value − mean) / std` | After: both std ≈ 1 |
| **Scaler** | The object that remembers mean and std | sklearn `StandardScaler` |

```
raw:     weight ~ few kg     hour ~ teens
scaled:  both dance around 0 with typical size 1
```

> **Tip:** Trees care less about scale (they ask “is delay > 4.5?”). Lines and neural nets care a lot.

> **Watch out:** Never scale using the **test** set’s mean. That peeks at the exam’s average.

---

## Setup

```bash
cd project/ml_playground
source .venv/bin/activate
```

---

## Hands-on

### Step 1 — Run the two-panel plot

Why now: the lie is visual. The printout is the receipt.

```bash
python classic_labs.py scale
```

**It worked when** two scatters open (`raw (hour dwarfs weight)` vs `scaled`) and the terminal prints:

```text
raw hour std 4.814545020040834 weight std 3.350756796512543
after scale, both columns std ≈ [1. 1.]
```

Left plot: hour stretches the vertical axis. Right plot: a rounder cloud — both axes speak the same numeric language.

### Step 2 — Walk `lab_scale`

Open `classic_labs.py`. Find `lab_scale`.

- Features: `weight_kg` and `hour` from 80 packing orders.
- `StandardScaler().fit_transform(X)` — compute mean/std, then transform.
- Two `scatter` panels. Title tells you the lesson: plots that stretch axes lie about importance.

**Honest limitation of this lab:** it fits the scaler on **all 80 rows** so the picture is simple. In real work you `.fit` on **train only**, then `.transform` train and test. Fitting on all rows leaks test scale (ml-06 + ml-07 thinking).

### Step 3 — Mini experiment

In `lab_scale`, print the means before and after:

```python
print("raw mean", X.mean(axis=0), "scaled mean", Xs.mean(axis=0))
```

Rerun.

- **Expect:** scaled means ≈ `[0, 0]`. That is the “subtract the average” half of the recipe.
- Remove the print when done.

- [ ] You saw std ≈ `[1. 1.]` after scaling
- [ ] You can say why the left plot lies
- [ ] You know this lab scaled all rows, and that train-only is the production rule

---

## How it works (deeper)

For each column:

```
new = (old − mean_of_that_column) / std_of_that_column
```

After that, a knob of size `1.0` means “this feature, in typical-distance units,” not “this feature, in leftover clock hours.”

Ridge (ml-13) needs this or hour eats the penalty budget. Nets need this or one input saturates the mix.

---

## Common pitfalls

1. **You thought color/axis stretch was importance.** It is range.
2. **You will later fit a scaler on train+test “to be extra accurate.”** That is exam peeking.
3. **`ModuleNotFoundError`.** Venv off. `source .venv/bin/activate`.

---

## Knowledge check

1. What does std 1 after scaling mean in words?
2. What two raw stds did the lab print (about)?
3. Why can a plot lie?
4. In production, on which split do you `.fit` the scaler?

<details>
<summary>Answers</summary>

1. Typical distance from the average is 1 in those new units.
2. Hour ≈ 4.81, weight ≈ 3.35.
3. Axis stretch changes what your eye calls important.
4. Train only. Then transform val/test with those frozen numbers.

</details>

---

## Recap

- **You scaled** weight and hour until both had std 1.
- **You understand** lying axes and why lines care.
- **Next** bias vs variance: too simple vs too wiggly.

Next: `ml-09-bias-variance`

---

## Stretch goal

Change the two columns to `weight_kg` and `zone`. Rerun.

- **Expect:** zone’s raw std is small (1–4). After scale, both still std ≈ 1.
- Put `hour` back.

---

## Feedback

Could you redo this lab from memory? Note **ml-08**, expected stds vs what you saw.

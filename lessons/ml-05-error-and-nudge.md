# ml-05 — Error, mean, and nudge the knob

**Level:** Absolute beginner  
**Time:** ~70 minutes  
**Prerequisites:** ml-04  
**Lab outcome:** You can explain MSE and one gradient step in warehouse words, then fit a line with no sklearn — 400 nudges on real packing dots

---

## At a glance

**Mean squared error (MSE)** = average of `(guess − truth)²`. Square so late and early both count, and big misses hurt more.

A **derivative** asks: if I bump knob `m` a tiny bit, how does MSE move?

**Gradient descent** = repeatedly step *opposite* that slope (down the error bowl).

**Learning rate** = how big a step. Too big: you jump over the bottom. Too small: you nap on the hillside.

By the end you have:

1. watched an orange path walk down a U-shaped bowl (one 5 kg box)
2. fitted `m` and `b` on 80 packing orders **without sklearn**

---

## Why this matters

Maya could try random slopes forever. Nudging downhill on the error bowl is the engine under almost all later training — lines, logistic, tiny nets, even the baby character model in ml-48.

If you skip this, “the model learned” stays a slogan. After this, it is “we subtracted a bit times the slope of the bowl.”

---

## Concept primer

One 5 kg box. Truth = 13 minutes. Guess = `m × 5`.

| Word | Plain English | This bowl |
| --- | --- | --- |
| **Error** | Guess minus truth | `5m − 13` |
| **Squared error** | Error times itself | `(5m − 13)²` |
| **MSE** | Average of squares (here: one box, so just the square) | Same as squared error |
| **Gradient vs m** | How fast the bowl rises if m grows | `2 × (5m − 13) × 5` |
| **Update** | Step opposite the gradient | `m ← m − learning_rate × gradient` |

True `m` for this toy is `13/5 = 2.6`. We start at `m = 0` and walk there.

```
MSE
  |     *
  |    * *
  |   *   *
  |  *     *
  | *   o---o---o  ← orange nudges downhill
  +---------------- m
        0        2.6
```

> **Tip:** MSE is not “percent correct.” It is minutes-squared. Compare MSE to MSE, not to a gut percent.

> **Watch out:** The fit lab only uses **weight**. True minutes also use zone. Leftover error is missing features, not a broken nudge.

---

## Setup

```bash
cd project/ml_playground
source .venv/bin/activate
```

---

## Hands-on

### Step 1 — Walk the bowl (one knob, one box)

Why now: 80 boxes and two knobs is a fog if you have never seen a U. This plot is the U.

```bash
python m0_labs.py bowl
```

**It worked when** a U-shaped curve opens titled `ml-05: bowl of error. Each nudge follows the slope of the bowl.` and the terminal prints:

```text
started m=0, ended m= 2.6 true m would be 2.6
```

Orange dots are 25 steps with `learning rate = 0.01`. They walk from `m = 0` to `m = 2.6`.

Close the window. You just watched gradient descent on one number.

### Step 2 — Walk `lab_bowl` in the file

Open `m0_labs.py`. Find `lab_bowl`.

- `x = 5.0`, `y = 13.0` — one box.
- `mse = (m * x - y) ** 2` — the U, drawn for many candidate `m` values.
- Loop:

```text
grad = 2 * (mk * x - y) * x
mk = mk - lr * grad
```

That is the entire “AI” of this picture. Chain rule in warehouse clothes: error times input.

### Step 3 — Fit a line on 80 real boxes (the M0 project)

Why now: the bowl was a cartoon. This is Maya’s table. Still no sklearn.

```bash
python m0_labs.py fit
```

**It worked when** the terminal prints a falling MSE table and a scatter with an orange fit line.

Your numbers (seed frozen):

```text
step  mse  m  b
   0  315.254   2.466   0.333
  40    5.162   2.351   1.170
  80    3.904   2.263   1.871
 120    3.025   2.189   2.456
 160    2.411   2.128   2.946
 200    1.982   2.076   3.355
 240    1.683   2.033   3.696
 280    1.473   1.998   3.982
 320    1.327   1.968   4.221
 360    1.225   1.943   4.421
Maya-ish truth was about m=1.8 b=4 plus zone. You only used weight.
```

Read that table as a story:

- Step 0’s MSE **315** is “we started at `m=0, b=0` and the first update already jumped `m` to 2.47.” The printed step-0 row is *after* the first nudge inside the loop (the print is every 40 steps including 0).
- By step 360, MSE is **1.225**, `m ≈ 1.94`, `b ≈ 4.42`.
- Hidden truth is `m ≈ 1.8`, `b ≈ 4`, plus **0.6 × zone**. You cannot recover zone from weight alone. `m` soaked up a little of that missing story, so it sits a bit above 1.8.

- [ ] MSE fell
- [ ] You can say why `m` is not exactly 1.8
- [ ] You know sklearn was not imported

### Step 4 — Walk `lab_fit`

Same file, `lab_fit`:

- 80 orders, `m, b = 0.0, 0.0`, `lr = 0.01`, **400** steps.
- `pred = m * x + b`
- `err = pred - y`
- Nudge:

```text
m -= lr * (2 / n) * sum(err * x)
b -= lr * (2 / n) * sum(err)
```

The `2 / n` is the derivative of mean squared error. `n` is how many boxes. `sum(err * x)` is “error, times the feature, added up.”

This is ml-03’s mix, scored with ml-00’s error, then nudged.

### Step 5 — Mini experiment

In `lab_fit`, change `lr = 0.01` to `lr = 0.2`. Save. Rerun.

- **Expect:** MSE may explode (huge numbers, `nan`, or a wild line). That is a too-big step off the bowl.
- Put `0.01` back. Rerun once to see the sane table again.

Optional second try: `lr = 0.0001`.

- **Expect:** after 400 steps, MSE still high; `m` and `b` barely crawled.

---

## How it works (deeper)

Gradient descent does not “understand packing.” It asks one question, many times:

> If I wiggle this knob, does squared error go up or down? Step the other way.

sklearn `LinearRegression` (ml-10) solves the same bowl more directly (ordinary least squares). You still need this lab: neural nets *only* have the nudge version.

---

## Common pitfalls

1. **You reported step-0 MSE 315 as “the model is terrible forever.”** Look at step 40: already 5.16. The first print is the worst on purpose.
2. **Learning rate 0.2 and a crash.** Put `0.01` back. Huge lr is a real failure mode, not a broken install.
3. **Chasing MSE to 0.** Zone is missing. Noise is in the data (`normal(0, 0.8)` in `packing_orders`). Zero is the wrong god.
4. **Plot window, then you thought the script died.** Close the figure; the prints already happened above it.

---

## Knowledge check

1. Why square the error instead of averaging raw `guess − truth`?
2. What happens if the learning rate is huge?
3. After `fit`, is sklearn required?
4. At step 360, about what are MSE, `m`, and `b`?
5. Why is fitted `m` a bit above the hidden 1.8?

<details>
<summary>Answers</summary>

1. So late and early do not cancel, and big misses hurt more.
2. `m` leaps past the bottom and can explode.
3. No. You only added a bit to `m` and `b` each step.
4. MSE ≈ 1.225, m ≈ 1.94, b ≈ 4.42.
5. Zone also adds minutes; a weight-only line steals some of that into a steeper slope.

</details>

---

## Recap

- **You fitted** a line by 400 nudges. MSE fell from hundreds to about 1.2.
- **You understand** MSE and a gradient step.
- **Next** M1 hygiene: train vs test, so you stop grading the homework as if it were the exam.

Next: `ml-06-train-val-test`

---

## Stretch goal

In `lab_fit`, print one extra row at step 399 (last step), not only every 40.

- **Expect:** MSE a little under the 360 value (~1.2), `m` a hair closer to 1.8–1.9, `b` a hair closer to 4.5.
- Revert the extra print if you want the lesson table to stay tidy.

---

## Feedback

Could you redo this lab from memory? Note **ml-05**, the command (`bowl` vs `fit`), expected vs saw.

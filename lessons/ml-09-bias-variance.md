# ml-09 — Bias vs variance

**Level:** Absolute beginner  
**Time:** ~50 minutes  
**Prerequisites:** ml-08  
**Lab outcome:** You recognize a too-simple line vs a wiggly memorizer on a sine cloud, and you can point at the middle panel as the teaching target

---

## At a glance

**Bias:** always missing the same way (too simple). A flat “always 8 minutes” never learns the curve.

**Variance:** jumping around if the data wiggles (too flexible). A polyline through every box recites last night’s noise.

Dartboard: all darts left of the bull vs darts everywhere. You want a tight cluster near the bull.

Tonight: `np.polyfit` at degrees **1**, **3**, and **12** on 30 noisy sine points.

---

## Why this matters

Maya can use a flat rule or a polyline through every box. Both miss tonight.

If you skip this, later words like *overfit*, *regularization*, and *dropout* have no picture. This three-panel figure is the dartboard you will keep pointing at through ml-30.

---

## Concept primer

| Word | Plain English | This lab |
| --- | --- | --- |
| **Bias** | Systematic miss from a stiff recipe | Degree 1: a straight line through a wave |
| **Variance** | Recipe changes a lot if data wiggles | Degree 12: snakes through noise |
| **Polynomial degree** | How many bends you allow | 1 = line, 3 = a few bends, 12 = chaos on 30 points |
| **Noise** | Random leftover that is not the real pattern | `normal(0, 0.15)` added to the sine |

```
high bias          just enough           high variance
  /                  ~~~~                  /\/\/\/\
 /  (misses wave)   (follows sine)       (memorizes dots)
```

> **Tip:** More knobs need more data. M0’s two-knob line is low variance, some bias.

> **Watch out:** Low training error + high test error is the variance smell. This lab is a picture, not a test split — you will smell it again in ml-12 and ml-30.

---

## Setup

```bash
cd project/ml_playground
source .venv/bin/activate
```

---

## Hands-on

### Step 1 — Open the three panels

Why now: the words “bias” and “variance” stay mush until you see the snake.

```bash
python classic_labs.py biasvar
```

**It worked when** one window with **three** panels opens, shared y-axis, titled with the dartboard idea:

- left: **high bias (too simple)** — a stiff line
- middle: **just enough** — a curve that follows the sine through the cloud
- right: **high variance (memorizes)** — a wild wiggle through the dots

The dots are the same 30 points in every panel. Only the recipe flexibility changes.

### Step 2 — Walk `lab_bias_var`

Open `classic_labs.py`. Find `lab_bias_var`.

- `x` from 0 to 1, 30 points.
- `y = sin(2πx) + noise` — a wave plus jitter.
- Loop degrees `[1, 3, 12]` with `np.polyfit` then `np.polyval`.
- Degree is the **flexibility knob**. Not a moral law. Middle is the teaching target on *this* cloud.

### Step 3 — Mini experiment

Change the noisy degree from `12` to `25`. Save. Rerun.

- **Expect:** the right panel gets even more unhinged between dots (if numpy still fits it). You are adding knobs, not adding truth.
- Put `12` back.

- [ ] You can point at high bias vs high variance on the figure
- [ ] You know degree 3 is “just enough” *here*, not everywhere
- [ ] You did not treat the middle panel as a universal law

---

## How it works (deeper)

A degree-1 polynomial *cannot* draw a sine. That miss is bias.

A degree-12 polynomial *can* draw almost anything through 30 points, including the noise. Tomorrow’s points (a new seed) would get a different snake. That instability is variance.

The goal is not “most knobs” or “fewest knobs.” It is “enough shape for the real pattern, not enough to recite jitter.”

---

## Common pitfalls

1. **You thought the right panel was “more advanced.”** It is the failure mode.
2. **You will copy degree 12 onto packing weight later.** Packing is almost a line plus zone. High degree there is ml-12’s warning.
3. **Plot did not open.** Unset `ML_HEADLESS` on a laptop.

---

## Knowledge check

1. Which panel is high bias?
2. Which is high variance?
3. What function is the hidden truth (before noise)?
4. What does polynomial degree control in this lab?

<details>
<summary>Answers</summary>

1. The too-simple line (degree 1).
2. The degree-12 wiggle.
3. A sine: `sin(2πx)`.
4. Flexibility / how many bends you allow.

</details>

---

## Recap

- **You compared** three fits on the same noisy sine.
- **You understand** the dartboard: stiff vs scattered.
- **Next** sklearn linear regression — the named tool for M0’s line.

Next: `ml-10-one-feature-regression`

---

## Stretch goal

Change noise from `0.15` to `0.0` (perfect sine). Rerun.

- **Expect:** even degree 12 looks calmer — there is no jitter to memorize. Put `0.15` back so the variance panel stays honest.

---

## Feedback

Could you redo this lab from memory? Note **ml-09**, which panel confused you, expected vs saw.

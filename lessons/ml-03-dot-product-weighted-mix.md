# ml-03 — Dot product as a weighted mix

**Level:** Absolute beginner  
**Time:** ~55 minutes  
**Prerequisites:** ml-02  
**Lab outcome:** You can compute a tiny dot product by hand and with sliders, and you know why we glue a `1` onto the feature list

---

## At a glance

The **dot product** mixes two lists: multiply matching pairs, then add. One number comes out.

Maya’s line from ml-01 is a dot product in costume:

```text
guess = w0 × 1  +  w1 × weight
```

The `1` is a fake feature so the intercept is “just another mix.”

By the end you can explain two meanings of the word **weight**: kilograms on the box vs knobs in the recipe.

---

## Why this matters

Maya trusts weight more than hour-of-day. Those trusts **are** the knobs `w`. The dot product is how the mix becomes one number (minutes, or later a chance of refund).

If you skip this, every later “the model scored the ticket” is a slogan. With this, it is multiply-add.

---

## Concept primer

| Word | Plain English | Example |
| --- | --- | --- |
| **Dot product** | Pairwise multiply, then add | `[1, 5] · [4, 1.8] = 4 + 9 = 13` |
| **Knob / weight w** | How much this feature counts | `w1 = 1.8` minutes per kilo |
| **Bias / intercept w0** | The mix from the fake feature `1` | `w0 = 4` minutes of setup |
| **`@` in numpy** | Dot product (or matrix multiply) | `sample @ w` |

Worked number you should do now, before the plot:

```text
[2, 3] · [4, 5] = 2×4 + 3×5 = 8 + 15 = 23
```

```
 features [ 1 | weight ]     knobs [ w0 | w1 ]
              \_____  _____/
                    \/
              one guess (minutes)
```

> **Tip:** If `w1` is negative, heavier boxes get *smaller* guesses. The math allows it. Maya would not, for packing time.

> **Watch out:** “Weight” means kilograms *and* knobs. In this lesson, say **kilos** vs **knobs** out loud when you feel the collision.

---

## Setup

```bash
cd project/ml_playground
source .venv/bin/activate
```

---

## Hands-on

### Step 1 — Open the mix sliders

Why now: you already dragged `m` and `b` in ml-01. This is the same line, spelled as a mix.

```bash
python m0_labs.py dot
```

**It worked when** a plot titled `ml-03: dot product = mix. guess = w0*1 + w1*weight` opens with:

- warehouse dots (truth)
- an orange line `w0 + w1*weight`
- sliders **w0 intercept** and **w1 weight mix**
- plot text: `first box dot = … minutes` that updates as you drag

Start values: `w0 = 4`, `w1 = 1.5`.

### Step 2 — Read the first-box mix

Leave sliders at the start. The first packing weight in this lab’s sample is whatever `packing_orders(40)` row 0 is (same seed as other labs). The overlay is:

```text
first box dot = [1, weight_0] · [w0, w1]
```

Drag `w1` up toward 2. The line steepens. The printed first-box minutes rise.

Drag `w1` through zero into the negatives. Heavy boxes now get *smaller* guesses. That is legal arithmetic and a nonsense packing policy.

- [ ] You made `w1` negative on purpose and saw the line fall
- [ ] You can say the first-box number as a mix, not as “the AI”

### Step 3 — Walk the code

Open `m0_labs.py`. Find `lab_dot`.

- `ones = np.ones_like(xs)` — a column of `1`s, the fake feature.
- `guess = ones * w[0] + xs * w[1]` — the mix in slow motion.
- The comment tells the truth: `sample = np.array([1.0, float(x[0])])` then `sample @ w`.

`@` is numpy’s dot. Same as a for-loop of multiply-add. No extra magic.

ml-01’s `m` is this lab’s `w1`. ml-01’s `b` is `w0`. Same function, new spelling so later layers (many knobs) have a name: **dot**.

### Step 4 — Mini experiment

In `redraw`, print the mix for a *10 kg* box, not only the first sample:

```python
print("10kg mix", float(np.array([1.0, 10.0]) @ w))
```

Rerun, move sliders once (prints on each redraw — noisy but clear).

- **Expect:** at start `w0=4, w1=1.5`, a 10 kg box mixes to `4 + 15 = 19` minutes.
- Remove the `print` when you are done.

---

## How it works (deeper)

Dot product is “how much do these two lists agree, with knobs deciding the importance.”

For packing:

```
guess = w · [1, weight]
```

For later refund chance, the list grows: `[1, delay, angry_words, price]`. Still one mix, then a squash (ml-14).

---

## Common pitfalls

1. **You multiplied the two lists into a new list and stopped.** Dot product **adds** after the multiplies. Output is one number.
2. **You set w1 = 2 because ml-00 used 2.** Fine as an experiment; the hidden rate is ~1.8 plus zone. Do not treat 2 as sacred.
3. **Negative intercept panic.** `w0` can be negative in the math. For minutes it is usually a small positive setup time.

---

## Knowledge check

1. Compute `[2, 3] · [4, 5]`.
2. Why glue a `1` onto the feature list?
3. In this lab, if `w1` is negative, what happens to heavy boxes?
4. What does `sample @ w` mean in `lab_dot`?

<details>
<summary>Answers</summary>

1. `8 + 15 = 23`.
2. So the intercept is a mix too: `w0 × 1`.
3. Their minute guesses get smaller — usually nonsense for packing time.
4. Numpy dot product of `[1, first_weight]` with `[w0, w1]`.

</details>

---

## Recap

- **You mixed** intercept and kilos with a dot product.
- **You understand** knobs vs kilograms.
- **Next** many orders at once: a table (matrix).

Next: `ml-04-tables-as-matrices`

---

## Stretch goal

Change `s1`’s range from `(-1, 4)` to `(-4, 4)` so a strongly negative mix is easier to see. Rerun. Put the original range back.

---

## Feedback

Could you redo this lab from memory? Note **ml-03**, step, expected vs saw.

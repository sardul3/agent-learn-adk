# ml-15 — Decision boundary

**Level:** Absolute beginner  
**Time:** ~45 minutes  
**Prerequisites:** ml-14  
**Lab outcome:** You see two colors of tickets split by a straight fence in delay × angry-words space, and you can say the fence is where `p = 0.5`

---

## At a glance

A **decision boundary** is the fence where the guess flips class.

Logistic with two features: a **straight** fence. Where `p = 0.5`, the mix `z = 0`, so:

```text
w1×delay + w2×angry_words + b = 0
```

That is a line in the delay–angry plane.

---

## Why this matters

Maya can picture “too delayed and too angry → refund path.” The fence is that policy’s sketch.

If you skip this, “classifier” is only an accuracy number. After this, it is geography.

---

## Concept primer

| Word | Plain English | Tonight |
| --- | --- | --- |
| **Feature plane** | Two facts as x and y | delay vs angry_words |
| **Fence / boundary** | Where the color flips | `z = 0` → `p = 0.5` |
| **`contourf`** | Fill a grid with predicted class | Two-tone background |

> **Tip:** If classes overlap a lot, no fence is clean. That is life, not a broken lab.

> **Watch out:** A wiggly fence (deep nets) can hug noise. Straight can be the honest warehouse rule.

---

## Setup

```bash
cd project/ml_playground
source .venv/bin/activate
```

---

## Hands-on

### Step 1 — Open the two-tone map

Why now: the S-curve was one axis. Refunds in real tickets use more than delay.

```bash
python classic_labs.py boundary
```

**It worked when** a plot titled `ml-15: decision boundary — two colors of warehouse tickets` opens with:

- a filled two-tone background (the model’s guess on a grid)
- dots colored by the **true** label (`coolwarm`)

The color *change* in the background is the fence. Dots of the “wrong” color on a side are overlap + the 8% flips in `tickets()`.

You may see a feature-name warning on the grid. Ignore it.

### Step 2 — Walk `lab_boundary`

Open `classic_labs.py`. Find `lab_boundary`.

- `X = delay_days, angry_words`. `y = became_refund`.
- `LogisticRegression().fit`
- `meshgrid` of delays 0–10 and angry 0–12.
- `clf.predict` on every grid point, reshaped, then `contourf`.
- Scatter the real tickets on top.

`predict` uses the default 0.5 cut on `p`. The fence is that cut, drawn.

### Step 3 — Mini experiment

Change angry grid max from `12` to `20` in `linspace(0, 12, 80)`. Rerun.

- **Expect:** more empty map above the data. The fence formula does not change; you just zoomed out.
- Put `12` back.

- [ ] You can point at the fence (color change)
- [ ] You know why it is straight (logistic is linear in z)
- [ ] You did not panic about mixed-color dots

---

## How it works (deeper)

`p = 0.5` when `z = 0` because squash(0) = 0.5. Two knobs plus `b` make a line. Three features would make a plane you cannot draw — same idea.

---

## Common pitfalls

1. **Thinking the background is truth.** It is the *recipe*. Dots are truth.
2. **Wanting a squiggly fence to catch every red dot.** That is ml-09 variance.
3. **Forgetting price.** The generator also refunds expensive items. Some “wrong” dots are that missing axis.

---

## Knowledge check

1. Where is `p = 0.5` on this plot?
2. Why is the fence straight?
3. What are the two axes?
4. What does a mixed-color region mean?

<details>
<summary>Answers</summary>

1. Along the color change.
2. Logistic is linear in `z`.
3. `delay_days` and `angry_words`.
4. Overlap, missing features (price), or label noise — not necessarily a crashed lab.

</details>

---

## Recap

- **You saw** the fence.
- **You understand** `z = 0`.
- **Next** the four mistake cells: confusion, precision, recall.

Next: `ml-16-confusion-precision-recall`

---

## Stretch goal

Add `price_usd` as a third feature (drop the plot or keep 2-D on delay/angry with a model that also saw price). Easiest: print `clf.score` with two vs three columns in a scratch `python -c` using the same `tickets(200)`. Revert any file edits.

---

## Feedback

Could you redo this lab from memory? Note **ml-15**, fence vs dots, expected vs saw.

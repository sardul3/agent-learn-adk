# ml-28 — Stacked ReLU

**Level:** Absolute beginner  
**Time:** ~55 minutes  
**Prerequisites:** ml-27; Python 3.14.6, numpy 2.5.2, sklearn 1.9.0 from the ml-00 venv  
**Lab outcome:** You watch a two-layer ReLU net’s loss fall from 0.4326 to 0.2022 and walk the W1/W2 updates

---

## At a glance

One neuron (ml-27) draws a **soft line**. A **stack** of ReLUs can bend. This lab’s label is a **circle-ish** rule: “yes if x² + y² > 1.2.”

**Loss must fall.** On this frozen seed it goes **0.4326 → 0.2022** over **400** steps with **lr = 0.15**.

By the end you can:

- point at start loss **0.4326** and end loss **0.2022**
- name the pieces: 200 points, 2 inputs, **6** hidden ReLUs, 1 sigmoid output
- walk **one** backprop pass on `W1` and `W2` in the actual loop

You will run `later_labs.py relustack` and walk `lab_relu_stack`.

---

## Why this matters

Maya’s “heavy vs light” packing line was a line. Damage vs not-damage in feature space is often a **ring** or a blob: “too far from typical” in every direction.

A single neuron cannot draw a ring. Six hidden ReLUs can glue half-planes into a bent fence.

If you skip this lab, “deep” means “more slides.” Tonight it means: **W1**, ReLU, **W2**, sigmoid, then nudge both W’s so mean squared error drops.

---

## Concept primer

| Word | Plain English | In this lab |
| --- | --- | --- |
| **Hidden layer** | Neurons whose outputs you do not ship; they feed the next layer | 6 ReLUs |
| **W1** | Weights from 2 inputs → 6 hidden | shape `(2, 6)` |
| **W2** | Weights from 6 hidden → 1 output | shape `(6, 1)` |
| **ReLU gate** | `pre > 0` — pass the gradient only where the hidden unit was on | `dL_dh * (pre > 0)` |
| **Learning rate lr** | How big a nudge | **0.15** |
| **Step** | One full forward + backward + update | **400** steps |
| **Loss** | Mean of `(p − y)²` | start **0.4326**, end **0.2022** |
| **Circle-ish label** | y = 1 if radius² > 1.2 else 0 | `r² = x0² + x1²` |

```text
X (200×2)
  →  X @ W1 = pre
  →  ReLU(pre) = h
  →  h @ W2 = z
  →  sigmoid(z) = p
  →  loss = mean((p − y)²)
  →  backprop: dW2, dW1
  →  W2 -= lr * dW2;  W1 -= lr * dW1
```

> **Tip:** If loss **rises**, you have a bug (or a huge lr). This file was just fixed so the curve **falls**. Trust the print: 0.4326 then 0.2022.

> **Watch out:** The plot is **loss vs step**, not the circle. The circle is the hidden *job*. The picture you stare at is “did the score get better?”

---

## Setup (short)

You already made the virtual environment in **ml-00**. Reuse it. Do not recreate it. Do not pip-install torch.

### Step 1 — Enter the playground and turn the island on

Why now: `later_labs.py` must be found in the current folder.

```bash
cd project/ml_playground
source .venv/bin/activate
```

- `cd` means “change directory.” There is no dash-flag here.
- `source` runs `activate` in **this** shell so `python` points at the island.

**It worked when** your prompt shows `(.venv)` and this prints the pinned stack:

```bash
python --version
python -c "import numpy, sklearn; print(numpy.__version__); print(sklearn.__version__)"
```

```text
Python 3.14.6
2.5.2
1.9.0
```

- `--version` prints the interpreter version.
- `-c` means “run the next string as Python.”

---

## Hands-on

### Step 2 — Run the stacked-ReLU lab

Why this command now: you need to *see* the curve fall and lock the two loss numbers.

```bash
python later_labs.py relustack
```

`relustack` is a lab name, not a flag.

**It worked when** a plot opens titled `ml-28: stacked ReLU can bend a circle-ish rule (loss should fall)`, x-axis `step`, and the terminal prints:

```text
start loss 0.4326308728987482 end 0.20222762918533732
```

Say it as **0.4326 → 0.2022**. End is **lower**. That is the whole pass/fail for this lab.

The curve should trend down (it can wiggle). Close the window after you believe the print.

- [ ] Start ≈ 0.4326 and end ≈ 0.2022
- [ ] End is smaller than start

### Step 3 — Name the data and the shapes

Open `lab_relu_stack`. The data is **not** Meridian SKUs. It is a synthetic cloud so the circle is obvious:

1. `rng = np.random.default_rng(0)` — frozen generator. Seed **0**.
2. `X = rng.normal(size=(200, 2))` — 200 points, 2 coordinates, bell-shaped around 0.
3. `y = ((X[:, 0] ** 2 + X[:, 1] ** 2) > 1.2)` — **1** if outside the circle of radius √1.2, else **0**. Then `.astype(float).reshape(-1, 1)` so y is 200 × 1.
4. `W1 = rng.normal(scale=0.8, size=(2, 6))` — start random, not zeros.
5. `W2 = rng.normal(scale=0.8, size=(6, 1))`
6. `lr = 0.15`

Why 1.2? It is a cutoff on **radius squared**. Points near the origin are class 0. Points farther out are class 1. A straight line through the origin cannot separate that. A stack can approximate the ring.

- [ ] You found `> 1.2` in the file
- [ ] You found `size=(2, 6)` and `size=(6, 1)`

### Step 4 — Walk one backprop update (the actual lines)

Stay in the `for _ in range(400):` loop. These are the lines that run.

**Forward**

1. `pre = X @ W1` — 200 × 2 times 2 × 6 → 200 × 6 mixes (six neurons, ml-27 style, in parallel).
2. `h = _relu(pre)` — `np.maximum(0, pre)`. Negatives become 0.
3. `z = h @ W2` — 200 × 6 times 6 × 1 → 200 × 1.
4. `p = 1 / (1 + np.exp(-z))` — sigmoid probabilities.
5. `loss = mean((p - y) ** 2)` — same “how wrong” idea as ml-00, squared so late and early do not cancel.

**Backward** (read bottom-up: output toward W1)

6. `dL_dp = 2.0 * (p - y) / len(y)` — derivative of mean squared error w.r.t. `p`. The `2` is from d(u²)/du. The `/ len(y)` is from the mean.
7. `dL_dz = dL_dp * p * (1 - p)` — multiply by sigmoid’s derivative `p(1-p)`.
8. `dW2 = h.T @ dL_dz` — how to nudge **W2**. Hidden activations times output error.
9. `dL_dh = dL_dz @ W2.T` — send the error back into the six hidden units.
10. `dW1 = X.T @ (dL_dh * (pre > 0))` — how to nudge **W1**. `(pre > 0)` is the ReLU gate: if that hidden unit was off, its slice of the gradient is zero.
11. `W2 -= lr * dW2` and `W1 -= lr * dW1` — step **opposite** the gradient. `lr = 0.15`.

Do that 400 times. `losses.append(loss)` so the plot can draw the trail. Print `losses[0]` and `losses[-1]`.

> **Tip:** `-=` is the train. If you wrote `+=`, loss would climb. Opposite of the gradient = downhill.

> **Watch out:** `(pre > 0)` is True/False, used as 1/0. It is **not** a second ReLU on the gradient magically. It is a mask: dead units do not update through that path this step.

### Step 5 — Mini experiment (do it)

In `lab_relu_stack`, change **one number**: `lr = 0.15` to `lr = 0.01`.

Save. Run:

```bash
python later_labs.py relustack
```

**Expect:** loss still **falls**, but the end is **higher** than 0.2022 (smaller nudges, 400 steps is not enough to get as far). Start stays ≈ 0.4326 because the first forward happens before any update.

Put `0.15` back when you are done.

- [ ] End loss got worse (larger) than 0.2022
- [ ] You put 0.15 back

---

## How it works (deeper)

A ReLU unit is a bent line: off on the left, slope on the right. Six of them, mixed by W2, can approximate a curved fence around the origin.

```text
layer 1: six half-plane “on/off” lamps
layer 2: one mix of those lamps → sigmoid → p
loss: how far p is from the circle-ish labels
backprop: blame W2 first, then W1, mask with ReLU
```

The computer still does not “know a circle.” It nudges 2×6 + 6×1 = **18** weights (no extra bias in this lab) until mean squared error drops from 0.4326 to 0.2022.

ml-29 will slow this down to **four numbers** so the same `-= lr * dW` is something you can finish with a pencil.

---

## Common pitfalls

1. **`ModuleNotFoundError`.** Venv off. Redo Step 1.
2. **Plot never opens.** `unset ML_HEADLESS` on a laptop.
3. **Loss went up.** You are not on the current `later_labs.py` (this lab was just fixed), or you flipped `-=` to `+=`, or lr is huge. Re-pull/re-save the file; expect 0.4326 → 0.2022.
4. **You thought the plot was the circle.** It is loss vs step.
5. **You pip-installed torch to stack layers.** Numpy is the stack. ml-31 will skip torch on purpose.
6. **You changed 1.2 and then compared losses to this lesson.** Different labels, different curve. Put 1.2 back after any stretch.

---

## Knowledge check

Answer from the printout and the loop you walked.

1. What are start loss and end loss (four decimals are enough)?
2. How many steps, what lr, how many hidden ReLUs?
3. What does `y = (x0² + x1² > 1.2)` mean in one sentence?
4. In the update, which line changes W2? Which line applies the ReLU gate to W1’s gradient?
5. Why must loss fall for this lab to “work”?

<details>
<summary>Answers</summary>

1. 0.4326 start, 0.2022 end (`0.4326308728987482` and `0.20222762918533732`).
2. 400 steps; lr 0.15; hidden size 6.
3. Label 1 if the point is outside a circle of radius √1.2, else 0.
4. `W2 -= lr * dW2`. The gate is `(pre > 0)` inside `dW1 = X.T @ (dL_dh * (pre > 0))`.
5. Training is “nudge to reduce the score.” If loss rises, the stack is not learning this fence.

</details>

---

## Recap

- **You built** a 2-6-1 ReLU net whose loss fell 0.4326 → 0.2022.
- **You understand** stack = hidden ReLUs then a mix; backprop fills `dW2` then `dW1`; lr scales the nudge.
- **Next** you will walk the same idea on **four numbers** you can finish by hand.

Next: `ml-29-backprop-four-numbers`

---

## Stretch goal

Change `range(400)` to `range(40)`. Rerun.

- **Expect:** start still ≈ 0.4326; end **higher** than 0.2022 (not enough steps).
- Put `400` back when you are done.

---

## Feedback

Could you redo this lab from memory? Note the **lesson id** (`ml-28`), the **step number**, what you **expected**, and what you **saw**.

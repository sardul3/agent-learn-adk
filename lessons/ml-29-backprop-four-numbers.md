# ml-29 — Backprop, four numbers

**Level:** Absolute beginner  
**Time:** ~50 minutes  
**Prerequisites:** ml-28; Python 3.14.6, numpy 2.5.2, sklearn 1.9.0 from the ml-00 venv  
**Lab outcome:** You walk one hidden ReLU and one output through forward, backward, and a single lr=0.1 update

---

## At a glance

**Backprop** (backpropagation) is the recipe that answers: “If I wiggle this weight, how does **loss** change?” Then you step the weight the other way.

This lab freezes **four numbers** plus a learning rate:

- input **x = 2**
- hidden weight **w1 = 0.5**
- output weight **w2 = −0.4**
- truth **y = 1**
- **lr = 0.1**

By the end you can recite:

- forward: **h = 1.0**, **yhat = −0.4**, **loss = 0.98**
- grads: **dL/dw2 = −1.4**, **dL/dw1 = 1.12**
- update: **new w2 = −0.26**, **new w1 = 0.388**

You will type the arithmetic, run `python -c`, then run `later_labs.py backprop`.

---

## Why this matters

ml-28 updated 18 weights 400 times. That is too many to stare at. Maya still deserves one pass she can finish at the dock with a pencil.

If you skip this lab, `loss.backward()` in later frameworks is a spell. Tonight it is chain rule on a two-step recipe: `h = ReLU(w1 * x)`, `yhat = w2 * h`.

---

## Concept primer

| Word | Plain English | In this lab |
| --- | --- | --- |
| **Forward** | Compute h, yhat, loss from the current weights | h=1.0, yhat=−0.4, loss=0.98 |
| **Loss** | `0.5 * (yhat − y)²` | 0.5 × (−0.4 − 1)² = 0.98 |
| **Gradient dL/dw** | How loss changes if that weight wiggles | dL/dw2 = −1.4 |
| **Chain rule** | Multiply local slopes along the path | dL/dw1 = (dL/dh) × (dh/dw1) |
| **Update** | `w ← w − lr * dL/dw` | new w2 = −0.26 |

```text
x --w1--> ReLU --> h --w2--> yhat      y=1
                      loss = 0.5 (yhat − y)²
then walk backwards: yhat → w2 → h → w1
```

> **Tip:** The `0.5` in the loss is a convenience so the derivative is `(yhat − y)` instead of `2(yhat − y)`. Same bowl shape.

> **Watch out:** yhat is **negative** (−0.4) while y is **1**. The net is badly wrong on purpose so the gradients are chunky, not ~0.

---

## Setup (short)

You already made the virtual environment in **ml-00**. Reuse it. Do not recreate it. Do not pip-install torch.

### Step 1 — Enter the playground and turn the island on

Why now: you will run both `python -c` and `later_labs.py` from this folder.

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

### Step 2 — Forward pass, typed

Why now: backward is impossible if forward is fuzzy. Type these (do not only read them):

```text
h    = max(0, w1 * x) = max(0, 0.5 * 2) = max(0, 1.0) = 1.0
yhat = w2 * h         = (-0.4) * 1.0                 = -0.4
loss = 0.5 * (yhat - y)^2
     = 0.5 * (-0.4 - 1)^2
     = 0.5 * (-1.4)^2
     = 0.5 * 1.96
     = 0.98
```

Check with the interpreter:

```bash
python -c "
x, w1, w2, y = 2.0, 0.5, -0.4, 1.0
h = max(0.0, w1 * x)
yhat = w2 * h
loss = 0.5 * (yhat - y) ** 2
print(h, yhat, loss)
"
```

**Expect:** `1.0 -0.4 0.9799999999999999` — that is **0.98**.

- [ ] You typed the forward lines
- [ ] Python printed h=1.0, yhat=−0.4, loss≈0.98

### Step 3 — Backward pass, typed

Why now: these are the two numbers the lab prints as `dL/dw2` and `dL/dw1`.

```text
dL/dyhat = yhat - y = -0.4 - 1 = -1.4

dL/dw2 = dL/dyhat * h = -1.4 * 1.0 = -1.4

dL/dh  = dL/dyhat * w2 = -1.4 * (-0.4) = 0.56

dh/dw1 = x  if (w1*x > 0) else 0
       = 2  (because 1.0 > 0, ReLU was on)

dL/dw1 = dL/dh * dh/dw1 = 0.56 * 2 = 1.12
```

Then the nudge:

```text
new w2 = w2 - lr * dL/dw2 = -0.4 - 0.1 * (-1.4) = -0.4 + 0.14 = -0.26
new w1 = w1 - lr * dL/dw1 =  0.5 - 0.1 * (1.12)  =  0.5 - 0.112 = 0.388
```

Check:

```bash
python -c "
x, w1, w2, y, lr = 2.0, 0.5, -0.4, 1.0, 0.1
h = max(0.0, w1 * x)
yhat = w2 * h
dloss_dyhat = yhat - y
dloss_dw2 = dloss_dyhat * h
dloss_dh = dloss_dyhat * w2
dloss_dw1 = dloss_dh * (x if w1 * x > 0 else 0.0)
print(dloss_dw2, dloss_dw1)
print(w2 - lr * dloss_dw2, w1 - lr * dloss_dw1)
"
```

**Expect:** `-1.4 1.12` then `-0.26 0.388`.

- [ ] dL/dw2 is **−1.4** (negative — increasing w2 would *help*, because yhat is too small)
- [ ] new weights are **−0.26** and **0.388**

### Step 4 — Run the lab and walk `lab_backprop`

```bash
python later_labs.py backprop
```

`backprop` is a lab name, not a flag.

**It worked when** you see:

```text
forward h 1.0 yhat -0.4 loss 0.9799999999999999
dL/dw2 -1.4 dL/dw1 1.1199999999999999
new w2 -0.26 new w1 0.388
```

Open `later_labs.py`. Find `lab_backprop`. Line up each print with Step 2–3:

1. `x, w1, w2, y = 2.0, 0.5, -0.4, 1.0` — the four numbers.
2. `h = max(0.0, w1 * x)` — ReLU hidden.
3. `yhat = w2 * h` — **no extra bias, no sigmoid**. Linear output. That keeps the pencil honest.
4. `loss = 0.5 * (yhat - y) ** 2`
5. `dloss_dyhat = yhat - y` — matches the 0.5 in the loss.
6. `dloss_dw2 = dloss_dyhat * h`
7. `dloss_dh = dloss_dyhat * w2`
8. `dloss_dw1 = dloss_dh * (x if w1 * x > 0 else 0.0)` — ReLU gate. If the hidden unit had been off, this would be **0** and w1 would not move.
9. `lr = 0.1` then `w - lr * dL/dw`.

> **Tip:** `1.1199999999999999` is **1.12**. Same float dust as ml-27’s 2.8000…003.

> **Watch out:** w2 is negative. After the update it is **less negative** (−0.26). yhat will move toward zero, then toward y=1 if you kept stepping. This lab does **one** step only.

### Step 5 — Mini experiment (do it)

Change **one number**: `lr = 0.1` to `lr = 0.5`.

Save. Run:

```bash
python later_labs.py backprop
```

**Expect:** forward and dL/dw **unchanged** (lr is not in the forward). New weights jump farther:  
`new w2 = -0.4 - 0.5*(-1.4) = 0.3`  
`new w1 = 0.5 - 0.5*1.12 = -0.06`

Put `0.1` back when you are done.

- [ ] You saw new w2 become **0.3**
- [ ] You put lr 0.1 back

---

## How it works (deeper)

Chain rule in one warehouse sentence: **blame the output weight first, then the hidden weight, and zero the hidden blame if ReLU was off.**

```text
loss depends on yhat
yhat depends on w2 and h
h depends on w1 (and x), but only if w1*x > 0
```

ml-28 was this, with matrices: `dW2 = h.T @ dL_dz`, then `dW1 = X.T @ (dL_dh * (pre > 0))`. Same arrows. More numbers.

A framework’s `backward()` writes these products for you. It does not replace them.

---

## Common pitfalls

1. **`ModuleNotFoundError`.** Venv off. Redo Step 1.
2. **You used `(yhat − y)²` without the `0.5` and then expected the lab’s 0.98.** Without 0.5, loss would be 1.96. The file uses 0.5.
3. **You forgot ReLU and wrote h = w1*x anyway.** Here it matched because 1.0 > 0. If w1 were −0.5, h would be 0 and dL/dw1 would be 0.
4. **You added lr instead of subtracting.** Downhill is `w − lr * grad`.
5. **You thought yhat uses a sigmoid.** Not in this file. Linear `w2 * h`.
6. **You pip-installed torch to “see real backprop.”** This *is* real backprop. Four numbers.

---

## Knowledge check

Answer from the printout you ran with lr=0.1.

1. What are x, w1, w2, y, and lr?
2. What are forward h, yhat, and loss?
3. What are dL/dw2 and dL/dw1?
4. What are new w2 and new w1?
5. If w1*x had been ≤ 0, what would dL/dw1 be?

<details>
<summary>Answers</summary>

1. 2, 0.5, −0.4, 1, 0.1.
2. h=1.0, yhat=−0.4, loss=0.98.
3. −1.4 and 1.12.
4. −0.26 and 0.388.
5. 0.0 — ReLU off, no path to w1 this step.

</details>

---

## Recap

- **You built** one complete forward/backward/update on four numbers.
- **You understand** backprop = chain rule; update = minus lr times gradient; ReLU can block w1.
- **Next** you will see a **wiggly** fit and treat dropout as the story of not trusting one teammate.

Next: `ml-30-overfitting-dropout`

---

## Stretch goal

Change `y = 1.0` to `y = 0.0` in `lab_backprop`. Rerun.

- **Expect:** yhat still −0.4; loss = 0.5*(−0.4−0)² = 0.08; gradients shrink; new weights barely move.
- Put `y = 1.0` back when you are done.

---

## Feedback

Could you redo this lab from memory? Note the **lesson id** (`ml-29`), the **step number**, what you **expected**, and what you **saw**.

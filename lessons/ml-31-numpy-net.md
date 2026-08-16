# ml-31 — Numpy net (torch skipped)

**Level:** Absolute beginner  
**Time:** ~50 minutes  
**Prerequisites:** ml-30; Python 3.14.6, numpy 2.5.2, sklearn 1.9.0 from the ml-00 venv  
**Lab outcome:** You train a tiny logistic net in numpy until loss falls 0.2788 → 0.0611, and you treat the torch branch as a skipped import — not as a pip homework

---

## At a glance

A **numpy net** here is one linear layer plus a sigmoid, trained with the same “minus the gradient” rule as ml-29.

**Loss must fall:** **0.2788 → 0.0611** over **200** steps.

This playground **does not install PyTorch**. The lab tries `import torch`, catches the error, and prints:

```text
torch skipped: ModuleNotFoundError — numpy path already trained.
```

That line is **success** on this track. Do **not** pip-install a GPU wheel. Do **not** pip-install torch on Python 3.14.6 to “finish” the lesson. The numpy path already trained.

By the end you can:

- read `loss start/end 0.2787746165295428 0.06108068880240457`
- walk `z = X @ W + b`, sigmoid, MSE, the W and b updates
- explain why the `try/except` exists (torch is missing) without installing anything

You will run `later_labs.py numpynet` and walk `lab_numpy_net`.

---

## Why this matters

Frameworks are calculators for ml-29. If Maya only ever types `loss.backward()`, she cannot debug when the calculator is missing.

Python 3.14.6 in this venv has numpy 2.5.2 and sklearn 1.9.0. It does **not** have torch. The lesson is: **you still trained a net.**

If you skip this lab, “we’ll just use PyTorch” becomes a stall. Tonight the stall is already handled in four print words: `torch skipped: ModuleNotFoundError`.

---

## Concept primer

| Word | Plain English | In this lab |
| --- | --- | --- |
| **Logistic net** | Linear mix, then sigmoid, then a yes/no score | `p = sigmoid(X @ W + b)` |
| **W, b** | Weight column (2×1) and bias | start small random W, b=0 |
| **MSE** | Mean of `(p − y)²` | the printed loss |
| **SGD-style step** | Nudge opposite the gradient | `W -= 0.5 * ...`; `b -= 0.5 * ...` |
| **ModuleNotFoundError** | Python cannot import that name | torch is not installed — **expected** |
| **Numpy path** | The training loop that already ran | 80 points, 200 steps, loss 0.2788 → 0.0611 |

```text
80 × 2 random X
y = 1 if (x0 + 0.5*x1 > 0) else 0
200 steps of numpy SGD
then: try torch → ModuleNotFoundError → print skipped
```

> **Tip:** The label is a **line** in 2D, not a circle (that was ml-28). One neuron is enough.

> **Watch out:** `except Exception` is how the lab prints a friendly skip. It is not an invitation to install torch. Leave the venv as ml-00 left it.

---

## Setup (short)

You already made the virtual environment in **ml-00**. Reuse it. Do not recreate it. **Do not pip-install torch.**

### Step 1 — Enter the playground and turn the island on

Why now: `later_labs.py` must import numpy from this island.

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

Prove torch is absent (this should **fail** to import):

```bash
python -c "import torch"
```

**Expect:** `ModuleNotFoundError: No module named 'torch'`. That is the same exception the lab catches. You are done. Do not pip.

---

## Hands-on

### Step 2 — Run the numpy-net lab

Why this command now: the two losses plus the skip line are the whole scoreboard.

```bash
python later_labs.py numpynet
```

`numpynet` is a lab name, not a flag.

**It worked when** you see **exactly** this pair of ideas (numbers pinned):

```text
loss start/end 0.2787746165295428 0.06108068880240457
torch skipped: ModuleNotFoundError — numpy path already trained.
```

Read it as:

- start **0.2788**, end **0.0611** — loss **fell**
- torch **skipped** — not a broken install you must fix

No plot. The earlier labs used windows; this one is print-only.

- [ ] End loss is about 0.0611, smaller than 0.2788
- [ ] You did **not** run `pip install torch`

### Step 3 — Walk the numpy loop (do not paste blindly)

Open `later_labs.py`. Find `lab_numpy_net`.

**Data**

1. `rng = np.random.default_rng(2)` — seed **2**.
2. `X = rng.normal(size=(80, 2))` — 80 points, 2 features.
3. `y = (X[:, 0] + 0.5 * X[:, 1] > 0).astype(float)` — a **linear** rule. Weight the second feature half as much.

**Knobs**

4. `W = rng.normal(size=(2, 1)) * 0.1` — small random start.
5. `b = 0.0`

**Each of 200 steps**

6. `z = X @ W + b` — the mix (ml-27, batched).
7. `p = sigmoid(z)` then `.ravel()` so p is length 80.
8. `loss = mean((p - y) ** 2)` — append to `losses`.
9. `grad = ((p - y) * p * (1 - p)).reshape(-1, 1)` — MSE times sigmoid slope, per row.
10. `W -= 0.5 * X.T @ grad / len(X)` — lr **0.5**, average over the 80 rows.
11. `b -= 0.5 * float(grad.mean())` — same lr on the bias.

After the loop: `print("loss start/end", losses[0], losses[-1])`.

That is a complete trained model. W and b moved. Loss fell 0.2788 → 0.0611.

> **Tip:** `/ len(X)` is the mean. Without it, the nudge would grow with 80 and you would overshoot.

> **Watch out:** `0.5` here is the **learning rate**, not the `0.5 * (yhat−y)²` from ml-29. Two different 0.5s in two files. This loop’s loss is **mean** of squares, no extra 0.5 in the loss itself.

### Step 4 — Walk the torch `try` (read it; do not feed it)

Still in `lab_numpy_net`, after the numpy print:

```python
try:
    import torch
    from torch import nn
    ...
    print("torch cpu end loss", last)
except Exception as e:
    print("torch skipped:", type(e).__name__, "— numpy path already trained.")
```

On this machine:

- `import torch` raises **`ModuleNotFoundError`**
- `type(e).__name__` is the string `ModuleNotFoundError`
- you never reach `nn.Linear` or `opt.step()`

If torch *were* installed, that block would run 200 SGD steps on `nn.Linear(2, 1)` with `lr=0.2` and print a CPU end loss. It is a **translation** of the same job, not a higher grade.

You are not behind. You are on the numpy path the track chose.

> **Tip:** `type(e).__name__` prints the error **class** without a traceback storm. You still know it was ModuleNotFoundError.

> **Watch out:** Do not “complete” the lesson with `pip install torch` on Python 3.14. Wheels lag; GPU wheels are the wrong extra. This bonus track stays CPU numpy.

### Step 5 — Mini experiment (do it)

Change **one number**: `for _ in range(200):` (the **numpy** loop, the first one) to `for _ in range(20):`.

Save. Run:

```bash
python later_labs.py numpynet
```

**Expect:** start still ≈ 0.2788; end **larger** than 0.0611 (not finished descending). The torch skip line is unchanged.

Put `200` back when you are done.

- [ ] End loss got worse with 20 steps
- [ ] You put 200 back
- [ ] Torch still skipped

---

## How it works (deeper)

Same bowl as ml-29, batched:

```text
p = sigmoid(X W + b)
loss = mean((p − y)²)
nudge W and b downhill
repeat 200 times
```

The hidden rule `y = (x0 + 0.5 x1 > 0)` is a straight fence. A logistic neuron can match that fence. That is why 0.0611 is reachable without a hidden layer.

PyTorch would compute `grad` for you (`loss.backward()`). Numpy makes you write ` (p-y) * p * (1-p) `. You already did that. The import skip does not erase the training.

---

## Common pitfalls

1. **`ModuleNotFoundError: numpy`.** Venv off. Redo Step 1. This is the *bad* missing module.
2. **`ModuleNotFoundError: torch` from your own `python -c`.** Expected. Do not pip.
3. **You pip-installed a CUDA wheel “to be advanced.”** Wrong track. No GPU required. Undo that install if you did it; this lesson does not use it.
4. **You thought skipped meant the numpy net failed.** Numpy already printed start/end. Read line 1 first.
5. **You edited the torch loop’s `range(200)` for Step 5.** That loop never runs here. Edit the **first** `range(200)`.
6. **Wrong folder.** `cd project/ml_playground`.

---

## Knowledge check

Answer from the printout and the numpy loop.

1. What are loss start and end (four decimals)?
2. How many rows of X, how many steps, what learning rate on W?
3. What exact skip line should print on this venv?
4. Should you pip-install torch on Python 3.14.6 for this lesson?
5. What is the hidden labeling rule for y?

<details>
<summary>Answers</summary>

1. 0.2788 start, 0.0611 end (`0.2787746165295428` and `0.06108068880240457`).
2. 80 rows; 200 steps; lr 0.5 on W and b.
3. `torch skipped: ModuleNotFoundError — numpy path already trained.`
4. No.
5. `y = 1` if `x0 + 0.5*x1 > 0`, else 0.

</details>

---

## Recap

- **You built** a trained logistic neuron in numpy; loss fell 0.2788 → 0.0611.
- **You understand** torch is optional here and **missing** by design; numpy is the lesson.
- **Next** you will see why **order** of words matters once bags throw it away.

Next: `ml-32-order-matters`

---

## Stretch goal

Change `W = rng.normal(size=(2, 1)) * 0.1` to `* 0.01` (tinier start). Rerun.

- **Expect:** start loss may sit closer to “untrained sigmoid ~0.25–0.5”; end should still fall if 200 steps remain. Compare to 0.2788 / 0.0611, then put `0.1` back.

---

## Feedback

Could you redo this lab from memory? Note the **lesson id** (`ml-31`), the **step number**, what you **expected**, and what you **saw**. If torch printed anything other than `ModuleNotFoundError`, write that class name down — do not install packages to chase it.

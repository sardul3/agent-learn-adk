# ml-27 — One neuron

**Level:** Absolute beginner  
**Time:** ~50 minutes  
**Prerequisites:** ml-26; Python 3.14.6, numpy 2.5.2, sklearn 1.9.0 from the ml-00 venv  
**Lab outcome:** You mix two facts with two weights, add a bias, then squash with ReLU and sigmoid — and you type the arithmetic yourself

---

## At a glance

A **neuron** is a tiny recipe: **multiply, add, squash**.

Maya has two facts: box weight **2.0** and delay **0.5**. The neuron has weights **1.5** and **−0.8**, plus bias **0.2**.

By the end you can:

- compute **z = 2.8** with a pencil (and with `python -c`)
- say **ReLU(2.8) = 2.8** (negatives would have become 0)
- say **sigmoid(2.8) ≈ 0.943**
- refuse to call this “the AI thinking”

You will run `later_labs.py neuron`, then type the same multiply-add in the terminal. No plot.

---

## Why this matters

Every later net in this track (stacked ReLU, backprop, numpy net) is this neuron glued to more neurons.

If you skip the arithmetic, “layer” is a buzzword. Tonight it is four numbers and a plus sign.

Maya does not need a GPU. She needs to see that **2.8** came from **2.0**, **0.5**, **1.5**, **−0.8**, and **0.2**.

---

## Concept primer

| Word | Plain English | In Maya’s warehouse |
| --- | --- | --- |
| **Input x** | Facts you already have | `x = [2.0, 0.5]` → weight kg, delay-ish |
| **Weight w** | Knobs on each fact | `w = [1.5, −0.8]` → “heavier → more”, “delay → less” |
| **Bias b** | A knob with no fact | `b = 0.2` → a baseline nudge |
| **z (pre-activation)** | The mix before the squash | `z = w·x + b = 2.8` |
| **Dot product** | Multiply pairs, add them up | `1.5×2.0 + (−0.8)×0.5` |
| **ReLU** | `max(0, z)` — zeros the negatives | ReLU(2.8) = **2.8** |
| **Sigmoid** | Squash z into (0, 1) | ≈ **0.943** — “pretty sure yes” |

```text
x  →  multiply by w, add b  →  z  →  ReLU and/or sigmoid
```

> **Tip:** ReLU and sigmoid are two different *stories* for the same z. The lab prints both. A real layer usually picks one.

> **Watch out:** `w @ x` in numpy is the dot product. It is not an email address. The `@` is matrix multiply; for two 1D arrays it is the mix.

---

## Setup (short)

You already made the virtual environment in **ml-00**. Reuse it. Do not recreate it. Do not pip-install anything new. **PyTorch is not part of this lesson.**

### Step 1 — Enter the playground and turn the island on

Why now: `later_labs.py` must be the current folder’s script.

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

### Step 2 — Type the mix (then the computer)

Why now: if you only run the lab, you will nod at 2.8. You will not *own* it.

Type these four lines in your terminal notes or a scratch `.txt` — you are doing the arithmetic, not filling a take-home sheet:

```text
1.5 × 2.0  =  3.0
-0.8 × 0.5 = -0.4
3.0 + (-0.4) = 2.6
2.6 + 0.2    = 2.8
```

Now force the same arithmetic through Python. `-c` means “run this string as Python”:

```bash
python -c "print(1.5*2.0 + (-0.8)*0.5 + 0.2)"
```

**Expect:**

```text
2.8
```

If you got 2.8, the neuron has no remaining magic.

- [ ] You typed the four lines of arithmetic
- [ ] `python -c` printed 2.8

### Step 3 — Run the neuron lab

Why this command now: it prints ReLU and sigmoid next to the same z, with numpy’s tiny float tail.

```bash
python later_labs.py neuron
```

`neuron` is a lab name, not a flag.

**It worked when** you see:

```text
z (mix) = 2.8000000000000003 relu = 2.8000000000000003 sigmoid ≈ 0.9426758241011313
```

Read it as:

- **z = 2.8** (the extra `00000000003` is binary float dust — say 2.8)
- **ReLU = 2.8** because 2.8 is already positive
- **sigmoid ≈ 0.943** (the lab’s `≈` is honest)

Confirm sigmoid yourself:

```bash
python -c "import numpy as np; z=2.8; print(1/(1+np.exp(-z)))"
```

**Expect:** `0.9426758241011313` — same as the lab.

- [ ] Lab z matched your pencil 2.8
- [ ] Sigmoid matched ~0.943

### Step 4 — Walk `lab_neuron` (do not paste blindly)

Open `later_labs.py`. Find `lab_neuron` and `_relu`.

1. `x = np.array([2.0, 0.5])` — two facts. Comment in the file says `# weight, delay`.
2. `w = np.array([1.5, -0.8])` — two knobs.
3. `b = 0.2` — the leftover knob.
4. `z = float(w @ x + b)` — mix, then turn a 0-d numpy value into a Python float for printing.
5. `max(0.0, z)` — ReLU written inline (same idea as `_relu`).
6. `1 / (1 + np.exp(-z))` — sigmoid.

`_relu` is used later in `lab_relu_stack`. Tonight the print uses `max(0.0, z)` so you can see the definition without jumping.

ReLU on a **negative** z would be 0. Try it:

```bash
python -c "print(max(0.0, -1.3))"
```

**Expect:** `0.0`. That is the “off” switch. A negative mix does not go more negative through ReLU; it dies.

> **Tip:** Sigmoid(0) = 0.5. Sigmoid(2.8) is close to 1 but not 1. It never quite hits 0 or 1. That is why later lessons can still nudge it.

> **Watch out:** A **layer** is many neurons side by side (same x, different w and b). You have **one** neuron. ml-28 stacks a second layer on six hidden ReLUs.

### Step 5 — Mini experiment (do it)

In `lab_neuron`, change **one number**: `x = np.array([2.0, 0.5])` to `x = np.array([3.0, 0.5])` (heavier box).

Save. Run:

```bash
python later_labs.py neuron
```

Pencil check: `1.5×3.0 + (−0.8)×0.5 + 0.2 = 4.5 − 0.4 + 0.2 = 4.3`.

**Expect:** z ≈ **4.3**, ReLU 4.3, sigmoid even closer to 1.

Put `2.0` back when you are done.

- [ ] You saw z move from 2.8 to ~4.3
- [ ] You put 2.0 back

---

## How it works (deeper)

The computer is not “seeing a box.” It is doing:

```text
z = w1*x1 + w2*x2 + b
relu = max(0, z)
sigmoid = 1 / (1 + e^(-z))
```

**Training** (ml-28, ml-29) means: nudge `w` and `b` so a **loss** gets smaller. Tonight the knobs are frozen. The recipe still counts. Same lesson as Maya’s `5 + 2×weight` in ml-00: a model does not have to be trained to be a model.

`e` in the sigmoid is Euler’s number (~2.718). You do not compute it by hand. `np.exp(-z)` does.

---

## Common pitfalls

1. **`ModuleNotFoundError`.** Venv off. Redo Step 1.
2. **Wrong folder.** `cd project/ml_playground`.
3. **You added 1.5 + 2.0 instead of multiplying.** Mix is **multiply then add**.
4. **You treated 2.8000000000000003 as a different answer.** It is 2.8. Floats are binary.
5. **You pip-installed PyTorch “to see a real neuron.”** Not on this track. Numpy is the neuron.
6. **You called sigmoid a probability of a real refund.** It is a squash of *this* z. Calibration is a later, harder topic.

---

## Knowledge check

Answer from your pencil and the printout.

1. What are x, w, and b in the lab?
2. Show the four arithmetic lines that make z = 2.8.
3. Why is ReLU(2.8) equal to 2.8, not 0?
4. What is sigmoid(2.8) to three decimals, as the lab prints it?
5. If z were −1.3, what would ReLU be?

<details>
<summary>Answers</summary>

1. `x = [2.0, 0.5]`, `w = [1.5, −0.8]`, `b = 0.2`.
2. `1.5×2.0 = 3.0`; `−0.8×0.5 = −0.4`; `3.0−0.4 = 2.6`; `2.6+0.2 = 2.8`.
3. ReLU is `max(0, z)`. 2.8 is already greater than 0.
4. ≈ 0.943 (`0.9426758241011313` in the print).
5. 0.0.

</details>

---

## Recap

- **You built** (by hand and by script) one mix z = 2.8 with ReLU 2.8 and sigmoid ≈ 0.943.
- **You understand** neuron = weighted sum + squash; `@` is the mix.
- **Next** you will stack six hidden ReLUs and watch **loss fall**.

Next: `ml-28-relu-stacking`

---

## Stretch goal

Change `b = 0.2` to `b = 0.0`. Rerun `python later_labs.py neuron`.

- **Expect:** z = 2.6, ReLU 2.6, sigmoid a little below 0.943 (`python -c "import numpy as np; print(1/(1+np.exp(-2.6)))"`).
- Put `b = 0.2` back when you are done.

---

## Feedback

Could you redo this lab from memory? Note the **lesson id** (`ml-27`), the **step number**, what you **expected**, and what you **saw**.

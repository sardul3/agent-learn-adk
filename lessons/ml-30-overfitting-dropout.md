# ml-30 — Overfitting and dropout (the story)

**Level:** Absolute beginner  
**Time:** ~50 minutes  
**Prerequisites:** ml-29; Python 3.14.6, numpy 2.5.2, sklearn 1.9.0 from the ml-00 venv  
**Lab outcome:** You plot a degree-12 polynomial that wiggles around a sine, and you can name dropout and early stopping as two ways Maya refuses to trust that wiggle

---

## At a glance

**Overfitting** means the recipe memorized the sample — including the noise — and will lie on the next box.

This lab’s **picture** is a **degree-12** polynomial chasing 40 noisy sine points. The true wave is `sin(3x)`. The wiggle is the villain.

**Dropout** is the **story** you attach to that picture: do not trust one wiggly teammate. Randomly mute hidden units during training so no single path can memorize. The file does **not** zero neurons. It shows the wiggle dropout is meant to fight.

**Early stopping** is the sibling story: stop nudging when the *exam* score gets worse, even if the training score still looks prettier.

By the end you can:

- point at the scatter, the true sine, and the high-variance poly
- say “dropout” and “early stopping” as two warehouse policies, not two extra plots
- change degree **12** to **3**, see the wiggle calm, put 12 back

You will run `later_labs.py dropout` and walk `lab_dropout`.

---

## Why this matters

Maya can fit a crazy packing-time formula that hits every stopwatch on *tonight’s* 40 boxes and then fails tomorrow. Customers do not care that training error was 0.00.

Neural nets have enough knobs to do the same thing. Dropout and early stopping are two of the seatbelts (ml-13’s L2 was another).

If you skip this lab, “regularization” is a word cloud. Tonight you have a picture of a poly that cannot sit still.

---

## Concept primer

| Word | Plain English | In this lab |
| --- | --- | --- |
| **True wave** | The hidden sine Maya does not get to look up | `sin(3x)` |
| **Noise** | Random jitter on the 40 points | `rng.normal(0, 0.15, n)`, seed 1 |
| **Degree-12 poly** | A wiggly polynomial with 13 coefficients | `np.polyfit(x, y, 12)` |
| **High variance** | Recipe jumps around to hit each point | The legend: `memorizes (high variance)` |
| **Dropout (story)** | During training, randomly turn hidden units off so the net cannot rely on one path | Not implemented as a mask here; the wiggle is why you would want it |
| **Early stopping (sibling)** | Halt when validation loss rises | Named in this lesson; not a second curve in the file |

```text
40 noisy dots  →  fit a degree-12 poly  →  wiggle
                 →  overlay true sin(3x)
```

> **Tip:** Dropout in a real net is a **coin flip per hidden unit per step** (typical rate 0.2–0.5). At test time you keep everyone and scale. Remember the story; do not invent a mask in this file.

> **Watch out:** The script name is `dropout` because of the story. If you search `lab_dropout` for `dropout(` you will find **nothing**. That is honest. The picture is `polyfit(..., 12)`.

---

## Setup (short)

You already made the virtual environment in **ml-00**. Reuse it. Do not recreate it. Do not pip-install torch.

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

### Step 2 — Run the dropout-story lab

Why this command now: the wiggle is the evidence. Words without the plot bounce off.

```bash
python later_labs.py dropout
```

`dropout` is a lab name, not a flag.

**It worked when** a plot opens titled `ml-30: dropout idea — do not trust one wiggly teammate`.

On the plot:

- **dots** = 40 noisy observations (`n = 40`, x from −1 to 1)
- **one curve** = degree-12 polynomial (`memorizes (high variance)`)
- **other curve** = `sin(3x)` (`true wave`)

The poly hugs dots and **bends between them**. The sine stays smooth. Close the window after you can point at a bend that exists only to catch noise.

The lab prints **nothing**. That is fine. Your job is the picture plus the code.

- [ ] You saw dots, a wiggly line, and a smooth sine
- [ ] You said the title out loud once (dropout is the idea, not a layer in this file)

### Step 3 — Measure the wiggle with three x-values

Why now: “it wiggles” needs a couple of numbers. Same venv:

```bash
python -c "
import numpy as np
rng = np.random.default_rng(1)
x = np.linspace(-1, 1, 40)
y = np.sin(3 * x) + rng.normal(0, 0.15, 40)
c = np.polyfit(x, y, 12)
for t in (0.0, 0.95, 1.0):
    print(t, 'poly', round(float(np.polyval(c, t)), 3), 'sine', round(float(np.sin(3*t)), 3))
print('max |coef|', round(float(np.max(np.abs(c))), 2))
"
```

`-c` means “run this string as Python.”

**Expect** (pinned seed 1):

```text
0.0 poly -0.002 sine 0.0
0.95 poly 0.214 sine 0.287
1.0 poly 0.179 sine 0.141
```

```text
max |coef| 41.07
```

Near the middle the poly can look almost fine. Near the edge (x=1) it is already off the true wave (0.179 vs 0.141) and the **coefficients are huge** (41). Huge knobs are a classic overfit smell — same family as ml-13’s L2 story.

- [ ] `max |coef|` printed about 41
- [ ] At x=1 the poly and the sine disagree

### Step 4 — Walk `lab_dropout` (do not paste blindly)

Open `later_labs.py`. Find `lab_dropout`.

1. `rng = np.random.default_rng(1)` — seed **1** (not 0). Frozen noise.
2. `n = 40` then `x = np.linspace(-1, 1, n)` — 40 x’s evenly spaced.
3. `y = np.sin(3 * x) + rng.normal(0, 0.15, n)` — true wave plus noise std **0.15**.
4. `c_hi = np.polyfit(x, y, 12)` — **degree 12**. That is the one number that creates the wiggle.
5. Scatter the 40 dots.
6. `np.polyval(c_hi, xs)` on a fine grid of 100 x’s — the wiggly line.
7. `np.sin(3 * xs)` — the true wave Maya does not get in production.
8. `ax.legend()` so you can read the two names.

**Dropout, in words you can tell Maya:**

- Imagine six hidden ReLUs from ml-28.
- Each training step, flip a coin and **mute** some of them (set those activations to 0).
- The remaining teammates must still predict.
- No single wiggly path can memorize a dot.
- At test time, use all teammates (and scale).

**Early stopping, sibling:**

- Split a val pile (ml-06).
- Plot train loss and val loss.
- When val loss turns **up**, stop — even if train loss still falls.
- You did not add dropout. You just refused extra wiggle.

L2 (ml-13) is the third sibling: tax huge coefficients (that `41.07`).

> **Tip:** High **degree** here plays the same role as “too many hidden units” in a net. More knobs, more wiggle.

> **Watch out:** `np.polyfit` is not a neural net. We use it because the wiggle is visible on a laptop in two seconds. The dropout *policy* still applies to nets.

### Step 5 — Mini experiment (do it)

In `lab_dropout`, change **one number**: `np.polyfit(x, y, 12)` to `np.polyfit(x, y, 3)`.

Save. Run:

```bash
python later_labs.py dropout
```

**Expect:** the “memorizes” curve calms down and sits closer to the sine. Some noise is ignored. That is **lower variance**, maybe a little **more bias** (ml-09).

Put `12` back when you are done so this lesson’s screenshot still matches.

- [ ] Degree 3 looked calmer
- [ ] You put 12 back

---

## How it works (deeper)

A degree-12 polynomial can make 11 bends. 40 noisy points are easy to chase. Tomorrow’s x will not have the same noise, so those bends become mistakes.

```text
too many knobs  →  hit every tonight-dot  →  miss tomorrow
dropout         →  force many knobs to share the work
early stop      →  quit when tomorrow-like val gets worse
L2              →  keep coefficients from exploding (41 → smaller)
```

The computer is not “being creative.” It is interpolating. Maya’s job is to pick a seatbelt.

---

## Common pitfalls

1. **`ModuleNotFoundError`.** Venv off. Redo Step 1.
2. **Plot never opens.** `unset ML_HEADLESS` on a laptop.
3. **You grepped for `dropout` in the function body and thought the lab was broken.** The title and the lesson carry the story. The code shows the wiggle.
4. **You called the sine “the model.”** The sine is **truth**. The poly is the overfit recipe.
5. **You added a dropout layer in PyTorch.** Not this track. Numpy picture only.
6. **You treated early stopping as “stop at 12 steps always.”** It is “watch val loss,” not a magic integer.

---

## Knowledge check

Answer from the plot, Step 3, and the file.

1. How many points, what degree, what is the true function?
2. What is `max |coef|` on this seed, roughly?
3. Does `lab_dropout` randomly zero hidden units?
4. What is dropout, in one Maya sentence?
5. What is early stopping, and why is it a sibling rather than a rival?

<details>
<summary>Answers</summary>

1. 40 points; degree 12; `sin(3x)`.
2. About 41.07.
3. No. It fits `np.polyfit(..., 12)` and plots.
4. Do not trust one wiggly teammate — randomly mute hidden units while training so the recipe cannot memorize through a single path.
5. Early stopping quits when the val score worsens. Same goal (less wiggle), different knob. You can use both.

</details>

---

## Recap

- **You built** a picture of a degree-12 poly vs a sine plus noise.
- **You understand** overfit = memorize noise; dropout = mute teammates; early stopping = quit on val.
- **Next** you will train a **numpy** logistic net until loss falls, and skip PyTorch on this Python.

Next: `ml-31-numpy-net`

---

## Stretch goal

Change `rng.normal(0, 0.15, n)` to `rng.normal(0, 0.01, n)` (almost no noise). Keep degree 12. Rerun.

- **Expect:** the poly sits closer to the sine because there is less noise to memorize. Overfit is quieter when the world is cleaner — that does not make degree 12 safe on real tickets.
- Put `0.15` back when you are done.

---

## Feedback

Could you redo this lab from memory? Note the **lesson id** (`ml-30`), the **step number**, what you **expected**, and what you **saw**.

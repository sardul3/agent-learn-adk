# ml-01 — Functions, slope, intercept

**Level:** Absolute beginner  
**Time:** ~50 minutes  
**Prerequisites:** ml-00 (venv already created in `project/ml_playground`)  
**Lab outcome:** You can say what slope and intercept mean for packing minutes, and you have dragged both until the line sits on Maya’s dots

---

## At a glance

A **function** is a machine: put a number in, get a number out. For a straight line:

```text
minutes = m × weight + b
```

- **m** (slope) = extra minutes per extra kilo
- **b** (intercept) = minutes even if the box were weightless (a starting offset)

By the end you can explain:

- why a too-small slope makes heavy boxes late
- why you match the cloud’s *tilt* before you slide the line up or down
- why a perfect line through every dot is the wrong goal

---

## Why this matters

If Maya’s slope is too small, a 10 kg crate is always late to the van while a 1 kg envelope looks fine. Slope is not a ski hill here. It is a **rate**: minutes per kilogram.

You already saw her frozen recipe `5 + 2 × weight` in ml-00. Today you *move* the 2 and the 5 with sliders until the orange line matches the warehouse cloud by eye. That eye-fit is the skill underneath automatic training in ml-05.

---

## Concept primer

| Word | Plain English | Warehouse sentence |
| --- | --- | --- |
| **Function** | A rule: in → out | Put in 3 kg, get out a minute guess |
| **Slope m** | How much the output changes when the input goes up by 1 | Extra minutes per kilo |
| **Intercept b** | Output when input is 0 | Minutes of “setup” even for a feather |
| **Line** | The picture of that function | Orange stroke across the scatter |

Worked number: if `m = 2` and `b = 4`, a 3 kg box is `2×3 + 4 = 10` minutes.

A slope of **0** means weight does not change the guess. The line is flat. Maya would never ship that.

> **Tip:** Real boxes are not 0 kg. Intercept is still useful: it soaks up “fixed” time (grab tape, walk to the bench).

> **Watch out:** A perfect line through every dot is not the goal. Night-shift noise exists. A good line is honestly close.

---

## Setup

If your prompt does not show `(.venv)`, finish Setup in ml-00 first.

```bash
cd project/ml_playground
source .venv/bin/activate
```

- `source` runs the activate script in *this* terminal so `python` is the island’s Python.

**It worked when** `(.venv)` is at the front of the prompt.

---

## Hands-on

### Step 1 — Open the slider lab

Why now: reading `m` and `b` is cheap. Feeling them move the line is what sticks.

```bash
python m0_labs.py slope
```

`slope` is the lab name (an argparse choice), not a dash-flag.

**It worked when** a window opens titled `ml-01: drag slope (m) and intercept (b). Guess = m*weight + b` with:

- a cloud of warehouse dots
- two sliders at the bottom: **slope m** (0 to 4) and **intercept b** (−2 to 12)
- an orange line that moves when you drag

Starting values in the code are `m = 1.0` and `b = 2.0`. That first line is usually too flat and too low. That is on purpose.

### Step 2 — Match tilt, then height

1. Drag **slope m** until the orange line’s tilt matches the cloud. Ignore up/down for a moment.
2. Then drag **intercept b** to slide the line up or down onto the middle of the cloud.
3. Stay until you can say “this looks about right” without chasing every outlier.

**It worked when** most dots sit near the line, with scatter above and below, not a line that snakes through every point (you cannot snake — it is a straight line).

> **Tip:** Tilt first, height second. If you only slide `b`, a wrong slope stays wrong forever.

> **Watch out:** The hidden story in `packing_orders` is about `m ≈ 1.8` and a base near 4 *plus zone*. You only have weight on this plot, so the “right” line is a compromise. Do not hunt for a magic pair that zeros every error.

### Step 3 — Walk the code

Open `m0_labs.py`. Find `lab_slope`.

- `packing_orders(60)` — sixty dots so the cloud has a shape. ml-00 used 12 so you could read a table.
- `Slider(..., valinit=1.0)` — starting slope.
- Inside `redraw`:

```text
xs = evenly spaced weights from lightest to heaviest
line = m * xs + b
```

`line.set_data(...)` is the function. Every slider twitch re-runs that multiply-add.

`s_m.on_changed(redraw)` means “when the slope slider moves, call `redraw`.” Same for `s_b`.

- [ ] You dragged both sliders
- [ ] You can say slope in a Maya sentence (“extra minutes per kilo”)
- [ ] You found `line.set_data` in the file

### Step 4 — Mini experiment

In `lab_slope`, change the slope slider’s maximum from `4.0` to `8.0`:

```python
s_m = Slider(ax_m, "slope m", 0.0, 8.0, valinit=1.0)
```

Save. Rerun `python m0_labs.py slope`.

- **Expect:** you *can* now make a ridiculous steep line (a kilo “costs” 8 minutes). The extra room is not wiser. It is just a wider toy.
- Put `4.0` back when you are done.

---

## How it works (deeper)

A line has two knobs. That is the whole flexibility of this model.

```
weight ──► × m ──► + b ──► minutes
```

Later, **training** will nudge `m` and `b` using error (ml-05). Today *you* are the trainer. Your eye is a loss function: “does this look close?”

sklearn’s `LinearRegression` (ml-10) solves the same two knobs, just without sliders.

---

## Common pitfalls

1. **Sliders do nothing.** You clicked the plot, not the thin bars at the bottom. Aim at the **slope m** / **intercept b** tracks.
2. **Window frozen after close.** Close the figure to get the terminal back, then rerun. matplotlib `show()` blocks.
3. **`(.venv)` missing after a new tab.** Activation is per terminal. `source .venv/bin/activate` again.
4. **You flattened m to 0 “to be simple.”** That model ignores weight. Heavy crates would all get the same guess.

---

## Knowledge check

1. If `m = 2` and `b = 4`, what is the guess for a 3 kg box?
2. What does a slope of 0 mean in the warehouse?
3. Why match tilt before height?
4. The sliders start at `m = 1.0`, `b = 2.0`. Is that pair the hidden truth in `packing_orders`?

<details>
<summary>Answers</summary>

1. `2×3 + 4 = 10` minutes.
2. Weight does not change the guess; the line is flat.
3. A wrong slope cannot be fixed by sliding the line up. You would miss light and heavy boxes in opposite ways.
4. No. The hidden minutes are about `4 + 1.8×weight + 0.6×zone + noise`. The start values are just a weak first try.

</details>

---

## Recap

- **You dragged** slope `m` and intercept `b` across real packing dots.
- **You understand** slope as extra minutes per kilo, intercept as a starting offset.
- **Next** a vector is just an ordered list of features, drawn as an arrow.

Next: `ml-02-vectors-as-feature-lists`

---

## Stretch goal

Set `valinit` on the slope slider to `1.8` (closer to the hidden rate) and reopen the lab.

- **Expect:** the first line is already closer; you mostly tune `b`.
- Put `valinit=1.0` back so the “too flat” first impression remains for the next reader (you, tomorrow).

---

## Feedback

Could you redo this lab from memory? Note **ml-01**, the step number, what you expected, and what you saw.

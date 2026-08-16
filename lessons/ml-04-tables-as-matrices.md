# ml-04 — Tables as matrices

**Level:** Absolute beginner  
**Time:** ~45 minutes  
**Prerequisites:** ml-03  
**Lab outcome:** You can say what a row and a column mean in the packing heatmap, and why you must not average a mixed-unit row

---

## At a glance

A **matrix** is a table of numbers. No mystic object.

- **Rows** = orders (examples)
- **Columns** = features (weight, zone, hour)

Shape `(20, 3)` means 20 rows and 3 columns. Later, “matrix × vector” is just the ml-03 mix on **every row**.

By the end you can read the first five printed rows and point at the heatmap without calling color “temperature of the warehouse.”

---

## Why this matters

Training does not look at one box. It looks at a stack of boxes. Maya’s night is a table. If you cannot say “row 0 is one order,” later words like *batch* are fog.

This lab also plants a lie you will kill in ml-08: **hour looks “more important” only because 6–21 is a bigger number than 0.4–12 kg.**

---

## Concept primer

| Word | Plain English | In this lab |
| --- | --- | --- |
| **Matrix** | Rectangle of numbers | 20 orders × 3 features |
| **Row** | One example | One packing order |
| **Column** | One feature across examples | All weights, or all zones, or all hours |
| **Shape** | `(rows, columns)` | `(20, 3)` |
| **Heatmap** | Color = bigger/smaller | `imshow` of the table |

```
          weight   zone   hour
order 0    7.65     2      10
order 1   10.81     1      13
...
```

> **Tip:** Zone is 1–4, hour is 6–21. Hour glows hotter on the magma scale. That is not “hour matters more.” That is units.

> **Watch out:** Do not average a row that mixes kg, zone-id, and hour and call it “the order’s vibe.” Units differ.

---

## Setup

```bash
cd project/ml_playground
source .venv/bin/activate
```

---

## Hands-on

### Step 1 — Print five rows and open the heatmap

Why now: you need the numbers *and* the picture. The picture without the print is just a pretty rug.

```bash
python m0_labs.py matrix
```

**It worked when** the terminal prints:

```text
Rows = orders. Columns = features.
[[ 7.65  2.   10.  ]
 [10.81  1.   13.  ]
 [ 9.4   4.   12.  ]
 [ 3.01  1.    9.  ]
 [ 3.88  4.   21.  ]]
```

and a heatmap titled `ml-04: a matrix is a table of numbers` with x-ticks **weight / zone / hour**.

Read row 0 out loud: “7.65 kg, zone 2, hour 10.”

Hour 21 in row 4 should be the brightest cell in those five rows. That is the lying plot.

### Step 2 — Walk the code

Open `m0_labs.py`. Find `lab_matrix`.

- `packing_orders(20)` — twenty orders.
- `df[["weight_kg", "zone", "hour"]].to_numpy()` — drop the minutes column. The matrix is **inputs only**.
- `ax.imshow(mat, aspect="auto", cmap="magma")` — color from small (dark) to large (bright).
- `set_xticks([0, 1, 2], ["weight", "zone", "hour"])` — column names so you do not have to remember 0/1/2.

Truth minutes live in `pack_minutes`. They are **not** in this heatmap. This is features, not labels.

### Step 3 — Mini experiment

Add `pack_minutes` to the column list:

```python
mat = df[["weight_kg", "zone", "hour", "pack_minutes"]].to_numpy()
```

and add a fourth x-tick `"minutes"`. Rerun.

- **Expect:** a fourth column that also glows (minutes are ~5–25). You just mixed **inputs and the answer** in one picture. That is a visual cousin of leakage (ml-07).
- Put the three-column version back.

- [ ] You read row 0 as one order
- [ ] You know column 2 is hour
- [ ] You did not average a mixed row

---

## How it works (deeper)

A vector is one row. A matrix is a stack of rows.

When we later write `X @ w`, numpy does the ml-03 mix for each row:

```
guesses = matrix_of_orders  ×  knobs
          (20 × 3)             (3 × 1)
          → 20 guesses
```

You do not need to multiply by hand today. You need the *shape story*.

---

## Common pitfalls

1. **You thought magma color meant heat in the warehouse.** It means “larger number in that cell.”
2. **Wrong folder.** `cd project/ml_playground` so `meridian_data` imports.
3. **You included `pack_minutes` as a feature and called it extra intelligence.** That is the answer column. Keep it off the input matrix unless you are doing the stretch and then revert.

---

## Knowledge check

1. What does row 0 mean?
2. What does column 2 mean in this lab?
3. What is the shape of the matrix `lab_matrix` builds?
4. Why does hour dominate the color scale?

<details>
<summary>Answers</summary>

1. One order’s three features: weight, zone, hour.
2. Hour of day.
3. `(20, 3)`.
4. Hour values (~6–21) are numerically larger than kg (~0.4–12) and zone (1–4). Color follows the number, not importance.

</details>

---

## Recap

- **You viewed** a 20×3 packing table as a heatmap.
- **You understand** row = example, column = feature.
- **Next** you score error and nudge a knob downhill.

Next: `ml-05-error-and-nudge`

---

## Stretch goal

Print `mat.shape` and `mat.mean(axis=0)` (column averages).

- **Expect:** shape `(20, 3)`; three very different averages (kg vs zone vs hour).
- Remove the prints when done.

---

## Feedback

Could you redo this lab from memory? Note **ml-04**, step, expected vs saw.

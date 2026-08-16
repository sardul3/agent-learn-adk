# ml-20 — PCA rotate

**Level:** Absolute beginner  
**Time:** ~50 minutes  
**Prerequisites:** ml-19; Python 3.14.6, numpy 2.5.2, sklearn 1.9.0 from the ml-00 venv  
**Lab outcome:** You scale length and weight by hand, rotate with PCA(2), and know the colors are a cheat sheet

---

## At a glance

**PCA** (principal component analysis) is a recipe that **rotates** a table so the first new axis points the way the cloud spreads most.

It is not a classifier. It does not read SKU names. It does not use `true_group`.

By the end you can:

- scale a column (subtract mean, divide by std) and say why
- point at **pc1** vs **pc2** on the plot
- say out loud: “the colors are `true_group` — a cheat sheet for my eyes; PCA never saw that column”

You will run `later_labs.py pca` and walk `lab_pca`.

---

## Why this matters

Maya still has the same 90 SKUs from ml-19: length in cm, weight in kg. After clustering, she wants a picture where “size” is one left-right number, not two columns she has to squint at.

If length stayed in centimeters (roughly 4–59) and someone added `price_cents` (thousands), the big numbers would dominate any “spread” recipe. Scaling is the seatbelt. PCA is the rotation after the seatbelt.

If you skip this lab, later “embeddings” look like magic. Tonight they are: center, stretch, rotate.

---

## Concept primer

| Word | Plain English | In Maya’s warehouse |
| --- | --- | --- |
| **Scale** | Put each column in comparable units | `(length − mean) / std` so both axes are “how many stds from typical” |
| **Mean** | Average | Raw length mean **24.41** cm; weight mean **6.92** kg |
| **Std** | Typical spread around the mean | Raw length std **16.26**; weight std **6.85** |
| **PCA** | Rotate to directions of most spread | pc1 ≈ “overall size”; pc2 ≈ “long-but-light vs short-but-heavy” |
| **pc1 / pc2** | The new axes after rotation | Plot x = pc1, y = pc2 |
| **Cheat-sheet color** | A label you paint on after, for your eyes | `true_group` colors; **not** an input to PCA |

```text
raw table  →  subtract mean, divide std  →  rotate (PCA)  →  2D dots
                    ↑
              PCA never sees true_group
```

> **Tip:** If both columns already have similar-sized numbers, PCA still works. Scaling is still the honest default so one unit does not bully the other.

> **Watch out:** Pretty colors do not mean “the model used the label.” This lab paints `true_group` on purpose so you can *see* the three blobs. That is a legend for humans, not a feature for PCA.

---

## Setup (short)

You already made the virtual environment in **ml-00**. Reuse it. Do not recreate it. Do not pip-install anything new.

### Step 1 — Enter the playground and turn the island on

Why now: `later_labs.py` imports `meridian_data.py` from the current folder. If you skip `cd`, the import fails.

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

If the venv is missing, go back to ml-00 Setup once.

---

## Hands-on

### Step 2 — Run the PCA lab

Why this command now: the plot is the whole point. PCA without a picture is two new column names.

```bash
python later_labs.py pca
```

`pca` is a lab name, not a flag.

**It worked when** a scatter plot opens titled `ml-20: PCA rotates so the spread is easy to see`, with axes labeled `pc1` and `pc2`.

The lab prints **nothing** else. That is on purpose. Your job is the picture plus the code.

On the plot:

- **x** = pc1 (direction of most spread after scaling)
- **y** = pc2 (the leftover direction)
- **dot color** = `true_group` (0 / 1 / 2) — **cheat sheet**

Close the window after you can see three color families stretched along pc1.

- [ ] The window title matches ml-20
- [ ] You said “colors are true_group, not PCA’s output”

### Step 3 — Prove the scale with four numbers

Why now: if you skip this, “we standardized” is a slogan. Type this while the venv is on:

```bash
python -c "
from meridian_data import skus
import numpy as np
X = skus()[['length_cm','weight_kg']].to_numpy()
print('raw mean', np.round(X.mean(0), 2))
print('raw std', np.round(X.std(0), 2))
Xs = (X - X.mean(0)) / X.std(0)
print('scaled mean', np.round(Xs.mean(0), 6))
print('scaled std', np.round(Xs.std(0), 6))
"
```

`-c` means “run this string as Python.”

**Expect:**

```text
raw mean [24.41  6.92]
raw std [16.26  6.85]
scaled mean [-0.  0.]
scaled std [1. 1.]
```

After scale, each column is “how many stds from typical.” Mean **0**, std **1**. That is the seatbelt.

- [ ] Raw means matched 24.41 and 6.92
- [ ] Scaled means printed as zeros

### Step 4 — Walk `lab_pca` (do not paste blindly)

Open `later_labs.py`. Find `lab_pca`.

1. `df = skus()` — same 90 rows as ml-19.
2. `X = df[["length_cm", "weight_kg"]].to_numpy()` — a 90 × 2 table. **No** `true_group` in `X`.
3. `Xs = (X - X.mean(0)) / X.std(0)` — **manual** scale. `0` here means “along columns.” This is not sklearn’s `StandardScaler`; it is the same arithmetic written in the open.
4. `z = PCA(2).fit_transform(Xs)` — fit the rotation on the scaled table, then transform every row into two new numbers (pc1, pc2).
5. `ax.scatter(z[:, 0], z[:, 1], c=df["true_group"], cmap="tab10")` — plot those two numbers. **Color comes from `true_group` after the fact.**

`PCA(2)` means “give me 2 principal components.” You already have 2 input columns, so this is a rotation (plus a possible flip of sign), not a compression to a smaller table. Compression would be `PCA(1)`: one number per SKU.

On this frozen seed, sklearn’s PCA reports:

- pc1 explains **0.9093** of the scaled variance (about 91%)
- pc2 explains **0.0907** (about 9%)
- the first loading is `[0.7071, 0.7071]` — equal mix of scaled length and scaled weight. That is “overall size.”

You do not need to print those in the lab. They are here so “pc1 is the spread axis” is a number, not a vibe.

> **Tip:** `fit_transform` means “learn the rotation from this table, then apply it to the same table.” Later, on new SKUs, you would `transform` only — do not refit on the exam pile (ml-07 leakage still applies).

> **Watch out:** If you colored by K-means labels instead, you would be staring at ml-19’s piles. This lesson colors by **truth** so you can see that a rotation of the *features* still lines up with groups PCA was never told about. That is a picture for you. It is not PCA “cheating.”

### Step 5 — Mini experiment (do it)

In `lab_pca`, change the scale line so you **skip** dividing by std — wait, that is two edits. Change **one number** instead: call `skus(n=30)` instead of `skus()`.

`n` is how many SKUs to draw. Default is 90.

Save. Run:

```bash
python later_labs.py pca
```

**Expect:** fewer dots, same two axes, colors still mean `true_group`. The cloud is sparser. Put `skus()` back (drop `n=30`) when you are done.

- [ ] You saw 30 dots instead of 90
- [ ] You put the call back

---

## How it works (deeper)

Think of the 90 scaled pairs as a pancake of dots on the table.

PCA finds the direction you would stretch a rubber band to cover the pancake’s longest axis. That direction becomes pc1. The leftover perpendicular direction becomes pc2.

```text
scaled SKU  →  mix length and weight  →  pc1 (size)
            ↘ mix length minus weight →  pc2 (shape leftover)
```

The computer is not “understanding bulk.” It is lining up axes with variance.

**Supervised** recipes (ml-10–ml-18) used a label to score guesses. PCA scores nothing against Maya’s tiny/mid/bulky names. Those names only tint the scatter so your eyes can check “did the blobs survive the rotation?”

This is also **not** Pack D RAG embeddings. Those are a different recipe on text. Same geometric idea (nearby = similar), different factory.

---

## Common pitfalls

1. **`ModuleNotFoundError`.** Venv off. `source .venv/bin/activate` in `project/ml_playground`.
2. **Cannot import `meridian_data`.** Wrong folder. `cd` first.
3. **Plot never opens.** `unset ML_HEADLESS` on a laptop and rerun.
4. **You said “PCA predicted the group.”** It did not predict. You painted `true_group` on the dots.
5. **You skipped scale and then blamed PCA.** On this toy both columns are already similar magnitude. On a table with `length_cm` and `price_cents`, skipping scale makes pc1 ≈ price. Always look at means and stds (Step 3).
6. **You thought `PCA(2)` invented two extra facts.** You still have two numbers per SKU. They are rotated, not multiplied out of thin air.

---

## Knowledge check

Answer from Step 3, the plot, and `lab_pca`.

1. What are the raw means of length and weight on these 90 SKUs?
2. After `(X - mean) / std`, what should the column means be?
3. Which column does `PCA(2).fit_transform(Xs)` use: `Xs` or `true_group`?
4. Why are the dots colored if PCA is unsupervised?
5. pc1 explains about **0.91** of scaled variance here. Does that mean Maya can throw weight in the trash?

<details>
<summary>Answers</summary>

1. Length 24.41 cm; weight 6.92 kg.
2. About 0.0 (the print shows `[-0.  0.]`).
3. Only `Xs` (scaled length and weight).
4. `c=df["true_group"]` is a legend for your eyes. PCA did not use that column.
5. No. pc1 is a **mix** of scaled length and scaled weight (loadings both ~0.71). Weight is still in the recipe. You would throw a column away only after you prove it adds nothing — not because pc1 is large.

</details>

---

## Recap

- **You built** a pc1/pc2 scatter of 90 scaled SKUs.
- **You understand** scale = mean 0, std 1; PCA = rotate to spread; colors can be a cheat sheet.
- **Next** you will flag weird scan times without a “this scan is bad” label.

Next: `ml-21-anomaly-scan-times`

---

## Stretch goal

In `lab_pca`, change `skus()` to `skus(seed=99)`. Rerun.

- **Expect:** a different cloud, still 2D, colors still `true_group`.
- Put `skus()` back (seed 11 by default) when you are done.

---

## Feedback

Could you redo this lab from memory? Note the **lesson id** (`ml-20`), the **step number**, what you **expected**, and what you **saw** (traceback or plot).

# ml-21 — Anomaly scan times

**Level:** Absolute beginner  
**Time:** ~50 minutes  
**Prerequisites:** ml-20; Python 3.14.6, numpy 2.5.2, sklearn 1.9.0 from the ml-00 venv  
**Lab outcome:** You flag four weird scan seconds and know which two were planted

---

## At a glance

An **anomaly** is a row that does not look like the others. Maya does not have a column named `is_weird`. She has 120 scan times in seconds.

**Isolation Forest** is a recipe that tries to isolate points that are easy to cut away from the pack. You tell it a **contamination** — the fraction you are willing to call weird.

By the end you can:

- read flagged indices `[17 42 58 88]` and their values
- point at the two **planted** bugs in `scan_times()`: `times[17] = 9.8` and `times[88] = 0.05`
- explain why 42 and 58 also went red: `contamination=0.03` asked for about four flags

You will run `later_labs.py anomaly` and walk `lab_anomaly`.

---

## Why this matters

Every box at Meridian gets a barcode scan. Typical time is a bit over two seconds. A hung scanner that sits on one box for **9.8** seconds jams the line. A scan of **0.05** seconds is “it beeped at empty air.”

Maya cannot hire someone to label 120 scans as good/bad tonight. She needs a recipe that shouts “this one is not like the others.”

If you skip this lab, “anomaly detection” stays a vendor slide. Tonight it is four red dots on a line plot, two of which you planted on purpose.

---

## Concept primer

| Word | Plain English | In Maya’s warehouse |
| --- | --- | --- |
| **Anomaly / outlier** | A point far from the usual pack | 9.8 s scan among ~2.4 s scans |
| **Inlier** | A point that looks typical | Most of the 120 times |
| **Isolation Forest** | Many random trees that isolate points; easy-to-isolate = weirder | sklearn `IsolationForest` |
| **Contamination** | The fraction you *budget* as weird | `0.03` × 120 ≈ **3.6**, so the lab flags **4** |
| **Predict −1 / +1** | sklearn’s outlier / inlier codes | `flag = predict(...) == -1` |
| **Planted** | A value you shoved in by hand to test the recipe | Index 17 = 9.8; index 88 = 0.05 |

```text
120 scan seconds  →  IsolationForest(contamination=0.03)  →  red flags
                         ↑
              you asked for ~3% weird, not “only planted bugs”
```

> **Tip:** Contamination is a **budget**, not a truth. If you budget 3%, you will get about 3% red dots even when only two scans are actually broken.

> **Watch out:** A flag is not a conviction. Index 42 at ~1.90 s is a bit fast, not a 9.8 s freeze. Maya still looks with her eyes.

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

---

## Hands-on

### Step 2 — Run the anomaly lab

Why this command now: you need the four indices in your terminal, not in a summary.

```bash
python later_labs.py anomaly
```

`anomaly` is a lab name, not a flag.

**It worked when** a line plot opens titled `ml-21: weird scan seconds`, with four red dots, and the terminal prints:

```text
flagged indices [17 42 58 88] values [9.8        1.90054583 3.00793313 0.05      ]
```

Read that as:

| Index | Seconds | What it is |
| --- | --- | --- |
| **17** | **9.8** | Planted freeze (way too slow) |
| **42** | **~1.90** | Extra flag from the 3% budget (a bit fast) |
| **58** | **~3.01** | Extra flag from the 3% budget (a bit slow) |
| **88** | **0.05** | Planted ghost beep (way too fast) |

The line is all 120 times in order. Red dots sit on the flagged indices. Close the window after you find the spike at 17 and the dip at 88.

- [ ] Indices printed `[17 42 58 88]`
- [ ] You can say which two were planted

### Step 3 — Open the plant in `scan_times()`

Why now: if you only trust the plot, you might think the forest “found fraud.” It found **easy-to-isolate** points. Two of them you shoved in.

Open `meridian_data.py`. Find `scan_times`.

```text
times = rng.normal(2.4, 0.25, size=n)   # n=120, seed=5
times[17] = 9.8
times[88] = 0.05
```

- Most scans are drawn as a bell around **2.4** seconds with std **0.25**.
- Then index **17** is overwritten to **9.8**.
- Then index **88** is overwritten to **0.05**.

There is **no** `times[42] = ...` and **no** `times[58] = ...`. Those two survived as ordinary random draws and still got flagged.

On this seed the whole series (including plants) has mean **2.3988** and std **0.7435**. The std jumped because 9.8 and 0.05 sit far away. The *hidden* generator’s std was 0.25 before the plants.

- [ ] You found both assignment lines
- [ ] You confirmed 42 and 58 are not assigned by hand

### Step 4 — Walk `lab_anomaly` (do not paste blindly)

Open `later_labs.py`. Find `lab_anomaly`.

1. `t = scan_times()` — a length-120 numpy vector of seconds.
2. `IsolationForest(contamination=0.03, random_state=0)` — build the recipe.
3. `.fit(t.reshape(-1, 1))` — sklearn wants a **column** (120 rows, 1 feature). `reshape(-1, 1)` means “whatever length, one column.”
4. `iso.predict(...) == -1` — predict returns **−1** for outlier, **+1** for inlier. `flag` is True on the red ones.
5. `np.where(flag)[0]` — the indices where flag is True: `17, 42, 58, 88`.
6. `t[flag]` — the four second values.
7. `ax.plot(t)` then `ax.scatter(...)` in red (`color="C3"`) on top (`zorder=3` so dots sit above the line).

Constructor knobs:

- `contamination=0.03` — treat about 3% of rows as outliers. `0.03 * 120 = 3.6`, so you get **4** flags on this run.
- `random_state=0` — freeze the forest’s random cuts so your four indices match this lesson.

> **Tip:** `predict` codes are easy to mix up. **−1** is the weird one. That is why the lab writes `== -1` instead of `== 1`.

> **Watch out:** Isolation Forest will spend the whole contamination budget. If you plant two monsters and budget four flags, two extra “kinda weird” scans go red. That is not a bug in sklearn 1.9.0. That is the knob you set.

### Step 5 — Mini experiment (do it)

In `lab_anomaly`, change **one number**: `contamination=0.03` to `contamination=0.01`.

Save. Run:

```bash
python later_labs.py anomaly
```

**Expect:** fewer red dots (about `0.01 * 120 ≈ 1` flag, often the most extreme plant). The 9.8 s freeze should still be easy to isolate. Index 42 at ~1.90 s should drop off the list.

Put `0.03` back when you are done.

- [ ] You saw the flag list shrink
- [ ] You put 0.03 back

---

## How it works (deeper)

A normal scan sits in a tight crowd around 2.4 seconds. To isolate it, a random tree has to make fussy cuts. A 9.8 second scan sits alone. One coarse cut (“greater than 5?”) isolates it. “Easy to isolate” becomes a high anomaly score.

```text
for many random trees:
    keep splitting the seconds axis at random
    points that fall into a tiny leaf in few splits = weirder
then:
    rank points, paint the worst contamination fraction red
```

The computer is not “knowing” a scanner froze. It is ranking isolation. Maya still decides whether to reboot the gun or ignore a 1.90 s blip.

This is still **unsupervised**: no `is_jam` label in the fit. Same family as k-means and PCA, different question (“who is unlike the pack?” vs “who sits together?” vs “which way does the cloud stretch?”).

---

## Common pitfalls

1. **`ModuleNotFoundError`.** Venv off. Redo Step 1.
2. **Wrong folder.** `cd project/ml_playground` first.
3. **Plot never opens.** `unset ML_HEADLESS` on a laptop.
4. **You called all four flags “planted.”** Only 17 and 88 are planted. 42 and 58 are budget extras.
5. **You read `predict == 1` as outlier.** In this API, **+1** is inlier. **−1** is outlier.
6. **You set contamination=0.5 “to be safe.”** Half the line goes red. Maya cannot act on 60 flags. Start small.

---

## Knowledge check

Answer from the printout and `scan_times()`, not from a vibe.

1. Which indices were flagged, and what are the four values (rounded is fine for 42 and 58)?
2. Which two values were assigned by hand in `scan_times()`, and to which indices?
3. Why did indices 42 and 58 flag if nobody planted them?
4. What does `contamination=0.03` mean on 120 scans, as a count?
5. What does `reshape(-1, 1)` do, and why does `fit` want it?

<details>
<summary>Answers</summary>

1. Indices 17, 42, 58, 88. Values 9.8, ~1.90, ~3.01, 0.05.
2. `times[17] = 9.8` and `times[88] = 0.05`.
3. Isolation Forest spends the contamination budget. After the two plants, it still needs more flags to reach ~3%. 42 (fast-ish) and 58 (slow-ish) were next.
4. About 3.6, so this run flagged 4.
5. It turns a length-120 vector into a 120 × 1 table. sklearn estimators expect rows = samples, columns = features.

</details>

---

## Recap

- **You built** a scan-time plot with four red flags `[17, 42, 58, 88]`.
- **You understand** planted ≠ every flag; contamination is a budget; −1 means outlier here.
- **Next** you will split a ticket sentence into **tokens** and a **vocab**.

Next: `ml-22-tokens-vocab`

---

## Stretch goal

In `scan_times()` inside `meridian_data.py`, change `times[17] = 9.8` to `times[17] = 2.4` (a normal-looking value). Rerun `python later_labs.py anomaly`.

- **Expect:** index 17 may drop out of the flags. 88 at 0.05 should still be easy to isolate. Other indices may rotate into the budget.
- Put `9.8` back when you are done so this lesson still matches.

---

## Feedback

Could you redo this lab from memory? Note the **lesson id** (`ml-21`), the **step number**, what you **expected**, and what you **saw** (traceback or plot).

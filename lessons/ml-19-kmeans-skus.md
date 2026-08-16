# ml-19 — K-means SKUs

**Level:** Absolute beginner  
**Time:** ~50 minutes  
**Prerequisites:** ml-18; Python 3.14.6, numpy 2.5.2, sklearn 1.9.0 from the ml-00 venv  
**Lab outcome:** You cluster 90 SKUs on length × weight into three piles and read the three centers

---

## At a glance

**Unsupervised** means: no teacher, no refund label, no “this SKU is tiny.” You only have facts.

**K-means** is a recipe that places **K** center points and assigns each SKU to the nearest center. You chose **K = 3** because Maya already thinks in tiny / mid / bulky.

By the end you can:

- point at the three printed centers and name which pile is which
- say what `n_clusters`, `n_init`, and `random_state` do, in one sentence each
- explain why K-means did **not** look at `true_group`

You will run `later_labs.py kmeans`, stare at colored dots plus black **x** marks, and walk `lab_kmeans`.

---

## Why this matters

Meet **Maya**, night-shift warehouse lead at Meridian. New SKUs land every week. She needs similar boxes on similar shelves: tiny jewelry near tiny jewelry, bulky totes near bulky totes.

Nobody labeled those 90 rows as tiny / mid / bulky for the computer. The hidden column `true_group` is a cheat sheet **you** can read later. K-means never sees it.

If you skip this lab, “cluster” stays a slide word. Tonight it is three piles of boxes.

---

## Concept primer

| Word | Plain English | In Maya’s warehouse |
| --- | --- | --- |
| **Unsupervised** | Learn structure with no yes/no label | SKU table has length and weight only, for the recipe |
| **Cluster / pile** | A group of similar rows | Tiny SKUs sitting near each other on a scatter plot |
| **K** | How many piles you asked for | Maya wants 3: tiny, mid, bulky |
| **Center** | The average location of one pile | Tiny pile sits near 7.88 cm and 0.98 kg |
| **Assign** | Put each SKU on the nearest center | A 10 cm / 1 kg box joins the tiny pile |
| **Inertia** | Sum of squared distances to assigned centers | Lower = tighter piles. `n_init` keeps the lowest |

The loop is two steps, repeated:

```text
1. Assign: each SKU joins its nearest center.
2. Move: each center jumps to the mean of its pile.
Repeat until the centers stop jumping.
```

A person can do this with sticky notes on a table. sklearn just does it faster.

> **Tip:** K is a **product** choice. The algorithm will always give you K piles, even if nature only has two.

> **Watch out:** K-means does not know the words “tiny” or “bulky.” It only knows distances. You name the piles after you look at the centers.

---

## Setup (short)

You already made the virtual environment in **ml-00**. Reuse it. Do not recreate it. Do not pip-install anything new.

### Step 1 — Enter the playground and turn the island on

Why now: `later_labs.py` imports `meridian_data.py` from the **current** folder. If you skip `cd`, the import fails.

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

If the venv is missing, go back to ml-00 Setup once. This lesson assumes that is done.

---

## Hands-on

### Step 2 — Run the k-means lab

Why this command now: it opens the exact picture this lesson is about. If you skip it, “three piles” stays abstract.

```bash
python later_labs.py kmeans
```

`kmeans` is a **lab name**, not a flag. `argparse` only accepts names from a frozen list (`kmeans`, `pca`, `anomaly`, …). There is no `-k` here.

**It worked when** a scatter plot opens titled `ml-19: three piles of SKUs (tiny / mid / bulky)`, and the terminal prints:

```text
centers [[ 7.88  0.98]
 [43.81 14.86]
 [21.74  4.84]]
```

On the plot:

- **colored dots** = 90 SKUs (color = K-means pile id, **not** the hidden truth)
- **black x marks** = the three centers

Close the plot window when you have stared at the left clump, the middle clump, and the far-right clump.

- [ ] The three centers printed with those numbers
- [ ] You can point at the tiny x (near 8 cm, 1 kg) vs the bulky x (near 44 cm, 15 kg)

### Step 3 — Name the three centers out loud

The printed rows are `[length_cm, weight_kg]`. Say this with the numbers filled in:

> “Center **0** is **7.88 cm** and **0.98 kg** — that is the **tiny** pile.”  
> “Center **1** is **43.81 cm** and **14.86 kg** — that is the **bulky** pile.”  
> “Center **2** is **21.74 cm** and **4.84 kg** — that is the **mid** pile.”

K-means label numbers are **not** the same as `true_group` in `meridian_data.py`:

| Hidden `true_group` | Typical size (means) | K-means label that landed there |
| --- | --- | --- |
| 0 tiny | 6.85 cm, 0.65 kg | label **0** (center 7.88, 0.98) |
| 1 mid | 19.50 cm, 3.80 kg | label **2** (center 21.74, 4.84) |
| 2 bulky | 42.55 cm, 14.57 kg | label **1** (center 43.81, 14.86) |

The computer did not read that table. You did, after the fact.

- [ ] You said all three sentences
- [ ] You noticed label 1 is bulky, not mid — ids are arbitrary

### Step 4 — Walk `lab_kmeans` (do not paste blindly)

Open `later_labs.py`. Find `lab_kmeans`. Open `meridian_data.py` and find `skus`.

1. `df = skus()` loads **90** fake SKUs, seed **11**, with columns `sku`, `length_cm`, `weight_kg`, `true_group`.
2. `KMeans(...)` builds the recipe. Then `.fit(...)` places the centers.
3. The fit uses **only** `df[["length_cm", "weight_kg"]]`. `true_group` is not in that pair of columns.
4. `ax.scatter(..., c=km.labels_, cmap="tab10")` colors dots by the **assigned** pile.
5. `ax.scatter(*km.cluster_centers_.T, marker="x", ...)` draws the three black x marks.
6. `print("centers", np.round(km.cluster_centers_, 2))` is the table you copied above.

Now the constructor, word by word:

```python
KMeans(n_clusters=3, n_init=10, random_state=0)
```

- `n_clusters=3` — how many piles Maya asked for. This is K.
- `n_init=10` — run the whole assign/move loop **10 times** from different random starting centers. Keep the run with the **lowest inertia**. One unlucky start can freeze in a bad split; retries make you less unlucky.
- `random_state=0` — freeze the random number generator so your centers match this lesson. Change it and the printed matrix can move.

This run needed **4** assign/move rounds (`n_iter_`) after it picked a start. Inertia landed at **4219.2**. You do not need to memorize those; they prove the loop actually stopped.

> **Tip:** `n_init` is not “10 clusters.” It is 10 **attempts** at 3 clusters.

> **Watch out:** Length is in centimeters (about 4–59) and weight is in kilograms (about 0.1–22). Here both axes have similar-sized numbers, so the plot is readable. If one column were `price_cents` in the tens of thousands, that axis would bully the distance. Scale first in that case (you do that on purpose in ml-20).

### Step 5 — Mini experiment (do it)

In `lab_kmeans`, change **one number**: `n_clusters=3` to `n_clusters=2`.

Save. Run again:

```bash
python later_labs.py kmeans
```

**Expect:** two centers, not three. Maya’s mid pile gets eaten by tiny or bulky. The algorithm is not “confused.” You asked for two piles.

Put `n_clusters=3` back so later screenshots still match.

- [ ] You changed K, reran, and saw two x marks
- [ ] You put 3 back

---

## How it works (deeper)

K-means is not “understanding boxes.” It is averaging coordinates.

```text
pick 3 starting centers (a guess)
repeat:
    for each SKU:
        assign it to the nearest center
    for each center:
        move it to the mean length and mean weight of its SKUs
until centers barely move
keep the best of n_init=10 random starts
```

**Nearest** means Euclidean distance on the two numbers you passed in: √[(Δlength)² + (Δweight)²].

The hidden story in `skus()` is three blobs by construction (`g` is 0, 1, or 2, then length/weight are drawn from different ranges). K-means recovered three blobs close to those means. That is luck of this toy, not a guarantee on messy real SKUs.

A **label** in the supervised sense (refund / not) never entered the fit. `km.labels_` are just pile ids 0, 1, 2.

---

## Common pitfalls

1. **`ModuleNotFoundError: numpy` (or sklearn).** The venv is not active. Prompt must show `(.venv)`. Redo Step 1’s `source` line.
2. **`No such file` / cannot import `meridian_data`.** You are not in `project/ml_playground`. `cd` there first.
3. **Plot never opens.** You exported `ML_HEADLESS=1`, or you are on a server with no display. On a laptop: `unset ML_HEADLESS` and rerun.
4. **You treated K-means colors as `true_group`.** They are `km.labels_`. The ids do not line up (bulky is label 1 here, truth 2).
5. **You thought `n_init=10` means 10 piles.** It means 10 random restarts of a 3-pile run.
6. **You asked for K=3 because “the plot looks nicer.”** Maya chose 3 from warehouse layout. Always have a reason for K.

---

## Knowledge check

Answer from the printout and the code you opened, not from a blog.

1. What are the three printed centers, and which pile is tiny / mid / bulky?
2. Did K-means use `true_group` when it placed those centers?
3. What does `n_init=10` do? What does `random_state=0` do?
4. Why is K-means label **1** the bulky pile instead of the mid pile?
5. If Maya set `n_clusters=5` on the same 90 SKUs, would the algorithm refuse because “nature has three groups”?

<details>
<summary>Answers</summary>

1. `[7.88, 0.98]` tiny; `[43.81, 14.86]` bulky; `[21.74, 4.84]` mid.
2. No. Fit used only `length_cm` and `weight_kg`.
3. `n_init=10` retries 10 random starts and keeps the lowest inertia. `random_state=0` freezes the RNG so your numbers match this lesson.
4. Pile ids are arbitrary. K-means numbered bulky as 1. Hidden `true_group` numbered bulky as 2. Same stuff, different integers.
5. No. It would always return 5 piles. K is your choice, not a discovery the computer is allowed to veto.

</details>

---

## Recap

- **You built** a three-pile map of 90 Meridian SKUs and read centers `[[7.88, 0.98], [43.81, 14.86], [21.74, 4.84]]`.
- **You understand** unsupervised = no label in the fit; K-means = assign, average, repeat; `n_init` retries starts.
- **Next** you will scale the same two columns and **rotate** them so the spread is easy to see.

Next: `ml-20-pca-rotate`

---

## Stretch goal

In `lab_kmeans`, change `random_state=0` to `random_state=1`. Rerun.

- **Expect:** centers may shift a little (or a lot). The *meaning* (three piles on length × weight) does not change.
- Put `random_state=0` back when you are done so this lesson’s numbers still match.

---

## Feedback

Could you redo this lab from memory? Note the **lesson id** (`ml-19`), the **step number**, what you **expected**, and what you **saw** (traceback or plot).

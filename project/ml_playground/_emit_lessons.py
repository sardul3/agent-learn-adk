"""One-shot emitter for bonus ML lessons. Run from repo root if regenerating."""

from __future__ import annotations

from pathlib import Path

LESSONS = Path(__file__).resolve().parents[2] / "lessons"

SETUP = """
### Setup (once per machine)

Why now: every lab imports `meridian_data.py` from this folder.

```bash
cd project/ml_playground
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

- `-m venv` means “run the standard-library module named venv.”
- `-r` means “read this file as the list of packages.”

**It worked when** `(.venv)` shows in the prompt and `python -c "import numpy, matplotlib, sklearn"` prints nothing.
"""


def lesson(
    slug: str,
    title: str,
    time: str,
    prereq: str,
    outcome: str,
    glance: str,
    why: str,
    math: str,
    cmd: str,
    expect: str,
    walk: str,
    tip: str,
    watch: str,
    q: list[str],
    a: list[str],
    recap: str,
    next_slug: str,
) -> str:
    qs = "\n".join(f"{i}. {t}" for i, t in enumerate(q, 1))
    ans = "\n".join(f"{i}. {t}" for i, t in enumerate(a, 1))
    return f"""# {title}

**Level:** Absolute beginner  
**Time:** {time}  
**Prerequisites:** {prereq}  
**Lab outcome:** {outcome}

---

## At a glance

{glance}

---

## Why this matters

{why}

---

## Concept primer

{math}

{SETUP}

---

## Hands-on

Why this command now: it opens the exact picture this lesson is about. If you skip it, the words stay abstract.

```bash
{cmd}
```

**It worked when** {expect}

Walk the code (do not paste blindly — open the file, find the function, read it):

{walk}

> **Tip:** {tip}

> **Watch out:** {watch}

- [ ] You ran the command
- [ ] You can say the new word in a Maya sentence
- [ ] You know what “it worked” looked like

---

## How it works (deeper)

The computer is not “understanding packing.” It is doing arithmetic you could do with a pencil, just faster. The picture is there so the arithmetic has a face.

---

## Common pitfalls

1. **Plot never opens.** You are on a server without a display. On a laptop, matplotlib should pop a window. If you must, this is still a local lab.
2. **`ModuleNotFoundError`.** The venv is not active. Redo Setup.
3. **Wrong folder.** `cd project/ml_playground` first so imports find `meridian_data.py`.

---

## Knowledge check

{qs}

<details>
<summary>Answers</summary>

{ans}

</details>

---

## Recap

{recap}

Next: `{next_slug}`

---

## Feedback

Could you redo this lab from memory? Note the **lesson id**, what you **expected**, and what you **saw** (traceback or plot).
"""


ITEMS: list[dict] = []

def add(**k):
    ITEMS.append(k)


add(
    slug="ml-00-what-a-model-is",
    title="ml-00 — What a model even is",
    time="~45 minutes",
    prereq="Python 3.11+; no ML, no linear algebra",
    outcome="You can point at Maya’s guesses and say which numbers are inputs, which are the recipe, which are errors",
    glance="A **model** is a recipe that turns facts you have into a guess. Maya already has one: “about 5 minutes plus 2 per kilo.” You will plot her guess next to the stopwatch.",
    why="Maya’s night shift needs packing-time guesses so the dock does not idle. If her rule is systematically late, vans wait. We start here because every later ‘AI’ is still this: inputs, recipe, guess, score.",
    math="**Input:** facts (box weight). **Output:** a guess (minutes). **Error:** guess minus truth. No neural net yet. If you can subtract, you can score a model.",
    cmd="python m0_labs.py model",
    expect="a table of true minutes vs Maya guesses prints, and a scatter plot opens with dots and x marks.",
    walk="`lab_model` in `m0_labs.py` loads `packing_orders`, builds `maya = 5 + 2 * weight`, plots both. The mean error line is the first **loss** you will meet — an average of how wrong.",
    tip="A person can be a model. A spreadsheet can be a model. A neural net is a model with more knobs.",
    watch="Do not call this ‘the AI decided.’ Maya’s line is a formula. You can read every number.",
    q=["What three parts does every model have in this lesson?", "Is Maya’s rule a model even though it is not trained?"],
    a=["Inputs, a recipe, a guess (then we add error when we have truth).", "Yes. Trained only means ‘we nudged the recipe using data.’ The recipe still counts."],
    recap="- **You built** a plot of Maya vs the stopwatch.\n- **You understand** model = recipe.\n- **Next** you will drag slope and intercept.",
    next_slug="ml-01-functions-slope-intercept",
)

add(
    slug="ml-01-functions-slope-intercept",
    title="ml-01 — Functions, slope, intercept",
    time="~50 minutes",
    prereq="ml-00",
    outcome="You can say what slope and intercept mean for packing minutes",
    glance="A **function** is a machine: put a number in, get a number out. For a line, `minutes = m * weight + b`. **m** is slope (extra minutes per kilo). **b** is intercept (minutes even for a featherweight).",
    why="If Maya’s slope is too small, heavy boxes are always late to the van. Slope is not a ski hill here — it is a rate.",
    math="**Rate of change:** if weight goes up by 1 kg and minutes go up by 1.8, slope is 1.8. **Intercept:** the value when weight is 0. Real boxes are not 0 kg; intercept is still a useful starting offset.",
    cmd="python m0_labs.py slope",
    expect="you can drag sliders named slope m and intercept b and the orange line moves across the cloud of warehouse dots.",
    walk="`lab_slope` uses matplotlib `Slider`. `line.set_data(xs, s_m.val * xs + s_b.val)` is the function. Stay until you can make the line look ‘about right’ by eye.",
    tip="Match the cloud’s tilt first (slope), then slide the line up/down (intercept).",
    watch="A perfect line through every dot is not the goal. Noise exists. A good line is honestly close.",
    q=["If m=2 and b=4, what is the guess for a 3 kg box?", "What does a slope of 0 mean?"],
    a=["2*3+4=10 minutes.", "Weight does not change the guess; the line is flat."],
    recap="- **You dragged** m and b.\n- **You understand** slope as extra minutes per kilo.\n- **Next** vectors as lists.",
    next_slug="ml-02-vectors-as-feature-lists",
)

add(
    slug="ml-02-vectors-as-feature-lists",
    title="ml-02 — Vectors as feature lists",
    time="~50 minutes",
    prereq="ml-01",
    outcome="You can add and scale a 2-number list and draw it as an arrow",
    glance="A **vector** is an ordered list of numbers. `[weight, delay]` is a vector. An arrow is the same list drawn from the origin. **Add** tip-to-tail. **Scale** stretches the arrow.",
    why="Maya never has only weight. She has weight and delay and zone. Linear algebra is mostly ‘lists of features’ with two operations: add, scale.",
    math="Length of `[3, 4]` is `sqrt(9+16)=5` (how far from zero). We will not need fancy names like ‘norm’ beyond ‘length.’",
    cmd="python m0_labs.py vectors",
    expect="three arrows: A, A then B, and A+B dashed. The terminal prints length and 2*A.",
    walk="`lab_vectors` in `m0_labs.py`. `a + b` is numpy adding pairwise. That is the whole of vector addition.",
    tip="Order matters for meaning: `[3, 1]` is not `[1, 3]` — different features swapped.",
    watch="People say ‘vector’ and mean both the list and the arrow. Same thing.",
    q=["What is `[1, 2] + [3, 4]`?", "What is `2 * [1, 3]`?"],
    a=["[4, 6]", "[2, 6]"],
    recap="- **You saw** arrows add.\n- **You understand** features as coordinates.\n- **Next** mixing with a dot product.",
    next_slug="ml-03-dot-product-weighted-mix",
)

add(
    slug="ml-03-dot-product-weighted-mix",
    title="ml-03 — Dot product as a weighted mix",
    time="~55 minutes",
    prereq="ml-02",
    outcome="You can compute a tiny dot product by hand and with sliders",
    glance="The **dot product** mixes two lists: multiply pairs, then add. `guess = w0*1 + w1*weight`. The 1 is a fake feature so intercept is just another mix.",
    why="Maya trusts weight more than hour-of-day. Those trusts **are** the weights `w`. Dot product is how the mix becomes one number.",
    math="`[1, 5] · [4, 1.8] = 1*4 + 5*1.8 = 13`. Units: minutes, if you chose weights that way.",
    cmd="python m0_labs.py dot",
    expect="sliders w0 and w1 move a line; the plot text shows the first box’s dot product.",
    walk="`lab_dot` uses `sample @ w` (`@` is numpy’s dot). Same as writing a for-loop of multiply-add.",
    tip="If w1 is negative, heavier boxes get *smaller* guesses — usually nonsense for packing time. The math allows it; Maya would not.",
    watch="Weight here means ‘knob,’ not kilograms. Two meanings of the word ‘weight.’",
    q=["Compute `[2, 3] · [4, 5]`.", "Why glue a 1 onto the feature list?"],
    a=["8+15=23.", "So the intercept is a mix too: w0*1."],
    recap="- **You mixed** with a dot.\n- **You understand** knobs vs kilograms.\n- **Next** tables as matrices.",
    next_slug="ml-04-tables-as-matrices",
)

add(
    slug="ml-04-tables-as-matrices",
    title="ml-04 — Tables as matrices",
    time="~45 minutes",
    prereq="ml-03",
    outcome="You can say what a row and a column mean in the heatmap",
    glance="A **matrix** is a table of numbers. Rows = orders. Columns = features (weight, zone, hour). No mystic object.",
    why="Twenty orders at once is how training works. One vector is one order. A matrix is a stack of them.",
    math="Shape `(20, 3)` means 20 rows, 3 columns. We will multiply matrix × vector later as ‘dot product on every row.’",
    cmd="python m0_labs.py matrix",
    expect="the first five rows print, and a heatmap of 20×3 glows.",
    walk="`lab_matrix` takes `df[['weight_kg','zone','hour']].to_numpy()` then `imshow`. Color is only ‘bigger/smaller,’ not temperature.",
    tip="Zone is 1–4, hour is 6–21. Hour looks ‘more important’ only because the numbers are bigger — that lie is M1 scaling.",
    watch="Do not average a row that mixes kg and hours and call it ‘the order’s vibe.’ Units differ.",
    q=["What does row 0 mean?", "What does column 2 mean in this lab?"],
    a=["One order’s three features.", "hour of day."],
    recap="- **You viewed** a matrix as a heatmap.\n- **You understand** row=example.\n- **Next** error bowls and nudges.",
    next_slug="ml-05-error-and-nudge",
)

add(
    slug="ml-05-error-and-nudge",
    title="ml-05 — Error, mean, and nudge the knob",
    time="~70 minutes",
    prereq="ml-04",
    outcome="You can explain MSE and one gradient step in warehouse words, then fit a line with no sklearn",
    glance="**Mean squared error (MSE)** = average of (guess−truth)². Square so late and early both count, and big misses hurt more. A **derivative** asks: if I bump knob m a tiny bit, how does MSE move? **Gradient descent** = repeatedly step opposite that slope.",
    why="Maya could try random slopes forever. Nudging downhill on the error bowl is the engine under almost all later training.",
    math="For one 5 kg box with truth 13 minutes, error = m*5−13. MSE = that square. Slope of the bowl vs m is `2*(m*5−13)*5`. Step: `m ← m − learning_rate * that`. **Learning rate** = how big a step. Too big: you jump over the bottom. Too small: you nap on the hillside.",
    cmd="python m0_labs.py bowl",
    expect="an orange path walks down a U-shaped curve. Terminal prints start m=0 and an ending m near 13/5=2.6.",
    walk="`lab_bowl` then run `python m0_labs.py fit` for the **project**: 400 nudges on real packing dots. Printed mse should fall.",
    tip="The fit only uses weight. True minutes also use zone, so the line cannot be perfect. That leftover is not failure — it is missing features (M2).",
    watch="MSE is not ‘percent correct.’ It is minutes-squared. Compare MSE to MSE, not to a gut percent.",
    q=["Why square the error?", "What happens if the learning rate is huge?", "After `fit`, is sklearn required?"],
    a=["So signs cancel less, and outliers hurt more.", "m leaps past the bottom and can explode.", "No. You only added a bit to m and b."],
    recap="- **You fitted** a line by nudging.\n- **You understand** MSE and a gradient step.\n- **Next** M1 data hygiene.",
    next_slug="ml-06-train-val-test",
)

# M1
add(slug="ml-06-train-val-test", title="ml-06 — Train, val, test", time="~40 minutes", prereq="ml-05",
    outcome="You split packing rows and can say which split is the exam",
    glance="**Train** = homework you may study. **Validation** = practice tests you may retake while tuning. **Test** = the exam once. Mixing them is cheating.",
    why="Maya could memorize last night’s 80 boxes and still fail tonight. A test split is tonight.",
    math="A 75/25 split is a fraction of rows, not a mystic ratio. Random split needs a seed so your lab is repeatable.",
    cmd="python classic_labs.py split",
    expect="it prints train vs test counts and three train rows.",
    walk="`train_test_split` from scikit-learn. `test_size=0.25` means a quarter held out. `random_state=0` freezes the shuffle.",
    tip="If you have little data, the test set is noisy. Still do not peek to pick knobs.",
    watch="Shuffling time series without care can leak the future. Packing rows here are independent enough for a first lab.",
    q=["Which split may you look at while choosing slope?", "Why a seed?"],
    a=["Train (and val if you have it). Not test.", "So the split does not change every run while you learn."],
    recap="- **You split** rows.\n- **You understand** the exam metaphor.\n- **Next** leakage.",
    next_slug="ml-07-leakage")

add(slug="ml-07-leakage", title="ml-07 — Leakage", time="~45 minutes", prereq="ml-06",
    outcome="You see a fake high accuracy from an answer-sheet column, then an honest score",
    glance="**Leakage** is when the recipe sees information that would not exist at guess-time. Example: `refund_already_paid` to predict `became_refund`.",
    why="Meridian finance could ‘prove’ a model that is just reading the ledger. Then it fails on new tickets.",
    math="Accuracy = fraction of labels you got right. High accuracy is not virtue if the feature is the label in disguise.",
    cmd="python classic_labs.py leak",
    expect="LEAKY test acc is much higher than honest.",
    walk="`lab_leak` in `classic_labs.py`. Compare column lists. The paid flag copies the label.",
    tip="Ask: ‘Would Maya have this field *before* the outcome?’ If no, drop it.",
    watch="Leakage can be subtle (using post-refund notes as input). This lab is the loud version.",
    q=["Why is refund_already_paid illegal here?", "Does higher accuracy always mean a better warehouse tool?"],
    a=["It is the outcome wearing a costume.", "No. It can mean you cheated."],
    recap="- **You broke** a model on purpose.\n- **You understand** leakage.\n- **Next** scaling.",
    next_slug="ml-08-scaling-lying-plots")

add(slug="ml-08-scaling-lying-plots", title="ml-08 — Scaling and lying plots", time="~45 minutes", prereq="ml-07",
    outcome="You scale weight and hour and see why raw axes lie",
    glance="**Scaling** puts columns on a similar numeric range (often mean 0, std 1). Plots with unmatched axes make hour look ‘more important’ than kg.",
    why="Dot-product models treat 21 hours as a bigger shove than 8 kg unless you scale. Maya does not think hour is 3× more real.",
    math="Standard score: subtract mean, divide by std. After that, both columns have std ≈ 1.",
    cmd="python classic_labs.py scale",
    expect="two scatters: raw vs scaled. Terminal prints stds.",
    walk="`StandardScaler().fit_transform`. Fit on train only in real work (M2) — fitting on all rows leaks test scale. This lab shows the picture.",
    tip="Trees care less about scale. Lines and neural nets care a lot.",
    watch="Never scale using test-set mean. That peeks at the exam’s average.",
    q=["What does std 1 after scaling mean in words?", "Why can a plot lie?"],
    a=["Typical distance from the average is 1 in those units.", "Axis stretch changes what your eye calls important."],
    recap="- **You scaled** two columns.\n- **You understand** lying axes.\n- **Next** bias vs variance.",
    next_slug="ml-09-bias-variance")

add(slug="ml-09-bias-variance", title="ml-09 — Bias vs variance", time="~50 minutes", prereq="ml-08",
    outcome="You recognize a too-simple line vs a wiggly memorizer on a sine cloud",
    glance="**Bias:** always missing the same way (too simple). **Variance:** jumping around if the data wiggles (too flexible). The dartboard: all darts left of bull vs darts everywhere.",
    why="Maya can use a flat ‘always 8 minutes’ (bias) or a polyline through every box (variance). Both miss tonight.",
    math="Polynomial degree is a flexibility knob in this lab. Degree 1 is a line. Degree 12 can wiggle through noise.",
    cmd="python classic_labs.py biasvar",
    expect="three panels: stiff line, reasonable curve, wild wiggle.",
    walk="`np.polyfit` with degrees 1, 3, 12. The middle is the teaching target, not a universal law.",
    tip="More knobs need more data. M0’s two-knob line is low variance, some bias.",
    watch="Low training error + high test error is the variance smell.",
    q=["Which panel is high bias?", "Which is high variance?"],
    a=["The too-simple line.", "The degree-12 wiggle."],
    recap="- **You compared** three fits.\n- **You understand** the dartboard.\n- **Next** regression as a named tool.",
    next_slug="ml-10-one-feature-regression")

# M2
add(slug="ml-10-one-feature-regression", title="ml-10 — One-feature regression", time="~45 minutes", prereq="ml-09",
    outcome="You fit sklearn LinearRegression on weight→minutes and read m, b, test MSE",
    glance="**Linear regression** is the line-fitting job with a library that does the nudging for you. Same idea as `m0_labs.py fit`.",
    why="You should not hand-roll every time. You should still know what m and b mean.",
    math="sklearn solves the same MSE bowl (ordinary least squares). Test MSE is the exam score.",
    cmd="python classic_labs.py reg1",
    expect="printed m near 1.8-ish, b near 4–6, and a test scatter with x marks.",
    walk="`LinearRegression().fit(Xtr, ytr)` then `predict`. Compare to your M0 nudger.",
    tip="If m is negative, you shuffled columns or inverted labels — stop and look.",
    watch="Never report train MSE as if it were test.",
    q=["What is the input column?", "What number tells you exam quality here?"],
    a=["weight_kg", "test MSE"],
    recap="- **You used** sklearn for a line.\n- **You still know** m and b.\n- **Next** many features.",
    next_slug="ml-11-many-features")

add(slug="ml-11-many-features", title="ml-11 — Many features", time="~50 minutes", prereq="ml-10",
    outcome="You read a residual plot for weight+zone+hour",
    glance="Each feature gets its own knob. Guess = b + w1*weight + w2*zone + w3*hour. **Residual** = truth − guess. A banana shape means the line is the wrong shape.",
    why="Zone changes walking time. Hour changes staffing. Ignoring them blames weight for everything.",
    math="Now the bowl is in many dimensions. We cannot draw it; residuals are how we look.",
    cmd="python classic_labs.py regmany",
    expect="printed weights and a residual scatter that should look like a cloud.",
    walk="`lab_reg_many`. If residuals fan out, variance is not constant — advanced later; for now, notice the cloud.",
    tip="A leftover pattern is a missing idea (maybe weekend vs weekday — we did not include it).",
    watch="Do not add 50 columns to 80 rows. Variance explodes (ml-09).",
    q=["What should residuals look like if the line is honest?", "What is a residual?"],
    a=["A shapeless cloud around 0.", "truth minus prediction."],
    recap="- **You fitted** three knobs.\n- **You read** residuals.\n- **Next** bends.",
    next_slug="ml-12-polynomial-bend")

add(slug="ml-12-polynomial-bend", title="ml-12 — Polynomial bend", time="~40 minutes", prereq="ml-11",
    outcome="You compare degree 1 vs 4 on packing weight",
    glance="**Polynomial features** add weight², weight³, … so a ‘line in new coordinates’ bends in the original plot.",
    why="Maybe tiny boxes have a setup cost and then time grows slower. A bend can capture that — or wiggle.",
    math="`PolynomialFeatures(d)` builds columns. The model is still linear in those columns.",
    cmd="python classic_labs.py poly",
    expect="two curves over the scatter; degree 4 bends more.",
    walk="`lab_poly`. Degree is a bias/variance knob. You already saw degree 12 go feral in ml-09.",
    tip="Prefer a missing real feature (zone) over a wild polynomial when you know the warehouse.",
    watch="Extrapolating a cubic past 12 kg can dive into negative minutes. Nonsense.",
    q=["Is a polynomial still a linear model in the new columns?", "Name one risk of high degree."],
    a=["Yes.", "Wiggles / bad extrapolation."],
    recap="- **You bent** a line.\n- **You remember** ml-09.\n- **Next** L2.",
    next_slug="ml-13-l2-regularization")

add(slug="ml-13-l2-regularization", title="ml-13 — L2 regularization", time="~40 minutes", prereq="ml-12",
    outcome="You watch Ridge shrink weights as alpha grows",
    glance="**L2 / Ridge** adds a penalty for large knobs. Alpha is ‘how shy.’ Big alpha → weights crawl toward 0.",
    why="Maya should not bet the dock on one noisy column. Shyness is a safety rail.",
    math="Minimize MSE + alpha * (w1² + w2² + …). The extra term is the ‘don’t be dramatic’ tax.",
    cmd="python classic_labs.py ridge",
    expect="three lines of weights; alpha=50 looks smaller than alpha=0.",
    walk="`Ridge(alpha=...)`. Alpha=0 is almost ordinary regression.",
    tip="Scale features before Ridge or hour will eat the penalty budget.",
    watch="Too much alpha = high bias. You under-trust every column.",
    q=["What does a bigger alpha do?", "Why square the weights in the tax?"],
    a=["Shrinks knobs toward 0.", "So +3 and −3 are equally dramatic."],
    recap="- **You shrank** weights.\n- **You understand** the shyness tax.\n- **Next** classification.",
    next_slug="ml-14-logistic-squash")

# M3
add(slug="ml-14-logistic-squash", title="ml-14 — Logistic squash", time="~50 minutes", prereq="ml-13",
    outcome="You plot P(refund) as a rising S-curve vs delay",
    glance="**Classification** guesses a label (refund / not). **Logistic** takes a line, then **squash** with 1/(1+e^(−z)) into 0–1 as a probability.",
    why="Minutes are a quantity. Refund is a yes/no. A line that goes to 15 is not a probability.",
    math="Let z = w*delay + b. Then p = 1/(1+exp(−z)). Always between 0 and 1.",
    cmd="python classic_labs.py logistic",
    expect="dots at 0 and 1, orange S-curve of P(refund).",
    walk="`LogisticRegression` + `predict_proba`. The S-curve is the squash.",
    tip="Threshold 0.5 is a choice, not a law. Maya might want fewer false refunds.",
    watch="Do not treat 0.51 as ‘the model is sure.’ It is a hair over the default cut.",
    q=["What does the squash fix?", "Name z in warehouse words."],
    a=["It bounds the guess into 0–1.", "A mix of delay (and later other facts) before turning into a chance."],
    recap="- **You saw** the S-curve.\n- **You understand** chance vs minutes.\n- **Next** boundaries.",
    next_slug="ml-15-decision-boundary")

add(slug="ml-15-decision-boundary", title="ml-15 — Decision boundary", time="~45 minutes", prereq="ml-14",
    outcome="You see two colors of tickets split by a line in delay×angry-words",
    glance="A **decision boundary** is the fence where the guess flips class. Logistic with two features: a straight fence.",
    why="Maya can picture ‘too delayed and too angry → refund path.’ The fence is that policy’s sketch.",
    math="Where p=0.5, z=0, so w1*x1 + w2*x2 + b = 0 — a line.",
    cmd="python classic_labs.py boundary",
    expect="a filled two-tone background and colored dots.",
    walk="`lab_boundary` predicts a grid. Contour is the fence.",
    tip="If classes overlap a lot, no fence is clean. That is life, not a broken lab.",
    watch="A wiggly fence (deep nets) can hug noise. Straight can be the honest warehouse rule.",
    q=["Where is p=0.5 on this plot?", "Why is the fence straight?"],
    a=["Along the color change.", "Logistic is linear in z."],
    recap="- **You saw** the fence.\n- **You understand** z=0.\n- **Next** confusion.",
    next_slug="ml-16-confusion-precision-recall")

add(slug="ml-16-confusion-precision-recall", title="ml-16 — Confusion, precision, recall", time="~50 minutes", prereq="ml-15",
    outcome="You read tn/fp/fn/tp as Maya’s two mistake types",
    glance="**Confusion matrix:** true no/yes vs guessed no/yes. **Precision:** of guessed refunds, how many were real. **Recall:** of real refunds, how many we caught.",
    why="False positive: refunded a fine order (money). False negative: ignored a smashed vase (trust). Maya must pick which hurt is worse.",
    math="precision = tp/(tp+fp). recall = tp/(tp+fn).",
    cmd="python classic_labs.py confusion",
    expect="a 2×2 matrix and two scores print.",
    walk="`confusion_matrix`, `precision_score`, `recall_score`. Map each cell to a warehouse story before you move on.",
    tip="Accuracy can look fine while recall on rare refunds is awful (ml-18).",
    watch="Do not optimize precision by never predicting refund. Recall dies.",
    q=["Which cell is ‘refunded a fine order’?", "Precision in one Maya sentence."],
    a=["False positive.", "When we say refund, how often are we right?"],
    recap="- **You named** four cells.\n- **You understand** precision vs recall.\n- **Next** trees.",
    next_slug="ml-17-trees-forests")

add(slug="ml-17-trees-forests", title="ml-17 — Trees and forests", time="~45 minutes", prereq="ml-16",
    outcome="You fit a shallow tree and a forest and read importances",
    glance="A **tree** asks yes/no questions (delay>4.5?). A **forest** is many trees voting — less drama from one weird question.",
    why="Maya already trains people with checklists. Trees look like checklists.",
    math="Importance here is ‘how much did this question reduce mixing of labels?’ Not a causal story.",
    cmd="python classic_labs.py trees",
    expect="two accuracies and a dict of importances.",
    walk="`DecisionTreeClassifier(max_depth=3)` vs `RandomForestClassifier`. Depth is a variance knob.",
    tip="Deep trees memorize. Forests average that away — still not magic.",
    watch="Importance is not ‘Maya should only look at this field.’",
    q=["What does max_depth limit?", "What does a forest add?"],
    a=["How long the checklist can be.", "Many trees vote."],
    recap="- **You fitted** tree and forest.\n- **You treated** importance as a hint.\n- **Next** imbalance.",
    next_slug="ml-18-class-imbalance")

add(slug="ml-18-class-imbalance", title="ml-18 — Class imbalance", time="~45 minutes", prereq="ml-17",
    outcome="You see a 95% always-no accuracy and a balanced model that actually predicts yes",
    glance="If 95% of tickets are not refunds, **always say no** is 95% accurate and useless. **Class weights** tax the common class so the rare class is seen.",
    why="Fraud and damage are rare. Meridian will celebrate accuracy while customers scream.",
    math="`class_weight='balanced'` reweights the loss. You can also resample. Pick a metric that cares (recall on yes).",
    cmd="python classic_labs.py imbalance",
    expect="always-say-no acc ~0.95, naive model predicts almost no positives, balanced predicts more.",
    walk="`lab_imbalance`. Count predicted positives, not only accuracy.",
    tip="Pair this with the confusion lesson. Accuracy is the villain’s metric here.",
    watch="Weights are not a substitute for more real rare examples.",
    q=["Why is 95% accuracy a trap?", "Name one fix in this lab."],
    a=["The majority class dominates.", "balanced class_weight."],
    recap="- **You refused** majority accuracy.\n- **You counted** predicted yes.\n- **Next** clusters.",
    next_slug="ml-19-kmeans-skus")

# M4–M12 remaining items in second batch in same file - continue add()
add(slug="ml-19-kmeans-skus", title="ml-19 — K-means SKUs", time="~45 minutes", prereq="ml-18",
    outcome="You cluster length×weight into three piles and see centers",
    glance="**Unsupervised** means no refund label. **K-means** places K centers and assigns each SKU to the nearest. You chose K=3 because Maya thinks tiny/mid/bulky.",
    why="Warehouse layout: similar sizes on similar shelves.",
    math="Iterate: assign to nearest center, move center to the mean of its pile, repeat.",
    cmd="python later_labs.py kmeans",
    expect="three colored clouds and x marks at centers; centers print.",
    walk="`KMeans(n_clusters=3, n_init=10)`. `n_init` retries starts so you are less unlucky.",
    tip="K is a product choice. The algorithm will always give you K piles even if nature has two.",
    watch="Different scales: scale first or length_cm dominates weight_kg.",
    q=["What does K mean here?", "Is there a refund label?"],
    a=["How many piles we asked for.", "No."],
    recap="- **You clustered** SKUs.\n- **You picked** K on purpose.\n- **Next** PCA.",
    next_slug="ml-20-pca-rotate")

add(slug="ml-20-pca-rotate", title="ml-20 — PCA rotate", time="~45 minutes", prereq="ml-19",
    outcome="You plot SKUs on two principal axes after scaling",
    glance="**PCA** rotates the table so the first new axis points along the biggest spread. It is not a crystal ball — it is a better camera angle.",
    why="Maya cannot stare at 20 numeric columns. Two spread-axes can still show clumps.",
    math="After centering/scaling, find directions of max variance. We plot two.",
    cmd="python later_labs.py pca",
    expect="a 2D scatter colored by true_group (only for teaching — PCA did not use it).",
    walk="`PCA(2).fit_transform`. Colors are the cheat sheet so you see clumps survived the rotate.",
    tip="If you color by a label, you are checking, not training. Keep that honest.",
    watch="PCA does not know ‘length is cm.’ Scale first.",
    q=["Does PCA use the refund label?", "What is pc1 in words?"],
    a=["No.", "The direction of biggest spread after rotate."],
    recap="- **You rotated** the view.\n- **You understand** spread, not magic.\n- **Next** anomalies.",
    next_slug="ml-21-anomaly-scan-times")

add(slug="ml-21-anomaly-scan-times", title="ml-21 — Anomaly scan times", time="~40 minutes", prereq="ml-20",
    outcome="You flag two weird scan seconds on a conveyor trace",
    glance="An **anomaly** is a point that does not fit the usual blob. Isolation forest tries to isolate odd points in few cuts.",
    why="A 9.8s scan or a 0.05s scan is a jam or a skipped scan. Maya wants a red dot, not a novel.",
    math="`contamination=0.03` is ‘about 3% are weird’ — a business guess, not truth from the gods.",
    cmd="python later_labs.py anomaly",
    expect="printed flagged indices including the planted 17 and 88, and a plot with red dots.",
    walk="`IsolationForest`. Planted outliers live in `scan_times()`.",
    tip="If you set contamination wrong, you cry wolf or miss the jam.",
    watch="Anomaly ≠ fraud by itself. It is ‘look here.’",
    q=["What did we plant?", "Is contamination a learned truth?"],
    a=["A huge time and a tiny time.", "No. It is a knob."],
    recap="- **You flagged** scans.\n- **You treated** contamination as a knob.\n- **Next** NLP tokens.",
    next_slug="ml-22-tokens-vocab")

add(slug="ml-22-tokens-vocab", title="ml-22 — Tokens and vocab", time="~40 minutes", prereq="ml-21",
    outcome="You split a ticket into tokens and a vocab set",
    glance="A **token** is a chunk (here: a word). A **vocab** is the set of chunks the recipe knows. Unknown words later become a problem (out of vocab).",
    why="Maya’s tickets are English, not vectors — yet. First we cut the string.",
    math="Lowercase + split on spaces is a crude tokenizer. Real NLP uses smarter cuts. Start crude so you see the job.",
    cmd="python later_labs.py tokens",
    expect="printed text, token list, sorted vocab.",
    walk="`lab_tokens`. Compare to later `CountVectorizer` which also drops tiny words sometimes.",
    tip="Order is lost when you only keep a set. That pain is M7.",
    watch="Punctuation glued to words (`order,`) becomes a fake token if you do not strip it.",
    q=["What is a vocab?", "Name one token in the sample."],
    a=["The set of chunks we know.", "Any printed token such as where / is / my."],
    recap="- **You tokenized** a ticket.\n- **You built** a vocab.\n- **Next** bags.",
    next_slug="ml-23-bag-of-words")

add(slug="ml-23-bag-of-words", title="ml-23 — Bag of words", time="~40 minutes", prereq="ml-22",
    outcome="You print a count vector for the first ticket",
    glance="A **bag of words** counts how often each vocab item appears. A bag has no order: ‘smashed late’ equals ‘late smashed’.",
    why="Fast baseline for intent. Enough for many tickets. Not enough for sarcasm or word order jokes.",
    math="Each ticket becomes a row of counts. Length = vocab size.",
    cmd="python later_labs.py bow",
    expect="a vocab snippet and first-row counts.",
    walk="`CountVectorizer`. Sparse matrix: mostly zeros.",
    tip="This is still a matrix (ml-04). Rows=tickets, columns=words.",
    watch="Common words like ‘the’ can dominate unless you filter (tf-idf next).",
    q=["Does the bag know word order?", "What is a column?"],
    a=["No.", "One vocab word’s count."],
    recap="- **You counted** words.\n- **You lost** order on purpose.\n- **Next** TF-IDF.",
    next_slug="ml-24-tfidf-ngrams")

add(slug="ml-24-tfidf-ngrams", title="ml-24 — TF-IDF and n-grams", time="~45 minutes", prereq="ml-23",
    outcome="You see n-grams and a sparser weighted row",
    glance="**TF-IDF** down-weights words that appear in almost every ticket (‘please’). **n-grams** are chunks of n tokens (‘want refund’) so some order sneaks back.",
    why="‘the’ should not outvote ‘smashed.’ Two-word phrases catch ‘want refund.’",
    math="TF = in this ticket. IDF = rare across tickets. Product is the weight.",
    cmd="python later_labs.py tfidf",
    expect="printed n-gram sample and nonzero count for row 0.",
    walk="`TfidfVectorizer(ngram_range=(1,2))`. Unigrams plus bigrams.",
    tip="Bigrams explode vocab. Tiny ticket set is OK for the lab.",
    watch="IDF on 10 documents is jumpy. Production needs more text.",
    q=["What does IDF punish?", "What is a bigram in this warehouse?"],
    a=["Words that show up everywhere.", "Two tokens in a row, e.g. want refund."],
    recap="- **You weighted** rare words.\n- **You added** phrases.\n- **Next** Bayes.",
    next_slug="ml-25-naive-bayes-tickets")

add(slug="ml-25-naive-bayes-tickets", title="ml-25 — Naive Bayes tickets", time="~45 minutes", prereq="ml-24",
    outcome="You classify three new sentences into wismo/refund/damage with probabilities",
    glance="**Naive Bayes** multiplies per-word chances (naive = pretends words are independent) and picks the label with the biggest product.",
    why="A strong baseline before neural NLP. Maya can ship this while you study transformers.",
    math="Independence is false (‘not smashed’ vs ‘smashed’) but the recipe still works often.",
    cmd="python later_labs.py nb",
    expect="three queries print a label and a three-number probability vector.",
    walk="`make_pipeline(TfidfVectorizer(), MultinomialNB())`. Pipeline = vectorize then classify.",
    tip="Look at probabilities, not only the argmax. 0.34/0.33/0.33 is a shrug.",
    watch="Ten toy sentences are a demo, not a production model.",
    q=["What is naive about Naive Bayes?", "What does the printed vector add up to (about)?"],
    a=["It treats word events as independent.", "About 1.0 (a chance split)."],
    recap="- **You classified** intent.\n- **You read** probabilities.\n- **Next** nearby meaning.",
    next_slug="ml-26-word-vectors")

add(slug="ml-26-word-vectors", title="ml-26 — Word vectors nearby meaning", time="~45 minutes", prereq="ml-25",
    outcome="You plot a toy map where refund sits near money",
    glance="**Word vectors** put words in space so similar usage → nearby dots. This lab uses a tiny co-occur table + PCA, not a 300-D download.",
    why="‘smashed’ near ‘dented’ helps damage routing even if the customer never said ‘damage.’",
    math="Co-occur matrix → PCA to 2D for your eyes. Real word2vec predicts neighbors; same spirit.",
    cmd="python later_labs.py wvec",
    expect="a scatter with word labels; refund near money, smash near dented/crushed.",
    walk="`lab_vectors_words`. Pairs are the teacher.",
    tip="Nearby ≠ synonym always. Nearby = used together in *this* tiny world.",
    watch="Do not ship this 2D toy as ‘embeddings for RAG.’ Lesson 18 uses real embedding APIs.",
    q=["What makes two words close here?", "Is this Pack D RAG?"],
    a=["They were paired in the toy list / co-occur.", "No. It is a picture of the idea."],
    recap="- **You mapped** words.\n- **You connected** this to later RAG.\n- **Next** neurons.",
    next_slug="ml-27-neuron-layer")

add(slug="ml-27-neuron-layer", title="ml-27 — Neuron and layer", time="~50 minutes", prereq="ml-26",
    outcome="You compute z and a squash for one fake neuron by hand via the script",
    glance="A **neuron** = dot product + optional squash (relu or sigmoid). A **layer** = many neurons in parallel (several mixes of the same inputs).",
    why="Deep learning is stacked mixes. One neuron is logistic’s cousin.",
    math="z = w·x + b. relu(z)=max(0,z) (turn off if negative). sigmoid as in ml-14.",
    cmd="python later_labs.py neuron",
    expect="printed z, relu, sigmoid for x=[2.0, 0.5].",
    walk="`lab_neuron`. Redo the multiply-add with a pencil.",
    tip="Negative relu is ‘this detector did not fire.’",
    watch="‘Neuron’ is a metaphor. It is arithmetic.",
    q=["Write relu(-3).", "What is a layer?"],
    a=["0.", "Several neurons sharing the same input list."],
    recap="- **You computed** one neuron.\n- **You defined** a layer.\n- **Next** stacking.",
    next_slug="ml-28-relu-stacking")

add(slug="ml-28-relu-stacking", title="ml-28 — ReLU and stacking", time="~50 minutes", prereq="ml-27",
    outcome="You watch a loss curve fall for a tiny stacked net on a circle-ish rule",
    glance="One mix is a straight fence. **Stacking** relu layers bends fences (xor, rings). That is why ‘deep’ exists.",
    why="Refund vs not is often not a straight fence in raw features. Stacks buy bends. They also buy overfitting.",
    math="Hidden = relu(X W1). Output squash of hidden W2. Loss should fall if learning rate is sane.",
    cmd="python later_labs.py relustack",
    expect="a falling loss plot; start loss > end loss in the printout.",
    walk="`lab_relu_stack`. This run is a demo of falling loss, not a full backprop walk (that is ml-29).",
    tip="If loss does not fall, learning rate or init is off. Here it should fall.",
    watch="Falling train loss ≠ good test. You learned that in M1.",
    q=["What does stacking buy vs one logistic line?", "What does ReLU do to negatives?"],
    a=["Bent decision regions.", "Sets them to 0."],
    recap="- **You stacked** relus.\n- **You saw** loss fall.\n- **Next** four-number backprop.",
    next_slug="ml-29-backprop-four-numbers")

add(slug="ml-29-backprop-four-numbers", title="ml-29 — Backprop four numbers", time="~70 minutes", prereq="ml-28",
    outcome="You follow dL/dw1 and dL/dw2 on a 4-number network",
    glance="**Backprop** is the chain rule: how a tiny change in an early knob changes the final error, by multiplying local slopes along the path.",
    why="Without this, ‘the net learned’ is a slogan. With this, it is a multiply chain.",
    math="h=relu(w1*x), yhat=w2*h, L=0.5*(yhat-y)². dL/dw2 = (yhat-y)*h. If h>0, dL/dw1 = (yhat-y)*w2*x.",
    cmd="python later_labs.py backprop",
    expect="forward numbers then two gradients then nudged weights.",
    walk="`lab_backprop`. Copy the prints onto paper. Change x in the file and rerun once.",
    tip="If relu is off (h=0), dL/dw1 is 0 — the early knob gets no vote this example.",
    watch="People skip the signs. (yhat-y) is ‘too high or too low.’",
    q=["If h=0, what is dL/dw1?", "What is backprop in one sentence?"],
    a=["0 in this relu setup.", "Multiply local slopes backward from the error."],
    recap="- **You walked** four numbers.\n- **You own** the chain.\n- **Next** dropout.",
    next_slug="ml-30-overfitting-dropout")

add(slug="ml-30-overfitting-dropout", title="ml-30 — Overfitting and dropout", time="~45 minutes", prereq="ml-29",
    outcome="You compare a wiggly polynomial to the true sine",
    glance="**Overfit** = memorized noise. **Dropout** (in nets) randomly silences teammates in training so no one teammate becomes a diva. This lab shows the wiggle; dropout is the story.",
    why="A net that recites last night’s tickets fails at dawn.",
    math="High-degree poly ≈ too many knobs for 40 points. Same smell as a wide net on tiny data.",
    cmd="python later_labs.py dropout",
    expect="scatter plus a wild curve vs the true sine.",
    walk="`lab_dropout`. Early stopping (stop when val loss rises) is the sibling trick.",
    tip="More data beats clever dropout. Dropout is a patch when data is short.",
    watch="Dropout at test time is usually turned off (scale weights). We are not implementing that here.",
    q=["What does the wild curve memorize?", "Name a sibling trick to dropout."],
    a=["Noise, not the sine.", "Early stopping / more data / weight tax (Ridge)."],
    recap="- **You saw** a memorizer.\n- **You named** dropout’s job.\n- **Next** numpy net ± torch.",
    next_slug="ml-31-numpy-net")

add(slug="ml-31-numpy-net", title="ml-31 — Numpy net then PyTorch", time="~55 minutes", prereq="ml-30",
    outcome="You train a logistic numpy net until loss falls; torch runs if installed, else numpy still counts",
    glance="Same bowl, two spellings. **PyTorch** writes the backward for you. CPU-only. If torch is missing on Python 3.14, the numpy path is the lesson.",
    why="You should not worship a framework. You should see it as a calculator for ml-29.",
    math="SGD: step opposite the gradient of MSE on sigmoid outputs.",
    cmd="python later_labs.py numpynet",
    expect="loss start/end printed; optionally `torch cpu end loss`.",
    walk="`lab_numpy_net`. Try/except around torch is because wheels may lag — numpy is required.",
    tip="When torch works, compare end losses. Same job.",
    watch="Do not pip-install a random GPU wheel on a CPU laptop ‘to be advanced.’",
    q=["What does torch buy you vs numpy here?", "Is GPU required?"],
    a=["Automatic gradients / a standard API.", "No."],
    recap="- **You trained** a tiny net.\n- **You treated** torch as optional CPU.\n- **Next** sequences.",
    next_slug="ml-32-order-matters")

add(slug="ml-32-order-matters", title="ml-32 — Order matters", time="~30 minutes", prereq="ml-31",
    outcome="You explain why bags fail on ‘late smashed’ vs ‘smashed late’",
    glance="Bags shuffle meaning. **Sequences** keep order. RNNs and transformers exist because of this.",
    why="‘not damaged’ vs ‘damaged not’ — a bag can panic.",
    math="No new formula. This is a motivation lab.",
    cmd="python later_labs.py order",
    expect="two phrases print as bag-indistinguishable.",
    walk="`lab_order`. Then you are ready to unroll.",
    tip="n-grams were a partial fix (ml-24). Sequences are the real fix.",
    watch="Do not jump to GPT to classify 10 tickets. Bayes may still win.",
    q=["Why do bags fail here?", "Name two model families that keep order."],
    a=["They ignore order.", "RNNs and transformers."],
    recap="- **You felt** the bag hole.\n- **Next** unroll an RNN.",
    next_slug="ml-33-rnn-unrolled")

add(slug="ml-33-rnn-unrolled", title="ml-33 — RNN unrolled", time="~55 minutes", prereq="ml-32",
    outcome="You view a hidden-state heatmap while reading A1-B2",
    glance="An **RNN** reuses the same mix each letter: hidden_new = tanh(x_letter mix + hidden_old mix). **Unroll** = draw that loop as a chain in time.",
    why="Warehouse codes are short sequences. Hidden state is the running memory of what you have read.",
    math="h_t = tanh(x_t Wxh + h_{t-1} Whh). tanh squishes to (-1,1).",
    cmd="python later_labs.py rnn",
    expect="a heatmap, x-axis letters of A1-B2, y-axis hidden units.",
    walk="`lab_rnn`. Random weights — you are watching the *shape* of memory, not a trained reader.",
    tip="Training would nudge Wxh/Whh like ml-29, through time (more chain rule).",
    watch="Vanilla RNNs forget far-back letters (ml-34).",
    q=["What does one column of the heatmap represent?", "What is reused each step?"],
    a=["Hidden units after reading that character.", "The same weight matrices."],
    recap="- **You unrolled** an RNN.\n- **You saw** memory as a vector.\n- **Next** LSTM/vanish.",
    next_slug="ml-34-lstm-vanishing")

add(slug="ml-34-lstm-vanishing", title="ml-34 — LSTM and vanishing", time="~45 minutes", prereq="ml-33",
    outcome="You can name three gates and why 0.7^10 is a problem",
    glance="**Vanishing gradient:** multiply a number <1 many times, the early letter’s vote dies. **LSTM** adds gates (forget/input/output) so memory can skip the multiply-death.",
    why="A 40-character ticket should still remember ‘refund’ at the start. Vanilla RNNs struggle.",
    math="0.7^10 ≈ 0.028. That is the fade.",
    cmd="python later_labs.py lstm",
    expect="printed gate sentences and 0.7^10.",
    walk="`lab_lstm` is the story lab. No giant LSTM train on CPU — the number is the lesson.",
    tip="Transformers later avoid this with attention (look directly at ‘refund’).",
    watch="Gates are still arithmetic. Not tiny brains with feelings.",
    q=["Name the three gates in this lesson.", "What does vanishing do to early tokens?"],
    a=["Forget, input, output.", "Their gradient/vote fades."],
    recap="- **You named** gates.\n- **You computed** fade.\n- **Next** pixels.",
    next_slug="ml-35-pixels-as-numbers")

add(slug="ml-35-pixels-as-numbers", title="ml-35 — Pixels as numbers", time="~40 minutes", prereq="ml-34",
    outcome="You display a 16×16 synthetic dented box and print min/max",
    glance="An image is a **matrix of brightness**. We generate boxes so you need no internet dataset.",
    why="Packing photos of crushed cartons are grids, not ‘vision magic.’",
    math="Shape (16,16). Values ~0 black to ~1 white in this lab.",
    cmd="python later_labs.py pixels",
    expect="a gray square with a darker dent patch; shape prints.",
    walk="`_box(True, 0)` draws a rectangle and a dent. Noise is slight.",
    tip="Color photos are three matrices (R,G,B). Same idea.",
    watch="16×16 is a teaching toy. Phone photos are huge — that is why convolution shares a stamp.",
    q=["What is one pixel here?", "Why synthetic?"],
    a=["A brightness number in the grid.", "No dataset hunt; CPU-small."],
    recap="- **You saw** pixels.\n- **Next** convolution stamps.",
    next_slug="ml-36-convolution-stamp")

add(slug="ml-36-convolution-stamp", title="ml-36 — Convolution stamp", time="~50 minutes", prereq="ml-35",
    outcome="You apply a 3×3 vertical-edge stamp and see a response map",
    glance="**Convolution** slides a small stamp (kernel) across the photo. Each position: multiply-overlap, add (a local dot product).",
    why="A dent is a local dark patch. A stamp can hunt edges without a unique knob per pixel.",
    math="Output[i,j] = sum of stamp * patch. We use a Sobel-ish vertical stamp.",
    cmd="python later_labs.py conv",
    expect="two plots: box and edge response.",
    walk="Nested loops in `lab_conv`. This is the CNN idea without a framework.",
    tip="Many stamps = many ‘what kind of edge’ detectors. A layer is a stack of stamps.",
    watch="Do not memorize kernel numbers. Remember ‘local mix.’",
    q=["What does the stamp multiply against?", "Why share one stamp everywhere?"],
    a=["A 3×3 patch of the image.", "A dent can appear anywhere; we reuse the detector."],
    recap="- **You stamped** edges.\n- **You understood** local dots.\n- **Next** pool/aug.",
    next_slug="ml-37-pooling-aug")

add(slug="ml-37-pooling-aug", title="ml-37 — Pooling and augmentation", time="~40 minutes", prereq="ml-36",
    outcome="You max-pool 16×16 to 8×8 and keep the dent visible",
    glance="**Pooling** shrinks the grid (max of 2×2). **Augmentation** is training on shifted/noisy copies so the recipe ignores camera luck.",
    why="Maya’s photos are never perfectly framed. Shrink also cheapens CPU.",
    math="Max-pool: each 2×2 → one number, the brightest/darkest extreme we chose max.",
    cmd="python later_labs.py pool",
    expect="two gray images; the dent survives at 8×8.",
    walk="`lab_pool` reshape+max. Augmentation in words: `_box` already adds noise — that is a tiny aug.",
    tip="Pooling throws away precise location. Sometimes you need that precision (measuring a tear).",
    watch="Too much pool = a blur that cannot tell dent from shadow.",
    q=["What does 2×2 max-pool output for a 16×16 input?", "Name one augmentation."],
    a=["8×8.", "Noise / shift / flip (in real pipelines)."],
    recap="- **You pooled.**\n- **You named** aug.\n- **Next** dent project.",
    next_slug="ml-38-dented-box")

add(slug="ml-38-dented-box", title="ml-38 — Dented box project", time="~45 minutes", prereq="ml-37",
    outcome="You train a linear-on-pixels toy to label dent vs not and print accuracy",
    glance="Project: 40 synthetic photos, flatten to vectors, logistic-like nudges. A real CNN would stamp first; this shows labels+pixels suffice for a *planted* dent.",
    why="End-to-end tiny loop before video.",
    math="Same as numpy net: p=sigmoid(Xw), nudge w.",
    cmd="python later_labs.py dented",
    expect="printed acc clearly above chance on this toy.",
    walk="`lab_dented`. Flattening ignores locality — the print reminds you a stamp is the real CNN.",
    tip="If you rotate dents randomly, this linear flatten model suffers; conv would cope better.",
    watch="High acc here is not ImageNet. It is a dark-patch detector.",
    q=["Why is flatten a cheat relative to conv?", "What did we plant?"],
    a=["It ignores that nearby pixels belong together unless the weights learn it the hard way.", "A dark rectangle dent."],
    recap="- **You labeled** boxes.\n- **You stayed** honest about toy acc.\n- **Next** video.",
    next_slug="ml-39-video-is-frames")

add(slug="ml-39-video-is-frames", title="ml-39 — Video is frames", time="~35 minutes", prereq="ml-38",
    outcome="You view 8 frames of a brightening box strip",
    glance="**Video** = images in time. No new magic object.",
    why="Chute cameras are GIFs in slow motion.",
    math="A clip is a stack of matrices. Shape (T, H, W).",
    cmd="python later_labs.py vframes",
    expect="eight tiny gray frames in a row.",
    walk="`lab_video_frames`. Brightness creeps with t — a fake ‘motion’ cue.",
    tip="Audio is another sequence. Same ‘order matters’ lesson.",
    watch="Do not download random YouTube for this CPU track.",
    q=["What is T in (T,H,W)?", "Is a video a different datatype than images?"],
    a=["Number of frames.", "It is many images ordered in time."],
    recap="- **You saw** frames.\n- **Next** sample every k.",
    next_slug="ml-40-sample-every-k")

add(slug="ml-40-sample-every-k", title="ml-40 — Sample every k", time="~30 minutes", prereq="ml-39",
    outcome="You compute 300 vs 20 frames for a 10s 30fps clip",
    glance="**Sample every k** keeps every k-th frame so CPU labs stay tiny while the story remains.",
    why="30 fps of a jam is mostly repeats. Maya needs the jam, not the blur.",
    math="300/15=20 if k=15.",
    cmd="python later_labs.py samplek",
    expect="printed 300 → 20 arithmetic.",
    walk="`lab_sample_k`. No plot — the numbers are the lab.",
    tip="Too large k skips the event (a 2-frame snag).",
    watch="Sports-slow-mo needs small k. A jammed belt does not.",
    q=["How many frames at 30fps for 10s?", "What is k for 20 frames from 300?"],
    a=["300.", "15."],
    recap="- **You subsampled** in arithmetic.\n- **Next** jam detector.",
    next_slug="ml-41-conveyor-jam")

add(slug="ml-41-conveyor-jam", title="ml-41 — Conveyor jam", time="~40 minutes", prereq="ml-40",
    outcome="You compare mean frame-to-frame change for moving vs jammed stacks",
    glance="If pictures barely change, the belt is dead. **Motion** ≈ average absolute difference between frames.",
    why="A one-number detector Maya could actually use at 2 a.m.",
    math="mean(|frame[t+1]−frame[t]|). Moving roll > jammed copies.",
    cmd="python later_labs.py jam",
    expect="moving change clearly larger than jammed.",
    walk="`np.roll` fakes motion. Jammed repeats `_box`.",
    tip="This is not a 3D CNN. It is the right first control. Deep video is optional GPU later.",
    watch="A camera shake looks like motion. Real systems stabilize or threshold with care.",
    q=["Which clip has larger mean change?", "Name a false motion source."],
    a=["Moving.", "Camera shake / lighting flicker."],
    recap="- **You detected** a jam with diffs.\n- **You stayed** CPU-honest.\n- **Next** attention.",
    next_slug="ml-42-attention-who")

add(slug="ml-42-attention-who", title="ml-42 — Attention who to look at", time="~50 minutes", prereq="ml-41",
    outcome="You print and plot a 4×4 attention map",
    glance="**Attention** = each token asks ‘who should I look at?’ Scores → softmax (shares of 100%) → mix.",
    why="When reading ‘not smashed,’ ‘not’ must look at ‘smashed.’ RNNs hope the hidden state still holds it. Attention looks back on purpose.",
    math="Softmax: exp(score)/sum(exp). Rows of A add to 1.",
    cmd="python later_labs.py attn",
    expect="a 4×4 printed matrix and a heatmap labeled A–D.",
    walk="`lab_attn` uses X @ X.T as a toy score (self-similarity). Real models use QKᵀ (next lesson).",
    tip="Darker cell = more look. A diagonal means ‘look at myself.’",
    watch="Random X means the map is not a trained linguist. You are learning the *shape*.",
    q=["What do rows of A sum to?", "Why look back instead of only hidden state?"],
    a=["About 1.", "Direct access to earlier tokens."],
    recap="- **You plotted** who-looks-at-whom.\n- **Next** QKV.",
    next_slug="ml-43-qkv-notebooks")

add(slug="ml-43-qkv-notebooks", title="ml-43 — QKV three notebooks", time="~50 minutes", prereq="ml-42",
    outcome="You print Q,K,V shapes and a mixed output shape",
    glance="**Q** query: what I am looking for. **K** key: what I advertise. **V** value: what I will hand over if chosen. Three linear mixes of the same X.",
    why="Without three notebooks, every look is ‘am I similar to you?’ With three, the model can look for *role* not just similarity.",
    math="Q=XWq, K=XWk, V=XWv. A=softmax(QKᵀ/√d). out=AV.",
    cmd="python later_labs.py qkv",
    expect="shapes (4,3) printed twice and mixed values (4,3).",
    walk="`lab_qkv`. √d scale keeps dots from exploding before softmax.",
    tip="Heads = several QKV sets in parallel, then concat. We skip coding that; the idea is ‘several look styles.’",
    watch="Letters QKV are not ‘quality.’ They are query/key/value.",
    q=["What does V carry?", "Why divide by √d?"],
    a=["The content mixed into the output.", "To keep scores from getting huge as d grows."],
    recap="- **You factored** three notebooks.\n- **Next** positions.",
    next_slug="ml-44-positions-encoder-decoder")

add(slug="ml-44-positions-encoder-decoder", title="ml-44 — Positions, encoder, decoder", time="~45 minutes", prereq="ml-43",
    outcome="You view a sine/cosine-ish position heatmap",
    glance="Attention has no left-to-right unless you **add position tags**. **Encoder** reads the whole input. **Decoder** writes the output one token at a time (often looking at encoder too).",
    why="‘box smashed’ vs ‘smashed box’ need different tags. GPT-style models are decoders; BERT-style are encoders.",
    math="Classic tags: sin/cos of position / 10000^{i/d}. The plot is the pattern, not a proof.",
    cmd="python later_labs.py pos",
    expect="an 8×4 heatmap of position tags.",
    walk="`lab_pos`. Encoder vs decoder is the printed story in the lesson; the plot is positions.",
    tip="If you skip positions, the model sees a bag of tokens again.",
    watch="There are other position recipes (learned, RoPE). Same job: mark where.",
    q=["What breaks if we skip positions?", "Does a decoder generate all words at once in the usual GPT setup?"],
    a=["Order.", "No. One after another (next token)."],
    recap="- **You tagged** positions.\n- **You split** encoder/decoder jobs.\n- **Next** tiny transformer table.",
    next_slug="ml-45-tiny-transformer")

add(slug="ml-45-tiny-transformer", title="ml-45 — Tiny transformer", time="~50 minutes", prereq="ml-44",
    outcome="You print a 3×3 next-char table on abcabcabc",
    glance="A transformer block is mix-with-attention then a small net, stacked. This CPU lab shows the **job**: next character, as a table — the same job GPT has, minus the stack.",
    why="You should feel next-token before claiming you ‘built GPT.’",
    math="Count P(next|now) on a repeating string. That is a bigram transformer-shaped table.",
    cmd="python later_labs.py tinytf",
    expect="a 3×3 probability table for a,b,c.",
    walk="`lab_tiny_tf`. After `b` you should see mass on `c`, etc.",
    tip="Stacking attention is how you get longer patterns than one previous letter.",
    watch="This is not training GPT-2. It is the skeleton.",
    q=["What does each row of P mean?", "What would a deeper transformer add?"],
    a=["Chance of next letter given now.", "Mix farther context, not only last char."],
    recap="- **You built** a next-char table.\n- **You connected** it to GPT’s job.\n- **Next** temperature.",
    next_slug="ml-46-next-token-temperature")

add(slug="ml-46-next-token-temperature", title="ml-46 — Next token and temperature", time="~40 minutes", prereq="ml-45",
    outcome="You print softmax at three temperatures",
    glance="**Logits** are raw scores. **Softmax** turns them into chances. **Temperature T** divides logits: low T → greedy winner; high T → more random.",
    why="Customer-facing Maya should use low T. A brainstorming copywriter might raise T. T is not weather.",
    math="p_i = exp(z_i / T) / sum exp(z_j / T).",
    cmd="python later_labs.py temp",
    expect="T=0.2 is peaky; T=2.0 is flatter.",
    walk="`lab_temp`. Same logits, three T.",
    tip="T→0 is argmax. T→∞ is uniform.",
    watch="High T + weak model = garbage that sounds confident if you do not read it.",
    q=["What does low T do?", "Are logits probabilities?"],
    a=["Sharpens on the winner.", "Not until softmax."],
    recap="- **You changed** T.\n- **You refuse** weather jokes.\n- **Next** three ways to specialize.",
    next_slug="ml-47-finetune-prompt-rag")

add(slug="ml-47-finetune-prompt-rag", title="ml-47 — Fine-tune vs prompt vs RAG", time="~40 minutes", prereq="ml-46",
    outcome="You can pick the right tool for a Meridian policy question",
    glance="**Prompt:** write instructions, freeze weights. **Fine-tune:** change weights on your texts (CPU: tiny only). **RAG:** fetch documents, then generate — Pack D Lesson 18.",
    why="People fine-tune when they needed a lookup. Maya’s refund policy changes weekly — RAG wins. Your chat style is stable — tiny fine-tune / you-bot.",
    math="No new equation. This is a product lesson.",
    cmd="python later_labs.py threeways",
    expect="three printed strategies.",
    walk="`lab_three_ways`. Then skim Lesson 18 title in the ADK track — do not skip Native ADK rules there.",
    tip="If the fact must be citeable and current, retrieve. If the voice must be yours, extra training data.",
    watch="Fine-tuning a huge model on a laptop is not this track. We said CPU-honest.",
    q=["Policy changes weekly: which way?", "You-bot voice: which way is this bonus track using?"],
    a=["RAG (and ADK tools).", "Tiny local counts / bigram-style fit on your file."],
    recap="- **You chose** among three.\n- **You pointed** at Lesson 18.\n- **Next** tiny GPT sample.",
    next_slug="ml-48-tiny-gpt-cpu")

add(slug="ml-48-tiny-gpt-cpu", title="ml-48 — Tiny GPT on CPU", time="~50 minutes", prereq="ml-47",
    outcome="You train a bigram character model on a warehouse sentence and sample 40 chars",
    glance="We nudge a vocab×vocab table to predict the next character. That is GPT’s job at the smallest scale. No billion weights.",
    why="You should hear a model babble ‘pack the box’ fragments and know why it is not ChatGPT.",
    math="Softmax loss on next char; gradient into the row of ‘current char.’",
    cmd="python later_labs.py tinygpt",
    expect="a sample string that vaguely echoes pack/scan/dock.",
    walk="`lab_tiny_gpt`. 200 steps, CPU, seconds.",
    tip="Longer text + attention (not in this file) = closer to a ‘real’ tiny GPT.",
    watch="If the sample is garbage, that is still a successful lab — you saw next-token noise.",
    q=["What is the output unit here?", "Did we train GPT-4?"],
    a=["Next character chances.", "No."],
    recap="- **You sampled** a baby LM.\n- **You stayed** honest.\n- **Next** you-bot.",
    next_slug="ml-49-you-bot")

add(slug="ml-49-you-bot", title="ml-49 — Chatbot that talks like you", time="~55 minutes", prereq="ml-48",
    outcome="You generate a cousin-of-you sample from my_voice.txt and judge it as Maya would",
    glance="Replace `my_voice.txt` with your sentences. We count char-to-next-char from **your** file. Quality is **cousin**, not clone. Eval: would Maya send this to a customer?",
    why="This is the fun packed project. It is also how you learn humility about ‘custom GPT.’",
    math="Same bigram table as ml-48, data = you.",
    cmd="python later_labs.py youbot",
    expect="first run writes a starter file; second run after you edit should sound slightly more like your paste. Still clumsy.",
    walk="`lab_youbot`. Keep the file **local**. Do not paste passwords or card numbers.",
    tip="More unique sentences > repeating one line 500 times (that overfits a loop).",
    watch="Do not deploy this as Meridian CX. Use ADK + Gemini + policy RAG for customers.",
    q=["What is the eval question?", "What must you never put in my_voice.txt?"],
    a=["Would Maya send this to a customer?", "Secrets, payment data, private customer PII."],
    recap="- **You trained** on your voice file.\n- **You refused** to ship cousin-spam.\n- **Next** RL worlds.",
    next_slug="bonus-rl-visual-playground")

add(slug="ml-50-q-vs-neural-policy", title="ml-50 — Q-tables vs neural policies", time="~40 minutes", prereq="bonus-rl-visual-playground",
    outcome="You can contrast a spreadsheet policy with a net that scores unseen states",
    glance="**Tabular Q** stores one cell per seen situation. A **neural policy** outputs action scores for states never stored. Same RL loop (the five worlds).",
    why="Dock grids fit a table. Pixel views of the field do not. That is when deep RL appears — still the same rewards.",
    math="Policy = greedy argmax Q vs softmax(net(state)).",
    cmd="python later_labs.py qvnet",
    expect="three printed sentences. Then reopen `python play.py` in `project/rl_playground` if you want the pictures.",
    walk="`lab_q_vs_net` plus the RL bonus lesson. Do not skip playing world 1.",
    tip="If n_states * n_actions is millions, tables look dead. That pain is the cue for a net.",
    watch="A net does not remove the need for a good reward. World 3 still teaches reward hacks.",
    q=["When does a table fail?", "Is the learning loop different?"],
    a=["Too many states to fill.", "No. Memory differs."],
    recap="- **You connected** RL playground to nets.\n- **Next** capstone.",
    next_slug="ml-51-meridian-cpu-capstone")

add(slug="ml-51-meridian-cpu-capstone", title="ml-51 — Capstone — ticket + photo + delay", time="~60 minutes", prereq="ml-49 and ml-38",
    outcome="You run a CPU slice that combines intent, dent score, and delay into a suggested path — and you can say why ADK+Gemini still exists",
    glance="One Meridian moment: text intent (Bayes), dent score (pixels), delay number. Print a suggested path. Contrast with tools+Gemini in the main track.",
    why="If you cannot assemble the parts, the bonus track was tourism. If you cannot name why this is not production CX, you missed Pack A.",
    math="No new math. Composition of M3/M5/M8.",
    cmd="python later_labs.py capstone",
    expect="printed intent, dent_score, delay, and a suggested line about damage path vs scans.",
    walk="`lab_capstone`. Then write one paragraph: what would Lesson 04 tools + Lesson 18 RAG add?",
    tip="This is the ‘feel the parts’ version. Production still Native ADK.",
    watch="Do not replace OrderOps with this script.",
    q=["Which three signals did we combine?", "Why still do the ADK track?"],
    a=["Ticket intent, dent score, delay.", "Tools, policy, evals, HITL, Gemini quality, safety."],
    recap="- **You assembled** a CPU slice.\n- **You understand** why Meridian still needs ADK.\n- **You can start** Pack A or Pack D with less magic.",
    next_slug="01-agentic-foundations",
)


def main() -> None:
    import os

    if os.environ.get("FORCE_EMIT_ML_STUBS") != "1":
        raise SystemExit(
            "Refusing to overwrite hand-written ML tutorials. "
            "The lessons in lessons/ml-*.md are the source of truth. "
            "Set FORCE_EMIT_ML_STUBS=1 only if you really want stub files back."
        )
    LESSONS.mkdir(parents=True, exist_ok=True)
    for item in ITEMS:
        slug = item["slug"]
        text = lesson(**item)
        path = LESSONS / f"{slug}.md"
        path.write_text(text, encoding="utf-8")
        print("wrote", path.name)
    print("count", len(ITEMS))


if __name__ == "__main__":
    main()

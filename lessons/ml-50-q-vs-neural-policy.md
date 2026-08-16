# ml-50 — Q-tables vs neural policies

**Level:** Absolute beginner  
**Time:** ~50 minutes  
**Prerequisites:** **`bonus-rl-visual-playground`** (the five-world window). Do that bonus **before** this lesson. Setup from ml-00 for the ML venv.  
**Lab outcome:** You print three sentences that name tabular Q vs a neural policy, then you can say why the *loop* is the same and the *memory* is not — and you reopen `play.py` in the **other** venv if you already did the bonus

---

## At a glance

**Tabular Q** = one spreadsheet cell per `(state, action)`. You watched that spreadsheet color in during the RL bonus.

**Neural policy** = a net that outputs action scores for states you have **never stored**. No cell for that exact situation.

Same loop:

```text
look → act → world replies with a reward → update memory → repeat
```

Different memory: a **table** vs a **net**.

Tables fail when `n_states * n_actions` is huge (pixels, raw dock cameras). That pain is the cue for deep RL — still not a reason to replace OrderOps with a toy.

You have **two virtual environments**. Do not mix them.

---

## Why this matters

Maya’s intern fills a Q table for “wind bucket × goal height × kick” (World 1). That is **1,200** cells. Doable.

The same intern wants “every camera pixel is a state.” A 160×90 grayscale frame is 14,400 numbers **before** you even pick an action. A table cannot have a row per image. It would be empty forever.

If you skip this lesson, “we need a neural net for RL” sounds like fashion. After this lesson it is arithmetic: **too many rows to fill**.

---

## Concept primer

| Word | Plain English | Where you already saw it |
| --- | --- | --- |
| **State** | What the agent is allowed to know *now* | Wind + goal buckets; dock (x, y, heading) |
| **Action** | One legal move | Kick combo; jump; turn left |
| **Q table** | Spreadsheet of “how good is this move here?” | `self.q` in `rl_core.py` |
| **Policy** | The rule that picks an action | Greedy: `argmax` of that row; or a net’s scores |
| **Neural policy** | A net: in = state features, out = scores for each action | Not trained in `later_labs.py`; named here |
| **n_states × n_actions** | How many cells the table needs | World 1: **25 × 48 = 1,200** |

```text
Tabular Q          Neural policy
─────────────      ──────────────────────────
row = state        net(state_features)
col = action       → scores for every action
must visit cells   can generalize to nearby states
empty if too big   can still fail if reward is dumb
```

> **Tip:** If you remember one sentence from the bonus: *RL is a running rumor about each move.* A net is a compressed rumor, not a different religion.

> **Watch out:** A net does **not** fix a bad reward. World 3 still taught reward hacks. Deep RL can hack faster.

---

## Setup — two islands

This playground is **Python 3.14.6**. The ML island pins **numpy 2.5.2** and **scikit-learn 1.9.0**. The RL island pins **pygame 2.6.1** and **numpy 2.2.6**. They are **separate** `.venv` folders.

| Folder | Activate | Libraries | Command today |
| --- | --- | --- | --- |
| `project/ml_playground` | `source .venv/bin/activate` | numpy 2.5.2, sklearn 1.9.0 | `python later_labs.py qvnet` |
| `project/rl_playground` | `source .venv/bin/activate` | pygame 2.6.1 | `python play.py` |

If your ML prompt does not show `(.venv)`, finish Setup in ml-00 first.

```bash
cd project/ml_playground
source .venv/bin/activate
```

- `source` runs the activate script in *this* terminal so `python` is the island’s Python.

**It worked when** `(.venv)` is at the front of the prompt **and** you are in `ml_playground` for Step 1.

If you never created `project/rl_playground/.venv`, stop and do `bonus-rl-visual-playground` first. That is a prerequisite, not optional flavor.

---

## Hands-on

### Step 1 — Print the three sentences (ML venv)

Why this command now: `qvnet` is the argparse name for `lab_q_vs_net`. The product of this CPU lab *is* those three lines.

```bash
python later_labs.py qvnet
```

`qvnet` is a lab name, not a dash-flag.

**It worked when** you see **exactly** these three lines:

```text
Tabular Q: one spreadsheet cell per (state, action). See project/rl_playground.
Neural policy: a net outputs action scores for states you have NEVER stored.
Same loop: act, reward, update. Different memory.
```

Point at each line:

1. Table = cell per pair. The bonus window *was* that table.
2. Net = scores for unseen states. No row allocated in advance.
3. Loop unchanged. Memory changed.

- [ ] You ran `python later_labs.py qvnet` **in the ML venv**
- [ ] You read all three sentences out loud

### Step 2 — Walk `lab_q_vs_net` and `rl_core.py`

Open `later_labs.py`. Find `lab_q_vs_net`. It is three `print` calls. That is the ML-side lab: **name the contrast**, then send you back to the playground.

Now open `project/rl_playground/rl_core.py` (editor is allowed to look across folders). Find `TabularQAgent`.

1. `self.q = np.zeros((n_states, n_actions))` — **this** is the spreadsheet. Size is baked in at construction.
2. `act`: with probability `epsilon`, random move; else `argmax` on **that row**.
3. `learn`: `new = old + alpha * (target - old)` with `target = reward + gamma * max(Q[next])` (or 0 if done).

A neural policy would **delete** `self.q` as the memory and instead do:

```text
scores = net(features_of_state)
pick from scores (greedy or softmax)
update net weights from the same (reward, next state) story
```

You do not train that net in this lesson. You name why it exists: **the zeros table cannot grow a row per pixel**.

World sizes you already met (bonus):

| World | n_states | n_actions | Cells |
| --- | --- | --- | --- |
| 1 Kick | 5×5 = **25** | 8×6 = **48** | **1,200** |
| 3 Dock | 8×6×4 = **192** | **3** | **576** |
| 4 Balance | 5×5×7×5 = **875** | **2** | **1,750** |

Those fill in minutes. A row per camera frame does not.

> **Tip:** `n_states * n_actions` is the question Maya should ask before anyone says “just Q-learn it.”

> **Watch out:** `later_labs.py` cannot import `play.py` from here without pygame. Stay in the ML venv for `qvnet`. Switch islands for the window.

### Step 3 — Reopen the bonus window (RL venv)

Why now: the three sentences need the heatmap in your eyes again. Same loop, table memory.

Leave the ML island first (new terminal, or `deactivate`):

```bash
cd project/rl_playground
source .venv/bin/activate
python play.py
```

- `cd` changes folder. This is a **different** `.venv` than `ml_playground`.
- `source` turns on **pygame 2.6.1** Python, not the sklearn island.

**It worked when** the window titled `RL playground — watch the spreadsheet fill in` opens. Press `1`–`5` as in the bonus.

If `No module named pygame`: you are still in the ML venv. `which python` should show `project/rl_playground/.venv/bin/python`.

This playground draws letters with `bitmap.py`. It does **not** call `pygame.font` (Python 3.14.6 + pygame 2.6.1).

Watch World 1 long enough to point at the heatmap and say: “each cell is one `(state, action)` rumor.” That is tabular Q.

Press `ESC` when you have said it.

- [ ] You activated **`rl_playground/.venv`**, not the ML one
- [ ] The window opened
- [ ] You pointed at a Q cell (heatmap) and named it memory

### Step 4 — Mini experiment (ML venv again)

Back in `project/ml_playground` with **that** venv active, open `lab_q_vs_net` and add one print:

```python
    print("kick table cells", 25 * 48)
```

Rerun:

```bash
python later_labs.py qvnet
```

**Expect:** a fourth line `kick table cells 1200`.

Delete that print when you are done (revert).

- [ ] You printed **1200** from `25 * 48`
- [ ] You reverted to three sentences

---

## How it works (deeper)

The bonus already ran the loop. Here is the memory fork:

```text
              ┌── Q[state, action]  (must have that row)
act, reward ──┤
              └── net(features)     (shares knobs across states)
```

**Generalize** means: a kick in a wind bucket *near* one you trained can still get a decent score from a net, even if that exact bucket was rare. A table gives **0.0** until you visit that row.

**Fail mode for tables:** `n_states * n_actions` in the millions. Visits never cover the sheet. The intern looks drunk forever. That is not “RL does not work.” That is “you bought the wrong memory.”

**Fail mode for nets:** you still need exploration, a sensible reward, and features (or pixels with a conv stack from M8). World 3’s heading check still matters.

Maya’s warehouse: a 8×6 dock grid with 4 headings is a table. A live camera over the bay is a net (or a person). Neither script is OrderOps.

---

## Common pitfalls

1. **`ModuleNotFoundError: pygame` after `qvnet`.** You ran `play.py` with the ML venv. Switch folders and `source project/rl_playground/.venv/bin/activate`.
2. **`ModuleNotFoundError: sklearn` after you played.** You are still in the RL venv. Go back to `ml_playground`’s `.venv`.
3. **You skipped the bonus.** This lesson will feel like slogans. Do `bonus-rl-visual-playground` first.
4. **You thought a neural policy changes the RL loop.** The third printed line is the punch: same loop, different memory.
5. **You wanted to replace OrderOps with `play.py`.** Do not. Cartoon docks are not ticket tools.

---

## Knowledge check

Answer from the three printed lines and the cell counts you walked.

1. What are the three exact sentences from `python later_labs.py qvnet`?
2. World 1: what is `n_states * n_actions`?
3. When does a Q table fail in one sentence?
4. Does a neural policy use a different loop than the bonus?
5. Why do you keep **two** venvs?

<details>
<summary>Answers</summary>

1. `Tabular Q: one spreadsheet cell per (state, action). See project/rl_playground.` / `Neural policy: a net outputs action scores for states you have NEVER stored.` / `Same loop: act, reward, update. Different memory.`
2. **1,200** (25 × 48).
3. When there are too many `(state, action)` cells to visit (huge `n_states * n_actions`).
4. No. Same act → reward → update. Different memory.
5. `ml_playground` is numpy 2.5.2 / sklearn 1.9.0. `rl_playground` is pygame 2.6.1 and numpy 2.2.6. Mixing them breaks imports.

</details>

---

## Recap

- **You printed** the three-sentence contrast, counted 1,200 kick cells, and reopened the bonus window in the **RL** venv.
- **You understand** tables die when the spreadsheet is huge; nets share knobs; the loop stays RL.
- **Next** one CPU Meridian slice: ticket intent + dent pixels + delay — and a **failure mode** when Bayes says refund on a mixed crushed+refund sentence.

Next: `ml-51-meridian-cpu-capstone`

---

## Stretch goal

In `lab_q_vs_net`, temporarily print a *toy* “pixel table” size (do not build it):

```python
    print("fake 160x90 pixels as states * 3 actions", 160 * 90 * 3)
```

Rerun `python later_labs.py qvnet`.

**Expect:** `43200`. That is already 36× World 1’s table, and it still pretends each **pixel combo** is not the real state space (real images are far worse). Feel why the intern wants a net.

Delete the print (revert).

- [ ] You saw **43200**
- [ ] You reverted

---

## Feedback

Could you redo this lab from memory? Note the **lesson id** (`ml-50`), the **step number**, which **venv** you were in, what you **expected**, and what you **saw** (traceback, three lines, or a pygame window).

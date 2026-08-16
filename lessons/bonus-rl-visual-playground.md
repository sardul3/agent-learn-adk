# Bonus lesson — Watch a brain learn: five visual RL playgrounds

**Level:** Absolute beginner (no machine-learning background)  
**Time:** ~2.5–3.5 hours if you run every world and tinker  
**Prerequisites:** Python 3.11+ installed; you can open a terminal and a text editor  
**Lab outcome:** A window where five cartoon agents get better at a job by trial and error — and you can explain *why* each number on the side panel moves

---

## At a glance

You will not train a giant neural net today. You will fill a **spreadsheet of guesses** while a ball flies, a courier jumps crates, a van docks, a waiter balances coffee, and a paddle catches boxes.

By the end you can explain, without hand-waving:

- what an **agent**, **environment**, **state**, **action**, and **reward** are
- why random mistakes are required at the start (**exploration**)
- the one update that is the inner loop of most of RL (**Q-learning**)
- why some problems need “tomorrow’s points” and a kick-the-ball problem does not

---

## Why this matters

Meet **Maya**, a night-shift warehouse lead at Meridian. She watches new hires:

- first week: they kick a dummy ball at a hoop, badly
- then: they time jumps over crates on the line
- then: they reverse a van into a dock without scraping the wall

Nobody hands them a perfect instruction booklet for every wind, crate gap, and dock angle. They **try**, they **feel the result**, they **try differently**.

**Reinforcement learning (RL)** is that idea as a computer loop: an agent acts, the world replies with a number (a **reward**), the agent updates its guesses, repeat.

You are going to *see* that loop, not only read the formula.

---

## Concept primer (only what you need before the window opens)

### The five words

| Word | Plain English | In Maya’s warehouse |
| --- | --- | --- |
| **Agent** | The learner that picks a move | The new hire (or our cartoon character) |
| **Environment** | The rules of the world, including physics and “you crashed” | The field, the line, the dock |
| **State** | What the agent is allowed to know *right now* | Wind + goal height; distance to next crate |
| **Action** | One legal move | Kick at 40° with medium power; jump; turn left |
| **Reward** | A score for *this* step or this kick — not a speech, a number | +100 goal, −60 hit crate, +1 still balanced |

### The loop (draw this on a sticky note)

```
  ┌─────────────┐
  │ Look (state)│
  └──────┬──────┘
         ▼
  ┌─────────────┐     sometimes random on purpose
  │ Pick action │◀──── exploration (epsilon)
  └──────┬──────┘
         ▼
  ┌─────────────┐
  │ World moves │
  └──────┬──────┘
         ▼
  ┌─────────────┐
  │ Get reward  │
  └──────┬──────┘
         ▼
  ┌─────────────┐
  │ Update Q    │  “that move was better/worse than I thought”
  └──────┬──────┘
         ▼
        (repeat)
```

**Q** is a table: rows = situations, columns = moves, cells = “how good I currently think this is.”

After one experience the agent does:

```text
new_guess = old_guess + alpha * (what_actually_happened - old_guess)
```

- **alpha** (learning rate): how hard it yanks the old number. `0.15` means “move 15% of the way toward the new story.”
- **what_actually_happened** = reward now, plus (usually) the best guess for the *next* situation, shrunk by **gamma**.
- **gamma** (discount): `0` means “only this kick matters.” `0.99` means “staying alive later is almost as real as points now.”

> **Tip:** If you remember one sentence: *RL is not “the computer knows the answer.” It is “the computer keeps a running rumor about each move and updates the rumor when life disagrees.”*

> **Watch out:** A **reward** is not the same as “the agent understood the task.” A badly designed reward makes a van spin in circles because spinning is cheaper than scraping a wall. We will see that in World 3.

### What we are *not* doing today

| Today (tabular Q-learning) | Later (deep RL) |
| --- | --- |
| Spreadsheet of numbers | A neural net approximates the spreadsheet |
| States must be a small integer | Pixels / huge state spaces |
| You can *see* every cell | You watch a loss curve instead |

The *loop* is the same. That is why these toys transfer.

---

## Setup (do this once)

You need a local folder with the playground code (already in this repo).

### Step 1 — Open a terminal in the playground

Why now: Python will look for `play.py` in the current folder. If you skip `cd`, the import of `rl_core` fails.

```bash
cd project/rl_playground
```

- `-` is not a flag here; `cd` means “change directory.”

### Step 2 — Make a private Python island (venv)

Why: so pygame and numpy do not fight with other projects on your machine.

```bash
python3 -m venv .venv
```

- `-m venv` means “run the standard-library module named venv.”
- `.venv` is the folder name for that island.

Turn it on (macOS/Linux):

```bash
source .venv/bin/activate
```

**It worked when** your prompt shows `(.venv)` at the front.

### Step 3 — Install the two libraries

Why: **pygame** draws the window; **numpy** holds the Q spreadsheet as a fast grid of numbers.

```bash
pip install -r requirements.txt
```

- `-r` means “read this file as the list of packages.”

**It worked when** you see pygame 2.6.1 in the pip output, no red traceback.

### Step 4 — Launch the live window

```bash
python play.py
```

**It worked when** a window titled `RL playground — watch the spreadsheet fill in` opens. World 1 is a football field. The right panel ticks `episode` upward.

If it did not:

- `No module named pygame` → the venv is not active; redo Step 2’s `source` line, then Step 3.
- Window opens then dies → on macOS, use the same Python you installed pygame into (`which python` should point inside `.venv`).
- `font module not available` / circular import in `pygame.font` → this is a Python 3.14 + pygame wheel bug. The playground does **not** use `pygame.font`; it draws letters with `bitmap.py`. Update to the latest `play.py` and run again. You should not see `SysFont` in `play.py`.

### Controls (keep this visible)

| Key | What it does | Why you care |
| --- | --- | --- |
| `1`–`5` | Switch world | Each world teaches one RL idea |
| `SPACE` | Pause | Freeze a kick or a jump to talk about it |
| `G` | Greedy demo | Turn randomness almost off; “show me what you believe” |
| `R` | Wipe Q to zeros | Watch it get stupid again, then relearn |
| `+` / `-` | Speed | Fast to train, slow to *see* |
| `ESC` | Quit | |

---

## Lab map — five projects, five ideas

Do them **in order**. Each world is a complete project you can later copy and change.

| # | Project | What you watch | The idea it stamps |
| --- | --- | --- | --- |
| 1 | Kick the football | Ball arc + Q heatmap | One-shot action; reward after physics |
| 2 | Jump the crates | Courier vs crates | Timing; same action, different state |
| 3 | Dock the van | Grid + facing arrow | State must include heading; step cost |
| 4 | Balance the tray | Leaning coffee | Delayed failure; gamma matters |
| 5 | Catch the packages | Falling boxes | Tracking; move before the box arrives |

Done criteria for the whole bonus:

- [ ] Window runs; episodes increase
- [ ] You can pause and point at **state / action / reward** on screen
- [ ] You pressed `R` once and saw skill collapse
- [ ] You pressed `G` after many episodes and the agent looks less drunk
- [ ] You changed **one** reward or **one** hyper-parameter and can say what broke or improved

---

## Project 1 — Kick the football

### Why this world first

A kick is one decision, then a movie. That matches how people think of “trying something.” The Q table is 2D on screen: **angle × power**. Color = “how much I like this combo *for the current wind and goal height*.”

### What Maya’s intern is learning

Wind changes. The goal mouth sits higher or lower. The intern does not get a coach yelling “42 degrees.” They get: ball in, or ball in the grass.

### Try it

1. Leave the window on world **1**.
2. Set speed with `+` until kicks fire every fraction of a second.
3. Watch the heatmap: early on, all cells look similar (the table is near zero).
4. After a few dozen **goals**, some cells go warm. Gold outline = the kick that just happened.
5. Press `G`. Randomness drops for the *choice* (training still updates). You should see fewer wild sky-balls.
6. Press `R`. The heatmap goes cold. Skill is **memory in the table**, not a magic personality.

**It worked when** the right-panel `avg reward (80)` climbs from messy negatives/small numbers toward more frequent big spikes (a goal is +100).

> **Tip:** World 1 uses `gamma = 0` on purpose. After the ball lands, there is no “next warehouse situation” that we credit. Only this kick’s reward rewrites Q. Open `play.py` and find `gamma=0.0` next to `idx == 0`.

> **Watch out:** If you only watch 20 episodes, it will still look random. Wind × goal is 25 situations, and each has 48 kicks. The intern needs many tries *per weather*. Let it run.

### Walk the inner working (kick)

Open `world_kick.py`.

**State** is not “the ball’s x,y every frame.” That would explode the spreadsheet. State is:

- wind bucket `0–4`
- goal-height bucket `0–4`

So `n_states = 25`. The flight is **animation + physics**, then one fat reward.

**Action** is a pair packed into one integer:

- `angle_i = action // 6`
- `power_i = action % 6`

`//` is integer divide (how many 6s fit). `%` is remainder (which power slot).

When the ball hits the goal rectangle, reward is `100`. If it dies on grass, reward is “how close did you get,” capped so a total miss is not a nuclear −1,000,000 (huge numbers make later updates unstable).

Open `rl_core.py` and stare at `learn`:

- `future = 0` if the episode is done **or** (in this world) gamma is 0
- `target = reward + gamma * future`
- the cell moves toward `target` by fraction `alpha`

That is the entire “AI.”

### Mini experiment (do it)

In `play.py`, for world 0 only, change `alpha=0.25` to `alpha=0.02`. Restart.

- **Expect:** heatmap changes like ketchup in a bottle — slow. Need more episodes.
- Put `0.25` back when you are done so later worlds stay sane.

---

## Project 2 — Jump the crates

### Why this world exists

Now the **same action** (jump) is brilliant or fatal depending on **distance to the crate**. That is the sentence “state matters.”

### Try it

1. Press `2`.
2. Slow down with `-` so you can see takeoff.
3. Early episodes: jumps into empty air, or face-plants into wood.
4. Watch the two numbers top-left: `run` vs `JUMP` Q-values for *this* moment. When a crate is close and the agent is on the ground, `JUMP` should eventually win.
5. Press `G` after the reward sparkline stops being a flat trench of −60s.

**It worked when** the courier clears several crates in a row more often, and `crates cleared this run` is not always 0.

> **Watch out:** If you jump *every* frame, you never get a clean run-up. The table has an “am I in the air?” bit so the agent can learn “don’t jump in mid-air” (the code already ignores jump if `air` is true — the *policy* still has to learn when to press jump on the ground).

### Walk the inner working (parkour)

State is a tiny integer built from three questions:

1. Airborne? `0/1`
2. How far is the next crate? 8 buckets
3. How tall is it? 3 buckets

Reward design (this is the “coaching”):

- small plus for surviving (`0.4`) — otherwise the agent could stand still forever in a different game
- `+8` the first time you pass a crate
- `−60` for a hit
- `+40` for finishing the lane

Open `world_parkour.py` and find `_credited`. That set exists so we do not pay `+8` on every pixel after a crate. **Double-paying** a reward is a classic bug: the intern would farm the crate edge.

### Mini experiment

Change the crash reward from `-60` to `-5`. Restart world 2 (`2` then `R`).

- **Expect:** more reckless face-plants; dying is “whatever.”
- Put `-60` back.

---

## Project 3 — Dock the van

### Why this world exists

A square on a map is not enough. Facing **east** on the dock is success; facing **west** on the same square is a confused intern. **State = (x, y, heading).**

Also: every step costs a little (`-0.3`). Without a step cost, a van that already knows the dock might wander for fun because wandering is free.

### Try it

1. Press `3`.
2. Gold dot on the van = nose / heading.
3. Green cell says `DOCK >` — you must arrive **and** face east.
4. Walls are dark. Hitting them is `-8`.
5. Let it run. Then `G`. You want fewer wall kisses and a path that actually ends.

**It worked when** greedy mode often reaches the green bay instead of bouncing on the same wall.

> **Tip:** `FWD / LEFT / RIGHT` Q-values are for *this* cell and heading. Turning has a cost too (`-0.4`) so the van does not pirouette forever.

> **Watch out:** `avg reward` can look ugly for a long time (many −80 timeouts). Watch **whether docks happen**, not only the average.

### Walk the inner working (dock)

Actions:

- `0` move forward in the current heading
- `1` rotate left
- `2` rotate right

Success check:

```text
position == dock AND heading == east
```

If you only required position, the intern could T-bone the bay and still get paid. Maya would not sign that off.

### Mini experiment

In `world_dock.py`, remove the heading check (success if position matches only). Retrain.

- **Expect:** faster “success,” sloppier parking.
- That is a **reward hack**: the number went up, the job got worse. Restore the heading check.

---

## Project 4 — Balance the coffee tray

### Why this world exists

Nothing “bad” happens on the first lean. Three beats later the mugs are on the floor. The agent must value **future** reward. Here **gamma is high** (`0.98`): tomorrow’s “still upright +1” is almost as real as today’s.

This is the same *shape* as the famous cart-pole demo, with a waiter instead of a pole textbook.

### Try it

1. Press `4`.
2. Slow speed. Watch the tray drift, then dump.
3. Speed up. Early: death in a handful of ticks.
4. After many episodes, `balanced for N ticks` climbs. A full save is 220 ticks (`+20` bonus).
5. `G` should look like tiny corrections, not random lunges — if the table has filled.

**It worked when** you see runs that last visibly longer than the first minute of training.

> **Watch out:** We **bin** (chop into buckets) position, speed, angle, spin. Two slightly different leans share a row in Q. Too few bins = blurry vision. Too many bins = empty spreadsheet (never visits each row enough). The constants `NX, NV, NTH, NW` in `world_balance.py` are that tradeoff.

### Walk the inner working (balance)

Each tick:

- left or right shove on the skateboard
- angle accelerates from gravity + shove
- `+1` for not dead
- `−40` for dump or driving off the stage

`learn` now uses a real **future**: `gamma * max(Q[next_state])`. That is the agent whispering: “this shove is good if it leaves me in a state whose best move is still good.”

### Mini experiment

In `play.py` for `idx == 3`, set `gamma=0.0` (only this tick counts). `R` and retrain.

- **Expect:** the waiter gets worse at long balance. There is no credit for “I set up the next second.”
- Restore `0.98`.

---

## Project 5 — Catch the falling packages

### Why this world exists

The box is still high. If you wait until it is on your head, you are late. The state includes **row** (how soon) so the paddle can start moving **now**.

### Try it

1. Press `5`.
2. Brown box = package. Blue bar = paddle.
3. `LEFT / STAY / RIGHT` Q-values: when the box is two columns away and not yet low, `LEFT` or `RIGHT` should beat `STAY` after learning.
4. Sparkline: misses are −14. Catches are +12. You want the average to crawl up.

**It worked when** greedy mode tracks the chute instead of hugging one wall.

> **Tip:** Episode ends after 8 misses or 180 steps. That is so one unlucky streak does not last forever on the sparkline.

### Walk the inner working (catch)

State = paddle column × box column × box row bucket.

If we omitted row, the agent could not tell “I have time” from “it lands this instant.”

### Mini experiment

Spawn the box always in column 3 (change `_spawn` in `world_catch.py`). Retrain.

- **Expect:** the paddle camps center. Looks smart, learned nothing about tracking.
- Restore random spawn. **Diversity of situations** is how the spreadsheet gets coverage.

---

## How it works (deeper dive)

### Exploration vs exploitation

**Epsilon** is the chance of a coin-flip random action.

- Start near `1.0`: intern tries everything, including stupid kicks.
- Multiply by `epsilon_decay` after each episode (see `decay_epsilon`).
- Floor at `epsilon_min` (`0.05`) so it never fully stops sampling.

`G` in the UI is “act greedy *this step*” — useful to *demo*. If you greedy-demo from episode 0, you freeze on zeros and ties; the code tie-breaks at random, but you still explore less. Let it be messy first.

### The update, with numbers

Suppose Q[state, jump] = 2.0, you jump, reward = −60, episode ends.

```text
target = -60 + gamma * 0   (done)
new    = 2.0 + 0.15 * (-60 - 2.0) = 2.0 + 0.15 * (-62) ≈ -7.3
```

One crash does not write −60 into the cell. It **nudges**. That is why you need many crashes and many successes.

### Why we did not use a neural net

A net can eat pixels. It also hides the rumor table. Your job today is to *point at a cell*. When you later meet “DQN,” translate: the net is a compressed Q table.

### Reward is a product decision

| Design | What the intern actually learns |
| --- | --- |
| Only +1 at the distant goal | Too rare; table stays empty (sparse reward) |
| −1 every step + jackpot at goal | Shorter paths (World 3) |
| Huge crash penalty | Fear; maybe never approaches the crate |
| Pay for “looking busy” | Weird dances that farm the number |

Maya’s real systems (refunds, routing) fail the same way if you score the wrong thing.

---

## Common pitfalls / troubleshooting

1. **“It never learns.”** Epsilon still ~1.0 and you only watched 30 episodes. Look at `episode` and `epsilon` on the panel. World 1 needs many kicks per weather.

2. **`ModuleNotFoundError: pygame`.** You installed into a different Python than you run. `which python` must be `.../project/rl_playground/.venv/bin/python`.

3. **Window is black / frozen.** You paused with `SPACE`. Or speed is 1 and you are on a slow kick flight — wait for the ball to land.

4. **Greedy looks worse than random.** Table is still near zero or you pressed `R`. Train first, then `G`.

5. **You edited a world and “nothing changed.”** Worlds are constructed in `make_pair`. Restart `python play.py` after edits. Pressing `2` does not reload `.py` files from disk.

6. **Dock average is −80 forever.** Timeouts are −15 plus step costs. Watch for occasional +50 docks; then `G`.

Headless sanity check (no window; proves episodes finish):

```bash
python smoke_train.py
```

**It worked when** five lines print with an `avg reward` number and no traceback.

---

## Knowledge check

Try to answer without scrolling. Then check below.

1. In World 1, why can `gamma` be 0 without breaking the idea of RL?
2. What three questions make up the parkour **state**?
3. Why does the dock require a heading, not only an (x, y)?
4. If `alpha = 1.0`, what does one crash do to that Q cell?
5. Epsilon is 0.05. What does that mean in one sentence?
6. You add `+1` reward every time the van *turns*. What ugly policy might appear?

<details>
<summary>Answers</summary>

1. The kick’s consequence is fully in that episode’s reward; there is no useful “next state” after the ball is dead. RL still happened: action → reward → Q update.
2. Airborne or not; bucketed distance to next crate; crate height bucket.
3. The bay is a directed job. Same tile, wrong nose = a crash in real life.
4. The cell is replaced by the target in one shot (`old + 1.0 * (target - old)`). Very jumpy; one unlucky crash can wipe a good estimate.
5. About 1 in 20 moves is still random, even late in training.
6. A pirouette farm: spinning is paid work. (We charge for turns to fight that.)

</details>

---

## Recap

- **You built** a live gym of five tiny environments sharing one Q-learning brain (`rl_core.py` + `play.py`).
- **You now understand** the observe → act → reward → update loop, why state must include the facts the job needs, and why gamma / epsilon / reward are coaching knobs, not decorations.
- **You can do next** copy `world_kick.py` into `world_mine.py`, register it in `WORLDS` inside `play.py`, and teach an agent a rule *you* invented.

---

## Stretch goal — your sixth world

Pick one:

1. **Moving goal posts:** in World 1, change goal x during flight (gust). State must include something about that, or the intern cannot adapt.
2. **Two-crate look-ahead:** parkour state only sees the *next* crate. Add a second distance bucket. Does jump timing improve?
3. **Slippery dock:** with 10% chance, `forward` does nothing. Does the van learn to retry, or freeze?

Keep the state space small enough to fill. If `n_states * n_actions` is in the millions, tabular Q-learning will look dead. That pain is your cue for deep RL later.

---

## Feedback

Could you, from memory, draw the RL loop and name alpha, gamma, and epsilon?

If something failed: write the **world number**, the **step** (setup vs a mini experiment), what you **expected**, and what you **saw** (panel numbers, traceback, or “van spun”). That is enough to fix the lesson for the next reader.

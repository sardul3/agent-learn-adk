# Bonus ML playground (CPU)

Step-by-step lessons live in `lessons/ml-00-*.md` through `ml-51`, plus `lessons/bonus-rl-visual-playground.md`.

Start at **ml-00**. Each lesson names the exact command, the function to open, and what “it worked” looks like.

```bash
cd project/ml_playground
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

- `-m venv` means “run the standard-library module named venv.”
- `-r` means “read this file as the list of packages.”

**It worked when** `(.venv)` shows in the prompt and `python -c "import numpy, matplotlib, sklearn, pandas"` prints nothing.

```bash
python m0_labs.py model
python classic_labs.py leak
python later_labs.py capstone
```

The word after the script is a lab name (argparse choice), not a dash-flag.

Plots open a matplotlib window. Close the window to get the terminal back. On a machine with no display:

```bash
export ML_HEADLESS=1
```

This playground is CPU-only (numpy, matplotlib, pandas, scikit-learn). It is **not** Native ADK. Do not use `pygame.font` here.

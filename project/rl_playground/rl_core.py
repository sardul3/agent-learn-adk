"""Tabular Q-learning: the same loop every world in this playground uses.

Plain English: keep a spreadsheet of "how good is this move in this situation?"
After each move, nudge that number toward what actually happened.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class QHyper:
    """Knobs that change *how* the agent learns, not *what* the game is."""

    # How big a correction to make after one experience. 0.1 = 10% toward the new estimate.
    alpha: float = 0.15
    # How much future points matter vs points right now. 0.99 = "tomorrow almost equals today."
    gamma: float = 0.99
    # Chance of a random move (explore). Starts high so the agent tries things.
    epsilon_start: float = 1.0
    epsilon_min: float = 0.05
    # After each episode, multiply epsilon by this (0.997 = slow fade of randomness).
    epsilon_decay: float = 0.997


class TabularQAgent:
    """One row per situation (state), one column per move (action)."""

    def __init__(self, n_states: int, n_actions: int, rng: np.random.Generator, hyper: QHyper):
        self.n_states = n_states
        self.n_actions = n_actions
        self.rng = rng
        self.hyper = hyper
        self.epsilon = hyper.epsilon_start
        # Optimistic-ish zeros: the agent has no opinion until it tries.
        self.q = np.zeros((n_states, n_actions), dtype=np.float64)

    def act(self, state: int, greedy: bool = False) -> int:
        if (not greedy) and self.rng.random() < self.epsilon:
            return int(self.rng.integers(0, self.n_actions))
        row = self.q[state]
        # Tie-break at random so the agent does not freeze on the first zero it sees.
        best = np.flatnonzero(row == row.max())
        return int(self.rng.choice(best))

    def learn(self, state: int, action: int, reward: float, next_state: int, done: bool) -> None:
        old = self.q[state, action]
        future = 0.0 if done else float(np.max(self.q[next_state]))
        target = reward + self.hyper.gamma * future
        self.q[state, action] = old + self.hyper.alpha * (target - old)

    def decay_epsilon(self) -> None:
        self.epsilon = max(self.hyper.epsilon_min, self.epsilon * self.hyper.epsilon_decay)

    def reset_brain(self) -> None:
        self.q.fill(0.0)
        self.epsilon = self.hyper.epsilon_start

"""Headless smoke: each world can finish an episode and Q-values move."""

from __future__ import annotations

import numpy as np

from rl_core import QHyper, TabularQAgent
from world_balance import BalanceWorld
from world_catch import CatchWorld
from world_dock import DockWorld
from world_kick import KickWorld
from world_parkour import ParkourWorld


def run_world(cls, episodes: int, hyper: QHyper) -> float:
    rng = np.random.default_rng(0)
    world = cls(rng)
    agent = TabularQAgent(world.n_states, world.n_actions, rng, hyper)
    totals = []
    for _ in range(episodes):
        s = world.reset()
        total = 0.0
        for _t in range(500):
            a = agent.act(s)
            ns, r, done, _ = world.step(a)
            agent.learn(s, a, r, ns, done)
            total += r
            s = ns
            if done:
                break
        agent.decay_epsilon()
        totals.append(total)
    return float(np.mean(totals[-20:]))


def main() -> None:
    checks = [
        (KickWorld, QHyper(alpha=0.25, gamma=0.0, epsilon_decay=0.99), 80),
        (ParkourWorld, QHyper(), 40),
        (DockWorld, QHyper(), 40),
        (BalanceWorld, QHyper(gamma=0.98), 40),
        (CatchWorld, QHyper(), 40),
    ]
    for cls, hyper, n in checks:
        avg = run_world(cls, n, hyper)
        print(f"{cls.name:24}  last-20 avg reward {avg:8.2f}")


if __name__ == "__main__":
    main()

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RunBudget:
    """Per-turn budget. Defaults are lab-sized for a WISMO / refund chat."""

    max_steps: int = 8
    max_cost_usd: float = 0.25
    steps: int = 0
    cost_usd: float = 0.0

    def charge(self, step_cost: float = 0.02) -> None:
        self.steps += 1
        self.cost_usd += step_cost
        if self.steps > self.max_steps:
            raise RuntimeError("KILL_SWITCH_MAX_STEPS")
        if self.cost_usd > self.max_cost_usd:
            raise RuntimeError("KILL_SWITCH_MAX_COST")
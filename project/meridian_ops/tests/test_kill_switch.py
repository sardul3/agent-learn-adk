import pytest

from meridian_ops.safety.kill_switch import RunBudget


def test_ninth_charge_trips_max_steps():
    budget = RunBudget(max_steps=8, max_cost_usd=10.0)
    for _ in range(8):
        budget.charge()
    with pytest.raises(RuntimeError, match="KILL_SWITCH_MAX_STEPS"):
        budget.charge()


def test_cost_cap_trips_before_steps():
    budget = RunBudget(max_steps=100, max_cost_usd=0.05)
    budget.charge(step_cost=0.04)  # 0.04, still under
    with pytest.raises(RuntimeError, match="KILL_SWITCH_MAX_COST"):
        budget.charge(step_cost=0.04)  # 0.08 > 0.05
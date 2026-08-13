from meridian_ops.tools.atp import suggest_substitute_for_short
import pytest

from meridian_ops.tools.atp import get_atp, reserve_substitute


@pytest.mark.asyncio
async def test_get_atp_organic_milk_is_zero():
    out = await get_atp("884210")
    assert out["status"] == "success"
    assert out["atp_qty"] == 0


@pytest.mark.asyncio
async def test_reserve_defaults_dry_run():
    out = await reserve_substitute("MC-1048310", "884210", "884299")
    assert out["dry_run"] is True
    assert out["reservation_id"] is None


@pytest.mark.asyncio
async def test_reserve_commit_returns_id():
    out = await reserve_substitute(
        "MC-1048310", "884210", "884299", dry_run=False
    )
    assert out["reservation_id"] == "RSV-MC-1048310-884299"

@pytest.mark.asyncio
async def test_suggest_picks_first_viable():
    out = await suggest_substitute_for_short(
        "MC-1048310",
        "884210",
        ["884299", "552100"],
    )
    assert out["chosen_substitute"] == "884299"
    assert out["preview"]["dry_run"] is True
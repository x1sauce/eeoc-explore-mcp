"""Reference answers independently read from the original workbooks."""

import runpy
from pathlib import Path

import pytest
from fastmcp import Client

from eeoc_explore.app import mcp
from eeoc_explore.tools import (
    ROWS,
    change,
    check_national_trend,
    compare_state_trends,
    explain_charge_outcomes,
)


def test_release_rebuild():
    script = Path(__file__).resolve().parents[1] / "scripts/build_snapshot.py"
    assert runpy.run_path(str(script))["build"]() == ROWS


async def test_registered_tools_and_resource():
    async with Client(mcp) as client:
        assert {t.name for t in await client.list_tools()} == {
            "check_national_trend",
            "compare_state_trends",
            "explain_charge_outcomes",
        }
        assert await client.read_resource("eeoc://coverage")
        assert await client.get_prompt("check_a_briefing")


async def test_national_claim():
    async with Client(mcp) as client:
        r = (
            await client.call_tool(
                "check_national_trend",
                dict(
                    metric="receipts",
                    start_fy=2024,
                    end_fy=2025,
                    claimed_direction="increase",
                ),
            )
        ).data
    assert (r["before"]["value"], r["after"]["value"]) == (88531, 88201)
    assert (r["delta_count"], r["percent_change"], r["claim_supported"]) == (
        -330,
        -0.37,
        False,
    )
    assert r["after"]["source"]["cell"] == "AD5"


async def test_state_trends():
    async with Client(mcp) as client:
        r = (
            await client.call_tool(
                "compare_state_trends",
                dict(
                    state_a="CA",
                    state_b="TX",
                    metric="retaliation_all",
                    start_fy=2021,
                    end_fy=2025,
                ),
            )
        ).data
    assert r["larger_percent_change"] == r["larger_count_change"] == "TX"
    for code, start, end, delta, pct, cell in [
        ("CA", 2158, 2926, 768, 35.59, "VK10"),
        ("TX", 3768, 5802, 2034, 53.98, "VK55"),
    ]:
        c = r["changes"][code]
        assert (c["before"]["value"], c["after"]["value"]) == (start, end)
        assert (c["delta_count"], c["percent_change"]) == (delta, pct)
        assert c["after"]["source"]["cell"] == cell


async def test_outcomes():
    async with Client(mcp) as client:
        r = (
            await client.call_tool("explain_charge_outcomes", {"fiscal_year": 2025})
        ).data
    assert (
        r["resolutions"]["value"] == 90744
        and r["resolutions"]["source"]["cell"] == "AD6"
    )
    assert r["source_difference"]["annual_report_count"] == 90743
    assert r["resolutions_minus_receipts"] == 2543


def test_suppression():
    r = compare_state_trends("AK", "TX", "epa", 2022, 2025)
    assert r["changes"]["AK"]["before"]["status"] == "suppressed"
    assert r["changes"]["AK"]["before"]["value"] is None
    assert "larger_count_change" not in r


def test_future_year():
    assert explain_charge_outcomes(2026)["status"] == "unavailable"


def test_basis_scope():
    r = check_national_trend("race", 2024, 2025)
    assert r["after"]["source"]["table"] == "E1a" and r["after"]["value"] == 29338
    assert "overlap" in r["basis_note"]


def test_no_baseline_for_new_statute():
    assert change("US", "pwfa", 2010, 2025)["status"] == "insufficient_data"


@pytest.mark.parametrize(
    "a,b,start,end", [("CA", "ca", 2021, 2025), ("CA", "TX", 2025, 2021)]
)
def test_invalid_comparison(a, b, start, end):
    assert (
        compare_state_trends(a, b, "receipts", start, end)["status"]
        == "invalid_comparison"
    )


def test_unknown_state():
    assert (
        compare_state_trends("XX", "TX", "race", 2022, 2023)["status"]
        == "insufficient_data"
    )

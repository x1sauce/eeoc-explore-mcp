"""Read-only agent tools backed by an immutable public workbook release."""

import json
from importlib.resources import files
from typing import Literal

from fastmcp import FastMCP

DATA = files("eeoc_explore").joinpath("data")
SOURCES = json.loads(DATA.joinpath("sources.json").read_text(encoding="utf-8"))
ROWS = json.loads(DATA.joinpath("counts.json").read_text(encoding="utf-8"))
INDEX = {
    (geo, year, metric): (value, table, cell, label)
    for geo, year, metric, value, table, cell, label in ROWS
}
BASIS_NOTE = (
    "A charge can allege several bases. A distinct union requires overlap counts."
)
CLOSURE_NOTE = (
    "Receipts count new charges. Resolutions count charges closed "
    "through the administrative process "
    "across all outcome types. Charges resolved this year can include earlier pending "
    "charges, current receipts and transfers from fair employment practices agencies."
)
GLOSSARY = "https://www.eeoc.gov/data/definitions-terms"
APR_URL = (
    "https://www.eeoc.gov/sites/default/files/2026-04/"
    "EEOC_APR_FY2025_APP_FY2027_508.pdf"
)
Change = Literal["increase", "decrease", "unchanged"]
Metric = Literal[
    "receipts",
    "resolutions",
    "race",
    "color",
    "sex",
    "national_origin",
    "religion",
    "retaliation_all",
    "retaliation_title_vii",
    "age",
    "disability",
    "epa",
    "gina",
    "pwfa",
    "settlements",
    "withdrawals_with_benefits",
    "administrative_closures",
    "no_reasonable_cause",
    "reasonable_cause",
    "successful_conciliations",
    "unsuccessful_conciliations",
    "merit_resolutions",
]
StateMetric = Literal[
    "receipts",
    "race",
    "color",
    "sex",
    "national_origin",
    "religion",
    "retaliation_all",
    "retaliation_title_vii",
    "age",
    "disability",
    "epa",
    "gina",
    "pwfa",
]


def observation(geo, year, metric):
    info = {"geography": geo, "fiscal_year": year, "metric": metric, "unit": "charges"}
    key = (geo, year, metric)
    if key not in INDEX:
        return {
            **info,
            "status": "unavailable",
            "value": None,
            "hint": "Check the coverage resource for supported years and geographies.",
        }
    value, table, cell, label = INDEX[key]
    status = "suppressed" if value == "*" else "unavailable" if value is None else "ok"
    return {
        **info,
        "status": status,
        "value": value if status == "ok" else None,
        "source": {
            "table": table,
            "sheet": SOURCES[table]["sheet"],
            "cell": cell,
            "label": label,
            "url": SOURCES[table]["url"],
        },
    }


def change(geo, metric, start, end):
    before, after = observation(geo, start, metric), observation(geo, end, metric)
    result = {"before": before, "after": after}
    if before["status"] != "ok" or after["status"] != "ok":
        return {**result, "status": "insufficient_data"}
    base = before["value"]
    delta = after["value"] - base
    return {
        **result,
        "status": "ok",
        "delta_count": delta,
        "percent_change": round(100 * delta / base, 2) if base else None,
        "direction": "increase"
        if delta > 0
        else "decrease"
        if delta < 0
        else "unchanged",
    }


def check_national_trend(
    metric: Metric, start_fy: int, end_fy: int, claimed_direction: Change | None = None
) -> dict:
    """Check a national trend and a draft's direction, FY 1997–2025."""
    if start_fy >= end_fy:
        return {
            "status": "invalid_period",
            "hint": "Use two years in chronological order.",
        }
    result = change("US", metric, start_fy, end_fy)
    if claimed_direction and result["status"] == "ok":
        result["claim_supported"] = claimed_direction == result["direction"]
    result["basis_note"] = BASIS_NOTE
    return result


def compare_state_trends(
    state_a: str, state_b: str, metric: StateMetric, start_fy: int, end_fy: int
) -> dict:
    """Compare count and percent changes for two geographic codes, FY 2009–2025."""
    a, b = state_a.strip().upper(), state_b.strip().upper()
    if a == b or start_fy >= end_fy:
        return {
            "status": "invalid_comparison",
            "hint": "Use different codes and increasing years.",
        }
    changes = {code: change(code, metric, start_fy, end_fy) for code in (a, b)}
    result = {
        "changes": changes,
        "note": (
            "Counts measure charges filed. Population and workforce size "
            "affect comparisons."
        ),
    }
    if any(c["status"] != "ok" for c in changes.values()):
        return {**result, "status": "insufficient_data"}

    def leader(field):
        x, y = changes[a][field], changes[b][field]
        if x is None or y is None:
            return None
        return a if x > y else b if y > x else "tie"

    # Compare the original ratios exactly; displayed percentages are rounded.
    left, right = changes[a], changes[b]
    lb, rb = left["before"]["value"], right["before"]["value"]
    pct_leader = None
    if lb and rb:
        gap = left["delta_count"] * rb - right["delta_count"] * lb
        pct_leader = a if gap > 0 else b if gap < 0 else "tie"
    return {
        **result,
        "status": "ok",
        "larger_count_change": leader("delta_count"),
        "larger_percent_change": pct_leader,
    }


def explain_charge_outcomes(fiscal_year: int) -> dict:
    """Explain one year's national receipts and resolutions using Table E1c."""
    receipts = observation("US", fiscal_year, "receipts")
    resolved = observation("US", fiscal_year, "resolutions")
    result = {
        "receipts": receipts,
        "resolutions": resolved,
        "explanation": CLOSURE_NOTE,
        "glossary_url": GLOSSARY,
    }
    if receipts["status"] != "ok" or resolved["status"] != "ok":
        return {**result, "status": "unavailable"}
    if fiscal_year == 2025:
        result["source_difference"] = {
            "annual_report_count": 90743,
            "annual_report_url": APR_URL,
            "workbook_count": resolved["value"],
            "note": (
                "This tool uses E1c. The publications differ by one. The reason "
                "is unverified."
            ),
        }
    return {
        **result,
        "status": "ok",
        "resolutions_minus_receipts": resolved["value"] - receipts["value"],
    }


def register(mcp: FastMCP):
    for tool in (check_national_trend, compare_state_trends, explain_charge_outcomes):
        mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": False})(tool)

    @mcp.resource("eeoc://coverage")
    def coverage() -> dict:
        """Supported metrics, geographic codes, years and workbook source links."""
        return {
            "national_years": [1997, 2025],
            "state_years": [2009, 2025],
            "geographies": sorted({r[0] for r in ROWS}),
            "sources": SOURCES,
            "national_metrics": sorted({r[2] for r in ROWS if r[0] == "US"}),
            "state_metrics": sorted({r[2] for r in ROWS if r[0] != "US"}),
            "availability": (
                "Some series begin later. Suppressed and blank cells have no "
                "numeric value."
            ),
            "basis_note": BASIS_NOTE,
            "outcome_note": CLOSURE_NOTE,
            "definitions": GLOSSARY,
        }

    @mcp.prompt()
    def check_a_briefing() -> str:
        """Demonstrate all three workflows with the public EEOC tables."""
        return (
            "Check the draft claim that US charge receipts increased from FY "
            "2024 to FY 2025. "
            "Compare California and Texas all-statutes retaliation charge "
            "growth from FY 2021 "
            "to FY 2025. Explain why resolutions could exceed receipts in FY 2025. "
            "Cite table and cell for each figure and identify any source discrepancy."
        )

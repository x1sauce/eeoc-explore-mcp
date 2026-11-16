"""Launch the actual stdio MCP server, execute all three demos and show source cells."""

import asyncio
import json
import sys
from pathlib import Path

from fastmcp import Client
from fastmcp.client.transports import StdioTransport

CASES = [
    (
        "check_national_trend",
        dict(
            metric="receipts", start_fy=2024, end_fy=2025, claimed_direction="increase"
        ),
    ),
    (
        "compare_state_trends",
        dict(
            metric="retaliation_all",
            state_a="CA",
            state_b="TX",
            start_fy=2021,
            end_fy=2025,
        ),
    ),
    ("explain_charge_outcomes", dict(fiscal_year=2025)),
]


async def main():
    entry = Path(__file__).resolve().parents[1] / "main.py"
    async with Client(
        StdioTransport(command=sys.executable, args=[str(entry)])
    ) as client:
        for name, inputs in CASES:
            result = await client.call_tool(name, inputs)
            print(json.dumps({"tool": name, "result": result.data}, indent=2))


if __name__ == "__main__":
    asyncio.run(main())

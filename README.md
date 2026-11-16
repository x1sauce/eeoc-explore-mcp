# EEOC Explore | Charge Statistics Assistant

A hackathon prototype for GSA's Dataset Access Server track. A public affairs analyst can check a briefing sentence, compare filing trends in two states and explain charge outcomes from the same MCP client. Each reported count comes with its fiscal year, geography, metric, workbook URL, worksheet and cell.

## Run the demo

Install Python and uv, open a terminal in the folder containing pyproject.toml, and run:

```powershell
uv sync --locked
uv run python scripts/demo.py
uv run pytest -q
```

The demo starts a real MCP server subprocess and calls all three tools over stdio. It prints structured responses and works without model credentials. An initial dependency install requires internet access. To use natural language, connect an MCP-capable host using its stdio configuration. Replace the example directory with the absolute path to this project and use the full uv executable path if the host cannot find uv.

```json
{"mcpServers":{"eeoc-explore":{"command":"uv","args":["--directory","C:/projects/eeoc-explore","run","--locked","python","main.py"]}}}
```

Use the host's chat box for the demo questions below. The host's model chooses the tool and writes the answer. The server does the lookup and arithmetic. Starting main.py directly waits for MCP input on stdin.

## Demo script

| Ask the agent | Expected evidence |
|---|---|
| My draft says EEOC received more charges in FY 2025 than FY 2024. Check it and suggest a corrected sentence. | 88,531 to 88,201, down 330 or 0.37%. E1c cells AC5 and AD5. |
| Which had the larger increase in all-statutes retaliation charge receipts from FY 2021 to FY 2025, California or Texas? Show both measures. | California 2,158 to 2,926 (+768, +35.59%). Texas 3,768 to 5,802 (+2,034, +53.98%). E1b cells PU10, VK10, PU55 and VK55. |
| How could EEOC resolve more charges than it received in FY 2025? Which source are you using? | E1c AD6 reports 90,744 resolutions and AD5 reports 88,201 receipts. Closures can include charges pending from earlier years and FEPA transfers. The FY 2025 annual report reports 90,743. The cause of the one-charge discrepancy is unverified. |

If asked for distinct charges alleging either race or retaliation, explain that the published counts overlap. The tables do not give the intersection needed to compute the union. Raw filing counts also do not measure the prevalence of discrimination in a population.

## Interfaces and source coverage

| MCP tool | Public workbook | Scope |
|---|---|---|
| check_national_trend | E1a and E1c | Compare one national metric over two fiscal years. Optionally check a proposed direction. |
| compare_state_trends | E1b | Compare two published geographic codes using the same basis and endpoints. Return source cells, absolute and percentage changes. |
| explain_charge_outcomes | E1c, EEOC definitions | Explain one fiscal year's receipts and resolutions. The 2025 response documents the cross-publication difference. |

The eeoc://coverage resource lists supported codes and metrics. The check_a_briefing prompt walks through all three tasks. National tables cover FY 1997–2025 and state data cover FY 2009–2025. Some statutes start later. Missing, suppressed and zero values are distinct. An unavailable endpoint prevents a numeric comparison. A zero baseline permits an absolute change only.

## Reproducibility

data/original contains the three original public Excel files. Source URLs, worksheet names and SHA-256 digests are in src/eeoc_explore/data/sources.json. The server uses a packaged snapshot. The importer extracts count cells and skips percentages, subtotals used as headers, and monetary measures. E1c supplies the national total receipts series. To rebuild the identical release, run the commands below. A new release requires deliberate review of headers, footnotes, hashes and reference tests.

```sh
uv run python scripts/build_snapshot.py
uv run pytest -q
```

## Sources

- [EEOC Enforcement and Litigation Statistics](https://www.eeoc.gov/data/enforcement-and-litigation-statistics-0)
- [EEOC definitions](https://www.eeoc.gov/data/definitions-terms)
- [EEOC FY 2025 Agency Performance Report, p. 36](https://www.eeoc.gov/sites/default/files/2026-04/EEOC_APR_FY2025_APP_FY2027_508.pdf)
- [GSA FastMCP starter](https://github.com/GSA-TTS/mcp-hackathon-template)
- [GSA hackathon criteria and deliverables](https://www.gsa.gov/super-intelligence/si-community-of-practice/events-and-training/mcp-server-and-si-agent-government-hackathon)

See eval/RESULTS.md and eval/stdio-results.json for the executed checks.

## Template files

The GSA agent skills are in `.agents/skills/`, vendor references in `docs/`, and optional hosting examples in `deploy/`. The Databricks evaluation example is in `eval/databricks/`. Its sample prompts and platform settings need to be adapted for a hosted evaluation. Local EEOC results are in `eval/RESULTS.md`.

`manifest.yaml` uses the project entry point and a user-provided cloud.gov route. For registry publication, replace the owner, repository, and endpoint placeholders in `server.json`. The local demo runs independently of both files.

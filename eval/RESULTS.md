# Evaluation | November 16, 2026

The 12 pytest cases passed locally with Python 3.11 and the locked dependencies. They check reconstruction from the original workbooks, tool discovery, resource and prompt availability, national figures, state comparisons, outcome definitions and the source discrepancy, suppressed counts, a year outside coverage, overlapping bases, a statute before its available period, invalid comparisons and an unknown geographic code. Pytest counts two invalid comparisons separately.

Three calls also completed through a separately launched MCP server using stdio. The recorded responses are in stdio-results.json. These automated checks measure retrieval, calculations, evidence and transport; they did not evaluate an LLM's tool selection or final prose. The manual OMP evaluation below covers those behaviors in this session. A hosted deployment and submission to GSA have not been evaluated here.

For a separate hosted-agent evaluation, submit the three README questions in fresh chats with the team's chosen host. Record the model, exact prompt, tool and arguments, final number, source cell, elapsed time and pass/fail. Score each answer against the corresponding reference cells. Add a suppressed-cell question (Alaska EPA receipts, FY 2022, E1b RP4) and an out-of-range question (national FY 2026 receipts). Both require an unavailable numeric answer.

## Manual OMP evaluation | this session

Four prompts were submitted in one conversation to the eeoc-explore MCP server. Model: `foundry/gpt-6-sol` (session runtime metadata). Deployment name: not recorded. Per-call elapsed time: not recorded. Test 1 explicitly specified the tool and all arguments; Tests 2–4 allowed the model to select the tool. These results are separate from the pytest and stdio checks above.

### 1. National receipts, FY 2024–2025 — PASS

Exact prompt (verbatim, including line breaks):

> Use the eeoc-explore MCP server to check this claim:
> “EEOC received more charges in FY 2025 than in FY 2024.”
>
> Call check_national_trend with metric receipts, start_fy 2024,
> end_fy 2025, and claimed_direction increase.
>
> Explain the result and cite the source table and cells.

Actual MCP call (session trace): `check_national_trend({"metric":"receipts","start_fy":2024,"end_fy":2025,"claimed_direction":"increase"})`.

Expected: Claim false; [E1c] AC5 = 88,531 (FY 2024), AD5 = 88,201 (FY 2025), change −330 (−0.37%).

Observed: Tool returned `direction: decrease`, `claim_supported: false`, 88,531 → 88,201, `delta_count: -330`, `percent_change: -0.37`, and E1c AC5/AD5. Final answer rejected the claim and cited both cells. **PASS.**

### 2. California versus Texas retaliation, FY 2021–2025 — PASS (presentation issue)

Exact prompt:

> Between FY 2021 and FY 2025, did California or Texas have the larger increase in all-statutes retaliation charge receipts? Show both the count change and percentage change, and cite the source cells

MCP call: `compare_state_trends({"state_a":"CA","state_b":"TX","metric":"retaliation_all","start_fy":2021,"end_fy":2025})`.

Expected: [E1b] California PU10 = 2,158 (FY 2021), VK10 = 2,926 (FY 2025), +768 (+35.59%); Texas PU55 = 3,768 (FY 2021), VK55 = 5,802 (FY 2025), +2,034 (+53.98%). Texas leads by count and percentage.

Observed: Tool returned all four counts and cells, both changes, and `larger_count_change: TX`, `larger_percent_change: TX`. Final answer included the two changes and four source cells. **PASS** on facts and evidence. Presentation issue reported: irrelevant opening commentary in the state comparison; it does not affect the numerical result.

### 3. FY 2025 receipts versus resolutions — PASS

Exact prompt:

> Why did EEOC resolve more charges than it received in FY 2025? Cite the figures and identify any difference between the workbook and annual report

MCP call: `explain_charge_outcomes({"fiscal_year":2025})`.

Expected: [E1c] AD5 = 88,201 receipts and AD6 = 90,744 resolutions, a difference of 2,543. Resolutions can include previously pending charges and transfers from fair employment practices agencies, not just the current year's receipts. The [FY 2025 annual report] reports 90,743 resolutions, one fewer than E1c; reason unverified.

Observed: Tool returned both workbook counts and cells, `resolutions_minus_receipts: 2543`, the pending-charges/transfers explanation, and the annual-report count of 90,743 with reason unverified. Final answer cited E1c AD5/AD6 and the annual report, without claiming the difference is solely a backlog reduction. **PASS.**

### 4. FY 2025 versus FY 2026 receipts — PASS

Exact prompt:

> Did national charge receipts increase from FY 2025 to FY 2026? Use the EEOC Explore data and cite your evidence.

MCP call: `check_national_trend({"metric":"receipts","start_fy":2025,"end_fy":2026,"claimed_direction":"increase"})`.

Expected: [E1c] AD5 = 88,201 for FY 2025; FY 2026 is outside the workbook's coverage, so the FY 2026 count and direction are unavailable. Do not assert an increase or invent a FY 2026 cell.

Observed: Tool returned FY 2025 = 88,201 at E1c AD5, FY 2026 `status: unavailable`, `value: null`, overall `status: insufficient_data`. Final answer said the comparison cannot be determined from EEOC Explore, cited E1c AD5, and gave no FY 2026 number. **PASS.**

[E1b]: https://www.eeoc.gov/sites/default/files/2026-04/Table_E1b._Charge_Receipts_by_State_%28includes_U.S._Territories%29_and_Basis_or_Statute_%28All_Statutes%29_FY_2009_-_FY_2025_suppressed_0.xlsx
[E1c]: https://www.eeoc.gov/sites/default/files/2026-03/Table_E1c._Charge_Receipts_and_Resolutions_by_Type_%28All_Statutes%29%2C_FY_1997_-_FY_2025.xlsx
[FY 2025 annual report]: https://www.eeoc.gov/sites/default/files/2026-04/EEOC_APR_FY2025_APP_FY2027_508.pdf

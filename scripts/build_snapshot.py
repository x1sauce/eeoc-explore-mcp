"""Rebuild packaged observations from the three unmodified EEOC workbooks."""

import hashlib
import json
import re
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "src/eeoc_explore/data"
ALIASES = {
    "Total Charges": "receipts",
    "Retaliation All Statutes": "retaliation_all",
    "Retaliation - All Statutes": "retaliation_all",
    "TVII Retaliation": "retaliation_title_vii",
    "Retaliation - Title VII only": "retaliation_title_vii",
    "Genetic Information Nondiscrimination Act": "gina",
    "Equal Pay Act": "epa",
    "Pregnant Workers Fairness Act*": "pwfa",
    "Withdrawals w/Benefits": "withdrawals_with_benefits",
}


def metric(label):
    return ALIASES.get(label, "_".join(label.lower().split()))


def build():
    records = []
    for table, source in sorted(
        json.loads((DATA / "sources.json").read_text()).items()
    ):
        path = ROOT / "data/original" / f"{table}.xlsx"
        if hashlib.sha256(path.read_bytes()).hexdigest() != source["sha256"]:
            raise ValueError(f"{table} differs from the documented release")
        book = load_workbook(path, read_only=True, data_only=True)
        rows = list(book[source["sheet"]].values)
        book.close()

        def add(geo, year, name, label, row, col):
            value = rows[row - 1][col - 1]
            if value not in (None, "*") and type(value) is not int:
                raise ValueError(f"Unexpected count at {table} row {row} col {col}")
            records.append(
                [geo, year, name, value, table, f"{get_column_letter(col)}{row}", label]
            )

        if table == "E1b":
            for col, header in enumerate(rows[2][2:], 3):
                if header is None or "%" in header:
                    continue
                year, label = re.fullmatch(r"FY (\d{4}) (.+)", header.strip()).groups()
                for row, (geo, *_) in enumerate(rows[3:], 4):
                    if geo and re.fullmatch(r"[A-Z]{2}", geo):
                        add(geo, int(year), metric(label), label, row, col)
        else:
            for row, cells in enumerate(rows[3:], 4):
                label = " ".join(str(cells[0] or "").split())
                if not label or not any(type(x) is int for x in cells[1:]):
                    continue
                if label.startswith("Monetary Benefits") or (
                    table == "E1a" and label == "Total Charges"
                ):
                    continue
                for col, header in enumerate(rows[2][1:], 2):
                    if header and re.fullmatch(r"FY \d{4}", str(header).strip()):
                        add(
                            "US",
                            int(header.strip()[3:]),
                            metric(label),
                            label,
                            row,
                            col,
                        )
    keys = {(r[0], r[1], r[2]) for r in records}
    if len(keys) != len(records):
        raise ValueError("Duplicate observations")
    return records


if __name__ == "__main__":
    (DATA / "counts.json").write_text(
        json.dumps(build(), separators=(",", ":")), encoding="utf-8"
    )

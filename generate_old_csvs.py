"""Utility to backfill historical Free Fire progress data into monthly CSV files.

This script reads the manually recorded data in ``data/old_data.csv`` and emits a
CSV per calendar month following the ``{year} {month} {uid}.csv`` naming
convention.  It also writes a ``summary.csv`` file that aggregates the monthly
and yearly totals to make the historical trends easier to inspect.

Run the script once after updating ``data/old_data.csv`` to refresh the derived
CSV files.
"""
from __future__ import annotations

import calendar
import csv
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List

UID = "2805365702"
SOURCE_PATH = Path("data/old_data.csv")
OUTPUT_DIR = Path("data")
MONTHLY_HEADER = [
    "Date",
    "BR Score",
    "Rank Gained",
    "Likes",
    "Likes Gained",
    "XP",
    "XP Gained",
    "Notes",
]
SUMMARY_HEADER = [
    "Year",
    "Month",
    "Days Logged",
    "Start XP",
    "End XP",
    "Total XP Gained",
    "Average Daily XP Gained",
]


@dataclass
class DataPoint:
    date_str: str
    date: datetime
    xp: int
    xp_gained: int
    notes: str

    @classmethod
    def from_row(cls, row: Dict[str, str]) -> "DataPoint":
        date_str = row["Date"].strip()
        date = datetime.strptime(date_str, "%m/%d/%Y")
        xp = int(row["XP"].replace(",", ""))
        xp_gained_raw = row.get("XP Gained", "").strip()
        xp_gained = int(xp_gained_raw) if xp_gained_raw else 0
        notes = row.get("Notes", "").strip()
        extras = row.get(None)
        if extras:
            extra_notes = [part.strip() for part in extras if part and part.strip()]
            if notes:
                notes = ", ".join([notes] + extra_notes)
            else:
                notes = ", ".join(extra_notes)
        return cls(date_str=date_str, date=date, xp=xp, xp_gained=xp_gained, notes=notes)


def load_data(source: Path) -> List[DataPoint]:
    with source.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return [DataPoint.from_row(row) for row in reader]


def ensure_output_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_monthly_files(data: Iterable[DataPoint]) -> Dict[int, List[DataPoint]]:
    by_year: Dict[int, Dict[int, List[DataPoint]]] = defaultdict(lambda: defaultdict(list))
    for point in data:
        by_year[point.date.year][point.date.month].append(point)

    ensure_output_dir(OUTPUT_DIR)

    for year, months in by_year.items():
        for month, rows in months.items():
            rows.sort(key=lambda p: p.date)
            month_name = calendar.month_name[month]
            filename = f"{year} {month_name} {UID}.csv"
            path = OUTPUT_DIR / filename

            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                writer.writerow(MONTHLY_HEADER)
                for row in rows:
                    writer.writerow(
                        [
                            row.date_str,
                            "",
                            "",
                            "",
                            "",
                            row.xp,
                            row.xp_gained if row.xp_gained else "",
                            row.notes,
                        ]
                    )

    # Flatten data grouped by year for summary generation.
    grouped_by_year: Dict[int, List[DataPoint]] = {
        year: sorted(
            (point for month_rows in months.values() for point in month_rows),
            key=lambda p: p.date,
        )
        for year, months in by_year.items()
    }
    return grouped_by_year


def write_summary(data_by_year: Dict[int, List[DataPoint]]) -> None:
    rows: List[List[str]] = []

    for year in sorted(data_by_year):
        points = data_by_year[year]
        monthly: Dict[int, List[DataPoint]] = defaultdict(list)
        for point in points:
            monthly[point.date.month].append(point)

        for month in sorted(monthly):
            month_points = monthly[month]
            month_points.sort(key=lambda p: p.date)
            total_gain = sum(p.xp_gained for p in month_points)
            days_logged = len(month_points)
            avg_gain = total_gain / days_logged if days_logged else 0
            rows.append(
                [
                    str(year),
                    calendar.month_name[month],
                    str(days_logged),
                    str(month_points[0].xp),
                    str(month_points[-1].xp),
                    str(total_gain),
                    f"{avg_gain:.2f}",
                ]
            )

        total_gain_year = sum(p.xp_gained for p in points)
        days_logged_year = len(points)
        avg_gain_year = total_gain_year / days_logged_year if days_logged_year else 0
        rows.append(
            [
                str(year),
                "ALL",
                str(days_logged_year),
                str(points[0].xp),
                str(points[-1].xp),
                str(total_gain_year),
                f"{avg_gain_year:.2f}",
            ]
        )

    summary_path = OUTPUT_DIR / "summary.csv"
    with summary_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(SUMMARY_HEADER)
        writer.writerows(rows)


def main() -> None:
    if not SOURCE_PATH.exists():
        raise SystemExit(f"Missing source data: {SOURCE_PATH}")

    data = load_data(SOURCE_PATH)
    grouped_by_year = write_monthly_files(data)
    write_summary(grouped_by_year)


if __name__ == "__main__":
    main()

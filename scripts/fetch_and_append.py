"""Daily Free Fire progress fetcher that updates monthly CSV exports."""
from __future__ import annotations

import calendar
import csv
import os
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Tuple
from zoneinfo import ZoneInfo

import requests

SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from scripts.config import DEFAULT_UID, build_api_url

UID = os.getenv("FREEFIRE_UID", DEFAULT_UID)
API_URL = build_api_url(UID)

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

TIMEZONE = ZoneInfo("Asia/Colombo")


def format_mdY(dt: datetime) -> str:
    return f"{dt.month}/{dt.day}/{dt.year}"


def monthly_file_path(dt: datetime) -> Path:
    month_name = calendar.month_name[dt.month]
    filename = f"{dt.year} {month_name} {UID}.csv"
    return BASE_DIR / filename


def ensure_monthly_header(path: Path) -> None:
    if not path.exists():
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(MONTHLY_HEADER)


def monthly_already_logged(path: Path, today_str: str) -> bool:
    if not path.exists():
        return False
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if row.get("Date") == today_str:
                return True
    return False


def parse_monthly_filename(path: Path) -> Tuple[int, int]:
    parts = path.stem.split(" ")
    if len(parts) != 3 or not parts[0].isdigit() or parts[2] != UID:
        raise ValueError(f"Unexpected monthly filename format: {path.name}")
    year = int(parts[0])
    month = datetime.strptime(parts[1], "%B").month
    return year, month


def iter_monthly_files() -> Iterator[Path]:
    paths: List[Tuple[int, int, Path]] = []
    for candidate in BASE_DIR.glob(f"* {UID}.csv"):
        if candidate.is_file():
            try:
                year, month = parse_monthly_filename(candidate)
            except ValueError:
                continue
            paths.append((year, month, candidate))
    for _, _, path in sorted(paths, key=lambda item: (item[0], item[1])):
        yield path


def parse_int(value: Optional[str]) -> Optional[int]:
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    value = value.replace(",", "")
    try:
        return int(value)
    except ValueError:
        return None


def load_last_logged_entry() -> Tuple[Optional[Dict[str, str]], Optional[Path]]:
    last_row: Optional[Dict[str, str]] = None
    last_path: Optional[Path] = None
    for path in iter_monthly_files():
        with path.open("r", newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                if row.get("Date"):
                    last_row = row
                    last_path = path
    return last_row, last_path


def append_monthly_entry(path: Path, row: Dict[str, object]) -> None:
    ensure_monthly_header(path)
    today = row["Date"]
    if today and monthly_already_logged(path, today):
        return

    ordered = [
        row.get("Date", ""),
        row.get("BR Score", ""),
        row.get("Rank Gained", ""),
        row.get("Likes", ""),
        row.get("Likes Gained", ""),
        row.get("XP", ""),
        row.get("XP Gained", ""),
        row.get("Notes", ""),
    ]

    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(ordered)


def load_monthly_stats(path: Path) -> Tuple[int, int, Dict[str, float]]:
    year, month_number = parse_monthly_filename(path)
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        xp_values: List[int] = []
        xp_gains: List[int] = []
        for row in reader:
            xp = parse_int(row.get("XP"))
            if xp is not None:
                xp_values.append(xp)
            xp_gain = parse_int(row.get("XP Gained"))
            if xp_gain is not None:
                xp_gains.append(xp_gain)

    if not xp_values:
        raise ValueError(f"Monthly file {path} contains no XP data")

    start_xp = xp_values[0]
    end_xp = xp_values[-1]
    total_gain = sum(xp_gains) if xp_gains else end_xp - start_xp
    days_logged = len(xp_values)
    avg_gain = total_gain / days_logged if days_logged else 0

    stats: Dict[str, float] = {
        "start_xp": start_xp,
        "end_xp": end_xp,
        "total_gain": total_gain,
        "days_logged": days_logged,
        "avg_gain": avg_gain,
    }
    return year, month_number, stats


def update_summary() -> None:
    summary_path = BASE_DIR / "summary.csv"
    month_stats: List[Tuple[int, int, Dict[str, float]]] = []
    for path in iter_monthly_files():
        try:
            stats = load_monthly_stats(path)
        except ValueError:
            continue
        month_stats.append(stats)

    if not month_stats:
        return

    rows: List[List[str]] = []
    by_year: Dict[int, List[Tuple[int, Dict[str, float]]]] = defaultdict(list)

    for year, month_number, stats in sorted(month_stats, key=lambda item: (item[0], item[1])):
        by_year[year].append((month_number, stats))
        rows.append(
            [
                str(year),
                calendar.month_name[month_number],
                str(int(stats["days_logged"])),
                str(int(stats["start_xp"])),
                str(int(stats["end_xp"])),
                str(int(stats["total_gain"])),
                f"{stats['avg_gain']:.2f}",
            ]
        )

    for year in sorted(by_year):
        year_stats = sorted(by_year[year], key=lambda item: item[0])
        start_xp = year_stats[0][1]["start_xp"]
        end_xp = year_stats[-1][1]["end_xp"]
        total_gain = sum(stat["total_gain"] for _, stat in year_stats)
        days_logged = sum(stat["days_logged"] for _, stat in year_stats)
        avg_gain = total_gain / days_logged if days_logged else 0
        rows.append(
            [
                str(year),
                "ALL",
                str(int(days_logged)),
                str(int(start_xp)),
                str(int(end_xp)),
                str(int(total_gain)),
                f"{avg_gain:.2f}",
            ]
        )

    with summary_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(SUMMARY_HEADER)
        writer.writerows(rows)


def main() -> None:
    now_colombo = datetime.now(TIMEZONE)
    today_str = format_mdY(now_colombo)

    response = requests.get(API_URL, timeout=30)
    response.raise_for_status()
    data = response.json()

    basic_info = data.get("basicInfo", {})
    ranking_points = int(basic_info.get("rankingPoints", 0))
    likes = int(basic_info.get("liked", 0))
    xp = int(basic_info.get("exp", 0))

    current_month_path = monthly_file_path(now_colombo)
    last_row, last_path = load_last_logged_entry()
    if last_row and last_row.get("Date") == today_str and last_path == current_month_path:
        print(f"Row for {today_str} already exists; no changes.")
        return

    last_br = parse_int(last_row.get("BR Score")) if last_row else None
    last_likes = parse_int(last_row.get("Likes")) if last_row else None
    last_xp = parse_int(last_row.get("XP")) if last_row else None

    rank_gained = ranking_points - last_br if last_br is not None else 0
    likes_gained = likes - last_likes if last_likes is not None else 0
    xp_gained = xp - last_xp if last_xp is not None else 0

    row = {
        "Date": today_str,
        "BR Score": ranking_points,
        "Rank Gained": rank_gained if rank_gained else "",
        "Likes": likes,
        "Likes Gained": likes_gained if likes_gained else "",
        "XP": xp,
        "XP Gained": xp_gained if xp_gained else "",
        "Notes": "",
    }

    append_monthly_entry(current_month_path, row)
    update_summary()
    print("Appended:", row)


if __name__ == "__main__":
    main()

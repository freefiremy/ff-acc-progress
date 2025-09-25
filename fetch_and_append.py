import calendar
import csv
import os
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple
from zoneinfo import ZoneInfo

import requests

UID = os.getenv("FREEFIRE_UID", "2805365702")
API_URL = f"https://7ama-info.vercel.app/info?uid={UID}"
CSV_PATH = os.getenv("CSV_PATH", "freefire_daily.csv")

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


def read_last_row(path: str):
    if not os.path.exists(path):
        return None
    with open(path, "r", newline="", encoding="utf-8") as csvfile:
        rows = list(csv.DictReader(csvfile))
    return rows[-1] if rows else None


def write_header_if_needed(path: str) -> None:
    if not os.path.exists(path):
        with open(path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(
                [
                    "Date",
                    "BR Score",
                    "Rank Gained",
                    "Likes",
                    "Likes Gained",
                    "XP",
                    "XP Gained",
                ]
            )


def append_row(path: str, row_dict: dict) -> None:
    with open(path, "a", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(
            [
                row_dict["Date"],
                row_dict["BR Score"],
                row_dict["Rank Gained"],
                row_dict["Likes"],
                row_dict["Likes Gained"],
                row_dict["XP"],
                row_dict["XP Gained"],
            ]
        )


def already_logged_today(path: str, today_str: str) -> bool:
    if not os.path.exists(path):
        return False
    with open(path, "r", newline="", encoding="utf-8") as csvfile:
        for row in csv.DictReader(csvfile):
            if row.get("Date") == today_str:
                return True
    return False


def monthly_file_path(dt: datetime) -> Path:
    month_name = calendar.month_name[dt.month]
    filename = f"{dt.year} {month_name} {UID}.csv"
    return Path(filename)


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


def append_monthly_entry(dt: datetime, today_str: str, xp: int, xp_gained: int) -> None:
    path = monthly_file_path(dt)
    ensure_monthly_header(path)
    if monthly_already_logged(path, today_str):
        return
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                today_str,
                "",
                "",
                "",
                "",
                xp,
                xp_gained if xp_gained else "",
                "",
            ]
        )


def parse_int(value: str) -> int | None:
    value = value.strip()
    if not value:
        return None
    value = value.replace(",", "")
    try:
        return int(value)
    except ValueError:
        return None


def load_monthly_stats(path: Path) -> Tuple[int, int, Dict[str, float]]:
    parts = path.stem.split(" ")
    if len(parts) != 3 or not parts[0].isdigit() or parts[2] != UID:
        raise ValueError(f"Unexpected monthly filename format: {path.name}")

    year = int(parts[0])
    month_name = parts[1]
    month_number = datetime.strptime(month_name, "%B").month

    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        xp_values: List[int] = []
        xp_gains: List[int] = []
        for row in reader:
            xp = row.get("XP", "")
            parsed_xp = parse_int(xp) if xp is not None else None
            if parsed_xp is not None:
                xp_values.append(parsed_xp)
            xp_gain_raw = row.get("XP Gained", "")
            parsed_gain = parse_int(xp_gain_raw) if xp_gain_raw is not None else None
            if parsed_gain is not None:
                xp_gains.append(parsed_gain)

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
    summary_path = Path("summary.csv")
    monthly_paths = sorted(
        (p for p in Path(".").glob(f"* {UID}.csv") if p.is_file()),
        key=lambda p: p.stem,
    )

    month_stats: List[Tuple[int, int, Dict[str, float]]] = []
    for path in monthly_paths:
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

    write_header_if_needed(CSV_PATH)

    if already_logged_today(CSV_PATH, today_str):
        print(f"Row for {today_str} already exists; no changes.")
        return

    last_row = read_last_row(CSV_PATH)
    if last_row:
        try:
            last_br = int(last_row.get("BR Score", 0))
        except (TypeError, ValueError):
            last_br = 0
        try:
            last_likes = int(last_row.get("Likes", 0))
        except (TypeError, ValueError):
            last_likes = 0
        try:
            last_xp = int(last_row.get("XP", 0))
        except (TypeError, ValueError):
            last_xp = 0
        rank_gained = ranking_points - last_br
        likes_gained = likes - last_likes
        xp_gained = xp - last_xp
    else:
        rank_gained = 0
        likes_gained = 0
        xp_gained = 0

    row = {
        "Date": today_str,
        "BR Score": ranking_points,
        "Rank Gained": rank_gained,
        "Likes": likes,
        "Likes Gained": likes_gained,
        "XP": xp,
        "XP Gained": xp_gained,
    }

    append_row(CSV_PATH, row)
    append_monthly_entry(now_colombo, today_str, xp, xp_gained)
    update_summary()
    print("Appended:", row)


if __name__ == "__main__":
    main()

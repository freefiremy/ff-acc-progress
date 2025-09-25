import csv
import os
from datetime import datetime
from zoneinfo import ZoneInfo

import requests

UID = os.getenv("FREEFIRE_UID", "2805365702")
API_URL = f"https://7ama-info.vercel.app/info?uid={UID}"
CSV_PATH = os.getenv("CSV_PATH", "freefire_daily.csv")
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
    print("Appended:", row)


if __name__ == "__main__":
    main()

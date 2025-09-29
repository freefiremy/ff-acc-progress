"""Automate sending likes via the Free Fire likes API and log the results."""
from __future__ import annotations

import csv
import os
import sys
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import requests
from zoneinfo import ZoneInfo

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.config import (
    DEFAULT_LIKES_API_KEY,
    DEFAULT_LIKES_UIDS,
    build_api_url,
    build_likes_api_url,
    parse_uid_list,
)

TIMEZONE = ZoneInfo("Asia/Colombo")
PLAYERS_DIR = PROJECT_ROOT / "players"
LIKES_LOG_HEADER = [
    "Date",
    "Likes Before",
    "Likes After",
    "Likes Received",
    "Success",
]

LIKES_API_KEY = os.getenv("FREEFIRE_LIKES_KEY", DEFAULT_LIKES_API_KEY)


def ensure_player_dir(uid: str) -> Path:
    path = PLAYERS_DIR / uid
    path.mkdir(parents=True, exist_ok=True)
    return path


def determine_target_uids() -> List[str]:
    list_raw = os.getenv("FREEFIRE_LIKES_UIDS")
    single_raw = os.getenv("FREEFIRE_LIKES_UID")
    if list_raw:
        candidates = parse_uid_list(list_raw, DEFAULT_LIKES_UIDS)
    elif single_raw:
        candidates = parse_uid_list(single_raw, DEFAULT_LIKES_UIDS)
    else:
        candidates = DEFAULT_LIKES_UIDS
    cleaned = [uid for uid in candidates if uid]
    return cleaned if cleaned else DEFAULT_LIKES_UIDS



def sync_default_likes_log(uid: str, path: Path) -> None:
    """Copy the default likes log back to the repository root."""
    if not DEFAULT_LIKES_UIDS or uid != DEFAULT_LIKES_UIDS[0]:
        return
    shutil.copyfile(path, PROJECT_ROOT / 'likes_activity.csv')

def ensure_log_header(path: Path) -> None:
    if path.exists():
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(LIKES_LOG_HEADER)


def parse_int(value: Optional[str | int]) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    text = str(value).strip()
    if not text:
        return None
    text = text.replace(",", "")
    try:
        return int(text)
    except ValueError:
        return None


def load_entries(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader)


def success_already_logged(path: Path, date_str: str) -> bool:
    for row in load_entries(path):
        if row.get("Date") == date_str and row.get("Success", "").lower() == "true":
            return True
    return False


def fetch_current_likes(uid: str) -> int:
    response = requests.get(build_api_url(uid), timeout=30)
    response.raise_for_status()
    data = response.json()
    likes_raw = data.get("basicInfo", {}).get("liked")
    likes = parse_int(likes_raw)
    if likes is None:
        raise ValueError("Unable to parse likes count from info API response")
    return likes


def safe_current_likes(uid: str) -> int:
    try:
        return fetch_current_likes(uid)
    except Exception as exc:  # pylint: disable=broad-except
        print(f"[{uid}] Failed to obtain likes count for logging: {exc}")
        return 0


def append_log_entry(
    path: Path,
    date_str: str,
    likes_before: int,
    likes_after: int,
    likes_received: int,
    success: bool,
) -> None:
    ensure_log_header(path)
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                date_str,
                likes_before,
                likes_after,
                likes_received,
                "TRUE" if success else "FALSE",
            ]
        )


def call_likes_api(uid: str, api_key: str) -> Dict[str, object]:
    url = build_likes_api_url(uid, api_key)
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()


def process_uid(uid: str) -> None:
    player_dir = ensure_player_dir(uid)
    log_path = player_dir / "likes_activity.csv"
    now_colombo = datetime.now(TIMEZONE)
    today_str = now_colombo.strftime("%Y-%m-%d")

    if success_already_logged(log_path, today_str):
        print(f"[{uid}] Likes already sent successfully today; skipping API call.")
        return

    try:
        payload = call_likes_api(uid, LIKES_API_KEY)
    except requests.RequestException as exc:
        likes_current = safe_current_likes(uid)
        append_log_entry(
            log_path,
            today_str,
            likes_current,
            likes_current,
            0,
            False,
        )
        sync_default_likes_log(uid, log_path)
        print(f"[{uid}] Likes API request failed: {exc}")
        return

    status = payload.get("status")
    if status == 1:
        response = payload.get("response", {})
        likes_before = parse_int(response.get("LikesbeforeCommand"))
        likes_after = parse_int(response.get("LikesafterCommand"))
        likes_received = parse_int(response.get("LikesGivenByAPI")) or 0
        if likes_before is None or likes_after is None:
            likes_before = safe_current_likes(uid)
            likes_after = likes_before + likes_received
        append_log_entry(
            log_path,
            today_str,
            likes_before,
            likes_after,
            likes_received,
            True,
        )
        sync_default_likes_log(uid, log_path)
        print(
            f"[{uid}] Likes API success:",
            {
                "likes_before": likes_before,
                "likes_after": likes_after,
                "likes_received": likes_received,
            },
        )
        return

    likes_current = safe_current_likes(uid)
    append_log_entry(
        log_path,
        today_str,
        likes_current,
        likes_current,
        0,
        False,
    )
    sync_default_likes_log(uid, log_path)
    message = payload.get("message") or payload.get("response", {}).get("message")
    print(
        f"[{uid}] Likes API did not grant likes:",
        {
            "status": status,
            "message": message,
        },
    )


def main() -> None:
    uids = determine_target_uids()
    for uid in uids:
        process_uid(uid)


if __name__ == "__main__":
    main()

"""Prune unsuccessful entries from the likes activity logs."""
from __future__ import annotations

import csv
import os
from pathlib import Path
from typing import List

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
PLAYERS_DIR = PROJECT_ROOT / "players"

from scripts.config import DEFAULT_LIKES_UIDS, parse_uid_list

LIKES_LOG_HEADER = [
    "Date",
    "Likes Before",
    "Likes After",
    "Likes Received",
    "Success",
]


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
    return [uid for uid in candidates if uid]


def log_path_for(uid: str) -> Path:
    return ensure_player_dir(uid) / "likes_activity.csv"


def clean_likes_log(path: Path) -> bool:
    """Return True if the log was modified by removing failed rows or normalising case."""
    if not path.exists():
        print(f"Log file not found: {path}")
        return False

    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)

    changes_made = False
    kept_rows = []
    for row in rows:
        success_raw = (row.get("Success") or "").strip()
        if success_raw.lower() == "true":
            if success_raw != "TRUE":
                changes_made = True
            row["Success"] = "TRUE"
            kept_rows.append(row)
        else:
            if success_raw:
                changes_made = True

    if len(kept_rows) != len(rows):
        changes_made = True

    if not changes_made:
        print("No unsuccessful rows found; log already clean.")
        return False

    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(LIKES_LOG_HEADER)
        for row in kept_rows:
            writer.writerow([row.get(column, "") for column in LIKES_LOG_HEADER])

    removed = len(rows) - len(kept_rows)
    print(f"Removed {removed} unsuccessful entries; {len(kept_rows)} remain in {path.parent.name}.")
    return True


def main() -> None:
    changed_any = False
    for uid in determine_target_uids() or [DEFAULT_LIKES_UIDS[0]]:
        path = log_path_for(uid)
        if clean_likes_log(path):
            changed_any = True
    if not changed_any:
        print("No logs required cleaning.")


if __name__ == "__main__":
    main()

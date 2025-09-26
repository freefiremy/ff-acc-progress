"""Prune unsuccessful entries from the likes activity log."""
from __future__ import annotations

import csv
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
LIKES_LOG_PATH = PROJECT_ROOT / "likes_activity.csv"
LIKES_LOG_HEADER = [
    "Date",
    "Likes Before",
    "Likes After",
    "Likes Received",
    "Success",
]


def clean_likes_log(path: Path = LIKES_LOG_PATH) -> bool:
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
    print(f"Removed {removed} unsuccessful entries; {len(kept_rows)} remain.")
    return True


def main() -> None:
    clean_likes_log()


if __name__ == "__main__":
    main()

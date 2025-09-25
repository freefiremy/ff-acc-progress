# ff-acc-progress

This repository tracks daily Free Fire account progress automatically.

## How it works

- `scripts/fetch_and_append.py` calls the public endpoint `https://7ama-info.vercel.app/info?uid=<UID>` and records the BR score, likes, and XP in the current month's CSV (`{year} {month} {UID}.csv`).
- Day-over-day changes (gains) are computed automatically from the most recent logged entry across all monthly files.
- A scheduled GitHub Action (`.github/workflows/daily-freefire-log.yml`) runs every day at 08:00 Asia/Colombo (UTC+5:30) and commits the refreshed monthly CSV and the aggregated summary back to the repository.
- `scripts/send_likes.py` triggers the likes API and stores the results in `likes_activity.csv`. The workflow `.github/workflows/freefire-likes.yml` runs every 30 minutes from 00:00–06:00 Asia/Colombo until a successful like grant is logged for the day.

## Backfilling historical data

- Manually recorded progress that predates the automation lives in `old_data.csv`.
- Run `python scripts/generate_old_csvs.py` after editing the file to regenerate:
  - One CSV per month (`{year} {month} {UID}.csv`) stored alongside the other project files. Missing columns from the automated log are left blank.
  - `summary.csv`, which summarizes the monthly and yearly XP totals for quick insights.

## Configuration

- Update the defaults in `scripts/config.py` to change the tracked UID or API endpoint.
- Change the `FREEFIRE_UID` environment variable in the workflow file if you want to log a different account without editing the repo.
- Adjust `FREEFIRE_LIKES_UID` / `FREEFIRE_LIKES_KEY` in `scripts/config.py` or via workflow environment variables to control the likes automation.
- You can also run the script locally:

  ```bash
  python -m pip install -r scripts/requirements.txt
  python scripts/fetch_and_append.py
  python scripts/send_likes.py  # optional: run the likes automation locally
  ```

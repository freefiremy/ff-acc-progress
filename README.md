# ff-acc-progress

This repository tracks daily Free Fire account progress automatically.

## How it works

- `scripts/fetch_and_append.py` calls the public endpoint `https://7ama-info.vercel.app/info?uid=<UID>` and records the BR score, likes, and XP in the current month's CSV (`{year} {month} {UID}.csv`).
- Day-over-day changes (gains) are computed automatically from the most recent logged entry across all monthly files.
- A scheduled GitHub Action (`.github/workflows/daily-freefire-log.yml`) runs every day at 08:00 Asia/Colombo (UTC+5:30) and commits the refreshed monthly CSV and the aggregated summary back to the repository.

## Backfilling historical data

- Manually recorded progress that predates the automation lives in `old_data.csv`.
- Run `python scripts/generate_old_csvs.py` after editing the file to regenerate:
  - One CSV per month (`{year} {month} {UID}.csv`) stored alongside the other project files. Missing columns from the automated log are left blank.
  - `summary.csv`, which summarizes the monthly and yearly XP totals for quick insights.

## Configuration

- Update the defaults in `scripts/config.py` to change the tracked UID or API endpoint.
- Change the `FREEFIRE_UID` environment variable in the workflow file if you want to log a different account without editing the repo.
- You can also run the script locally:

  ```bash
  python -m pip install -r scripts/requirements.txt
  python scripts/fetch_and_append.py
  ```

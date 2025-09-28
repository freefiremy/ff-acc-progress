# ff-acc-progress

This repository tracks daily Free Fire account progress automatically.

## How it works

- `scripts/fetch_and_append.py` calls the public endpoint `https://7ama-info.vercel.app/info?uid=<UID>` for every configured account (defaults: `2805365702`, `667352678`) and records BR score, likes, and XP in that player's monthly file (`players/<UID>/{year} {month}.CSV`).
- Day-over-day changes (gains) are computed automatically from the most recent logged entry across all monthly files.
- A scheduled GitHub Action (`.github/workflows/daily-freefire-log.yml`) runs every day at 08:00 Asia/Colombo (UTC+5:30) and commits the refreshed `players/<UID>` folder (monthly CSV + `summary.csv`) back to the repository.
- `scripts/send_likes.py` triggers the likes API and stores the results in `players/<UID>/likes_activity.csv`. By default only UID `667352678` receives automated likes; the workflow runs every 30 minutes from 00:00-06:00 Asia/Colombo until a successful like grant is logged for the day.

## Backfilling historical data

- Manually recorded progress that predates the automation lives in `old_data.csv`.
- Run `python scripts/generate_old_csvs.py` after editing the file to regenerate:
  - One CSV per month (`{year} {month} {UID}.csv`) stored under `players/<UID>/`. Missing columns from the automated log are left blank.
  - `players/<UID>/summary.csv`, which summarizes the monthly and yearly XP totals for quick insights.

## Configuration

- Update the defaults in `scripts/config.py` to change the tracked UID or API endpoints. The helper `default_env_vars()` function mirrors those values for GitHub Actions.
- Want to track more than one account? Populate `DEFAULT_UIDS` / `DEFAULT_LIKES_UIDS` in `scripts/config.py` or set `FREEFIRE_UIDS` / `FREEFIRE_LIKES_UIDS` (comma-separated). By default the repository logs overall progress for `2805365702` and `667352678`, while only `667352678` is queued for automated likes.
- The workflows load their runtime environment from `scripts/config.py` at execution time. If you need to override a value without changing the repository, set a repository or organization secret (for example `FREEFIRE_UID`) and the scripts will pick it up automatically.
- You can also run the scripts locally:

  ```bash
  python -m pip install -r scripts/requirements.txt
  python scripts/fetch_and_append.py
  python scripts/send_likes.py  # optional: run the likes automation locally
  ```

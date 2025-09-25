# ff-acc-progress

This repository tracks daily Free Fire account progress automatically.

## How it works

- `fetch_and_append.py` calls the public endpoint `https://7ama-info.vercel.app/info?uid=<UID>` and records the BR score, likes, and XP in `freefire_daily.csv`.
- Day-over-day changes (gains) are computed automatically from the previous entry.
- A scheduled GitHub Action (`.github/workflows/daily-freefire-log.yml`) runs every day at 08:00 Asia/Colombo (UTC+5:30) and commits the updated CSV back to the repository.

## Configuration

- Change the `FREEFIRE_UID` environment variable in the workflow file if you want to log a different account.
- Adjust `CSV_PATH` in the workflow if you prefer a different file name or location.
- You can also run the script locally:

  ```bash
  python -m pip install -r requirements.txt
  python fetch_and_append.py
  ```

  By default it appends to `freefire_daily.csv` in the project root. Set `FREEFIRE_UID` and `CSV_PATH` environment variables if you need different values.

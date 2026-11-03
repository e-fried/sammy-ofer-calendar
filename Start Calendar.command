#!/bin/bash
set -e
cd "$(dirname "$0")"
if ! command -v python3 >/dev/null 2>&1; then
  echo 'Install Python 3.10 or newer from python.org, then run this again.'
  read -r -p 'Press Enter to close.'
  exit 1
fi
if [ ! -x .venv/bin/python ]; then
  python3 -m venv .venv
fi
.venv/bin/python -m pip install -r requirements.txt
echo 'Refreshing the calendar now and every 24 hours. Keep this window open.'
.venv/bin/python run_calendar.py --watch

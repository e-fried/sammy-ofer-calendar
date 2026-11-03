# Run on your Windows PC or Mac — no paid service

This script reads the public stadium schedule. It does not access Gmail, Outlook, or any personal email account.

## Windows

1. Download this GitHub repository: **Code → Download ZIP**, then extract it.
2. Install Python 3.10 or newer from python.org, including the Python launcher.
3. Double-click **Start Calendar.cmd**.
4. Keep the window open. It updates immediately, then every six hours.

The calendar is saved as `public/calendar.ics` inside the extracted folder. Downloading or opening that file in a calendar app is a snapshot; it does not create a Google subscription.

## Mac

1. Download and extract the repository, and install Python 3.10 or newer from python.org if needed.
2. In Terminal, type `bash ` (including the trailing space), drag **Start Calendar.command** into the Terminal window, and press Enter.
3. Keep the window open. It updates immediately, then every six hours.

Both launchers install Python dependencies into a project-local `.venv` folder. Press Ctrl+C to stop. The computer must be awake and online for updates. After a restart, launch it again.

## Run once or use an OS scheduler

After the first setup, run one refresh without a persistent window:

- Windows: `.venv\Scripts\python.exe run_calendar.py`
- Mac: `.venv/bin/python run_calendar.py`

For Windows Task Scheduler, create a task that repeats every six hours, with the program set to the **full path** of `.venv\Scripts\python.exe` and the argument set to the **quoted full path** of `run_calendar.py`. Select “Run only when user is logged on” for a personal-machine setup. The runner resolves its own working folder.

An OS schedule is not installed by these files; the launchers use the visible six-hour loop. Logs are in `output/refresh.log`. Failed fetches preserve the last valid calendar. Keep `.calendar-state/fixtures.json` between runs so existing events retain their identity.

## How to get automatic updates in Google Calendar

Running locally updates the file, but Google cannot fetch a file that exists only on your PC. The current GitHub repository is private, and Pages publishing is not enabled.

The simplest free end-to-end option remains **a public GitHub repository plus GitHub Pages**: enable Pages with GitHub Actions as its source. The existing workflow already runs the same updater online every six hours, so your PC can be off. Only calendar code and public match information were uploaded; no old email-pilot data was uploaded.

If you keep the repository private, you can still run the local updater for snapshots. For an updating subscription, publish the generated `public/` folder to an accessible HTTPS host; a private GitHub raw URL or a local file path will not work for other subscribers.

Do not repeatedly import the file expecting it to update the original events; that can create duplicates. Subscribe by an accessible URL once hosting is ready.

Windows launcher/Task Scheduler behavior has not been tested on a Windows computer. The Python updater and tests have been exercised on macOS and GitHub's Linux runners.

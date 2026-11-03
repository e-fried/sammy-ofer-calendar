# Sammy Ofer traffic calendar

Calendar-only fixture scraper. No email access or signup required.

## Add to Google Calendar (automatic updates)

Once GitHub Pages is enabled:

1. Open Google Calendar on a **computer**.
2. Next to **Other calendars**, click **+ → From URL**.
3. Paste `https://e-fried.github.io/sammy-ofer-calendar/calendar.ics`.
4. Click **Add calendar**. Done—Google will periodically fetch updates.

Initial setup is not supported in the Google Calendar mobile app. Notifications may need to be enabled separately in your calendar settings.

## Download a copy (one-time import)

For Outlook automatic updates, see the instructions below. Downloading gives a snapshot only.

1. From the published page, click **Download the calendar (.ics)**.
2. In Google Calendar, open **Settings → Import & export**.
3. Select the file, choose the destination calendar, and click **Import**.

Downloaded copies do not update. Use only one method to avoid duplicates.

## Add to Outlook (automatic updates)

Once GitHub Pages is enabled:

1. Open **Outlook in your browser → Calendar**.
2. Click **Add calendar → Subscribe from web**.
3. Paste `https://e-fried.github.io/sammy-ofer-calendar/calendar.ics`.
4. Name it **Sammy Ofer traffic** and click **Import** or **Import and Save**.

For a one-time import instead: **Calendar → Add calendar → Upload from file**, select the downloaded `.ics` file, choose a destination calendar, and click **Import**.

Outlook may take more than 24 hours to show subscription updates. [Microsoft's instructions](https://support.microsoft.com/en-us/outlook/import-or-subscribe-to-a-calendar-in-outlook-com-or-outlook-on-the-web).

## Hosting status

Code is uploaded, but the public page returned 404 at the latest check. Enable **Settings → Pages → Source: GitHub Actions**, then rerun the publishing workflow before sharing the subscription URL.

## Development

Run `pip install -r requirements.txt`, then `python update_calendar.py` to generate `public/calendar.ics`. The traffic window starts 235 minutes before kickoff.

The workflow refreshes every six hours and publishes only the generated public directory. Keep `.calendar-state/fixtures.json` between runs to preserve revisions. Failed scrapes retain the previous published calendar. Missing source listings are not treated as cancellations.

Run tests: `python -m unittest discover -s tests -v`.


## Run on Windows or Mac

See [the local setup guide](LOCAL_SETUP.md). Launch `Start Calendar.cmd` on Windows, or run `bash "Start Calendar.command"` on Mac. The updater refreshes the local file every six hours while running. Google subscriptions still require a publicly accessible calendar URL.

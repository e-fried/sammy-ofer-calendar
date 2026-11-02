# Sammy Ofer traffic calendar

Calendar-only fixture scraper. No email access or signup required.

Run `pip install -r requirements.txt`, then `python update_calendar.py` to produce `public/calendar.ics`. The default traffic window starts 235 minutes before kickoff.

GitHub Actions runs every six hours and publishes only the generated public directory. Enable GitHub Pages with GitHub Actions as the source in repository Settings → Pages. Subscribers add the published calendar.ics URL using Google Calendar → Other calendars → From URL. Importing a file is a one-time snapshot.

Run tests: `python -m unittest discover -s tests -v`.

Keep .calendar-state/fixtures.json between runs to preserve event revisions. Failed scrapes retain the previous published calendar. Calendar clients control refresh timing. Missing source listings are not treated as cancellations.

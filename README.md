# Sammy Offer Calendar

**Know when the match starts—and when to plan for traffic around Sammy Ofer Stadium in Haifa.**

Subscribe once in Google Calendar, Outlook, or Apple Calendar. This project reads the stadium’s published fixture schedule and creates an automatically updated calendar. No signup, email invitations, or access to your email account is needed.

## What appears in your calendar?

Each match creates **two events**:

| Event | Title | Time |
| --- | --- | --- |
| Match | The actual home and away teams | Published kickoff, with an estimated two-hour duration |
| Traffic block | **Game traffic** | Three hours before kickoff until kickoff |

For a match starting at **20:00**, you see **Game traffic from 17:00–20:00** and the **match from 20:00–22:00**. The traffic event’s description includes the teams and kickoff time.

Kickoff times come from the [official stadium fixture page](https://www.haifa-stadium.co.il/לוח_המשחקים_באצטדיון/). Times are interpreted in **Asia/Jerusalem**, including daylight saving time, then exported in UTC so your calendar displays them in your chosen time zone. The source does not provide finish times; the two-hour game duration is an estimate. Traffic blocks are planning reminders, not live congestion predictions.

## Add the calendar

Once GitHub Pages is enabled and publication succeeds, use this subscription URL:

```text
https://e-fried.github.io/sammy-ofer-calendar/calendar.ics
```

[Calendar page](https://e-fried.github.io/sammy-ofer-calendar/) · [Refresh status](https://e-fried.github.io/sammy-ofer-calendar/status.json)

**If those links return 404, complete the hosting setup below first.**

### Google Calendar

1. Open [Google Calendar](https://calendar.google.com/) in a desktop browser.
2. Beside **Other calendars**, click **+ → From URL**.
3. Paste the subscription URL above and select **Add calendar**.
4. If Google uses the URL as the name, open that calendar’s settings and rename it **Sammy Offer Calendar**.

After subscribing, enable the calendar in your mobile app if it is not already visible.

### Outlook

1. Open Outlook’s **Calendar** in your browser.
2. Select **Add calendar → Subscribe from web**.
3. Paste the subscription URL, name it **Sammy Offer Calendar**, and save/import.

Some company accounts block external calendar subscriptions. A separate subscribed calendar also may not mark you busy on your primary work calendar.

### Apple Calendar

Choose **File → New Calendar Subscription**, paste the subscription URL, and set your preferred refresh interval.

**Subscribe by URL for updates.** Downloading and importing an `.ics` file creates a snapshot. Repeated imports can create duplicates. Calendar apps control when they refresh and whether they show reminders; changes are not instant.

## Free hosting and automatic updates

For this repository, use a **public GitHub repository**, **GitHub Pages**, and standard GitHub Actions runners. No custom domain or always-on computer is needed.

1. In repository **Settings → General → Danger Zone**, set visibility to **Public**.
2. In **Settings → Pages**, choose **GitHub Actions** as the source.
3. In **Actions → Update and publish calendar**, choose **Run workflow**.
4. Wait for a successful run, then open the calendar page above before subscribing.

The workflow tests the code, fetches fixtures, builds the calendar, saves event revision state, and publishes the site. It is scheduled every six hours at minute 17 (UTC). GitHub schedules can be delayed; check the Actions tab and `status.json` for the last successful refresh.

Only public fixture data and code belong in the repository. The runtime does not send email or store subscriber accounts.

## Run on Windows or Mac

See [the local setup guide](LOCAL_SETUP.md) for the double-click Windows launcher, Mac instructions, and optional OS scheduling.

For a manual setup with Python 3.10 or newer:

```sh
python -m venv .venv
# Activate .venv using the command for your operating system, then:
python -m pip install -r requirements.txt
python update_calendar.py
```

Output is written to `public/calendar.ics`, `public/index.html`, and `public/status.json`. Keep `.calendar-state/fixtures.json` between runs: it preserves event revisions.

```sh
python run_calendar.py          # Refresh once
python run_calendar.py --watch  # Refresh now and every six hours
python -m unittest discover -s tests -v
```

A local file cannot be fetched by Google Calendar. Publish `public/` at an accessible HTTPS address for subscriptions, or import the file for a one-time snapshot.

## Reliability and limitations

- **Coverage:** only fixtures published by the stadium, not a guaranteed season or fixed number of months ahead. The feed retains the last 30 days plus available future games.
- **Schedule changes:** stable IDs let calendar apps update both events when kickoff changes. Existing traffic-event IDs are preserved during the transition to two events per match.
- **Failed refresh:** empty, malformed, or unconfirmed-time source data stops the update and preserves the last published calendar. Inspect failed Actions runs; a preserved calendar can become stale.
- **Missing listings:** games disappearing from the source are retained, not automatically cancelled. Verify cancellations against the stadium. This avoids silently deleting events when the source is incomplete.
- **Identity:** IDs use season, competition/round, and teams. A change to those labels can appear as a new fixture; two otherwise identical listings are rejected for review.
- **Refresh timing:** the script checks every six hours; Google/Outlook may take longer to fetch the new feed. This is not a real-time alert service.

## Code map

| File | Purpose |
| --- | --- |
| `reminder.py` | Parse the official schedule and calculate traffic start times |
| `subscriptions.py` | Store fixtures and revision history; no subscriber accounts |
| `calendar_feed.py` | Generate paired match and traffic events |
| `update_calendar.py` | Build the static calendar, landing page, and status file |
| `run_calendar.py` | Local refresh runner with logging and optional loop |
| `.github/workflows/update-calendar.yml` | Scheduled refresh and Pages publication |
| `app.py`, `worker.py`, `subscription_worker.py` | Optional read-only local web service and refresh worker |
| `tests/` | Parser, timing, migration, update safety, and calendar-only regression checks |

Advanced use: `--lead-minutes` supports 120, 180, 235, or 240 minutes; the default is **180**. The optional web service also accepts `?lead=...`. GitHub Pages serves a static file, so URL query parameters do not change its timing.

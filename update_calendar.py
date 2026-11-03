"""Refresh a static subscription calendar for GitHub Pages or any web host.

Only public fixture data is stored. No email accounts or credentials are used.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import tempfile
from urllib.request import Request, urlopen
from icalendar import Calendar
from calendar_feed import build_feed, LEAD_TIMES
from reminder import SOURCE, parse
from subscriptions import Store


def atomic_write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix='.' + path.name)
    try:
        with os.fdopen(fd, 'wb') as output:
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def update(output_dir, state_path, html=None, lead=235):
    # Fetch and parse before changing any previously published files or state.
    if html is None:
        with urlopen(Request(SOURCE, headers={'User-Agent': 'SammyOferCalendar/1.0'}), timeout=30) as response:
            html = response.read().decode('utf-8')
    games = parse(html)
    with tempfile.TemporaryDirectory() as temporary:
        store = Store(temporary)
        if state_path.exists():
            state = json.loads(state_path.read_text())
            if state.get('version') != 1:
                raise ValueError('Unsupported saved state version; keep the previous calendar')
            with store.db() as db:
                for row in state['fixtures']:
                    db.execute('INSERT INTO fixtures VALUES(?,?)', (row['uid'], row['payload']))
                for row in state['revisions']:
                    db.execute('INSERT INTO feed_revisions VALUES(?,?,?,?)',
                               (row['uid'], row['fingerprint'], row['sequence'], row['modified']))
        store.sync(games)
        calendar, synced = build_feed(store, lead)
        events = Calendar.from_ical(calendar).walk('VEVENT')
        with store.db() as db:
            state = {'version': 1, 'last_success': synced,
                     'fixtures': [dict(row) for row in db.execute('SELECT * FROM fixtures ORDER BY uid')],
                     'revisions': [dict(row) for row in db.execute('SELECT * FROM feed_revisions ORDER BY uid')]}
    status = {'last_success': synced, 'source': SOURCE, 'source_fixtures': len(games),
              'calendar_events': len(events), 'lead_minutes': lead}
    page = f'''<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Sammy Ofer traffic calendar</title>
<style>body{{max-width:700px;margin:60px auto;padding:24px;font:18px/1.6 system-ui;color:#173e30;background:#f4f6f0}}a{{color:#126342}}code{{overflow-wrap:anywhere}}</style>
<h1>Sammy Ofer traffic calendar</h1>
<p>Subscribe once. Game-day traffic blocks start {lead} minutes before kickoff.</p>
<h2>Add to Google Calendar — automatic updates</h2>
<ol><li>On a computer, open <a href="https://calendar.google.com/">Google Calendar</a>.</li>
<li>Right-click <a href="calendar.ics">this calendar link</a> and choose <strong>Copy link address</strong>.</li>
<li>In Google Calendar, next to <strong>Other calendars</strong>, click <strong>+ → From URL</strong>.</li>
<li>Paste the link and click <strong>Add calendar</strong>. Setup is complete.</li></ol>
<p>Google refreshes it automatically; updates may not appear immediately. Initial setup requires a computer browser, not the Google Calendar mobile app.</p>
<h2>Download a copy — no automatic updates</h2>
<ol><li><a href="calendar.ics" download="sammy-ofer-calendar.ics">Download the calendar (.ics)</a>.</li>
<li>In Google Calendar, open <strong>Settings → Import &amp; export</strong>.</li>
<li>Select the downloaded file, choose a calendar, and click <strong>Import</strong>.</li></ol>
<p>Use only one method to avoid duplicate events. Choose the subscription above if you want future updates.</p>
<p>No email signup, Gmail access, or personal credentials required.</p>
<p>Last successful source refresh: <time>{synced}</time> (UTC). {len(events)} calendar events.</p>
<p>Calendar apps control refresh timing and notifications. This separate calendar does not automatically reserve availability on your primary work calendar.</p>
<p><a href="status.json">Refresh status</a> · <a href="{SOURCE}">Official fixture source</a></p>
</html>'''
    # Publish the validated feed atomically; a failed fetch never truncates it.
    # The GitHub job deploys the whole directory only after every write succeeds.
    atomic_write(output_dir / 'calendar.ics', calendar)
    atomic_write(output_dir / 'index.html', page.encode())
    atomic_write(output_dir / 'status.json', (json.dumps(status, indent=2) + '\n').encode())
    atomic_write(output_dir / '.nojekyll', b'')
    atomic_write(state_path, (json.dumps(state, ensure_ascii=False, indent=2) + '\n').encode())
    return status


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=Path('public'))
    parser.add_argument('--state', type=Path, default=Path('.calendar-state/fixtures.json'))
    parser.add_argument('--html', type=Path, help='Use saved HTML for testing instead of fetching')
    parser.add_argument('--lead-minutes', type=int, choices=LEAD_TIMES, default=235)
    args = parser.parse_args()
    try:
        result = update(args.output_dir, args.state,
                        args.html.read_text() if args.html else None, args.lead_minutes)
    except Exception as exc:
        parser.exit(1, f'Calendar update failed: {exc}\n')
    print(f"Updated {args.output_dir / 'calendar.ics'}: {result['calendar_events']} events")


if __name__ == '__main__':
    main()

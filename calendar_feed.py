"""Public fixture-only calendar; no subscriber details or email side effects."""
from datetime import datetime, timedelta, timezone
import json
from icalendar import Alarm, Calendar, Event
from reminder import SOURCE, traffic_start

LEAD_TIMES = (120, 180, 235, 240)


def build_feed(store, lead=180):
    if lead not in LEAD_TIMES:
        raise ValueError('Unsupported lead time')
    with store.db() as db:
        rows = db.execute('''SELECT f.payload, r.sequence, r.modified
            FROM fixtures f JOIN feed_revisions r ON f.uid=r.uid ORDER BY f.uid''').fetchall()
        sync = db.execute("SELECT value FROM sync_status WHERE name='last_success'").fetchone()
    if not sync:
        raise ValueError('No successful fixture sync yet')
    feed = Calendar()
    feed.add('version', '2.0')
    feed.add('prodid', '-//Sammy Ofer Traffic//Calendar Subscription//EN')
    feed.add('name', 'Sammy Offer Calendar')
    feed.add('x-wr-calname', 'Sammy Offer Calendar')
    feed.add('x-wr-timezone', 'Asia/Jerusalem')
    feed.add('x-wr-caldesc', f'Matches and {lead}-minute traffic blocks from the official stadium schedule. Times may change.')
    # This is a hint, not a promise that a client will refresh at this interval.
    feed.add('refresh-interval', timedelta(hours=6))
    feed.add('x-published-ttl', 'PT6H')
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    for row in rows:
        game = json.loads(row['payload'])
        kickoff = datetime.fromisoformat(game['start'])
        if kickoff < cutoff:
            continue
        modified = datetime.fromisoformat(row['modified'])
        event = Event()
        event.add('uid', game['uid'])
        event.add('sequence', row['sequence'])
        event.add('dtstamp', modified)
        event.add('last-modified', modified)
        event.add('dtstart', traffic_start(game, lead).astimezone(timezone.utc))
        event.add('dtend', kickoff.astimezone(timezone.utc))
        event.add('summary', 'Game traffic')
        event.add('location', 'Sammy Ofer Stadium, Haifa')
        event.add('description', f"{game['title']}\n{game['competition']}\nKickoff: {game['start']}\n"
                  f'Traffic planning starts {lead} minutes earlier; this is not a live traffic prediction.\nSource: {SOURCE}')
        event.add('url', SOURCE)
        event.add('status', 'CONFIRMED')
        event.add('transp', 'OPAQUE')
        alarm = Alarm()
        alarm.add('action', 'DISPLAY')
        alarm.add('description', 'Sammy Ofer traffic planning starts')
        alarm.add('trigger', timedelta(0))
        event.add_component(alarm)
        feed.add_component(event)

        match = Event()
        # Keep the original UID for traffic so subscribers do not get duplicates.
        match.add('uid', 'match-' + game['uid'])
        match.add('related-to', game['uid'])
        match.add('sequence', row['sequence'])
        match.add('dtstamp', modified)
        match.add('last-modified', modified)
        match.add('dtstart', kickoff.astimezone(timezone.utc))
        match.add('dtend', kickoff.astimezone(timezone.utc) + timedelta(hours=2))
        match.add('summary', game['title'])
        match.add('location', 'Sammy Ofer Stadium, Haifa')
        match.add('description', f"{game['competition']}\nPublished kickoff: {game['start']}\n"
                  'End time is an estimate (two hours after kickoff), not an official finish time.\n'
                  f'Source: {SOURCE}')
        match.add('url', SOURCE)
        match.add('status', 'CONFIRMED')
        match.add('transp', 'OPAQUE')
        feed.add_component(match)
    return feed.to_ical(), sync['value']

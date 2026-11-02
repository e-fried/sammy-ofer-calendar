"""Scrape Sammy Ofer fixtures and export a calendar without email access."""
import argparse
from datetime import datetime, timedelta, timezone
import hashlib
from html.parser import HTMLParser
from pathlib import Path
import re
from urllib.parse import quote
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

SOURCE = 'https://www.haifa-stadium.co.il/' + quote('לוח_המשחקים_באצטדיון') + '/'
LOCAL = ZoneInfo('Asia/Jerusalem')


class Paragraphs(HTMLParser):
    def __init__(self):
        super().__init__()
        self.items = []
        self.current = None

    def handle_starttag(self, tag, attrs):
        if tag == 'p':
            self.current = ''
        elif tag == 'br' and self.current is not None:
            self.current += ' '

    def handle_data(self, data):
        if self.current is not None:
            self.current += data

    def handle_endtag(self, tag):
        if tag == 'p' and self.current is not None:
            self.items.append(' '.join(self.current.split()))
            self.current = None


def parse(html):
    games = []
    # Each fixture occupies one Elementor inner section with four paragraphs.
    for section in re.findall(r'<section\b[^>]*elementor-inner-section[^>]*>(.*?)</section>', html, re.S):
        parser = Paragraphs()
        parser.feed(section)
        rows = parser.items
        if not any(re.search(r'\d{2}/\d{2}/\d{4}', row) for row in rows):
            continue
        if len(rows) != 4:
            raise ValueError('Fixture layout changed; refusing a partial scrape')
        competition, home, when, away = rows
        date = re.search(r'\d{2}/\d{2}/\d{4}', when).group()
        time = re.search(r'\b\d{1,2}:\d{2}\b', when)
        if not time:
            raise ValueError(f'Kickoff time unconfirmed: {home} / {away}')
        start = datetime.strptime(date + ' ' + time.group(), '%d/%m/%Y %H:%M').replace(tzinfo=LOCAL)
        # Season + competition/round + teams survives kickoff changes.
        season = start.year if start.month >= 7 else start.year - 1
        identity = f'{season}|{competition}|{home}|{away}'
        uid = hashlib.sha256(identity.encode()).hexdigest()[:32] + '@sammy-offer-reminder'
        game = dict(uid=uid, title=f'{home} – {away}', competition=competition, start=start.isoformat())
        if any(g['uid'] == uid for g in games):
            raise ValueError('Duplicate fixture identity')
        games.append(game)
    if not games:
        raise ValueError('No fixtures found; source may be empty or its layout changed')
    return games


def escape(value):
    return value.replace('\\', '\\\\').replace('\n', '\\n').replace(';', '\\;').replace(',', '\\,')


def traffic_start(game, lead_minutes=235, daily_start=None):
    kickoff = datetime.fromisoformat(game['start']).astimezone(LOCAL)
    if daily_start:
        hour, minute = map(int, daily_start.split(':'))
        start = kickoff.replace(hour=hour, minute=minute)
    else:
        start = kickoff - timedelta(minutes=lead_minutes)
    if start >= kickoff:
        raise ValueError('Traffic block must start before kickoff')
    return start


def calendar(game, sequence=0, sender=None, recipient=None, reminder=0,
             lead_minutes=235, daily_start=None, manage_url=None):
    kickoff = datetime.fromisoformat(game['start']).astimezone(LOCAL)
    start = traffic_start(game, lead_minutes, daily_start)
    stamp = lambda d: d.astimezone(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    lines = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//Sammy Ofer Reminder//EN',
             'METHOD:REQUEST' if sender else 'METHOD:PUBLISH', 'BEGIN:VEVENT',
             'UID:' + game['uid'], f'SEQUENCE:{sequence}', 'DTSTAMP:' + stamp(datetime.now(timezone.utc)),
             'DTSTART:' + stamp(start), 'DTEND:' + stamp(kickoff),
             'SUMMARY:' + escape('Sammy Ofer traffic: ' + game['title']), 'LOCATION:' + escape('Sammy Ofer Stadium, Haifa'),
             'DESCRIPTION:' + escape(game['competition'] + '\nKickoff: ' + kickoff.strftime('%Y-%m-%d %H:%M %Z') + '\nTraffic planning block; ends at kickoff.\nSource: ' + SOURCE + ('\nManage or unsubscribe: ' + manage_url if manage_url else '')),
             'URL:' + SOURCE, 'STATUS:CONFIRMED', 'TRANSP:OPAQUE']
    if sender:
        lines += ['ORGANIZER:mailto:' + sender, 'ATTENDEE;RSVP=TRUE:mailto:' + recipient]
    lines += ['BEGIN:VALARM', f'TRIGGER:-PT{reminder}M', 'ACTION:DISPLAY',
              'DESCRIPTION:Sammy Ofer traffic planning starts', 'END:VALARM', 'END:VEVENT', 'END:VCALENDAR']
    # RFC 5545 folds at 75 octets without splitting UTF-8 characters.
    folded = []
    for line in lines:
        chunk = ''
        for char in line:
            if len((chunk + char).encode()) > 75:
                folded.append(chunk)
                chunk = ' '
            chunk += char
        folded.append(chunk)
    return ('\r\n'.join(folded) + '\r\n').encode()



def main():
    cli = argparse.ArgumentParser(description='Export the Sammy Ofer traffic calendar. No email access required.')
    cli.add_argument('--html', type=Path, help='Read a saved stadium page')
    cli.add_argument('--output', type=Path, default=Path('output/sammy-ofer-traffic.ics'))
    cli.add_argument('--data', type=Path, default=Path('data/calendar'))
    cli.add_argument('--lead-minutes', type=int, choices=(120, 180, 235, 240), default=235)
    args = cli.parse_args()
    if args.html:
        html = args.html.read_text()
    else:
        with urlopen(Request(SOURCE, headers={'User-Agent': 'SammyOferReminder/1.0'}), timeout=30) as response:
            html = response.read().decode('utf-8')
    from subscriptions import Store
    from calendar_feed import build_feed
    store = Store(args.data)
    store.sync(parse(html))
    data, _ = build_feed(store, args.lead_minutes)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(data)
    print(f'Calendar exported to {args.output}')


if __name__ == '__main__':
    main()

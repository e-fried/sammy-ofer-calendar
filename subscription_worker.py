"""Periodically refresh public stadium fixtures; no email dispatch."""
import argparse
import logging
import os
import time
from pathlib import Path
from urllib.request import Request, urlopen
from reminder import SOURCE, parse
from subscriptions import Store


def run(store, html=None):
    try:
        if html:
            content = Path(html).read_text()
        else:
            with urlopen(Request(SOURCE, headers={'User-Agent': 'SammyOferCalendar/1.0'}), timeout=30) as response:
                content = response.read().decode('utf-8')
        store.sync(parse(content))
        logging.info('Fixture calendar refreshed')
        return True
    except Exception as exc:
        logging.error('Fixture sync failed: %s', type(exc).__name__)
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--once', action='store_true')
    parser.add_argument('--html')
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    interval = int(os.getenv('SYNC_INTERVAL_SECONDS', '21600'))
    if interval < 60:
        parser.error('Sync interval must be at least 60 seconds')
    store = Store(os.getenv('DATA_DIR', 'data/calendar'), os.getenv('BASE_URL', 'http://127.0.0.1:8080'))
    while True:
        success = run(store, args.html)
        if args.once:
            raise SystemExit(0 if success else 1)
        time.sleep(interval)


if __name__ == '__main__':
    main()

"""Run the calendar updater once, or every 24 hours on Windows/macOS."""
import argparse
import logging
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--watch', action='store_true', help='Keep refreshing until stopped')
    parser.add_argument('--interval-minutes', type=int, default=1440)
    args = parser.parse_args()
    if args.interval_minutes < 1:
        parser.error('Interval must be at least one minute')
    (ROOT / 'output').mkdir(exist_ok=True)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s',
                        handlers=[logging.StreamHandler(), logging.FileHandler(ROOT / 'output' / 'refresh.log')])
    while True:
        try:
            result = subprocess.run([sys.executable, str(ROOT / 'update_calendar.py')], cwd=ROOT,
                                    capture_output=True, text=True, timeout=120)
            if result.returncode:
                logging.error('%s', result.stderr.strip())
            else:
                logging.info('%s', result.stdout.strip())
            code = result.returncode
        except subprocess.TimeoutExpired:
            logging.error('Update timed out; retrying at the next scheduled interval')
            code = 1
        if not args.watch:
            return code
        logging.info('Next refresh in %s minutes. Press Ctrl+C to stop.', args.interval_minutes)
        time.sleep(args.interval_minutes * 60)


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print('Calendar refresh stopped.')

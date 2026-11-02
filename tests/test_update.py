from pathlib import Path
from tempfile import TemporaryDirectory
from datetime import datetime, timezone
from unittest.mock import patch
import unittest
from icalendar import Calendar
from update_calendar import update


class UpdateTests(unittest.TestCase):
    def setUp(self):
        # The saved 2026 fixture must remain inside the feed's history window
        # even when scheduled tests run in later years.
        clock = patch('calendar_feed.datetime')
        mock_clock = clock.start()
        self.addCleanup(clock.stop)
        mock_clock.now.return_value = datetime(2026, 11, 1, tzinfo=timezone.utc)
        mock_clock.fromisoformat.side_effect = datetime.fromisoformat

    def test_repeat_and_reschedule_keep_identity(self):
        html = Path('tests/fixtures/stadium.html').read_text()
        with TemporaryDirectory() as root:
            output, state = Path(root) / 'public', Path(root) / 'state.json'
            update(output, state, html)
            first = (output / 'calendar.ics').read_bytes()
            update(output, state, html)
            self.assertEqual(first, (output / 'calendar.ics').read_bytes())
            update(output, state, html.replace('07/11/2026', '08/11/2026'))
            before = {str(e['UID']): e for e in Calendar.from_ical(first).walk('VEVENT')}
            after = {str(e['UID']): e for e in Calendar.from_ical((output / 'calendar.ics').read_bytes()).walk('VEVENT')}
            self.assertEqual(before.keys(), after.keys())
            changed = [uid for uid in after if int(after[uid]['SEQUENCE']) == 1]
            self.assertEqual(len(changed), 1)

    def test_bad_scrape_preserves_published_files_and_state(self):
        html = Path('tests/fixtures/stadium.html').read_text()
        with TemporaryDirectory() as root:
            output, state = Path(root) / 'public', Path(root) / 'state.json'
            update(output, state, html)
            previous = {p: p.read_bytes() for p in [*output.iterdir(), state]}
            with self.assertRaises(ValueError):
                update(output, state, '<html>Source unavailable</html>')
            for path, value in previous.items():
                self.assertEqual(path.read_bytes(), value)


if __name__ == '__main__':
    unittest.main()

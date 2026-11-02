from pathlib import Path
import unittest
from unittest.mock import patch
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import json
from reminder import parse, calendar, traffic_start


class ReminderTests(unittest.TestCase):
    def setUp(self):
        self.html = Path('tests/fixtures/stadium.html').read_text()

    def test_real_page(self):
        games = parse(self.html)
        self.assertEqual(len(games), 6)
        self.assertEqual(games[0]['start'], '2026-11-07T17:30:00+02:00')

    def test_reschedule_preserves_identity(self):
        before = parse(self.html)[0]
        after = parse(self.html.replace('07/11/2026', '08/11/2026'))[0]
        self.assertEqual(before['uid'], after['uid'])
        self.assertNotEqual(before['start'], after['start'])

    def test_invalid_source_fails(self):
        with self.assertRaises(ValueError):
            parse('<html>Unavailable</html>')
        with self.assertRaises(ValueError):
            parse(self.html.replace('17:30', 'TBD'))

    def test_invitation_encoding_and_utc(self):
        data = calendar(parse(self.html)[0], 2, 'sender@example.com', 'fan@example.com')
        self.assertTrue(all(len(line) <= 75 for line in data.split(b'\r\n')))
        unfolded = data.decode().replace('\r\n ', '')
        self.assertIn('DTSTART:20261107T113500Z', unfolded)
        self.assertIn('DTEND:20261107T153000Z', unfolded)
        self.assertIn('SEQUENCE:2', unfolded)
        self.assertIn('METHOD:REQUEST', unfolded)
        self.assertIn('מכבי חיפה', unfolded)

    def test_twenty_hundred_game_starts_at_1605(self):
        game = dict(parse(self.html)[0], start='2026-11-07T20:00:00+02:00')
        self.assertEqual(traffic_start(game).strftime('%H:%M'), '16:05')
        summer = dict(game, start='2027-08-07T20:00:00+03:00')
        self.assertEqual(traffic_start(summer).isoformat(), '2027-08-07T16:05:00+03:00')
        self.assertEqual(traffic_start(game, daily_start='16:05').strftime('%H:%M'), '16:05')
        with self.assertRaises(ValueError):
            traffic_start(game, daily_start='21:00')


if __name__ == '__main__':
    unittest.main()

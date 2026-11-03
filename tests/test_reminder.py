from pathlib import Path
from datetime import datetime, timedelta, timezone
import unittest
from reminder import parse, traffic_start


class ReminderTests(unittest.TestCase):
    def setUp(self):
        self.html = Path('tests/fixtures/stadium.html').read_text(encoding='utf-8')

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

    def test_twenty_hundred_game_traffic_starts_at_1700(self):
        game = dict(parse(self.html)[0], start='2026-11-07T20:00:00+02:00')
        self.assertEqual(traffic_start(game).strftime('%H:%M'), '17:00')
        summer = dict(game, start='2027-08-07T20:00:00+03:00')
        self.assertEqual(traffic_start(summer).isoformat(), '2027-08-07T17:00:00+03:00')
        self.assertEqual(traffic_start(game, daily_start='16:05').strftime('%H:%M'), '16:05')
        with self.assertRaises(ValueError):
            traffic_start(game, daily_start='21:00')


    def test_traffic_duration_across_daylight_saving_transition(self):
        game = dict(parse(self.html)[0], start='2026-10-25T04:00:00+02:00')
        start = traffic_start(game)
        kickoff = datetime.fromisoformat(game['start'])
        self.assertEqual(kickoff - start.astimezone(timezone.utc), timedelta(hours=3))

if __name__ == '__main__':
    unittest.main()

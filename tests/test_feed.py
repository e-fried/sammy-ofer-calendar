from datetime import datetime, timedelta, timezone
from tempfile import TemporaryDirectory
import unittest
from icalendar import Calendar
from app import create_app


class FeedTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.app = create_app(self.tmp.name, base_url='http://localhost:8080')
        self.client = self.app.test_client()
        self.store = self.app.extensions['store']
        self.game = dict(uid='fixture@example', title='Haifa match', competition='League',
                         start=(datetime.now(timezone.utc) + timedelta(days=5)).isoformat())

    def test_empty_source_is_unavailable_not_empty_calendar(self):
        self.assertEqual(self.client.get('/calendar.ics').status_code, 503)

    def test_public_feed_has_no_subscriber_data_or_side_effects(self):
        self.store.sync([self.game])
        response = self.client.get('/calendar.ics')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('Set-Cookie', response.headers)
        feed = Calendar.from_ical(response.data)
        self.assertNotIn('METHOD', feed)
        event = feed.walk('VEVENT')[0]
        self.assertEqual(event.decoded('DTEND') - event.decoded('DTSTART'), timedelta(minutes=235))
        self.assertNotIn('ATTENDEE', event)
        self.assertNotIn('ORGANIZER', event)
        with self.store.db() as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM sqlite_master WHERE name='outbox'").fetchone()[0], 0)

    def test_stable_response_conditional_get_and_reschedule(self):
        self.store.sync([self.game])
        first = self.client.get('/calendar.ics')
        self.store.sync([self.game])
        self.assertEqual(self.client.get('/calendar.ics').data, first.data)
        self.assertEqual(self.client.get('/calendar.ics', headers={'If-None-Match': first.headers['ETag']}).status_code, 304)
        moved = dict(self.game, start=(datetime.now(timezone.utc) + timedelta(days=6)).isoformat())
        self.store.sync([moved])
        changed = self.client.get('/calendar.ics')
        event = Calendar.from_ical(changed.data).walk('VEVENT')[0]
        self.assertEqual(str(event['UID']), self.game['uid'])
        self.assertEqual(int(event['SEQUENCE']), 1)
        self.assertNotEqual(changed.headers['ETag'], first.headers['ETag'])

    def test_lead_options_and_localhost_warning(self):
        self.store.sync([self.game])
        self.assertEqual(self.client.get('/calendar.ics?lead=bad').status_code, 400)
        event = Calendar.from_ical(self.client.get('/calendar.ics?lead=120').data).walk('VEVENT')[0]
        self.assertEqual(event.decoded('DTEND') - event.decoded('DTSTART'), timedelta(hours=2))
        self.assertIn(b'Google cannot fetch', self.client.get('/calendar').data)


if __name__ == '__main__':
    unittest.main()

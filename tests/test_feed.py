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
                         start=(datetime.now(timezone.utc) + timedelta(days=5)).replace(microsecond=0).isoformat())

    def test_empty_source_is_unavailable_not_empty_calendar(self):
        self.assertEqual(self.client.get('/calendar.ics').status_code, 503)

    def test_public_feed_has_no_subscriber_data_or_side_effects(self):
        self.store.sync([self.game])
        response = self.client.get('/calendar.ics')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('Set-Cookie', response.headers)
        feed = Calendar.from_ical(response.data)
        self.assertEqual(str(feed['NAME']), 'Sammy Offer Calendar')
        self.assertEqual(str(feed['X-WR-CALNAME']), 'Sammy Offer Calendar')
        self.assertNotIn('METHOD', feed)
        event = feed.walk('VEVENT')[0]
        self.assertEqual(event.decoded('DTEND') - event.decoded('DTSTART'), timedelta(hours=3))
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


    def test_two_events_have_expected_titles_times_and_unique_ids(self):
        self.store.sync([self.game])
        events = Calendar.from_ical(self.client.get('/calendar.ics').data).walk('VEVENT')
        self.assertEqual(len(events), 2)
        traffic, match = events
        kickoff = datetime.fromisoformat(self.game['start'])
        self.assertEqual(str(traffic['SUMMARY']), 'Game traffic')
        self.assertIn(self.game['title'], str(traffic['DESCRIPTION']))
        self.assertEqual(str(match['SUMMARY']), self.game['title'])
        self.assertEqual(traffic.decoded('DTSTART'), kickoff - timedelta(hours=3))
        self.assertEqual(traffic.decoded('DTEND'), kickoff)
        self.assertEqual(match.decoded('DTSTART'), kickoff)
        self.assertEqual(match.decoded('DTEND'), kickoff + timedelta(hours=2))
        self.assertIn('estimate', str(match['DESCRIPTION']))
        self.assertEqual(len({str(e['UID']) for e in events}), 2)
        for event in events:
            self.assertNotIn('ATTENDEE', event)
            self.assertNotIn('ORGANIZER', event)

    def test_existing_traffic_feed_migrates_once_preserving_identity(self):
        import json
        from subscriptions import digest
        self.store.sync([self.game])
        # Simulate the fingerprint and revision from the previous traffic-only release.
        with self.store.db() as db:
            db.execute('UPDATE feed_revisions SET fingerprint=?, sequence=7',
                       (digest(json.dumps(self.game, sort_keys=True)),))
        self.store.sync([self.game])
        first = self.client.get('/calendar.ics').data
        events = Calendar.from_ical(first).walk('VEVENT')
        self.assertEqual(str(events[0]['UID']), self.game['uid'])
        self.assertTrue(all(int(e['SEQUENCE']) == 8 for e in events))
        self.store.sync([self.game])
        self.assertEqual(self.client.get('/calendar.ics').data, first)

    def test_israel_winter_and_summer_kickoff_export_to_utc(self):
        for date, offset in (('2099-01-07', '+02:00'), ('2099-08-07', '+03:00')):
            # Future winter/summer dates avoid the historical cutoff.
            game = dict(self.game, start=date + 'T20:00:00' + offset)
            self.store.sync([game])
            traffic, match = Calendar.from_ical(self.client.get('/calendar.ics').data).walk('VEVENT')
            kickoff = datetime.fromisoformat(game['start'])
            self.assertEqual(match.decoded('DTSTART'), kickoff)
            self.assertEqual(traffic.decoded('DTSTART'), kickoff - timedelta(hours=3))

if __name__ == '__main__':
    unittest.main()

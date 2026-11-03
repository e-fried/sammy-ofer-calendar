"""Regression checks for retirement of the email pilot."""
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from app import create_app


class CalendarOnlyTests(unittest.TestCase):
    def test_no_signup_confirmation_or_mailbox_routes(self):
        with TemporaryDirectory() as root:
            app = create_app(root, 'http://localhost:8080')
            client = app.test_client()
            for path in ['/signup', '/confirm/example', '/manage/example', '/demo/inbox']:
                self.assertEqual(client.get(path).status_code, 404)
                self.assertEqual(client.post(path).status_code, 404)
            self.assertFalse(client.get('/health').json['email_enabled'])
            with app.extensions['store'].db() as db:
                tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                self.assertNotIn('subscribers', tables)
                self.assertNotIn('outbox', tables)

    def test_legacy_send_flag_rejected(self):
        result = subprocess.run([sys.executable, 'reminder.py', '--send'], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('unrecognized arguments: --send', result.stderr)

    def test_no_email_transport_in_runtime(self):
        for filename in ['app.py', 'subscriptions.py', 'subscription_worker.py', 'worker.py', 'reminder.py']:
            source = Path(filename).read_text(encoding='utf-8')
            self.assertNotIn('import smtplib', source)
            self.assertNotIn('SMTP_PASSWORD', source)


if __name__ == '__main__':
    unittest.main()

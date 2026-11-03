"""Fixture storage only; no email accounts or subscriber data."""
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


class Store:
    def __init__(self, root, base_url='http://127.0.0.1:8080'):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.base_url = base_url.rstrip('/')
        with self.db() as db:
            db.executescript('''
            CREATE TABLE IF NOT EXISTS fixtures (uid TEXT PRIMARY KEY, payload TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS feed_revisions (
              uid TEXT PRIMARY KEY, fingerprint TEXT NOT NULL,
              sequence INTEGER NOT NULL, modified TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS sync_status (name TEXT PRIMARY KEY, value TEXT NOT NULL);
            ''')

    @contextmanager
    def db(self):
        db = sqlite3.connect(self.root / 'calendar.sqlite3', timeout=30)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def sync(self, games):
        if not games:
            raise ValueError('Empty scrape; keeping last successful schedule')
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            for game in games:
                # Bump once when the rendered event contract changes, including migration
                # from the old traffic-only feed to paired match/traffic events.
                fingerprint = digest('paired-events-v2|' + json.dumps(game, sort_keys=True))
                old = db.execute('SELECT * FROM feed_revisions WHERE uid=?', (game['uid'],)).fetchone()
                if not old or old['fingerprint'] != fingerprint:
                    db.execute('INSERT OR REPLACE INTO feed_revisions VALUES(?,?,?,?)',
                               (game['uid'], fingerprint, old['sequence'] + 1 if old else 0,
                                datetime.now(timezone.utc).isoformat()))
                db.execute('INSERT OR REPLACE INTO fixtures VALUES(?,?)', (game['uid'], json.dumps(game)))
            db.execute('INSERT OR REPLACE INTO sync_status VALUES(?,?)',
                       ('last_success', datetime.now(timezone.utc).isoformat()))

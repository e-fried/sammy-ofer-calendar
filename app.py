"""Read-only calendar service. No email or account access."""
import argparse
import os
from pathlib import Path
from urllib.parse import urlsplit
from flask import Flask, Response, abort, render_template, request
from calendar_feed import build_feed, LEAD_TIMES
from subscriptions import Store, digest


def create_app(root='data/calendar', base_url='http://127.0.0.1:8080'):
    app = Flask(__name__)
    store = Store(root, base_url)
    app.config.update(MAX_CONTENT_LENGTH=8192, TRUSTED_HOSTS=[urlsplit(base_url).hostname])
    app.extensions['store'] = store

    @app.after_request
    def headers(response):
        response.headers['Referrer-Policy'] = 'no-referrer'
        if request.path != '/calendar.ics':
            response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Content-Security-Policy'] = "default-src 'self'; style-src 'self' 'unsafe-inline'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'"
        return response

    def lead_time():
        try:
            lead = int(request.args.get('lead', '235'))
            if lead not in LEAD_TIMES:
                raise ValueError()
            return lead
        except ValueError:
            abort(400, 'Unsupported lead time')

    @app.get('/')
    @app.get('/calendar')
    def calendar_page():
        lead = lead_time()
        feed_url = store.base_url + '/calendar.ics?lead=' + str(lead)
        local = urlsplit(store.base_url).hostname in ('localhost', '127.0.0.1', '::1')
        return render_template('calendar.html', feed_url=feed_url, lead=lead, local=local)

    @app.get('/calendar.ics')
    def calendar_feed():
        lead = lead_time()
        try:
            data, synced = build_feed(store, lead)
        except ValueError:
            return Response('Schedule not ready; retry later.', status=503, headers={'Retry-After': '300'})
        response = Response(data, content_type='text/calendar; charset=utf-8')
        response.headers['Cache-Control'] = 'public, max-age=300'
        response.headers['Content-Disposition'] = 'inline; filename="sammy-ofer-traffic.ics"'
        response.headers['X-Fixtures-Last-Sync'] = synced
        response.set_etag(digest(data.decode('utf-8')))
        return response.make_conditional(request)

    @app.get('/health')
    def health():
        with store.db() as db:
            db.execute('SELECT 1').fetchone()
        return {'status': 'ok', 'mode': 'calendar-only', 'email_enabled': False}

    return app


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8080)
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--html', type=Path)
    args = parser.parse_args()
    app = create_app(os.getenv('DATA_DIR', 'data/calendar'), os.getenv('BASE_URL', f'http://127.0.0.1:{args.port}'))
    if args.html:
        from reminder import parse
        app.extensions['store'].sync(parse(args.html.read_text()))
    from waitress import serve
    serve(app, host=args.host, port=args.port, threads=4)

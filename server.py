"""IlmBridge loopback-only server. Python 3.10+, standard library only."""
import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
from study import SAMPLE, MODEL, ModelUnavailable, ask, chunks, practice, status

ROOT = Path(__file__).resolve().parent
MAX_BODY = 150_000

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # Do not log student text, questions, or request URLs.

    def send(self, data, code=200, mime='application/json; charset=utf-8'):
        if isinstance(data, (dict, list)):
            data = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy', "default-src 'self'; style-src 'self'; script-src 'self'; connect-src 'self'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'none'")
        self.end_headers(); self.wfile.write(data)

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == '/api/status':
            return self.send(status())
        if path == '/api/sample':
            return self.send({'title': 'Photosynthesis: a small process, a living planet', 'text': SAMPLE})
        files = {'/': ('index.html', 'text/html'), '/app.js': ('app.js', 'text/javascript'), '/style.css': ('style.css', 'text/css')}
        if path in files:
            name, mime = files[path]
            return self.send((ROOT / 'static' / name).read_bytes(), mime=mime + '; charset=utf-8')
        self.send({'error': 'Not found'}, 404)

    def do_POST(self):
        # JSON-only requests plus same-origin checks prevent cross-site form submissions.
        origin = self.headers.get('Origin')
        if origin and origin != 'http://' + self.headers.get('Host', ''):
            return self.send({'error': 'Origin not allowed'}, 403)
        if self.headers.get_content_type() != 'application/json':
            return self.send({'error': 'Use application/json'}, 415)
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if size <= 0 or size > MAX_BODY:
                return self.send({'error': 'Request must be between 1 and 150000 bytes'}, 413)
            body = json.loads(self.rfile.read(size))
            if not isinstance(body, dict):
                raise ValueError('Expected a JSON object')
            text = body.get('text', '')
            if not isinstance(text, str) or not 30 <= len(text.strip()) <= 40000:
                raise ValueError('Add between 30 and 40000 characters of course material.')
            path = urlsplit(self.path).path
            if path == '/api/ask':
                q = body.get('question', '')
                if not isinstance(q, str) or not 3 <= len(q.strip()) <= 500:
                    raise ValueError('Ask a question between 3 and 500 characters.')
                mode, lang = body.get('mode', 'source'), body.get('language', 'English')
                if mode not in ('ai', 'source') or lang not in ('English', 'Urdu', 'Roman Urdu'):
                    raise ValueError('Choose a supported mode and language.')
                return self.send(ask(text, q, mode, lang))
            if path == '/api/practice':
                return self.send(practice(text))
            if path == '/api/analyze':
                return self.send({'passages': chunks(text), 'words': len(text.split())})
            self.send({'error': 'Not found'}, 404)
        except (ValueError, TypeError) as exc:
            self.send({'error': str(exc)}, 400)
        except ModelUnavailable as exc:
            self.send({'error': str(exc), 'model': MODEL}, 503)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run IlmBridge locally')
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    print(f'IlmBridge: http://127.0.0.1:{args.port}', flush=True)
    ThreadingHTTPServer(('127.0.0.1', args.port), Handler).serve_forever()

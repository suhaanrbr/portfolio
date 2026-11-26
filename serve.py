#!/usr/bin/env python3
"""Tiny static dev server for this site:  python serve.py [port]   (default 8767)
Unlike `python -m http.server` it sends Cache-Control: no-store, so the browser never reuses a stale
wall.json / glimpse.js after you regenerate or edit them. It also applies the response headers from
vercel.json (Content-Security-Policy and friends), so a policy problem shows up locally before it ships."""
import json
import sys
from pathlib import Path
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

ROOT = Path(__file__).resolve().parent


def vercel_headers():
    try:
        config = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    # Every rule in this repo applies to all paths ("/(.*)"), so the source pattern is not matched here.
    return [(h["key"], h["value"]) for rule in config.get("headers", []) for h in rule.get("headers", [])]


HEADERS = vercel_headers()


class DevHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store, max-age=0")
        for key, value in HEADERS:
            self.send_header(key, value.replace(" upgrade-insecure-requests", "").replace("; upgrade-insecure-requests", ""))
        super().end_headers()


port = int(sys.argv[1]) if len(sys.argv) > 1 else 8767
httpd = ThreadingHTTPServer(("127.0.0.1", port), DevHandler)
print(f"serving http://localhost:{port}/  (no-cache, {len(HEADERS)} headers from vercel.json)  Ctrl+C to stop")
try:
    httpd.serve_forever()
except KeyboardInterrupt:
    pass

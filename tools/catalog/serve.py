"""Serve a catalog folder on this machine and keep its votes.

    python tools/catalog/serve.py <catalog folder> [port]

Static files, with byte ranges so videos can be scrubbed. GET /votes returns the
folder's votes.json; POST /votes replaces it. It listens on 127.0.0.1 only.
"""

import json
import re
import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

MAX_VOTES_BYTES = 1_000_000


def clean_votes(data):
    """Keep only {item: {"vote": "like" | "dislike" | "", "note": text}}."""
    out = {}
    if not isinstance(data, dict):
        return out
    for key, value in data.items():
        if not isinstance(value, dict):
            continue
        vote = value.get("vote", "")
        note = str(value.get("note", ""))[:2000]
        if vote not in ("like", "dislike", ""):
            vote = ""
        if vote or note:
            out[str(key)[:200]] = {"vote": vote, "note": note}
    return out


def byte_range(header, size):
    """(start, end) inclusive for a Range header, or None when it is absent or unusable."""
    m = re.fullmatch(r"bytes=(\d*)-(\d*)", (header or "").strip())
    if not m or (not m.group(1) and not m.group(2)):
        return None
    if m.group(1):
        start = int(m.group(1))
        end = min(int(m.group(2)), size - 1) if m.group(2) else size - 1
    else:
        start, end = max(0, size - int(m.group(2))), size - 1
    return (start, end) if start <= end < size else None


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        return

    def _votes_file(self):
        return Path(self.directory) / "votes.json"

    def _json(self, code, body):
        raw = json.dumps(body, indent=1).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def end_headers(self):
        if "Cache-Control" not in "".join(h.decode("latin-1") for h in getattr(self, "_headers_buffer", [])):
            self.send_header("Cache-Control", "no-cache")  # always ask again: the page and videos are rebuilt in place
        super().end_headers()

    def do_GET(self):
        if self.path.split("?")[0] == "/votes":
            f = self._votes_file()
            self._json(200, json.loads(f.read_text(encoding="utf-8")) if f.exists() else {})
            return
        path = Path(self.translate_path(self.path))
        rng = byte_range(self.headers.get("Range"), path.stat().st_size) if path.is_file() else None
        if rng is None:
            super().do_GET()
            return
        start, end = rng
        self.send_response(206)
        self.send_header("Content-Type", self.guess_type(str(path)))
        self.send_header("Content-Range", f"bytes {start}-{end}/{path.stat().st_size}")
        self.send_header("Content-Length", str(end - start + 1))
        self.send_header("Accept-Ranges", "bytes")
        self.end_headers()
        with open(path, "rb") as fh:
            fh.seek(start)
            left = end - start + 1
            while left > 0:
                chunk = fh.read(min(65536, left))
                if not chunk:
                    break
                try:
                    self.wfile.write(chunk)
                except (BrokenPipeError, ConnectionError):
                    return
                left -= len(chunk)

    def do_POST(self):
        if self.path != "/votes":
            self.send_error(404)
            return
        size = int(self.headers.get("Content-Length") or 0)
        if size > MAX_VOTES_BYTES:
            self.send_error(413)
            return
        try:
            votes = clean_votes(json.loads(self.rfile.read(size).decode("utf-8")))
        except ValueError:
            self.send_error(400)
            return
        self._votes_file().write_text(json.dumps(votes, indent=1) + "\n", encoding="utf-8")
        self._json(200, {"saved": len(votes)})


def main():
    folder = Path(sys.argv[1]).resolve()
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8791
    server = ThreadingHTTPServer(("127.0.0.1", port), partial(Handler, directory=str(folder)))
    print(f"catalog at http://127.0.0.1:{port}/  (votes in {folder / 'votes.json'})", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()

from __future__ import annotations

import json
import re
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

IMPORT_HOST = "127.0.0.1"
IMPORT_PORT = 8765
MAX_IMPORT_BYTES = 1_000_000
EXTENSION_ORIGIN = re.compile(r"^chrome-extension://[a-p]{32}$")

_import_lock = threading.Lock()
_imported_words: list[str] | None = None
_server: ThreadingHTTPServer | None = None


class ImportRequestHandler(BaseHTTPRequestHandler):
    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = b"" if status == 204 else json.dumps(payload).encode("utf-8")
        self.send_response(status)
        origin = self.headers.get("Origin", "")
        if EXTENSION_ORIGIN.fullmatch(origin):
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if body:
            self.wfile.write(body)

    def _has_extension_origin(self) -> bool:
        return bool(EXTENSION_ORIGIN.fullmatch(self.headers.get("Origin", "")))

    def do_OPTIONS(self) -> None:
        if not self._has_extension_origin():
            self._send_json(403, {"error": "Only the browser extension can use this endpoint"})
            return
        self._send_json(204, {})

    def do_GET(self) -> None:
        if not self._has_extension_origin():
            self._send_json(403, {"error": "Only the browser extension can use this endpoint"})
            return
        if self.path != "/status":
            self._send_json(404, {"error": "Not found"})
            return

        with _import_lock:
            has_words = _imported_words is not None
        self._send_json(200, {"ready": has_words})

    def do_POST(self) -> None:
        global _imported_words

        if not self._has_extension_origin():
            self._send_json(403, {"error": "Only the browser extension can use this endpoint"})
            return
        if self.path != "/import":
            self._send_json(404, {"error": "Not found"})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > MAX_IMPORT_BYTES:
                self._send_json(413, {"error": "Import payload is empty or too large"})
                return
            payload = json.loads(self.rfile.read(length))
            if not isinstance(payload, dict) or not isinstance(payload.get("words"), list):
                self._send_json(400, {"error": "Invalid import payload"})
                return
            words = [
                word.strip().upper()
                for word in payload.get("words", [])
                if isinstance(word, str) and word.strip()
            ]
        except (ValueError, json.JSONDecodeError):
            self._send_json(400, {"error": "Invalid import payload"})
            return

        if not words:
            self._send_json(400, {"error": "No words found on the page"})
            return

        with _import_lock:
            _imported_words = list(dict.fromkeys(words))
        self._send_json(200, {"imported": len(_imported_words)})

    def log_message(self, format: str, *args: Any) -> None:
        return


def start_import_server() -> None:
    global _server

    if _server is not None:
        return

    _server = ThreadingHTTPServer((IMPORT_HOST, IMPORT_PORT), ImportRequestHandler)
    thread = threading.Thread(target=_server.serve_forever, daemon=True)
    thread.start()


def take_imported_words() -> list[str] | None:
    global _imported_words

    with _import_lock:
        words = _imported_words
        _imported_words = None
    return words

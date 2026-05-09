from __future__ import annotations

import argparse
import json
import mimetypes
import threading
import time
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from app.config import (
    AUTO_SYNC_ENABLED,
    AUTO_SYNC_INTERVAL_HOURS,
    AUTO_SYNC_YEARS_AHEAD,
    DATA_DIR,
    DEFAULT_HOST,
    DEFAULT_PORT,
    STATIC_DIR,
)
from app.providers.tanggal_merah import ProviderError, TanggalMerahProvider
from app.services.holiday_service import HolidayService
from app.storage.json_store import HolidayStore


def build_service() -> HolidayService:
    return HolidayService(HolidayStore(DATA_DIR), TanggalMerahProvider())


def create_handler(service: HolidayService):
    static_root = STATIC_DIR.resolve()

    class CalendarHandler(BaseHTTPRequestHandler):
        server_version = "KalenderIndonesia/1.0"

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path == "/api/health":
                self._send_json({"status": "ok"})
                return

            if parsed.path == "/api/years":
                self._send_json({"years": service.available_years()})
                return

            if parsed.path == "/api/holidays":
                self._handle_holidays(parsed.query)
                return

            self._serve_static(parsed.path)

        def do_POST(self) -> None:
            self._send_json({"error": "Not found"}, HTTPStatus.NOT_FOUND)

        def log_message(self, format: str, *args: Any) -> None:
            return

        def _handle_holidays(self, query: str) -> None:
            params = parse_qs(query)
            year = self._parse_year(params)
            if year is None:
                self._send_json({"error": "Query parameter year wajib berupa 4 digit tahun."}, HTTPStatus.BAD_REQUEST)
                return

            try:
                payload = service.get_holidays(year)
            except ProviderError as exc:
                self._send_json(
                    {
                        "error": "Data tahun ini belum tersedia dan sinkronisasi provider gagal.",
                        "detail": str(exc),
                        "year": year,
                    },
                    HTTPStatus.BAD_GATEWAY,
                )
                return

            self._send_json(payload)

        def _parse_year(self, params: dict[str, list[str]]) -> int | None:
            raw_year = params.get("year", [""])[0]
            if not raw_year.isdigit() or len(raw_year) != 4:
                return None

            year = int(raw_year)
            if year < 1900 or year > 2200:
                return None
            return year

        def _serve_static(self, request_path: str) -> None:
            relative_path = "/index.html" if request_path == "/" else request_path
            relative_path = relative_path.lstrip("/")

            candidate = (static_root / relative_path).resolve()
            if not self._is_inside_static(candidate) or not candidate.is_file():
                self._send_json({"error": "Not found"}, HTTPStatus.NOT_FOUND)
                return

            content_type = mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
            body = candidate.read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _is_inside_static(self, path: Path) -> bool:
            return path == static_root or static_root in path.parents

        def _send_json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return CalendarHandler


def start_auto_sync(service: HolidayService) -> None:
    if not AUTO_SYNC_ENABLED:
        return

    interval_seconds = max(AUTO_SYNC_INTERVAL_HOURS, 1) * 60 * 60

    def sync_loop() -> None:
        while True:
            current_year = datetime.now().year
            years = range(current_year, current_year + AUTO_SYNC_YEARS_AHEAD + 1)
            for year in years:
                try:
                    service.get_holidays(year)
                except ProviderError as exc:
                    print(f"Auto sync {year} gagal: {exc}")
            time.sleep(interval_seconds)

    thread = threading.Thread(target=sync_loop, name="holiday-auto-sync", daemon=True)
    thread.start()


def run(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> None:
    service = build_service()
    start_auto_sync(service)
    server = ThreadingHTTPServer((host, port), create_handler(service))
    print(f"Kalender Indonesia berjalan di http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Kalender Indonesia web server")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args()
    run(host=args.host, port=args.port)

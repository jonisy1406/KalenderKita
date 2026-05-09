from __future__ import annotations

from http import HTTPStatus
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

from app.providers.tanggal_merah import ProviderError
from app.vercel_adapter import PUBLIC_CACHE_HEADER, get_holidays_payload, parse_year, send_json


class handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        params = parse_qs(urlparse(self.path).query)
        year = parse_year(params.get("year", [None])[0])
        if year is None:
            send_json(
                self,
                {"error": "Query parameter year wajib berupa 4 digit tahun."},
                HTTPStatus.BAD_REQUEST,
            )
            return

        try:
            payload = get_holidays_payload(year)
        except ProviderError as exc:
            send_json(
                self,
                {
                    "error": "Data tahun ini belum tersedia dari provider.",
                    "detail": str(exc),
                    "year": year,
                },
                HTTPStatus.BAD_GATEWAY,
            )
            return

        send_json(self, payload, cache_control=PUBLIC_CACHE_HEADER)

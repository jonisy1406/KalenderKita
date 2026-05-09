from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.config import BASE_DIR
from app.providers.tanggal_merah import ProviderError, TanggalMerahProvider


SEED_DIR = BASE_DIR / "data" / "holidays"
PUBLIC_CACHE_HEADER = "public, s-maxage=86400, stale-while-revalidate=604800"
NO_STORE_HEADER = "no-store"


def parse_year(raw_year: str | None) -> int | None:
    if raw_year is None or not raw_year.isdigit() or len(raw_year) != 4:
        return None

    year = int(raw_year)
    if year < 1900 or year > 2200:
        return None
    return year


def send_json(
    handler: Any,
    payload: dict[str, Any],
    status: HTTPStatus = HTTPStatus.OK,
    cache_control: str = NO_STORE_HEADER,
) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Cache-Control", cache_control)
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def get_holidays_payload(year: int) -> dict[str, Any]:
    provider = TanggalMerahProvider()
    try:
        payload = provider.fetch_year(year)
        payload.setdefault("meta", {})
        payload["meta"]["cache_status"] = "fresh"
        payload["meta"]["runtime"] = "vercel"
        return payload
    except ProviderError as exc:
        seed = read_seed_year(year)
        if seed is None:
            raise

        seed.setdefault("meta", {})
        seed["meta"]["cache_status"] = "seed_fallback"
        seed["meta"]["sync_error"] = str(exc)
        seed["meta"]["runtime"] = "vercel"
        return seed


def read_seed_year(year: int) -> dict[str, Any] | None:
    path = SEED_DIR / f"{year}.json"
    if not path.exists():
        return None

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def is_authorized_cron(headers: Any) -> bool:
    secret = os.environ.get("CRON_SECRET")
    if not secret:
        return True

    return headers.get("authorization") == f"Bearer {secret}"


def jakarta_now() -> datetime:
    try:
        jakarta_timezone = ZoneInfo("Asia/Jakarta")
    except ZoneInfoNotFoundError:
        jakarta_timezone = timezone(timedelta(hours=7), name="Asia/Jakarta")

    return datetime.now(jakarta_timezone)


def sync_years() -> list[int]:
    years_ahead = int(os.environ.get("KALENDER_AUTO_SYNC_YEARS_AHEAD", "2"))
    years_ahead = max(0, min(years_ahead, 5))
    current_year = jakarta_now().year
    return list(range(current_year, current_year + years_ahead + 1))

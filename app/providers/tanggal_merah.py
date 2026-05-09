from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.config import HTTP_TIMEOUT_SECONDS, PROVIDER_BASE_URL
from app.models import HOLIDAY_TYPE, LEAVE_TYPE, Holiday


class ProviderError(RuntimeError):
    """Raised when the external holiday provider cannot be used."""


class TanggalMerahProvider:
    name = "Tanggal Merah API"

    def __init__(self, base_url: str = PROVIDER_BASE_URL, timeout: int = HTTP_TIMEOUT_SECONDS):
        self.base_url = base_url
        self.timeout = timeout

    def fetch_year(self, year: int) -> dict[str, Any]:
        url = f"{self.base_url}?{urlencode({'year': year})}"
        request = Request(url, headers={"Accept": "application/json", "User-Agent": "kalender-indonesia/1.0"})

        try:
            with urlopen(request, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            raise ProviderError(f"Provider returned HTTP {exc.code}") from exc
        except URLError as exc:
            raise ProviderError(f"Provider connection failed: {exc.reason}") from exc
        except TimeoutError as exc:
            raise ProviderError("Provider request timed out") from exc
        except json.JSONDecodeError as exc:
            raise ProviderError("Provider returned invalid JSON") from exc

        if not payload.get("success"):
            raise ProviderError(payload.get("error") or "Provider returned an unsuccessful response")

        raw_items = payload.get("data")
        if not isinstance(raw_items, list):
            raise ProviderError("Provider response does not contain a data list")

        items = [self._normalize_item(item, url).to_dict() for item in raw_items]
        items.sort(key=lambda item: item["date"])

        now = datetime.now(timezone.utc).isoformat()
        return {
            "year": year,
            "items": items,
            "meta": {
                "source": self.name,
                "source_url": url,
                "synced_at": now,
                "item_count": len(items),
            },
        }

    def _normalize_item(self, item: dict[str, Any], source_url: str) -> Holiday:
        source_type = item.get("type")
        if source_type == "holiday":
            holiday_type = HOLIDAY_TYPE
        elif source_type == "leave":
            holiday_type = LEAVE_TYPE
        else:
            raise ProviderError(f"Unsupported holiday type: {source_type!r}")

        date = item.get("date")
        name = item.get("name")
        if not isinstance(date, str) or not isinstance(name, str):
            raise ProviderError("Provider item is missing date or name")

        return Holiday(
            date=date,
            name=name,
            type=holiday_type,
            day=item.get("day") if isinstance(item.get("day"), str) else None,
            source=self.name,
            source_url=source_url,
        )

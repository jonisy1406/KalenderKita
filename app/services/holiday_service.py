from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from app.config import SYNC_MAX_AGE_HOURS
from app.providers.tanggal_merah import ProviderError, TanggalMerahProvider
from app.storage.json_store import HolidayStore


class HolidayService:
    def __init__(
        self,
        store: HolidayStore,
        provider: TanggalMerahProvider,
        max_age_hours: int = SYNC_MAX_AGE_HOURS,
    ):
        self.store = store
        self.provider = provider
        self.max_age = timedelta(hours=max_age_hours)

    def get_holidays(self, year: int, force_refresh: bool = False) -> dict[str, Any]:
        cached = self.store.read_year(year)
        should_refresh = force_refresh or cached is None or self._is_stale(cached)

        if should_refresh:
            try:
                fresh = self.provider.fetch_year(year)
                fresh["meta"]["cache_status"] = "fresh"
                self.store.write_year(year, fresh)
                return fresh
            except ProviderError as exc:
                if cached is not None:
                    cached.setdefault("meta", {})
                    cached["meta"]["cache_status"] = "stale"
                    cached["meta"]["sync_error"] = str(exc)
                    return cached
                raise

        cached.setdefault("meta", {})
        cached["meta"]["cache_status"] = "cached"
        return cached

    def sync_year(self, year: int) -> dict[str, Any]:
        fresh = self.provider.fetch_year(year)
        fresh["meta"]["cache_status"] = "fresh"
        self.store.write_year(year, fresh)
        return fresh

    def available_years(self) -> list[int]:
        return self.store.available_years()

    def _is_stale(self, payload: dict[str, Any]) -> bool:
        synced_at = payload.get("meta", {}).get("synced_at")
        if not synced_at:
            return True

        try:
            synced_time = datetime.fromisoformat(str(synced_at).replace("Z", "+00:00"))
        except ValueError:
            return True

        if synced_time.tzinfo is None:
            synced_time = synced_time.replace(tzinfo=timezone.utc)

        return datetime.now(timezone.utc) - synced_time > self.max_age

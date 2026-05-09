from __future__ import annotations

import uuid
import shutil
import unittest
from pathlib import Path

from app.providers.tanggal_merah import ProviderError
from app.services.holiday_service import HolidayService
from app.storage.json_store import HolidayStore


WORKSPACE_TMP = Path(__file__).resolve().parents[1] / ".tmp_tests"


def make_store_dir() -> Path:
    WORKSPACE_TMP.mkdir(exist_ok=True)
    directory = WORKSPACE_TMP / f"case_{uuid.uuid4().hex}"
    directory.mkdir()
    return directory


class FakeProvider:
    def __init__(self, should_fail: bool = False):
        self.should_fail = should_fail

    def fetch_year(self, year: int):
        if self.should_fail:
            raise ProviderError("offline")
        return {
            "year": year,
            "items": [
                {
                    "date": f"{year}-01-01",
                    "name": "Tahun Baru",
                    "type": "libur_nasional",
                }
            ],
            "meta": {
                "source": "fake",
                "synced_at": "2026-05-08T00:00:00+00:00",
            },
        }


class HolidayServiceTest(unittest.TestCase):
    def test_get_holidays_fetches_and_caches_when_missing(self):
        store_dir = make_store_dir()
        self.addCleanup(shutil.rmtree, store_dir, ignore_errors=True)
        store = HolidayStore(store_dir)
        service = HolidayService(store, FakeProvider(), max_age_hours=24)

        payload = service.get_holidays(2027)

        self.assertEqual(payload["year"], 2027)
        self.assertEqual(payload["items"][0]["date"], "2027-01-01")
        self.assertTrue(store.path_for_year(2027).exists())

    def test_get_holidays_returns_stale_cache_when_provider_fails(self):
        store_dir = make_store_dir()
        self.addCleanup(shutil.rmtree, store_dir, ignore_errors=True)
        store = HolidayStore(store_dir)
        store.write_year(
            2027,
            {
                "year": 2027,
                "items": [],
                "meta": {"synced_at": "2020-01-01T00:00:00+00:00"},
            },
        )
        service = HolidayService(store, FakeProvider(should_fail=True), max_age_hours=1)

        payload = service.get_holidays(2027)

        self.assertEqual(payload["meta"]["cache_status"], "stale")
        self.assertEqual(payload["meta"]["sync_error"], "offline")


if __name__ == "__main__":
    unittest.main()

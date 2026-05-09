from __future__ import annotations

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = Path(os.environ.get("KALENDER_STATIC_DIR", BASE_DIR / "public"))
DATA_DIR = Path(os.environ.get("KALENDER_DATA_DIR", BASE_DIR / "data" / "holidays"))

DEFAULT_HOST = os.environ.get("KALENDER_HOST", "127.0.0.1")
DEFAULT_PORT = int(os.environ.get("KALENDER_PORT", "8000"))

PROVIDER_BASE_URL = os.environ.get(
    "KALENDER_PROVIDER_BASE_URL",
    "https://tanggalmerah.upset.dev/api/holidays",
)

SYNC_MAX_AGE_HOURS = int(os.environ.get("KALENDER_SYNC_MAX_AGE_HOURS", "168"))
HTTP_TIMEOUT_SECONDS = int(os.environ.get("KALENDER_HTTP_TIMEOUT_SECONDS", "12"))

AUTO_SYNC_ENABLED = os.environ.get("KALENDER_AUTO_SYNC_ENABLED", "1") not in {"0", "false", "False"}
AUTO_SYNC_INTERVAL_HOURS = int(os.environ.get("KALENDER_AUTO_SYNC_INTERVAL_HOURS", "24"))
AUTO_SYNC_YEARS_AHEAD = int(os.environ.get("KALENDER_AUTO_SYNC_YEARS_AHEAD", "2"))

from __future__ import annotations

from http import HTTPStatus
from http.server import BaseHTTPRequestHandler

from app.providers.tanggal_merah import ProviderError
from app.vercel_adapter import get_holidays_payload, is_authorized_cron, send_json, sync_years


class handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if not is_authorized_cron(self.headers):
            send_json(self, {"success": False, "error": "Unauthorized"}, HTTPStatus.UNAUTHORIZED)
            return

        results = []
        for year in sync_years():
            try:
                payload = get_holidays_payload(year)
                results.append(
                    {
                        "year": year,
                        "success": True,
                        "count": len(payload.get("items", [])),
                        "cache_status": payload.get("meta", {}).get("cache_status"),
                    }
                )
            except ProviderError as exc:
                results.append({"year": year, "success": False, "error": str(exc)})

        success = any(item["success"] for item in results)
        send_json(
            self,
            {
                "success": success,
                "message": "Daily holiday sync completed.",
                "results": results,
            },
            HTTPStatus.OK if success else HTTPStatus.BAD_GATEWAY,
        )

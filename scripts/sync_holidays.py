from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.main import build_service
from app.providers.tanggal_merah import ProviderError


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync hari libur nasional dan cuti bersama")
    parser.add_argument("--year", type=int, help="Tahun spesifik yang akan disinkronkan")
    parser.add_argument("--from-year", type=int, help="Awal rentang tahun")
    parser.add_argument("--to-year", type=int, help="Akhir rentang tahun")
    return parser.parse_args()


def year_range(args: argparse.Namespace) -> list[int]:
    if args.year:
        return [args.year]

    if args.from_year and args.to_year:
        if args.from_year > args.to_year:
            raise ValueError("--from-year tidak boleh lebih besar dari --to-year")
        return list(range(args.from_year, args.to_year + 1))

    raise ValueError("Gunakan --year atau --from-year dan --to-year")


def main() -> int:
    args = parse_args()
    service = build_service()

    try:
        years = year_range(args)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    failed = False
    for year in years:
        try:
            payload = service.sync_year(year)
            count = len(payload.get("items", []))
            print(f"{year}: synced {count} tanggal")
        except ProviderError as exc:
            failed = True
            print(f"{year}: gagal sync: {exc}", file=sys.stderr)

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

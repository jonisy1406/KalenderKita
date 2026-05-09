from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class HolidayStore:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def path_for_year(self, year: int) -> Path:
        return self.data_dir / f"{year}.json"

    def read_year(self, year: int) -> dict[str, Any] | None:
        path = self.path_for_year(year)
        if not path.exists():
            return None

        with path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def write_year(self, year: int, payload: dict[str, Any]) -> None:
        path = self.path_for_year(year)
        temporary_path = path.with_suffix(".tmp")

        with temporary_path.open("w", encoding="utf-8") as file:
            json.dump(payload, file, ensure_ascii=False, indent=2)
            file.write("\n")

        temporary_path.replace(path)

    def available_years(self) -> list[int]:
        years: list[int] = []
        for path in self.data_dir.glob("*.json"):
            try:
                years.append(int(path.stem))
            except ValueError:
                continue
        return sorted(set(years))

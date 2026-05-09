from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


HOLIDAY_TYPE = "libur_nasional"
LEAVE_TYPE = "cuti_bersama"


@dataclass(frozen=True)
class Holiday:
    date: str
    name: str
    type: str
    day: str | None = None
    source: str | None = None
    source_url: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {key: value for key, value in asdict(self).items() if value is not None}

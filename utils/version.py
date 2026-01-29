# utils/version.py
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AppVersion:
    """アプリのバージョン情報。"""

    name: str
    version: str
    data_format_version: int


APP_VERSION: AppVersion = AppVersion(
    name="FTIV",
    version="1.0.0",
    data_format_version=1,
)

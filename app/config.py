from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import gettempdir

APP_NAME = "Storage Detective"
APP_SLUG = "storage-detective"


def app_data_dir() -> Path:
    base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
    return Path(base) / "StorageDetective"


DEFAULT_DB_PATH = app_data_dir() / "storage_detective.sqlite3"


def default_scan_roots() -> list[Path]:
    home = Path.home()
    roots = [
        home / "AppData" / "Local",
        home / "AppData" / "Roaming",
        Path(os.environ.get("PROGRAMDATA", r"C:\ProgramData")),
        Path(gettempdir()),
    ]
    extra_temp = [os.environ.get("TEMP"), os.environ.get("TMP")]
    roots.extend(Path(p) for p in extra_temp if p)
    deduped: list[Path] = []
    seen: set[str] = set()
    for root in roots:
        marker = os.path.normcase(os.path.abspath(str(root)))
        if marker not in seen:
            deduped.append(root)
            seen.add(marker)
    return deduped


@dataclass(slots=True)
class AppSettings:
    excluded_paths: list[str] = field(default_factory=list)
    theme: str = "dark"
    scan_depth: int = 2
    ai_explanations_enabled: bool = True
    min_folder_size_mb: int = 25

    def min_folder_size_bytes(self) -> int:
        return max(0, int(self.min_folder_size_mb)) * 1024 * 1024

    def to_dict(self) -> dict[str, object]:
        return {
            "excluded_paths": list(self.excluded_paths),
            "theme": self.theme,
            "scan_depth": self.scan_depth,
            "ai_explanations_enabled": self.ai_explanations_enabled,
            "min_folder_size_mb": self.min_folder_size_mb,
        }

    @classmethod
    def from_dict(cls, values: dict[str, object]) -> "AppSettings":
        return cls(
            excluded_paths=list(values.get("excluded_paths") or []),
            theme=str(values.get("theme") or "dark"),
            scan_depth=int(values.get("scan_depth") or 2),
            ai_explanations_enabled=bool(values.get("ai_explanations_enabled", True)),
            min_folder_size_mb=int(values.get("min_folder_size_mb") or 25),
        )


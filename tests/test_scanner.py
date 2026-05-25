from __future__ import annotations

import os
from pathlib import Path

from app.installed_apps import InstalledAppInventory
from app.models import CATEGORY_CACHE
from app.scanner import ScannerConfig, StorageScanner, directory_size
from app.safety import is_path_allowed


def write_bytes(path: Path, size: int) -> None:
    path.write_bytes(b"x" * size)


def test_directory_size_counts_nested_files(tmp_path: Path) -> None:
    nested = tmp_path / "Cache" / "Nested"
    nested.mkdir(parents=True)
    write_bytes(nested / "a.bin", 10)
    write_bytes(tmp_path / "b.bin", 5)

    assert directory_size(tmp_path) == 15


def test_scanner_finds_cache_candidate(tmp_path: Path) -> None:
    cache = tmp_path / "Discord" / "Cache"
    cache.mkdir(parents=True)
    write_bytes(cache / "blob.bin", 1024)
    config = ScannerConfig(
        scan_roots=[tmp_path],
        max_depth=3,
        min_folder_size_bytes=0,
        max_entries_per_root=50,
    )
    inventory = InstalledAppInventory(app_names={"Discord"})

    result = StorageScanner(config, inventory).scan()

    assert any(f.category == CATEGORY_CACHE and f.cleanup_eligible for f in result.findings)


def test_scanner_respects_exclusions(tmp_path: Path) -> None:
    cache = tmp_path / "SkipMe" / "Cache"
    cache.mkdir(parents=True)
    write_bytes(cache / "blob.bin", 1024)
    config = ScannerConfig(
        scan_roots=[tmp_path],
        excluded_paths=[tmp_path / "SkipMe"],
        max_depth=3,
        min_folder_size_bytes=0,
    )

    result = StorageScanner(config, InstalledAppInventory()).scan()

    assert result.findings == []


def test_safety_blocks_outside_roots(tmp_path: Path) -> None:
    root = tmp_path / "root"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()

    assert is_path_allowed(root / "Cache", [root]) is True
    assert is_path_allowed(outside, [root]) is False
    assert os.path.isdir(root)

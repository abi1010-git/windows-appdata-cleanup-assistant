from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable

from app.analyzer import build_finding, classify_path
from app.config import AppSettings, default_scan_roots
from app.installed_apps import InstalledAppInventory
from app.models import Finding, ScanResult, utc_now_iso
from app.safety import is_path_allowed, norm_path


ProgressCallback = Callable[[str, int, int], None]


@dataclass(slots=True)
class ScannerConfig:
    scan_roots: list[Path] = field(default_factory=default_scan_roots)
    excluded_paths: list[Path] = field(default_factory=list)
    max_depth: int = 2
    min_folder_size_bytes: int = 25 * 1024 * 1024
    max_entries_per_root: int = 250

    @classmethod
    def from_settings(cls, settings: AppSettings) -> "ScannerConfig":
        return cls(
            excluded_paths=[Path(p) for p in settings.excluded_paths if p],
            max_depth=max(1, int(settings.scan_depth)),
            min_folder_size_bytes=settings.min_folder_size_bytes(),
        )


class StorageScanner:
    def __init__(
        self,
        config: ScannerConfig | None = None,
        inventory: InstalledAppInventory | None = None,
    ) -> None:
        self.config = config or ScannerConfig()
        self.inventory = inventory or InstalledAppInventory.load()

    def scan(self, progress: ProgressCallback | None = None) -> ScanResult:
        started_at = utc_now_iso()
        findings: list[Finding] = []
        errors: list[str] = []
        roots = self._existing_roots()
        total = max(1, len(roots))
        for index, root in enumerate(roots, start=1):
            if progress:
                progress(str(root), index - 1, total)
            try:
                findings.extend(self._scan_root(root))
            except OSError as exc:
                errors.append(f"{root}: {exc}")
            if progress:
                progress(str(root), index, total)
        findings.sort(key=lambda f: f.size_bytes, reverse=True)
        return ScanResult(findings=findings, errors=errors, started_at=started_at, completed_at=utc_now_iso())

    def _existing_roots(self) -> list[Path]:
        roots: list[Path] = []
        seen: set[str] = set()
        for root in self.config.scan_roots:
            marker = norm_path(root)
            if marker in seen:
                continue
            if root.exists() and root.is_dir():
                roots.append(root)
                seen.add(marker)
        return roots

    def _scan_root(self, root: Path) -> list[Finding]:
        findings: list[Finding] = []
        candidates = list(self._candidate_directories(root))
        for candidate in candidates[: self.config.max_entries_per_root]:
            if not is_path_allowed(candidate, [root], self.config.excluded_paths):
                continue
            try:
                size = directory_size(candidate)
                last_modified = last_modified_time(candidate)
            except OSError:
                continue
            category, _ = classify_path(candidate)
            if size < self.config.min_folder_size_bytes and category not in {"cache", "temp"}:
                continue
            findings.append(
                build_finding(
                    path=candidate,
                    size_bytes=size,
                    last_modified=last_modified,
                    source_root=root,
                    inventory=self.inventory,
                )
            )
        return findings

    def _candidate_directories(self, root: Path) -> Iterable[Path]:
        yielded: set[str] = set()
        stack: list[tuple[Path, int]] = [(root, 0)]
        while stack:
            current, depth = stack.pop()
            try:
                children = [p for p in current.iterdir() if p.is_dir() and not p.is_symlink()]
            except OSError:
                continue
            for child in children:
                marker = norm_path(child)
                if marker in yielded:
                    continue
                yielded.add(marker)
                if depth >= 0:
                    yield child
                if depth + 1 < self.config.max_depth:
                    stack.append((child, depth + 1))


def directory_size(path: str | Path, *, max_files: int = 25000) -> int:
    total = 0
    counted = 0
    for root, dirs, files in os.walk(path, topdown=True, onerror=None, followlinks=False):
        dirs[:] = [d for d in dirs if not Path(root, d).is_symlink()]
        for file_name in files:
            if counted >= max_files:
                return total
            file_path = Path(root) / file_name
            try:
                if file_path.is_symlink():
                    continue
                total += file_path.stat().st_size
                counted += 1
            except OSError:
                continue
    return total


def last_modified_time(path: str | Path) -> float | None:
    latest: float | None = None
    try:
        latest = Path(path).stat().st_mtime
    except OSError:
        return None
    for root, dirs, files in os.walk(path, topdown=True, onerror=None, followlinks=False):
        dirs[:] = [d for d in dirs if not Path(root, d).is_symlink()]
        for name in files:
            try:
                mtime = (Path(root) / name).stat().st_mtime
            except OSError:
                continue
            latest = max(latest or mtime, mtime)
    return latest


from __future__ import annotations

import os
from pathlib import Path

from app.models import LOW_RISK_CLEANUP_CATEGORIES, Finding, RISK_SAFE, STATUS_READY


def norm_path(path: str | Path) -> str:
    return os.path.normcase(os.path.abspath(str(path)))


def is_relative_to(path: str | Path, root: str | Path) -> bool:
    path_norm = norm_path(path)
    root_norm = norm_path(root)
    try:
        common = os.path.commonpath([path_norm, root_norm])
    except ValueError:
        return False
    return common == root_norm


def critical_exact_paths() -> set[str]:
    home = Path.home()
    system_drive = Path(os.environ.get("SystemDrive", "C:") + "\\")
    paths = {
        system_drive,
        home,
    }
    return {norm_path(path) for path in paths}


def critical_subtree_paths() -> set[str]:
    home = Path.home()
    windir = Path(os.environ.get("WINDIR", r"C:\Windows"))
    program_files = [
        Path(os.environ.get("ProgramFiles", r"C:\Program Files")),
        Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")),
    ]
    paths = {
        windir,
        windir / "System32",
        windir / "SysWOW64",
        home / "Desktop",
        home / "Documents",
        home / "Downloads",
        home / "Pictures",
        home / "Videos",
        home / "Music",
    }
    paths.update(program_files)
    return {norm_path(path) for path in paths}


def is_critical_path(path: str | Path) -> bool:
    candidate = norm_path(path)
    if candidate in critical_exact_paths():
        return True
    for critical in critical_subtree_paths():
        if candidate == critical or candidate.startswith(critical + os.sep):
            return True
    return False


def is_path_inside_roots(path: str | Path, roots: list[str | Path]) -> bool:
    return any(is_relative_to(path, root) for root in roots)


def is_path_allowed(path: str | Path, roots: list[str | Path], excluded_paths: list[str | Path] | None = None) -> bool:
    if is_critical_path(path):
        return False
    if not is_path_inside_roots(path, roots):
        return False
    for excluded in excluded_paths or []:
        if is_relative_to(path, excluded):
            return False
    return True


def is_cleanup_allowed(finding: Finding, roots: list[str | Path], excluded_paths: list[str | Path] | None = None) -> bool:
    if finding.status != STATUS_READY:
        return False
    if finding.risk != RISK_SAFE:
        return False
    if finding.category not in LOW_RISK_CLEANUP_CATEGORIES:
        return False
    if not finding.cleanup_eligible:
        return False
    return is_path_allowed(finding.path, roots, excluded_paths)

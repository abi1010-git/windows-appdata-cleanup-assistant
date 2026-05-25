from __future__ import annotations

from pathlib import Path

from send2trash import send2trash

from app.models import Finding, STATUS_CLEANED
from app.safety import is_cleanup_allowed


class CleanupError(RuntimeError):
    pass


class CleanupManager:
    def __init__(self, scan_roots: list[str | Path], excluded_paths: list[str | Path] | None = None) -> None:
        self.scan_roots = scan_roots
        self.excluded_paths = excluded_paths or []

    def move_to_recycle_bin(self, finding: Finding, *, confirmed: bool = False) -> Finding:
        if not confirmed:
            raise CleanupError("Cleanup requires explicit confirmation.")
        if not is_cleanup_allowed(finding, self.scan_roots, self.excluded_paths):
            raise CleanupError("This item is not eligible for conservative cleanup.")
        path = Path(finding.path)
        if not path.exists():
            raise CleanupError("The selected path no longer exists.")
        try:
            send2trash(str(path))
        except Exception as exc:  # send2trash raises platform-specific exceptions.
            raise CleanupError(f"Could not move item to Recycle Bin: {exc}") from exc
        finding.status = STATUS_CLEANED
        finding.cleanup_eligible = False
        return finding


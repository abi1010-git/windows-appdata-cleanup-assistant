from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CATEGORY_CACHE = "cache"
CATEGORY_TEMP = "temp"
CATEGORY_LOGS = "logs"
CATEGORY_LEFTOVER = "leftover_app_data"
CATEGORY_DUPLICATE = "duplicate_app_data"
CATEGORY_UNUSED = "unused_app_data"
CATEGORY_OTHER = "other"

RISK_SAFE = "safe"
RISK_REVIEW = "review"
RISK_SENSITIVE = "sensitive"

STATUS_READY = "ready"
STATUS_IGNORED = "ignored"
STATUS_CLEANED = "cleaned"
STATUS_BLOCKED = "blocked"
STATUS_ERROR = "error"

LOW_RISK_CLEANUP_CATEGORIES = {CATEGORY_CACHE, CATEGORY_TEMP}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def format_bytes(size_bytes: int) -> str:
    size = float(max(0, size_bytes))
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            if unit == "B":
                return f"{int(size)} {unit}"
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def format_age_days(days: int | None) -> str:
    if days is None:
        return "Unknown"
    if days <= 0:
        return "Today"
    if days == 1:
        return "1 day ago"
    if days < 31:
        return f"{days} days ago"
    months = max(1, days // 30)
    if months < 12:
        return f"{months} month{'s' if months != 1 else ''} ago"
    years = max(1, days // 365)
    return f"{years} year{'s' if years != 1 else ''} ago"


@dataclass(slots=True)
class Finding:
    path: str
    name: str
    size_bytes: int
    last_modified: float | None
    category: str
    detected_app: str | None
    is_installed: bool | None
    risk: str
    status: str
    recommendation: str
    explanation: str
    cleanup_eligible: bool
    source_root: str
    reason_tags: list[str] = field(default_factory=list)
    error: str | None = None
    id: int | None = None

    @property
    def size_label(self) -> str:
        return format_bytes(self.size_bytes)

    @property
    def last_used_label(self) -> str:
        return format_age_days(self.age_days)

    @property
    def age_days(self) -> int | None:
        if self.last_modified is None:
            return None
        modified = datetime.fromtimestamp(self.last_modified, tz=timezone.utc)
        return max(0, (datetime.now(timezone.utc) - modified).days)

    @property
    def path_obj(self) -> Path:
        return Path(self.path)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "path": self.path,
            "name": self.name,
            "size_bytes": self.size_bytes,
            "last_modified": self.last_modified,
            "category": self.category,
            "detected_app": self.detected_app,
            "is_installed": self.is_installed,
            "risk": self.risk,
            "status": self.status,
            "recommendation": self.recommendation,
            "explanation": self.explanation,
            "cleanup_eligible": self.cleanup_eligible,
            "source_root": self.source_root,
            "reason_tags": list(self.reason_tags),
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "Finding":
        return cls(
            id=payload.get("id"),
            path=payload["path"],
            name=payload.get("name") or Path(payload["path"]).name,
            size_bytes=int(payload.get("size_bytes") or 0),
            last_modified=payload.get("last_modified"),
            category=payload.get("category") or CATEGORY_OTHER,
            detected_app=payload.get("detected_app"),
            is_installed=payload.get("is_installed"),
            risk=payload.get("risk") or RISK_REVIEW,
            status=payload.get("status") or STATUS_READY,
            recommendation=payload.get("recommendation") or "Review before cleaning.",
            explanation=payload.get("explanation") or "",
            cleanup_eligible=bool(payload.get("cleanup_eligible")),
            source_root=payload.get("source_root") or "",
            reason_tags=list(payload.get("reason_tags") or []),
            error=payload.get("error"),
        )


@dataclass(slots=True)
class ScanResult:
    findings: list[Finding]
    errors: list[str] = field(default_factory=list)
    started_at: str = field(default_factory=utc_now_iso)
    completed_at: str = field(default_factory=utc_now_iso)

    @property
    def total_recoverable_bytes(self) -> int:
        return sum(f.size_bytes for f in self.findings if f.cleanup_eligible and f.status == STATUS_READY)

    @property
    def safe_count(self) -> int:
        return sum(1 for f in self.findings if f.risk == RISK_SAFE)

    @property
    def review_count(self) -> int:
        return sum(1 for f in self.findings if f.risk == RISK_REVIEW)

    @property
    def sensitive_count(self) -> int:
        return sum(1 for f in self.findings if f.risk == RISK_SENSITIVE)

    @property
    def cache_count(self) -> int:
        return sum(1 for f in self.findings if f.category == CATEGORY_CACHE)

    @property
    def unused_count(self) -> int:
        return sum(1 for f in self.findings if f.category in {CATEGORY_LEFTOVER, CATEGORY_UNUSED})

    @property
    def risk_label(self) -> str:
        if self.sensitive_count:
            return "Review"
        if self.review_count:
            return "Low"
        return "Low"


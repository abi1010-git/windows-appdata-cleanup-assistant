from __future__ import annotations

from pathlib import Path

from app.installed_apps import InstalledAppInventory
from app.models import (
    CATEGORY_CACHE,
    CATEGORY_DUPLICATE,
    CATEGORY_LEFTOVER,
    CATEGORY_LOGS,
    CATEGORY_OTHER,
    CATEGORY_TEMP,
    CATEGORY_UNUSED,
    Finding,
    RISK_REVIEW,
    RISK_SAFE,
    RISK_SENSITIVE,
    STATUS_READY,
    LOW_RISK_CLEANUP_CATEGORIES,
)


CACHE_MARKERS = {"cache", "caches", "code cache", "gpucache", "shadercache", "shader-cache", "tmp-cache"}
TEMP_MARKERS = {"temp", "tmp", "temporary"}
LOG_MARKERS = {"log", "logs", "crashpad", "crashes", "reports"}
SENSITIVE_MARKERS = {"password", "credential", "keychain", "wallet", "token", "cert", "identity", "profile"}


def classify_path(path: str | Path) -> tuple[str, list[str]]:
    path_obj = Path(path)
    parts = [part.casefold() for part in path_obj.parts]
    name = path_obj.name.casefold()
    joined = " ".join(parts)
    tags: list[str] = []

    if any(marker in name or marker in joined for marker in SENSITIVE_MARKERS):
        tags.append("sensitive-name")
        return CATEGORY_OTHER, tags
    if any(marker == name or marker in name for marker in CACHE_MARKERS):
        tags.append("cache-marker")
        return CATEGORY_CACHE, tags
    if any(marker == name or marker in name for marker in TEMP_MARKERS):
        tags.append("temp-marker")
        return CATEGORY_TEMP, tags
    if any(marker == name or marker in name for marker in LOG_MARKERS):
        tags.append("log-marker")
        return CATEGORY_LOGS, tags
    if name.endswith(".old") or "backup" in name:
        tags.append("duplicate-marker")
        return CATEGORY_DUPLICATE, tags
    if "appdata" in joined:
        tags.append("appdata-folder")
        return CATEGORY_UNUSED, tags
    return CATEGORY_OTHER, tags


def risk_for(category: str, tags: list[str], age_days: int | None, is_installed: bool | None) -> str:
    if "sensitive-name" in tags:
        return RISK_SENSITIVE
    if category in LOW_RISK_CLEANUP_CATEGORIES:
        return RISK_SAFE
    if category == CATEGORY_LOGS and age_days is not None and age_days > 180:
        return RISK_REVIEW
    if is_installed is False and category in {CATEGORY_UNUSED, CATEGORY_DUPLICATE}:
        return RISK_REVIEW
    return RISK_REVIEW


def recommendation_for(category: str, risk: str, is_installed: bool | None) -> str:
    if risk == RISK_SENSITIVE:
        return "Keep this folder unless you know exactly what owns it."
    if category == CATEGORY_CACHE:
        return "Safe cleanup candidate. Review, then move to Recycle Bin if selected."
    if category == CATEGORY_TEMP:
        return "Temporary data candidate. Review active apps before cleaning."
    if category == CATEGORY_LOGS:
        return "Review old logs before cleaning; they may help with troubleshooting."
    if is_installed is False:
        return "Possible leftover app data. Review manually before cleanup."
    return "Review before cleaning."


def explanation_for(
    *,
    path: str | Path,
    size_bytes: int,
    age_days: int | None,
    category: str,
    detected_app: str | None,
    is_installed: bool | None,
    cleanup_eligible: bool,
) -> str:
    app_text = detected_app or "an unknown application"
    age_text = "an unknown amount of time"
    if age_days is not None:
        if age_days < 30:
            age_text = f"{age_days} days"
        elif age_days < 365:
            age_text = f"{max(1, age_days // 30)} months"
        else:
            age_text = f"{max(1, age_days // 365)} years"

    installed_text = ""
    if is_installed is True:
        installed_text = f" {app_text} appears to still be installed."
    elif is_installed is False:
        installed_text = f" {app_text} does not appear in the installed application inventory."

    category_text = {
        CATEGORY_CACHE: "cache data",
        CATEGORY_TEMP: "temporary files",
        CATEGORY_LOGS: "log or crash report data",
        CATEGORY_LEFTOVER: "leftover application data",
        CATEGORY_DUPLICATE: "duplicate-looking application data",
        CATEGORY_UNUSED: "application data",
    }.get(category, "application data")

    action_text = (
        "It is eligible for conservative cleanup after confirmation."
        if cleanup_eligible
        else "It is marked for manual review rather than automatic cleanup."
    )
    return (
        f"This folder appears to contain {category_text} related to {app_text}. "
        f"It was last modified about {age_text} ago.{installed_text} "
        f"Estimated recoverable storage: {size_bytes / (1024 ** 3):.1f} GB. {action_text}"
    )


def build_finding(
    *,
    path: str | Path,
    size_bytes: int,
    last_modified: float | None,
    source_root: str | Path,
    inventory: InstalledAppInventory,
) -> Finding:
    path_obj = Path(path)
    detected_app = inventory.detect_app_for_path(path_obj)
    is_installed = inventory.is_installed(detected_app)
    category, tags = classify_path(path_obj)
    age_days = None
    if last_modified is not None:
        from datetime import datetime, timezone

        modified = datetime.fromtimestamp(last_modified, tz=timezone.utc)
        age_days = max(0, (datetime.now(timezone.utc) - modified).days)
    if is_installed is False and category == CATEGORY_UNUSED:
        category = CATEGORY_LEFTOVER
        tags.append("app-not-installed")
    risk = risk_for(category, tags, age_days, is_installed)
    cleanup_eligible = risk == RISK_SAFE and category in LOW_RISK_CLEANUP_CATEGORIES
    recommendation = recommendation_for(category, risk, is_installed)
    explanation = explanation_for(
        path=path_obj,
        size_bytes=size_bytes,
        age_days=age_days,
        category=category,
        detected_app=detected_app,
        is_installed=is_installed,
        cleanup_eligible=cleanup_eligible,
    )
    return Finding(
        path=str(path_obj),
        name=path_obj.name,
        size_bytes=size_bytes,
        last_modified=last_modified,
        category=category,
        detected_app=detected_app,
        is_installed=is_installed,
        risk=risk,
        status=STATUS_READY,
        recommendation=recommendation,
        explanation=explanation,
        cleanup_eligible=cleanup_eligible,
        source_root=str(source_root),
        reason_tags=tags,
    )


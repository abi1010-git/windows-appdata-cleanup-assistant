from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import psutil


COMMON_APP_NAMES = {
    "adobe",
    "arc",
    "brave",
    "chrome",
    "discord",
    "docker",
    "dropbox",
    "edge",
    "figma",
    "firefox",
    "github",
    "google",
    "notion",
    "obsidian",
    "python",
    "slack",
    "spotify",
    "steam",
    "teams",
    "telegram",
    "vscode",
    "zoom",
}

APP_ALIASES = {
    "code": "Visual Studio Code",
    "discordcanary": "Discord",
    "googlechrome": "Google Chrome",
    "microsoftedge": "Microsoft Edge",
    "msedge": "Microsoft Edge",
    "slack": "Slack",
    "teams": "Microsoft Teams",
    "vscode": "Visual Studio Code",
}


def normalize_name(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"[^a-z0-9]+", "", value.casefold())


def display_name_from_token(token: str) -> str:
    normalized = normalize_name(token)
    if normalized in APP_ALIASES:
        return APP_ALIASES[normalized]
    token = re.sub(r"[_\-.]+", " ", token).strip()
    return token.title() if token else "Unknown"


@dataclass(slots=True)
class InstalledAppInventory:
    app_names: set[str] = field(default_factory=set)
    running_processes: set[str] = field(default_factory=set)
    known_names: set[str] = field(default_factory=lambda: set(COMMON_APP_NAMES))

    @property
    def normalized_apps(self) -> set[str]:
        return {normalize_name(name) for name in self.app_names if name}

    def is_installed(self, app_name: str | None) -> bool | None:
        normalized = normalize_name(app_name)
        if not normalized:
            return None
        names = self.normalized_apps
        if normalized in names:
            return True
        if any(normalized in name or name in normalized for name in names if len(name) >= 4):
            return True
        return False

    def detect_app_for_path(self, path: str | Path) -> str | None:
        parts = [p for p in Path(path).parts if p not in {"\\", "/"}]
        candidates: list[str] = []
        for part in reversed(parts):
            stem = normalize_name(part)
            if len(stem) >= 3:
                candidates.append(stem)

        searchable = self.normalized_apps | {normalize_name(name) for name in self.known_names}
        for candidate in candidates:
            if candidate in APP_ALIASES:
                return APP_ALIASES[candidate]
            for app in searchable:
                if len(app) >= 4 and (app in candidate or candidate in app):
                    return self._display_for_normalized(app)
        leaf = Path(path).name
        if normalize_name(leaf):
            return display_name_from_token(leaf)
        return None

    def _display_for_normalized(self, normalized: str) -> str:
        for name in self.app_names:
            if normalize_name(name) == normalized:
                return name
        if normalized in APP_ALIASES:
            return APP_ALIASES[normalized]
        return display_name_from_token(normalized)

    @classmethod
    def load(cls, include_powershell: bool = True) -> "InstalledAppInventory":
        names = set(COMMON_APP_NAMES)
        names.update(_registry_app_names())
        if include_powershell:
            names.update(_powershell_package_names())
        processes = _running_process_names()
        names.update(processes)
        return cls(app_names={n for n in names if n}, running_processes=processes)


def _registry_app_names() -> set[str]:
    if os.name != "nt":
        return set()
    try:
        import winreg
    except ImportError:
        return set()
    roots = [
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
    ]
    names: set[str] = set()
    for hive, key_path in roots:
        try:
            with winreg.OpenKey(hive, key_path) as key:
                for index in range(winreg.QueryInfoKey(key)[0]):
                    try:
                        subkey_name = winreg.EnumKey(key, index)
                        with winreg.OpenKey(key, subkey_name) as subkey:
                            display_name, _ = winreg.QueryValueEx(subkey, "DisplayName")
                            if display_name:
                                names.add(str(display_name))
                    except OSError:
                        continue
        except OSError:
            continue
    return names


def _powershell_package_names() -> set[str]:
    if os.name != "nt":
        return set()
    command = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-Command",
        "Get-AppxPackage | Select-Object -ExpandProperty Name",
    ]
    try:
        completed = subprocess.run(command, capture_output=True, text=True, timeout=6, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return set()
    if completed.returncode != 0:
        return set()
    return {line.strip() for line in completed.stdout.splitlines() if line.strip()}


def _running_process_names() -> set[str]:
    names: set[str] = set()
    for proc in psutil.process_iter(attrs=["name"]):
        try:
            name = proc.info.get("name") or ""
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
        stem = Path(name).stem
        if stem:
            names.add(stem)
    return names


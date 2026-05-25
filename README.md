# Storage Detective

Storage Detective is a Windows desktop cleanup assistant that scans common app-data and temp locations, explains what it finds, and only moves conservative cleanup candidates to the Recycle Bin after confirmation.

The MVP is intentionally cautious: it never permanently deletes files, never cleans automatically, and only marks low-risk cache/temp findings as cleanup eligible.

## Features

- PyQt6 Windows desktop interface with dashboard, results, analytics, settings, and scan history pages.
- Built-in modern dark/light styling, with optional `qdarktheme` support if that package is installed separately.
- Scans AppData Local, AppData Roaming, ProgramData, and temp folders.
- Detects cache folders, temporary data, logs, stale app-data folders, and suspicious duplicate-looking folders.
- Compares findings against installed Windows apps, Appx packages, common app names, and running processes.
- Stores scan history, findings, ignored paths, settings, and cleanup events in SQLite.
- Uses `send2trash` for Recycle Bin moves. No permanent deletion path exists in the app.

## Project Structure

```text
storage-detective/
|-- README.md
|-- requirements.txt
|-- main.py
|-- app/
|   |-- gui.py
|   |-- scanner.py
|   |-- analyzer.py
|   |-- installed_apps.py
|   |-- cleanup.py
|   |-- database.py
|   |-- safety.py
|   |-- config.py
|   |-- models.py
|   |-- ui/
|   |-- assets/
|   `-- styles/
`-- tests/
```

## Setup

```powershell
cd C:\Users\abhia\Documents\storage-detective
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Run

```powershell
python main.py
```

The app stores its SQLite database under `%LOCALAPPDATA%\StorageDetective\storage_detective.sqlite3`.

## Test

```powershell
pytest
```

The tests use temporary directories and mocked cleanup calls. They do not delete real files.

## Safety Model

- Approved scan roots are AppData Local, AppData Roaming, ProgramData, and temp folders.
- Critical paths such as `C:\Windows`, Program Files, and top-level user folders are blocked.
- Cleanup eligibility requires all of these conditions:
  - finding is still in `ready` status;
  - risk is `safe`;
  - category is `cache` or `temp`;
  - path is inside an approved scan root;
  - path is not excluded or ignored;
  - user confirms the Recycle Bin action.

## Future Packaging

Packaging is out of scope for this MVP, but the app is structured so a future release can add PyInstaller or MSIX packaging without changing scanner or cleanup behavior.

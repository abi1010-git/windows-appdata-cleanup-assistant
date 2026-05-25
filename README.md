# Storage Detective

Storage Detective is a Windows desktop cleanup assistant that scans common app-data and temp locations, explains what it finds, and only moves conservative cleanup candidates to the Recycle Bin after confirmation.

The MVP is intentionally cautious: it never permanently deletes files, never cleans automatically, and only marks low-risk cache/temp findings as cleanup eligible.

## Download and Use

Storage Detective is designed for Windows users who do not want to install Python or use a terminal.

### 1. Download the Windows App

1. Open the GitHub project page.
2. Select **Releases** on the right side of the page.
3. Download `Storage-Detective-Windows.zip` from the latest release.
4. Right-click the ZIP file and select **Extract All**.
5. Open the extracted folder.
6. Double-click `Storage Detective.exe`.

If Windows SmartScreen warns that the app is from an unknown publisher, select **More info**, then **Run anyway**. This can happen because the MVP is not code-signed yet.

### 2. Use the App Safely

1. Select **Start Scan** on the dashboard.
2. Review the results table after the scan finishes.
3. Select a folder to read the explanation and recommendation.
4. Use **Open** to inspect the folder in File Explorer.
5. Use **Move To Recycle Bin** only for items you want to remove.
6. Use **Ignore** for folders you want future scans to skip.

Storage Detective never permanently deletes files. Cleanup actions move selected eligible folders to the Recycle Bin after confirmation.

## Build a Windows App Package

Developers can build the same no-Python-needed Windows package locally:

```powershell
.\scripts\build_windows.ps1
```

The build creates:

```text
dist\Storage Detective\Storage Detective.exe
dist\Storage-Detective-Windows.zip
```

GitHub Actions also builds `Storage-Detective-Windows.zip` automatically on pushes to `main`, manual workflow runs, and published releases.

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

## Developer Setup

```powershell
cd C:\path\to\windows-appdata-cleanup-assistant
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
```

## Developer Run

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

The current package is a portable ZIP. A future version can add a signed installer through MSIX, Inno Setup, or WiX without changing scanner or cleanup behavior.

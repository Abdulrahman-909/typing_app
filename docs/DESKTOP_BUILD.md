# Windows desktop build
Target: Windows 10/11, Python 3.12 x64, Microsoft Edge WebView2 runtime.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements/desktop.txt
python -m desktop
.\scripts\build_windows.ps1
.\dist\TypeAtlas\TypeAtlas.exe
```

One-folder mode is intentional: distribute the whole dist/TypeAtlas directory, not only the executable. It avoids repeated extraction overhead. No signed installer is supplied. The console is retained for actionable startup diagnostics in this development release.

Data is stored under platformdirs' per-user location (normally %LOCALAPPDATA%\TypeAtlas). Assets/templates are read from the bundle; writable data never goes into _MEIPASS. First startup creates a random Django key, applies migrations, and seeds original content. Pending upgrades make an SQLite snapshot first. A lock prevents two processes sharing the DB. Second launch prints a notification rather than focusing the first window.

```powershell
python -m desktop --smoke
python -m desktop --backup "C:\Backups\typing.zip"
python -m desktop --restore "C:\Backups\typing.zip" --confirm-restore
```

Close the app before restore. The launcher lock enforces this. Restore validates names, sizes, format, hash, SQLite integrity, and migration compatibility, then creates a pre-restore backup. Backups contain personal data; protect them accordingly.

Local profiles can be created, switched, renamed, and deleted (explicit checkbox plus automatic backup). PIN protection is not included. Profiles separate progress, not OS-level access. Local lesson completion is stored separately from online-user progress and isolated per profile.

Networking is unnecessary for local practice. The source smoke test checks bootstrap, home, and gated health. The actual WebView GUI and frozen Windows executable could not be tested in this Linux environment. The Windows Actions job is supplied but has not run here. Missing WebView2 and native-library errors require Windows verification. Unsigned executables may prompt Windows reputation checks; sign distributed releases with your own certificate.

Read desktop.log in the data directory for failures. Use TYPEATLAS_DATA_DIR only for a separate test data folder. Backup commands currently run from source or through the packaged executable's CLI flags; no backup GUI is provided.

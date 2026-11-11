# TypeAtlas
A multilingual typing practice platform built with **Django, HTML, CSS and vanilla JavaScript**, with an offline desktop launcher for Windows.

**Development release, v0.1.0.** This is working source code, not a certified production deployment or a prebuilt Windows executable. Read [the requirement status](docs/ROADMAP.md) and [verification report](docs/VERIFICATION.md) for exact limits.

## Included
- English, Dari and Pashto timed tests (15/30/60/120 seconds) and word tests (10/25/50/100 words).
- Live feedback, server-replayed scores, results, charts, custom text and UTF-8 imports.
- Registration, login, password reset, preferences, private history and progress dashboard.
- Starter lessons, unlocking, weak-letter practice, goals, streaks and earned badges.
- Light/dark themes, text sizes, local sounds, responsive templates and joined RTL rendering.
- Ranked online sessions, filtered leaderboards, moderation and audit records.
- Teacher classrooms, consented enrollment and assigned-lesson progress.
- Daily shared challenges, basic WebSocket races, and duplicate-safe offline imports.
- Offline local profiles, backup/restore, startup migrations, single-instance lock, Waitress and pywebview launcher.
- Django migrations, original seed content, tests, Windows build recipe, Docker configuration and GitHub Actions.

## Quick start — Windows PowerShell
Use Python 3.12 x64. Extract the archive and open PowerShell inside the `typeatlas` folder.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements/dev.txt
python manage.py migrate
python manage.py seed_demo_data
python manage.py runserver
```
Open **http://127.0.0.1:8000/**. If PowerShell blocks activation, invoke `.\.venv\Scripts\python.exe` directly for each Python command instead of changing machine-wide execution policy.

## Quick start — Linux/macOS
```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements/dev.txt
python manage.py migrate
python manage.py seed_demo_data
python manage.py runserver
```
The development settings work without `.env`. Copy `.env.example` to `.env` when customizing settings. No demo accounts or shared passwords are created.

## Administration and teachers
```bash
python manage.py createsuperuser
```
Open `/admin/`. Create a group named `teacher` and add the intended teacher accounts. Staff can also create classes. Students join with a class code and explicitly consent to share assigned-lesson completion. Unrelated practice results remain private.

Passage content and review status can be edited in admin. Dari/Pashto starter text is machine-assisted and unreviewed. Have a native speaker review it before marking it reviewed. Keyboard guide mappings are illustrative and need verification; see [keyboard status](docs/KEYBOARD_LAYOUTS.md).

## Desktop edition
```powershell
pip install -r requirements/desktop.txt
python -m desktop
```
Choose/create a local profile through **Profiles** before practicing to save progress. Windows needs the WebView2 runtime. Build the executable on Windows:
```powershell
.\scripts\build_windows.ps1
.\dist\TypeAtlas\TypeAtlas.exe
```
Distribute the **entire** `dist/TypeAtlas/` folder. Actual Windows GUI and binary execution have not been verified here. See [desktop build instructions](docs/DESKTOP_BUILD.md), including backup/restore and troubleshooting.

## Multiplayer
Use the ASGI server instead of `runserver`:
```bash
daphne -b 127.0.0.1 -p 8000 config.asgi:application
```
Open `/races/` in two signed-in browsers. Share a room link and let the host start. Development uses an in-memory layer; production needs Redis. See [multiplayer notes](docs/MULTIPLAYER.md).

## Test and inspect
```bash
python manage.py check
python manage.py makemigrations --check --dry-run
pytest -q
node --test tests/scoring.test.js
ruff check .
ruff format --check .
python -m desktop --smoke
```
Node is only needed for the JavaScript unit tests, not to run the application. Python tests use a separate test database. `--smoke` creates desktop data in the normal profile location unless `TYPEATLAS_DATA_DIR` points to a test folder.

Browser E2E script: install Playwright and its Chromium browser, run the web server, then run `python tests/browser_e2e.py`. CI includes this workflow. Browser scripts and Windows CI have not run on GitHub yet; no passing CI badge is claimed.

## Data tools
```bash
python manage.py export_passages > passages.json
python manage.py import_passages passages.json
python manage.py cleanup_activity
```
Imports are validated before insertion and marked unreviewed. Schedule `cleanup_activity` to remove expired abandoned tests, race rooms, and sync tokens. Scores are recomputed at submission; raw event logs are deliberately not retained for later reprocessing.

## Structure
```text
typing_engine/      Pure scoring and Unicode replay
apps/accounts/     Users, registration and profiles
apps/practice/     Sessions, results and passage management
apps/lessons/      Lessons and isolated local progress
apps/dashboard/    History, statistics and goals
apps/challenges/   Leaderboards and moderation
apps/community/    Classes, daily challenges, sync and races
desktop/           Local server, profiles, backups and launcher
static/            Local CSS, ES modules, fonts and layout data
templates/         Django interface
```
Read [architecture](docs/ARCHITECTURE.md), [scoring](docs/SCORING.md), [timezone rules](docs/TIMEZONES.md), [sync](docs/SYNC.md), and [deployment](docs/DEPLOYMENT.md).

## Rename and publish to GitHub
Set `PROJECT_NAME` in `.env` to change UI branding and the desktop package name. Set the same environment value while building the executable. Update this README, license copyright and CI artifact paths to match your chosen public project name. Python package paths can stay unchanged.

Create your own empty GitHub repository, then initialize and push this folder using Git. Review `.gitignore` first. Do not commit `.env`, databases, local profiles, backups, virtual environments, `staticfiles/` or build output. No external repository was created automatically.

## Contributing and license
Keep scoring changes synchronized across Python and JavaScript and add regression cases. Review Arabic-script shaping visually, test permissions, and run the checks above. Mark native-language content reviewed only after actual review.

Original code/content use the MIT license as a permissive portfolio default. You may choose a different license before publishing. Bundled Noto font licensing is retained in [third-party notices](THIRD_PARTY_LICENSES.md).

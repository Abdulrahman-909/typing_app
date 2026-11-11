# Verification report — 11 November 2026
Environment: Linux, Python 3.12.14, Django 5.2.19, Node 24.22.1. No existing Git repository was present.

## Phase 1 — core website
Implemented: three-language practice, all length options, custom input, replay scoring, accounts, private results, dashboard, themes, signed sessions and moderation.

Observed commands:
- `python manage.py migrate`: all migrations applied.
- `python manage.py seed_demo_data`: 9 passages and 10 lessons seeded; no accounts created.
- `python manage.py check`: no issues.
- `python manage.py makemigrations --check --dry-run`: no changes detected.
- `node --test tests/scoring.test.js`: 5 tests passed.

Browser checks: English custom passage `calm focus` completed and showed calculated WPM, 100% accuracy and zero mistakes. Pashto `زما کتاب` completed and showed a result. Dari rendered joined right-to-left words in the bundled Noto font. Visual layout inspected at the browser's desktop viewport. No screenshot asset is distributed.

Remaining: exact RTL character caret, complete native IME test coverage, account export/deletion and stronger multi-worker rate limiting.

## Phase 2 — learning
Implemented: lesson unlocking, completion thresholds, local profile progress isolation, weak-character practice, custom imports, minute goals, goal snapshots, streaks and earned badges.

Unit tests include Unicode variants, corrected mistakes, invalid uploads, lesson locks, profile permissions, Kabul midnight and DST date handling, and historical goal changes. Keyboard mappings remain explicitly unverified and the curriculum is a starter set, not a complete typing course.

## Phase 3 — desktop
Observed command: `TYPEATLAS_DATA_DIR=/tmp/typeatlas-smoke python -m desktop --smoke`.
Result: `Desktop smoke: bootstrap, home, and authenticated health passed.`
The unauthenticated readiness probe returns the expected 403 because the local token gate is active. A shutdown warning found in the first run was fixed by draining the response and stopping worker threads before closing the server.

Backup tests cover round-trip restoration, explicit confirmation, traversal rejection, hash rejection, and newer-schema rejection. Local Host/token gate and local-progress isolation are tested.

Blocked: actual Windows `.exe` build and WebView GUI execution require Windows. A reproducible PowerShell/PyInstaller recipe and Windows Actions job are included but were not executed remotely. The Linux headless smoke does not prove Windows compatibility.

## Phase 4 — community
Implemented: teacher classes and consent, assignments, daily challenges, signed-score leaderboards, token-authorized imports and basic Channels races.

Tests include cross-class access denial, student write denial, enrollment consent/withdrawal, import deduplication/owner binding, hidden pending leaderboard entries, late race join rejection, and a two-client consumer test completing a race.

Not run: two physical browser race clients, Redis deployment/load tests, live HTTPS sync from Windows, external SMTP delivery or PostgreSQL service. CI recipes are supplied for later execution.

## Final suite
`python -m pytest -q --disable-warnings`: **64 passed**, 2 warnings, no failures.
`ruff check .`: all checks passed.
`ruff format --check .`: source formatting checked.
`python manage.py check --deploy` with a generated production secret and explicit host/origin: **no issues**.
Coverage measurement immediately before the final local-progress test: **66% overall**, **93% pure scoring module**, from the 63-test suite. This is a measured snapshot, not claimed final 100% coverage. Desktop subprocess smoke is not counted in pytest coverage.

Browser E2E/Windows/PostgreSQL workflows have been written, not remotely run. No CI success badge or production-readiness claim is made. See ROADMAP.md for every partial requirement, DECISIONS.md for assumptions, and README.md for Windows/Unix run commands.

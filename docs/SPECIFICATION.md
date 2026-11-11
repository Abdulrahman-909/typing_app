# Implementation Prompt: Multilingual Typing Practice Platform (Django Web + Offline Windows Desktop)

You are a senior full-stack engineer and software architect working in a real workspace. Your job is to **build, run, test, and document working software**, not to describe a plan. Deliver code, migrations, tests, and setup instructions, and report honestly on what is done, tested, and outstanding.

## 0. How to work

1. **Start by inspecting the workspace** (existing files, Python version, OS, installed tools, git state). Adapt to what you find.
2. **Make reasonable decisions without asking confirmation questions.** Record each non-trivial decision and assumption in `docs/DECISIONS.md` (short entries: decision, reason, alternatives).
3. **Build a working vertical slice first**: a guest can open the site, choose English, take a 30-second test, see live feedback, finish, and see a correctly computed result, with tests for the scoring. Only then expand.
4. **Never silently drop a requirement.** If something cannot be completed, keep it in `docs/ROADMAP.md` with status `not started / partial / done / blocked` and the reason.
5. **No fakes.** No invented statistics, nonfunctional buttons, placeholder features presented as finished, or claims that tests passed unless you actually ran them and saw them pass. Quote real command output summaries in your reports. If you cannot run something (for example a Windows build on Linux), say so plainly.
6. Work phase by phase (Section 9). At the end of each phase, run the full test suite, then give a **Phase Report**: implemented, tested (with the commands run and results), known issues, outstanding items, assumptions.
7. Keep the code readable for a developer who is learning from it: clear names, small modules, docstrings on non-obvious logic, and `docs/ARCHITECTURE.md` explaining how pieces fit.

## 1. Project, naming, and technology constraints

- **Working name: `TypeAtlas`.** Make the name trivially changeable: a single `PROJECT_NAME` setting and a single place for branding strings/logo; no hard-coded name scattered through templates, build specs, or docs (document the rename procedure in the README).
- **Backend:** Python and Django only. Do not replace Django with another framework. Choose a currently supported Django LTS and a Python version that is supported by Django, pywebview, and PyInstaller on Windows 10/11 (pin versions in the dependency files and document why).
- **Frontend:** Django templates, HTML, CSS, and vanilla JavaScript (ES modules). No heavy SPA framework. Small, reusable JS modules; no CDN dependencies (all fonts/scripts/styles served locally so the web build and desktop build behave identically).
- **Database:** SQLite for local development and the desktop edition; PostgreSQL supported for website deployment (settings selected by environment variables via `DATABASE_URL` or equivalent). CI must exercise at least SQLite, and ideally PostgreSQL via a service container.
- **Desktop:** `pywebview` window + local WSGI server (use a production-grade, Windows-compatible server such as Waitress; **never** package or use Django's `runserver` for the desktop edition) bound **only to `127.0.0.1`**. Package with PyInstaller for Windows 10/11.
- **Shared core:** website and desktop use the same Django apps and business logic. Differences live in settings modules (`settings/base.py`, `dev.py`, `prod.py`, `desktop.py`) and a separate `desktop/` launcher package.
- Dependencies: `pyproject.toml` (or `requirements/*.txt`) with pinned/compatible ranges, separated into base, dev/test, web-production, and desktop sets.

## 2. Repository layout (adjust sensibly, but keep this separation)

```
typeatlas/
  config/                 # Django project: settings/{base,dev,prod,desktop}.py, urls, wsgi/asgi
  apps/
    core/                 # shared utilities, i18n helpers, timezone helpers, feature flags
    accounts/             # users, profiles, roles, registration/login/reset
    practice/             # passages, tests, results, scoring, ranked-session logic
    lessons/              # lessons, exercises, keyboard layouts, finger maps, weak-key tracking
    dashboard/            # history, records, charts, goals, streaks, achievements
    challenges/           # leaderboards, daily challenges, suspicious-result review
    classes/              # teacher/class/student/assignment features (Phase 4)
    sync/                 # optional desktop<->online sync (Phase 4)
    races/                # real-time multiplayer (Phase 4, Channels)
  typing_engine/          # PURE PYTHON, no Django imports: scoring, normalization, comparison, grapheme handling
  static/                 # css, js (modules), fonts, sounds, images (all bundled locally)
  templates/
  desktop/                # launcher: startup, port selection, single-instance lock, server thread, pywebview, shutdown, paths, backup/restore
  data/                   # fixtures/seed passages and lessons (with review-status metadata)
  tests/
  docs/
  .github/workflows/ci.yml
  .env.example  .gitignore  LICENSE  README.md  pyproject.toml
```

Rules: typing calculations live in `typing_engine/` (pure, heavily unit-tested); UI behavior lives in JS modules plus templates; stored results live in `practice` models/services; desktop startup code lives only in `desktop/`. Views stay thin; business logic goes in service functions.

## 3. Core typing features (Phase 1 unless noted)

### 3.1 Test modes and settings
- Guest practice with no registration, always available even when accounts are enabled.
- **Passage languages:** English (LTR), Dari (RTL), Pashto (RTL). Passage language is selected **separately from interface language** (clear UI distinction; the interface may initially ship in English with Django i18n infrastructure in place so Dari/Pashto UI translations can be added; document the state honestly).
- **Timed tests:** 15, 30, 60, 120 seconds. **Word-count tests:** 10, 25, 50, 100 words.
- **Difficulty:** easy / medium / hard with documented, objective criteria (e.g., word length, vocabulary frequency tier, rare-letter density). Store criteria in the docs and the passage metadata.
- Optional punctuation and numbers toggles, using language-appropriate punctuation (e.g., Arabic comma `،`, question mark `؟`, Arabic-script digits policy documented: support Western digits and, as an option, Persian/Pashto digit forms where applicable).
- Passage generation: word-list based generation for timed tests (enough text to never run out), plus curated passages. Seeded random selection so a test can be reproduced and validated server-side.

### 3.2 Typing engine behavior (specify precisely, implement identically on client and server)
Create `typing_engine/` and `docs/SCORING.md` defining:
- **Text normalization:** Unicode NFC for target text and typed input. Documented policy for ZWNJ (U+200C)/ZWJ (U+200D), Arabic/Persian letter variants (e.g., Arabic Yeh/Kaf vs Persian Yeh/Keheh; Pashto-specific letters), tatweel, and diacritics. Define which are treated as equivalent for comparison and which are strict. Default to strict comparison of normalized code points with explicit, tested exceptions.
- **Comparison unit:** compare by normalized characters (grapheme-aware for combining marks) in logical order. Space handling: a space ends a word; typing a space early marks the word as incorrect and advances (state which behavior you chose and apply it consistently); extra characters beyond the word length are counted as errors and displayed; backspace corrects within the current word and (document your choice) may or may not cross word boundaries.
- **Metrics:**
  - `correct_chars` = characters in correctly typed words (plus the spaces between correct words) per documented rule.
  - **Net WPM** = (correct_chars / 5) / elapsed_minutes. **Raw WPM** = (all typed chars / 5) / elapsed_minutes. State the 5-character convention and that for Arabic-script it is a convention, not a linguistic claim.
  - **Accuracy** = correct keystrokes / total keystrokes counted per rule (document exactly how corrected mistakes are treated: errors made and later fixed still count against keystroke accuracy but not against final-text accuracy; report both if useful).
  - **Mistakes** = uncorrected errors plus total error keystrokes (report distinctly).
  - **Elapsed time:** starts at the **first typing input event** (not on page load or button click); for word-count tests ends at the last required character; for timed tests ends at the time limit. Use a monotonic clock (`performance.now()`) on the client.
  - **Consistency** (optional) = based on per-second WPM variance, documented.
- **Speed over time:** record per-second samples (WPM, raw WPM, errors) for the result chart.
- Edge cases handled and tested: empty input, one keystroke, finishing exactly at the limit, tab switch/blur, very long pauses, held keys, rapid keystrokes, zero-time division, paste, IME composition, and fast completion.

### 3.3 Live UI
- Per-character feedback for English. For Dari/Pashto, **do not wrap individual letters in separate inline elements in a way that breaks Arabic-script joining/shaping.** Render RTL passages with each *word* as a single text node/span (shaping preserved), and show correctness via word-level state plus a caret/position indicator computed from the logical index (e.g., using `Range` / `getClientRects` on the intact text node, or underline/background overlays that do not split glyph runs). Show typed-so-far feedback in a way that keeps connected letters intact; extra characters shown in a distinct marker without splitting shaping. Verify with the bundled fonts and document the technique and its limits.
- Use a hidden/visible `<input>`/`<textarea>` approach that properly supports **IME composition** (`compositionstart/update/end`, `beforeinput`/`input` events): never evaluate or score in the middle of composition, and process the final composed text on `compositionend`. Set `lang`, `dir`, `inputmode`, `autocomplete=off`, `autocapitalize=off`, `spellcheck=false`.
- Current-position indicator, live timer, live WPM, live accuracy, progress indicator, clear start-on-first-input state, ARIA live regions that announce meaningful states without spamming screen readers (announce test start/end and result, not every keystroke).
- Restart (new passage) and Try Again (same passage) controls with keyboard shortcuts that **do not interfere with typing**: use modifier-free keys only when the typing field is not active (e.g., `Esc` to blur/restart prompt, `Tab` then `Enter` pattern is a common approach); document them, make them discoverable, and allow disabling.
- Fonts: bundle open-licensed fonts with good Arabic-script support (e.g., Noto Naskh Arabic and/or Vazirmatn; include their licenses in the repo) and a clean Latin UI/mono font. Use `font-display: swap`, subset where practical.

### 3.4 Practice vs ranked
- **Practice mode:** no server-side ranking; paste is blocked in the typing field anyway (to keep the exercise meaningful) but not treated as a cheating incident; custom passages allowed; results saved for logged-in users (guests see results but results are not persisted server-side, or stored only in local storage with a clear explanation; choose and document).
- **Ranked mode (data model and validation in Phase 1; leaderboards in Phase 4):** the **server issues a signed test session** (passage ID/seed, language, mode, duration, difficulty, issued-at, expiry, nonce). The client submits the keystroke event log (key, timestamp deltas, input type); the server **recomputes** WPM/accuracy from the log and the server-held passage, rejects mismatches, rejects reused/expired/foreign sessions, enforces plausible-timing rules (e.g., impossible inter-key intervals, uniformity, WPM caps by language, session-duration vs. server-observed duration), and flags suspicious results for admin review instead of silently deleting them. Paste, drag-drop, and programmatic input are rejected in ranked mode. Custom text is **not** allowed in ranked mode. State clearly in the docs that client-side cheating cannot be fully eliminated; this is risk reduction and review tooling, not a guarantee.

### 3.5 Custom passages
- Users can paste/type custom text or import a `.txt` file. Safe handling: enforce a size limit (e.g., 100 KB), extension and content checks, UTF-8 (and documented fallback) decoding with a clear error, NFC normalization, control-character stripping, length bounds for a test, no server-side execution or path use of uploaded filenames, no storage of the raw upload beyond what's needed, and escaping on render. Detect language/direction heuristically (and let the user override). Custom passages are private to the user unless explicitly reported/approved through a future workflow.

## 4. Accounts and progress (Phase 1, with extensions in Phase 2)

- Registration, login, logout, **password reset for the web edition (email backend configurable; console backend in dev)**, profile management (display name, avatar optional, preferred passage language, interface language, theme, timezone, font size, sound preference), account deletion/export (basic data export is a plus).
- Use a custom user model from the start (`AUTH_USER_MODEL`), with role support (student, teacher, moderator, admin) via groups/permissions.
- Password validators, rate limiting/lockout for login and reset (document the mechanism), CSRF everywhere, secure session/cookie settings in production.
- **Dashboard:** practice history table with filters (language, duration/mode, difficulty, date range), personal records per language/mode/duration/difficulty, charts of speed and accuracy over time (render with a bundled local chart approach: lightweight library bundled in `static/`, or hand-rolled SVG/canvas; no CDN), and per-result detail pages with the speed-over-time chart.
- **Daily goals, streaks, achievements, badges (Phase 2):**
  - Goals configurable (minutes practiced, tests completed, or words typed).
  - **Timezone rules (document in `docs/TIMEZONES.md`):** a "day" is the user's profile-timezone calendar day; store timestamps in UTC; compute the day boundary at write time and store a `local_date` on the result/practice record; streak = consecutive local dates meeting the goal; handle DST and timezone changes without retroactively corrupting streaks (explain the rule); desktop profiles default to the system timezone captured at profile creation and are editable.
  - Achievements/badges defined as data with deterministic, tested unlock rules (e.g., first test, 7-day streak, 40/60/80 WPM thresholds at ≥95% accuracy per language, lessons completed). No fake or pre-awarded badges.
- Guests can always practice; if they later register, offer (do not force) importing locally stored guest results.

## 5. Learning features (Phase 2)

- **Structured lessons, beginner to advanced:** finger placement, home row, top row, bottom row, number row, shift/punctuation, then words, sentences, and mixed practice. Lesson model: ordered curriculum, per-language tracks, completion requirements (e.g., ≥N% accuracy and ≥M net WPM over K attempts; defined per lesson), progress storage, locked/unlocked states with clear UI, and the ability to review completed lessons.
- **Visual on-screen keyboard** highlighting the next key and the suggested finger, with a finger color map that does not rely on color alone (also label fingers). Support shift states and language-specific keys.
- **Explicitly identify supported keyboard layouts per language** and surface them in the UI and in `docs/KEYBOARD_LAYOUTS.md`:
  - English: US QWERTY (others, e.g., UK, as future options).
  - Dari: the standard Persian/Farsi layout (Windows "Persian (Standard)" / ISIRI 9147 style) with any Afghan-specific notes.
  - Pashto: Windows "Pashto" (Afghanistan) layout.
  - Mark layout data files with their source and "needs native-speaker/keyboard verification" status if you cannot verify it. Do not present unverified mappings as authoritative. Layouts are data-driven (JSON), not hard-coded in JS.
- **Weak-key tracking:** record per-character (and per-bigram, optional) error counts and latency; show "commonly mistyped characters" and generate **targeted practice** passages emphasizing those characters (using the language's word list).
- **Starter content:** include useful starter passages, word lists, and exercises in all three languages. Every item carries metadata: `source`, `license/original`, `difficulty`, `review_status` (`unreviewed` / `reviewed`), and the UI/admin visibly flags unreviewed Dari and Pashto content. State in the README that Dari/Pashto content was machine-assisted/unverified unless reviewed by a native speaker, and provide a documented review workflow in the admin. Use only original or properly licensed text; no copyrighted passages.

## 6. Design, accessibility, and UX (all phases)

- A polished, focused interface with a design-token system (CSS custom properties for color, spacing, type scale, radius), reusable template components/partials, consistent typography, and responsive layouts for desktop, tablet, and mobile (note: mobile typing relies on the device keyboard; document limitations honestly).
- Light and dark themes (respect `prefers-color-scheme`, user override persisted), adjustable typing font size, optional sounds (off by default, bundled local audio, volume control, respects reduced-motion/user preference), and `prefers-reduced-motion` support.
- Accessibility: full keyboard navigation, visible focus states, WCAG AA contrast targets in both themes, labels/ARIA for controls, error/correct feedback using **more than color** (underline styles, icons, text), proper `lang`/`dir` on mixed-direction content, logical RTL layout (use CSS logical properties) for Dari/Pashto, and bidi-safe mixing of numerals and Latin text.
- Empty states, loading states, helpful error pages (404/500/403), form validation with clear messages, and no dead buttons.
- Perform and document an accessibility self-check (automated checks where practical, e.g., axe via test tooling if available, plus a manual checklist).

## 7. Django administration

Use the built-in Django admin where suitable, customized with list filters, search, and inline editing:
- Manage languages, passages (with review status, difficulty, active flag), word lists, difficulty levels, lessons/exercises, challenges, achievements.
- Manage users and role permissions (groups; teacher/moderator permissions).
- Review queue for **reported content** (user can report a passage; admin resolves) and **suspicious results** (flag reasons, validation diffs, approve/reject actions that are audit-logged).
- Admin actions for bulk activate/deactivate and import/export of passages (CSV/JSON) with validation.

## 8. Desktop edition (Phase 3, with sync in Phase 4)

- **Offline-first:** bundled lessons, passages, tests, fonts, scripts, styles, sounds; **no CDN or network requirement** to run. Verify by running with networking disabled where possible.
- **Writable data location:** use the OS per-user data directory (e.g., `%LOCALAPPDATA%\<ProjectName>\` via `platformdirs`), never the install directory or PyInstaller's temporary extraction directory (`sys._MEIPASS`). Resolve bundled read-only resources via a helper that works in both dev and frozen modes. Store DB, logs, backups, and config separately; rotate logs.
- **Startup sequence (in `desktop/`):** acquire a single-instance lock (a second launch focuses/notifies the first instance rather than starting another server or corrupting the DB); choose a free port (bind to port 0 or scan, 127.0.0.1 only); run migrations safely before serving (backup the DB before migrating when a schema upgrade is pending; abort with a clear message on failure); start the Waitress server in a background thread; **poll for readiness** (health endpoint) with timeout before creating the pywebview window; show a friendly error window if startup fails (WebView2 runtime missing, port/DB errors) with the log location.
- **Clean shutdown:** closing the window stops the server thread, flushes/closes DB connections, releases the lock, and exits without orphan processes; handle crashes on startup gracefully.
- **Local-server hardening (loopback alone is not enough):** random per-launch secret token delivered to the webview at startup (not via a predictable URL that another local process/browser tab can use) exchanged for a session cookie (`SameSite=Strict`, `HttpOnly`); reject requests without it; validate the `Host` header (`127.0.0.1:<port>` only) to mitigate DNS rebinding; strict `ALLOWED_HOSTS`; CSRF enabled; no CORS; disable Django debug and the admin site on the desktop build (or protect the admin behind the same token and a flag); Content-Security-Policy; do not expose the server on `0.0.0.0`; no secrets in the repo (generate the desktop `SECRET_KEY` on first run and store it in the user-data dir with restrictive permissions where possible). Document the threat model and its limits (e.g., other processes running as the same Windows user).
- **Local profiles:** multiple local profiles for shared computers (create/rename/delete/switch, optional PIN), each with its own progress, settings, and records. **Local profiles are distinct from online accounts** (separate model/concept and UI wording); a local profile may later be linked to an online account explicitly. Deleting a profile requires confirmation and offers a backup first.
- **Backup and restore:** export profile data (or the whole DB) to a versioned, checksummed archive (e.g., zip with `manifest.json`, schema version, app version, SHA-256); restore **validates** the archive (structure, checksum, schema compatibility, size limits, safe extraction with path-traversal protection) and **never overwrites current data without making an automatic pre-restore backup and getting explicit confirmation**. Use SQLite's online backup API (or `VACUUM INTO`) rather than copying a live file. Test round-trips, corrupted archives, and newer-schema archives.
- **Windows packaging:** provide a PyInstaller `.spec` (one-folder mode preferred for startup speed and reliability; document one-file tradeoffs), including data files, hidden imports, Django templates/static (run `collectstatic` into the bundle), fonts, and version metadata; a `build_windows.ps1` script; an optional installer recipe (e.g., Inno Setup script) as a documented extra; and `docs/DESKTOP_BUILD.md` covering prerequisites (Python version, WebView2 runtime), build, signing notes, antivirus false-positive notes, and troubleshooting. **If you cannot build or test a Windows executable in your environment, say so explicitly**, still provide the reproducible workflow, and add a GitHub Actions `windows-latest` job that builds the artifact and runs a smoke test (launch, wait for the health endpoint, shutdown), reporting its status honestly.
- Test the desktop logic that can be tested headlessly (paths, port selection, readiness polling, single-instance lock, backup/restore, token/Host validation) with automated tests, separately from the GUI.

## 9. Phases, deliverables, and acceptance criteria

### Phase 1: Core website
**Deliverables:** project skeleton and settings split; `typing_engine` with tests; timed and word-count tests in English, Dari, Pashto; difficulty, punctuation, numbers options; live feedback; results page with WPM, accuracy, mistakes, elapsed time, personal bests, and speed-over-time chart; accounts (register/login/logout/password reset/profile); history and dashboard with filters and charts; practice vs ranked session model and server-side validation scaffolding; themes, font size, sounds; responsive and accessible UI; Django admin configuration; seed data command; README, `.env.example`, `.gitignore`, LICENSE, CI.
**Acceptance criteria:**
- `python manage.py migrate && python manage.py seed_demo_data && python manage.py runserver` yields a working site; a guest completes a test in each language and sees correct results.
- The timer starts only at the first input; all durations/word counts work; restart/try-again work without interfering with typing.
- RTL passages render connected, correctly shaped text; caret/position tracking is correct; IME composition does not corrupt scoring (documented manual test plus automated tests where feasible, e.g., Playwright/Selenium in CI for at least the happy path).
- Scoring unit tests cover the formulas in `docs/SCORING.md`, including edge cases and Unicode (NFC vs NFD input, ZWNJ, Persian vs Arabic letter forms, combining marks).
- Authenticated results persist; another user cannot view them (permission tests); filters and personal bests are correct (tests with fixed data).
- Ranked-session issuance and server recomputation work, and tampered logs are rejected (tests).
- Test suite passes in CI; lint/format (ruff, black or equivalent) pass; no secrets committed.

### Phase 2: Learning and engagement
**Deliverables:** lessons with progress and completion rules; visual keyboard with finger guidance and documented layouts; weak-key tracking and targeted practice; custom text and safe `.txt` import; daily goals, timezone-correct streaks, achievements, and badges; expanded starter content with review-status flags.
**Acceptance criteria:** lesson unlocking/completion logic is tested; keyboard layout data is validated by tests (no duplicate/missing keys, each language/layout has documented source and verification status); streak tests cover midnight boundaries, DST, and timezone changes; upload tests cover oversized files, wrong encodings, binary content, and malicious filenames; achievements unlock only by real data.

### Phase 3: Offline desktop
**Deliverables:** desktop launcher, local profiles, backup/restore, offline asset bundle, PyInstaller spec and build script, desktop settings and security hardening, docs.
**Acceptance criteria:** the app launches from source via `python -m desktop` with a pywebview window; works offline; data lives in the user-data directory; second launch is handled; random port and token/Host protections tested; migrations run on first launch and on upgrade with automatic pre-migration backup; backup/restore round-trip tests pass; Windows build instructions are reproducible and the CI Windows job (or an honest statement of why it could not run) is included.

### Phase 4: Community, teachers, sync, multiplayer
**Deliverables:**
- **Leaderboards** separated by language, test mode, duration, and difficulty, fed only by validated ranked results, with time-window filters and moderation hooks.
- **Daily challenges** with identical conditions for everyone (same seeded passage, language, mode, duration, difficulty, time window defined in UTC with display in the user's timezone).
- **Suspicious-result handling:** scoring flags, review queue, shadow-hide pending review, audit log; documentation that cheating cannot be fully prevented.
- **Teacher features:** teacher role, classes, join codes/invitations, student enrollment, assigned exercises/lessons with due dates, class progress views. **Strict permission checks:** students see only their own data; teachers see only students enrolled in their own classes (and only the data students have consented to share, documented); no cross-class or cross-teacher access; tests for each boundary (IDOR tests).
- **Optional desktop sync:** explicit online sign-in; sync only the user's own data; idempotent uploads using client-generated UUIDs to prevent duplicates; per-record `updated_at`/version fields with a documented conflict policy (e.g., append-only results merge, last-writer-wins for settings with timestamps, tombstones for deletions); retry-safe and resumable; **offline-created results are marked `source=desktop_offline` and are never eligible for ranked leaderboards**; ranked results require a live validated online session.
- **Real-time multiplayer races:** use Django Channels (ASGI, e.g., Daphne/Uvicorn) with Redis as the channel layer; room creation/join, synchronized start (server-authoritative countdown and passage), progress broadcasting with rate limits, server-side validation of finishing results, reconnect handling, and cleanup of abandoned rooms. Document the additional infrastructure (Redis, ASGI server, reverse-proxy WebSocket config, scaling limits) in `docs/MULTIPLAYER.md`. Provide tests with Channels' testing utilities.
**Acceptance criteria:** permission, validation, sync-idempotency, and conflict tests pass; leaderboards show only validated, non-hidden ranked results; two clients can complete a race locally using the documented setup; anything not completed is clearly marked in the roadmap rather than hidden.

## 10. Security and configuration requirements

- Environment-based configuration (`.env` loaded via `django-environ` or equivalent); no secrets in code; `DEBUG=False` by default in production settings; `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, HTTPS-related settings (`SECURE_SSL_REDIRECT`, HSTS, secure cookies) in `prod.py`; `python manage.py check --deploy` passes (or remaining warnings are documented).
- Content-Security-Policy and other security headers; output escaping; parameterized queries (ORM); file-upload validation; login/reset rate limiting; admin URL not left at a trivially guessable path in production (optional) and 2FA recommended in docs.
- Static files: WhiteNoise or documented Nginx setup; Gunicorn for WSGI deployments; a sample `Dockerfile`/`docker-compose.yml` (web + PostgreSQL, plus Redis for Phase 4) and deployment notes.
- Logging configuration appropriate for web and desktop; no sensitive data in logs.

## 11. Repository, documentation, testing, and CI

- **`.gitignore`:** exclude `.env`, virtualenvs, `__pycache__`, `*.sqlite3`, `db.sqlite3`, user-data/backups, `build/`, `dist/`, `*.spec` outputs as appropriate (keep the committed `.spec`), static collection output, logs, IDE files, and any private data.
- **`.env.example`** with every variable documented; no real values.
- **Management commands:** `seed_demo_data` (clearly labeled demo content and demo users with documented demo credentials only in dev; never in production), `import_passages`, `export_passages`, `create_local_profile` (desktop), and `recompute_results` (validation tool).
- **README:** overview with screenshots only if you actually generated them; installation; local development; running tests; architecture overview with an app/module diagram; scoring summary linking to `docs/SCORING.md`; keyboard-layout and language-review notes; desktop packaging; website deployment (Gunicorn/PostgreSQL/Docker); security notes; roadmap/status table; contributing; rename-the-project instructions.
- **License:** include MIT (or Apache-2.0) with a note on the assumption (permissive license suitable for a portfolio) and a note that bundled fonts/third-party assets have their own licenses; add `THIRD_PARTY_LICENSES.md`. Mention that the user can change the license.
- **Tests (pytest + pytest-django):** scoring and Unicode (unit); permissions and IDOR; result persistence and ranked validation; accounts flows; dashboard filters and records; lessons and streak logic; upload safety; desktop helpers; and end-to-end browser tests for the main typing flow (Playwright preferred) in CI. Provide coverage reporting with honest numbers.
- **CI (`.github/workflows/ci.yml`):** matrix over supported Python versions; install dependencies with caching; ruff/black/isort checks; `manage.py check` and `makemigrations --check`; test suite on SQLite and PostgreSQL service; browser tests; separate Windows job for desktop build/smoke test. Status badges only if the workflow exists.

## 12. Reporting requirements

After each phase and at the very end, produce a report with these sections, using real results only:
1. **Implemented** (feature list mapped to the requirements)
2. **Tested** (exact commands run, pass/fail counts, what was manually verified, what could not be verified and why)
3. **Outstanding / partial / blocked** (with reasons and next steps)
4. **Assumptions and decisions** (link to `docs/DECISIONS.md`)
5. **How to run it** (copy-paste commands for Windows PowerShell and for a Unix-like shell)

Begin now: inspect the workspace, record your plan briefly in `docs/ROADMAP.md`, then build the Phase 1 vertical slice, test it, and continue through the phases without stopping to ask unnecessary questions.
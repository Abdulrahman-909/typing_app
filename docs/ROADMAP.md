# Requirement status — v0.1.0
The original requested specification is preserved verbatim in SPECIFICATION.md. This is a development release; a phase being partial does not imply its working features are placeholders.

| Section | Status | Implemented and remaining |
|---|---|---|
| 0 workflow | done | Workspace inspected; source, tests, decisions, status and reports included. |
| 1 stack | partial | Django 5.2/Python 3.12, settings split, SQLite/Postgres config, templates, local assets, Waitress, pywebview/PyInstaller recipes. Windows compatibility needs native build verification; desktop dependencies are compatible ranges, not fully locked. |
| 2 architecture | done | Pure scoring, thin views, services, domain apps, desktop separation. Community features grouped in one app instead of four small apps. |
| 3.1 test modes | partial | All requested lengths/languages, difficulty datasets, punctuation/numbers, server-held random targets. Difficulty uses curated tiers rather than measured frequency metadata; Persian digit option and deterministic exported random seeds are not implemented. Timed target is 2,000 words, exceeding practical 120-second human tests rather than an infinite stream. |
| 3.2 scoring | partial | Documented formulas, NFC/graphemes, strict variants, replay, corrected-error accuracy, per-second chart, monotonic timing. Early spaces are positional errors rather than word skipping. Full native IME edge-case coverage is outstanding. |
| 3.3 UI | partial | English character feedback, intact RTL word feedback, active-word underline, input composition handling, fonts, timer, restart/retry. Exact RTL character-position caret is not implemented. Escape blurs; shortcut customization is not implemented. |
| 3.4 ranked | partial | Signed browser/account-bound expiring sessions, replay, consumed nonce, observed-duration checks, flagged review, synthetic-score rejection. Physical-input authenticity cannot be proven; advanced statistical detection and start handshake are not implemented. |
| 3.5 custom text | partial | Private text and UTF-8 .txt import, size/content validation, normalized whitespace and controls, escaping. Language is manually selected rather than heuristically detected. |
| 4 accounts | partial | Custom user, registration/login/reset, preferences, password validation, CSRF, baseline per-process throttling, dashboards, filters. Guest result import, avatars, account export/deletion, shared-cache rate limiting are not implemented. |
| 4 goals | partial | Minute goals, historical goal snapshots, local-date streaks, deterministic earned badges. Test-count/word-count goals and admin-managed badge definitions are not implemented. |
| 5 learning | partial | Starter curricula, lesson unlocking/completion, local and online progress, basic keyboard guide, weak-character practice. Full advanced curriculum, measured latency/bigrams and Shift/AltGr layers are not implemented. Native keyboard verification is required. |
| 6 UX | partial | Responsive CSS, themes, preferences, reduced motion, focus states, labels, text/error indicators, useful empty states. Automated axe/WCAG certification and physical mobile/IME testing have not been performed. |
| 7 admin | partial | Passages/languages via choices, lessons, reports, classes, sessions, review queues, audited ranking actions; JSON import/export CLI. Dedicated CSV admin import/export and data-managed badges are not implemented. |
| 8 desktop | partial | User-data paths, migrations/upgrade backups, lock, random port/token, Host gate, offline assets, profiles, local progress, CLI backup/restore, spec/build script/smoke. No Windows binary or GUI verification; second launch notifies via console; PINs, friendly GUI startup errors, system-zone detection and backup GUI are not implemented. |
| 9 Phase 1 | partial | Core website works and has passing tests/browser checks. Remaining core items above are explicit. |
| 9 Phase 2 | partial | Learning/engagement flows work; verified multilingual keyboard curriculum remains outstanding. |
| 9 Phase 3 | partial | Headless desktop lifecycle and backup tests pass; native Windows GUI/build is blocked by Linux host. |
| 9 Phase 4 | partial | Leaderboards, daily practice, classes, one-way imports, basic races implemented and tested. Full sync/reconnect/operational hardening remains. |
| 10 deployment | partial | Production security checks pass with production env; Docker/Postgres/Redis configurations included. Live deployment, HTTPS proxy, SMTP and load tests not run. |
| 11 repository/CI | partial | README, license, env example, migrations, JSON data tools, tests, CI incl. Postgres/Windows/browser jobs. CI is not executed remotely. recompute_results is intentionally omitted because raw logs are not persisted; server replays before saving. |
| 12 reports | done | VERIFICATION.md records commands, observed outcomes and unverified items. |

## Phase 4 detail
- Leaderboards: approved online scores only, language/duration/difficulty/time-window filters; not fully unique-person ranking (multiple attempts may appear). Word mode can be filtered by query parameter; UI defaults to timed mode.
- Daily challenge: same stored 25-word passage per language/UTC day. Currently practice only, with no dedicated daily leaderboard.
- Classes: teacher group/staff creation, join code, explicit consent, due-date assignments, permission-scoped completion counts. Invitations/email, per-student detailed analytics and roster administration remain.
- Sync: explicit HTTPS token-authorized immutable result import, UUID deduplication, batches/retry by rerun, separate unranked import view. No bidirectional settings sync, tombstones, conflict UI or automatic background retry.
- Races: authenticated rooms, countdown, server replay, state broadcast, reconnect to room state and expiry cleanup. Typed buffer recovery, room quotas, per-user global limits and large-scale/load testing remain.

## Next release priorities
1. Build and test the Windows artifact on clean Windows 10/11 machines, including WebView2 and installer behavior.
2. Verify Dari/Pashto mappings with a native keyboard user; add missing Pashto letters and Shift/AltGr layers.
3. Expand parity/IME/browser/accessibility tests and harden abuse controls before public ranking.
4. Add account data export/deletion, fully editable achievements and a backup GUI.
5. Expand sync and race recovery with explicit versioned protocols and load testing.

# Architecture
Browser templates + vanilla JS → Django views → practice services → pure Python scoring → SQLite/PostgreSQL.

- accounts: custom user, registration, profile, Django authentication views.
- practice: passages, signed session issuance/replay, results, admin moderation, import/export.
- lessons: curriculum and progress, local profiles.
- dashboard: read-only owner-scoped statistics and charts.
- challenges: leaderboard filtering and moderation audit records.
- community: classrooms, consented enrollment, daily passages, token-authorized offline imports, race rooms and consumers.
- desktop: per-user paths, lock, migrations, backup/restore, Waitress, WebView launcher.
- typing_engine: pure normalization, score and replay functions.

Results reference their owner, or a desktop local profile. Result detail queries always start with the current owner/profile scope. Teachers can see only completion counts for lessons assigned in their own classes. Offline imported scores are in a distinct model and cannot become ranked entries.

WebSockets use session authentication and allowed-origin validation in the ASGI router. Redis is the production group transport; development uses a single-process in-memory layer. Race progress is recomputed from logs. Race times start at a server-defined countdown rather than each participant's first input.

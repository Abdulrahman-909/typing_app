# Multiplayer
Install requirements/dev.txt. Migrate and seed content, then run:

```
daphne -b 127.0.0.1 -p 8000 config.asgi:application
```

Create two accounts in separate browsers, create a room under /races/, share the room URL, then let the host start. The server announces a three-second countdown, validates membership, and replays progress logs. Results are room-local and are not ranked leaderboard scores. The two-client consumer test exercises start and both finishes.

Production: use config.settings.prod, Redis through REDIS_URL, and Daphne behind an HTTPS reverse proxy with WebSocket Upgrade forwarding. Ensure ALLOWED_HOSTS contains the actual host. Do not use the in-memory channel layer across processes. Run cleanup_activity periodically to remove hour-old rooms and abandoned sessions.

Scope limits: progress snapshots are rate-limited per socket (150 ms), but there is no load test or global socket quota. Reconnect reloads room state; the local typed buffer is not recovered. Room size is not capped in this release. Composition behavior in races needs native IME review. Use for friendly practice, not high-stakes competition.

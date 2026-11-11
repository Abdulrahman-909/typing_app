# Explicit offline import
Sign into the website, open /sync/, and create a token. It expires after 30 days; a new token replaces prior tokens. Token hashes, not plaintext secrets, are stored server-side.

On the desktop source installation:
```
python -m desktop.sync https://your-domain.example --profile 1
```
The token is requested through a hidden prompt, not a command-line argument. Only the selected local profile's result ID, speed, accuracy and language are transmitted. Uploads use HTTPS, reject redirects, and send batches of 100. Re-running resumes safely because (owner, client UUID) is unique. First accepted payload wins for immutable result IDs. Revocation is available on the website.

Imports appear on /sync/ separately from verified online progress. They cannot enter leaderboards. This is one-way results import, not full bidirectional sync: settings, deletions, conflict editing, automatic retries and linked-profile UI are outstanding.

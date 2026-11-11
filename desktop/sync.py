"""Explicit one-way append-only upload of a selected local profile's results."""

import argparse
import getpass
import json
import sqlite3
import urllib.request
import urllib.parse
from .paths import data_dir


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("server")
    parser.add_argument("--profile", type=int, required=True)
    args = parser.parse_args()
    parsed = urllib.parse.urlparse(args.server)
    if parsed.scheme != "https" or not parsed.netloc or parsed.username:
        raise SystemExit("Use your HTTPS website URL.")
    token = getpass.getpass("Paste your online sync token (hidden): ")
    with sqlite3.connect(data_dir() / "data.sqlite3") as c:
        rows = c.execute(
            "SELECT id,wpm,accuracy,language FROM practice_result WHERE local_profile_id=?",
            (args.profile,),
        ).fetchall()
    for start in range(0, len(rows), 100):
        results = [
            dict(zip(["id", "wpm", "accuracy", "language"], row))
            for row in rows[start : start + 100]
        ]
        request = urllib.request.Request(
            args.server.rstrip("/") + "/api/sync/",
            data=json.dumps({"results": results}).encode(),
            headers={"Content-Type": "application/json", "Authorization": "Bearer " + token},
        )

        # Refuse redirects so credentials cannot follow an unexpected destination.
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, *a, **kw):
                return None

        with urllib.request.build_opener(NoRedirect).open(request, timeout=30) as response:
            print(response.read().decode())
    print("Upload complete. Re-running is safe: result IDs prevent duplicates.")


if __name__ == "__main__":
    main()

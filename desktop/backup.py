"""Consistent SQLite backups and validated, non-extracting restoration."""

import hashlib
import json
import sqlite3
import tempfile
import zipfile
import os
from pathlib import Path
from datetime import datetime, timezone

MAX_SIZE = 100 * 1024 * 1024


def backup(database, destination):
    database = Path(database)
    destination = Path(destination)
    with tempfile.TemporaryDirectory() as temp:
        snapshot = Path(temp) / "data.sqlite3"
        with sqlite3.connect(database) as source, sqlite3.connect(snapshot) as target:
            source.backup(target)
        content = snapshot.read_bytes()
        manifest = {
            "format": 1,
            "app_version": "0.1.0",
            "sha256": hashlib.sha256(content).hexdigest(),
        }
        with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("manifest.json", json.dumps(manifest))
            archive.writestr("data.sqlite3", content)
    return destination


def validate(archive):
    with zipfile.ZipFile(archive) as z:
        if sorted(z.namelist()) != ["data.sqlite3", "manifest.json"]:
            raise ValueError("Unexpected archive members")
        if (
            z.getinfo("manifest.json").file_size > 4096
            or z.getinfo("data.sqlite3").file_size > MAX_SIZE
        ):
            raise ValueError("Backup exceeds size limit")
        manifest = json.loads(z.read("manifest.json"))
        content = z.read("data.sqlite3")
    if manifest.get("format") != 1 or manifest.get("app_version") != "0.1.0":
        raise ValueError("Unsupported backup version")
    if hashlib.sha256(content).hexdigest() != manifest.get("sha256"):
        raise ValueError("Backup checksum mismatch")
    if not content.startswith(b"SQLite format 3\x00"):
        raise ValueError("Invalid SQLite database")
    return content


def restore(database, archive, confirmed=False):
    if not confirmed:
        raise ValueError("Explicit confirmation required")
    database = Path(database)
    content = validate(archive)
    with tempfile.TemporaryDirectory(dir=database.parent) as temp:
        candidate = Path(temp) / "candidate.sqlite3"
        candidate.write_bytes(content)
        with sqlite3.connect(candidate) as conn:
            if conn.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise ValueError("Database integrity check failed")
            incoming = set(conn.execute("SELECT app,name FROM django_migrations"))
        if database.exists():
            with sqlite3.connect(database) as conn:
                existing = set(conn.execute("SELECT app,name FROM django_migrations"))
            if not incoming.issubset(existing):
                raise ValueError("Backup uses a newer schema")
            backup(
                database,
                database.with_name(
                    "pre-restore-" + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f") + ".zip"
                ),
            )
        os.replace(candidate, database)

import sqlite3
import zipfile
import json
import pytest
from desktop.backup import backup, restore, validate


def database(path):
    with sqlite3.connect(path) as c:
        c.execute("CREATE TABLE django_migrations(app text,name text)")
        c.execute("INSERT INTO django_migrations VALUES ('app','0001')")
        c.execute("CREATE TABLE data(value text)")
        c.execute("INSERT INTO data VALUES ('original')")


def test_roundtrip(tmp_path):
    db = tmp_path / "db"
    database(db)
    archive = backup(db, tmp_path / "backup.zip")
    with sqlite3.connect(db) as c:
        c.execute("UPDATE data SET value='changed'")
    restore(db, archive, confirmed=True)
    with sqlite3.connect(db) as c:
        assert c.execute("SELECT value FROM data").fetchone()[0] == "original"
    assert list(tmp_path.glob("pre-restore-*.zip"))


def test_requires_confirmation(tmp_path):
    with pytest.raises(ValueError, match="confirmation"):
        restore(tmp_path / "db", "x")


def test_traversal_rejected(tmp_path):
    path = tmp_path / "bad.zip"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("../data.sqlite3", "bad")
    with pytest.raises(ValueError):
        validate(path)


def test_checksum_rejected(tmp_path):
    path = tmp_path / "bad.zip"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr(
            "manifest.json", json.dumps({"format": 1, "app_version": "0.1.0", "sha256": "bad"})
        )
        z.writestr("data.sqlite3", "bad")
    with pytest.raises(ValueError, match="checksum"):
        validate(path)


def test_new_schema_rejected(tmp_path):
    db = tmp_path / "db"
    other = tmp_path / "new"
    database(db)
    database(other)
    with sqlite3.connect(other) as c:
        c.execute("INSERT INTO django_migrations VALUES ('app','0002')")
    archive = backup(other, tmp_path / "new.zip")
    with pytest.raises(ValueError, match="newer schema"):
        restore(db, archive, confirmed=True)


@pytest.mark.django_db
def test_local_gate(settings, rf):
    from desktop.middleware import LocalGate
    from django.http import HttpResponse

    settings.DESKTOP_PORT = 12345
    settings.DESKTOP_TOKEN = "secret"
    gate = LocalGate(lambda r: HttpResponse("ok"))
    r = rf.get("/", HTTP_HOST="127.0.0.1:12345")
    r.session = {}
    assert gate(r).status_code == 403
    r.session = {"desktop_access": "secret"}
    assert gate(r).status_code == 200
    r.META["HTTP_HOST"] = "evil.test:12345"
    assert gate(r).status_code == 403

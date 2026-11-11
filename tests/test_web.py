import json
from datetime import timedelta
import pytest
from django.core.management import call_command
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from apps.practice.models import TestSession, Result

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def content():
    call_command("seed_demo_data", verbosity=0)


def issue(client, **kw):
    r = client.post(
        "/api/start/",
        data=json.dumps({"language": "en", "mode": "time", "amount": 15, **kw}),
        content_type="application/json",
    )
    assert r.status_code == 200, r.content
    data = r.json()
    TestSession.objects.filter(id=data["id"]).update(
        created_at=timezone.now() - timedelta(seconds=16)
    )
    return data


def finish(client, s, **kw):
    return client.post(
        "/api/submit/",
        data=json.dumps(
            {
                "token": s["token"],
                "elapsed": 15,
                "events": [{"t": 0, "v": s["target"][0], "kind": "insertText"}],
                **kw,
            }
        ),
        content_type="application/json",
    )


@pytest.mark.parametrize("language", ["en", "fa", "ps"])
def test_guest_complete(client, language):
    s = issue(client, language=language)
    r = finish(client, s)
    assert r.status_code == 200 and r.json()["saved"] is False
    assert Result.objects.count() == 0 and TestSession.objects.count() == 0


@pytest.mark.parametrize("amount", [15, 30, 60, 120])
def test_durations(client, amount):
    assert issue(client, amount=amount)["amount"] == amount


@pytest.mark.parametrize("amount", [10, 25, 50, 100])
def test_word_lengths(client, amount):
    assert len(issue(client, mode="words", amount=amount)["target"].split()) == amount


def test_login_save_and_isolation(client, django_user_model):
    user = django_user_model.objects.create_user("owner", password="long-test-password")
    other = django_user_model.objects.create_user("other", password="long-test-password")
    client.force_login(user)
    s = issue(client)
    r = finish(client, s)
    assert r.status_code == 200
    result = Result.objects.get()
    assert result.owner == user
    assert client.get(f"/results/{result.id}/").status_code == 200
    assert finish(client, s).status_code == 400
    client.force_login(other)
    assert client.get(f"/results/{result.id}/").status_code == 404


def test_foreign_session(client):
    s = issue(client)
    assert finish(Client(), s).status_code == 400


def test_tampered_signature(client):
    s = issue(client)
    s["token"] += "tamper"
    assert finish(client, s).status_code == 400


def test_tampered_duration(client):
    s = issue(client)
    assert finish(client, s, elapsed=999).status_code == 400


def test_ranked_guest_rejected(client):
    r = client.post("/api/start/", json.dumps({"ranked": True}), content_type="application/json")
    assert r.status_code == 400


def test_ranked_recomputed(client, django_user_model):
    client.force_login(django_user_model.objects.create_user("ranker"))
    s = issue(client, ranked=True)
    r = finish(client, s, wpm=900)
    assert r.status_code == 200 and r.json()["metrics"]["wpm"] != 900
    assert Result.objects.get().ranked


@pytest.mark.parametrize(
    "name,data",
    [("x.exe", b"hello"), ("x.txt", b"\x00abcde"), ("x.txt", b"\xffbad"), ("x.txt", b"a" * 102401)],
)
def test_bad_upload(client, name, data):
    assert client.post("/api/upload/", {"file": SimpleUploadedFile(name, data)}).status_code == 400


def test_valid_upload(client):
    r = client.post(
        "/api/upload/", {"file": SimpleUploadedFile("words.txt", "کتاب خوب است".encode())}
    )
    assert r.status_code == 200


def test_lesson_lock(client):
    from apps.lessons.models import Lesson

    lesson = Lesson.objects.filter(language="en", order=2).get()
    assert (
        client.post(
            "/api/start/", json.dumps({"lesson": lesson.pk}), content_type="application/json"
        ).status_code
        == 400
    )


def test_page_routes(client):
    for path in [
        "/",
        "/lessons/",
        "/leaderboard/",
        "/accounts/login/",
        "/accounts/register/",
        "/accounts/password_reset/",
    ]:
        r = client.get(path)
        assert r.status_code == 200, (path, r.status_code)


def test_csrf():
    c = Client(enforce_csrf_checks=True)
    assert c.post("/api/start/", "{}", content_type="application/json").status_code == 403


def test_profile_timezone_validation(client, django_user_model):
    client.force_login(django_user_model.objects.create_user("zone"))
    r = client.post(
        "/accounts/profile/", {"timezone": "Not/AZone", "daily_goal": 5, "preferred_language": "en"}
    )
    assert b"Use an IANA timezone" in r.content


def test_idempotent_seed():
    from apps.practice.models import Passage

    call_command("seed_demo_data")
    assert Passage.objects.count() == 9

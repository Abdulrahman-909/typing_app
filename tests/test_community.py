import json
import hashlib
import uuid
from datetime import timedelta
import pytest
from django.utils import timezone
from django.core.management import call_command
from apps.community.models import (
    Classroom,
    Enrollment,
    SyncToken,
    SyncedResult,
    Race,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def people(django_user_model):
    return [django_user_model.objects.create_user(n) for n in ["teacher", "student", "stranger"]]


def test_class_permissions(client, people):
    teacher, student, stranger = people
    room = Classroom.objects.create(teacher=teacher, title="Room")
    Enrollment.objects.create(classroom=room, student=student)
    client.force_login(stranger)
    assert client.get(f"/classes/{room.pk}/").status_code == 403
    assert client.post("/classes/", {"title": "Fake"}).status_code == 403
    client.force_login(student)
    assert client.get(f"/classes/{room.pk}/").status_code == 200
    assert (
        client.post(f"/classes/{room.pk}/", {"lesson": 1, "due": "2026-12-01"}).status_code == 403
    )
    client.force_login(teacher)
    assert client.get(f"/classes/{room.pk}/").status_code == 200


def test_join_requires_consent(client, people):
    teacher, student, _ = people
    room = Classroom.objects.create(teacher=teacher, title="Room")
    client.force_login(student)
    client.post("/classes/", {"code": room.code})
    assert not Enrollment.objects.exists()
    client.post("/classes/", {"code": room.code, "consent": "yes"})
    assert Enrollment.objects.count() == 1
    client.post(f"/classes/{room.pk}/", {"leave": "yes"})
    assert not Enrollment.objects.exists()


def test_sync_idempotent_and_unranked(client, people):
    user = people[1]
    SyncToken.objects.create(
        owner=user,
        digest=hashlib.sha256(b"token").hexdigest(),
        expires=timezone.now() + timedelta(days=1),
    )
    payload = {
        "results": [
            {
                "id": str(uuid.uuid4()),
                "language": "en",
                "wpm": 40,
                "accuracy": 99,
                "ranked": True,
                "owner": people[0].pk,
            }
        ]
    }
    for _ in range(2):
        assert (
            client.post(
                "/api/sync/",
                json.dumps(payload),
                content_type="application/json",
                HTTP_AUTHORIZATION="Bearer token",
            ).status_code
            == 200
        )
    item = SyncedResult.objects.get()
    assert item.owner == user and item.payload["ranked"] is False
    assert (
        client.post(
            "/api/sync/",
            json.dumps(payload),
            content_type="application/json",
            HTTP_AUTHORIZATION="Bearer bad",
        ).status_code
        == 403
    )


def test_daily_stable(client):
    call_command("seed_demo_data")
    client.get("/daily/")
    client.get("/daily/")
    from apps.community.models import DailyChallenge

    assert DailyChallenge.objects.count() == 1


def test_unapproved_not_on_board(client, people):
    from apps.practice.models import Result

    Result.objects.create(
        owner=people[0],
        language="en",
        mode="time",
        amount=30,
        difficulty="easy",
        wpm=90,
        accuracy=99,
        local_date=timezone.now().date(),
        ranked=True,
        review_status="pending",
    )
    assert b"teacher" not in client.get("/leaderboard/").content


def test_race_join_boundary(client, people):
    race = Race.objects.create(host=people[0], target="hello", starts_at=timezone.now())
    client.force_login(people[1])
    assert client.get(f"/races/{race.pk}/").status_code == 403

import pytest
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo
from django.utils import timezone as django_timezone
from apps.practice.models import Result

pytestmark = pytest.mark.django_db


def test_timezone_midnight():
    instant = datetime(2026, 1, 1, 20, 0, tzinfo=timezone.utc)
    assert instant.astimezone(ZoneInfo("Asia/Kabul")).date() == date(2026, 1, 2)


def test_dst_dates():
    before = datetime(2026, 3, 8, 6, 59, tzinfo=timezone.utc)
    after = datetime(2026, 3, 8, 7, 1, tzinfo=timezone.utc)
    zone = ZoneInfo("America/New_York")
    assert before.astimezone(zone).date() == after.astimezone(zone).date()
    assert before.astimezone(zone).hour == 1 and after.astimezone(zone).hour == 3


def test_goal_change_does_not_erase_streak(client, django_user_model):
    user = django_user_model.objects.create_user("goals", daily_goal=120, timezone="UTC")
    client.force_login(user)
    Result.objects.create(
        owner=user,
        language="en",
        mode="time",
        amount=60,
        difficulty="easy",
        wpm=30,
        accuracy=99,
        local_date=django_timezone.now().date(),
        goal_minutes=1,
        metrics={"elapsed": 60},
    )
    response = client.get("/dashboard/")
    assert response.context["streak"] == 1

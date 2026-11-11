import secrets
import uuid
from django.db import models
from django.conf import settings


def join_code():
    return secrets.token_urlsafe(8)


class Classroom(models.Model):
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True, default=join_code)


class Enrollment(models.Model):
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE)
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["classroom", "student"], name="one_enrollment")
        ]


class Assignment(models.Model):
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE)
    lesson = models.ForeignKey("lessons.Lesson", on_delete=models.CASCADE)
    due = models.DateField()


class DailyChallenge(models.Model):
    date = models.DateField()
    language = models.CharField(max_length=3)
    passage = models.TextField()

    class Meta:
        constraints = [models.UniqueConstraint(fields=["date", "language"], name="daily_language")]


class SyncToken(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    digest = models.CharField(max_length=64, unique=True)
    expires = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)


class SyncedResult(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    client_id = models.UUIDField(default=uuid.uuid4)
    payload = models.JSONField()
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["owner", "client_id"], name="sync_once")]


class Race(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    host = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    target = models.TextField()
    language = models.CharField(max_length=3, default="en")
    starts_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class RaceEntry(models.Model):
    race = models.ForeignKey(Race, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    progress = models.FloatField(default=0)
    result = models.JSONField(default=dict)
    finished = models.BooleanField(default=False)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["race", "user"], name="one_racer")]

import uuid
from django.conf import settings
from django.db import models


class Passage(models.Model):
    LANGUAGES = [("en", "English"), ("fa", "Dari"), ("ps", "Pashto")]
    title = models.CharField(max_length=120)
    language = models.CharField(max_length=3, choices=LANGUAGES)
    text = models.TextField()
    difficulty = models.CharField(max_length=10, default="easy")
    active = models.BooleanField(default=True)
    review_status = models.CharField(
        max_length=12,
        default="unreviewed",
        choices=[("unreviewed", "Unreviewed"), ("reviewed", "Reviewed")],
    )
    source = models.CharField(max_length=200, default="Original project content")
    license = models.CharField(max_length=60, default="MIT")

    def __str__(self):
        return self.title


class TestSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE
    )
    browser_key = models.CharField(max_length=64)
    target = models.TextField()
    language = models.CharField(max_length=3)
    mode = models.CharField(max_length=8)
    amount = models.PositiveIntegerField()
    difficulty = models.CharField(max_length=10)
    ranked = models.BooleanField(default=False)
    consumed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    lesson = models.ForeignKey("lessons.Lesson", null=True, blank=True, on_delete=models.SET_NULL)


class Result(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE
    )
    local_profile = models.ForeignKey(
        "lessons.LocalProfile", null=True, blank=True, on_delete=models.CASCADE
    )
    session = models.OneToOneField(TestSession, null=True, on_delete=models.SET_NULL)
    language = models.CharField(max_length=3)
    mode = models.CharField(max_length=8)
    amount = models.PositiveIntegerField()
    difficulty = models.CharField(max_length=10)
    wpm = models.FloatField()
    accuracy = models.FloatField()
    metrics = models.JSONField(default=dict)
    samples = models.JSONField(default=list)
    errors = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    local_date = models.DateField()
    goal_minutes = models.PositiveSmallIntegerField(default=5)
    source = models.CharField(max_length=20, default="web")
    ranked = models.BooleanField(default=False)
    review_status = models.CharField(max_length=12, default="unranked")
    flag_reason = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]


class Report(models.Model):
    passage = models.ForeignKey(Passage, on_delete=models.CASCADE)
    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    reason = models.CharField(max_length=500)
    resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

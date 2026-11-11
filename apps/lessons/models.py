from django.db import models
from django.conf import settings


class Lesson(models.Model):
    title = models.CharField(max_length=100)
    language = models.CharField(max_length=3, default="en")
    order = models.PositiveIntegerField(default=1)
    text = models.TextField()
    instruction = models.TextField()
    min_accuracy = models.PositiveIntegerField(default=90)
    min_wpm = models.PositiveIntegerField(default=10)
    review_status = models.CharField(max_length=12, default="unreviewed")

    class Meta:
        ordering = ["language", "order"]

    def __str__(self):
        return self.title


class LocalProfile(models.Model):
    name = models.CharField(max_length=60, unique=True)
    timezone = models.CharField(max_length=64, default="Asia/Kabul")


class LessonProgress(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE
    )
    local_profile = models.ForeignKey(LocalProfile, null=True, blank=True, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    attempts = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["local_profile", "lesson"], name="unique_local_lesson"),
            models.UniqueConstraint(fields=["user", "lesson"], name="unique_lesson_progress"),
        ]

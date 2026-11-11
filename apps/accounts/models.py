from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    timezone = models.CharField(max_length=64, default="Asia/Kabul")
    preferred_language = models.CharField(max_length=3, default="en")
    daily_goal = models.PositiveSmallIntegerField(default=5)
    display_name = models.CharField(max_length=60, blank=True)

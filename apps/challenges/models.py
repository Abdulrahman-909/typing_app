from django.conf import settings
from django.db import models


class ModerationLog(models.Model):
    moderator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    result = models.ForeignKey("practice.Result", on_delete=models.CASCADE)
    action = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

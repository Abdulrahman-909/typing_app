from django.contrib import admin
from .models import (
    Classroom,
    Enrollment,
    Assignment,
    DailyChallenge,
    Race,
    RaceEntry,
    SyncToken,
    SyncedResult,
)

admin.site.register(
    [Classroom, Enrollment, Assignment, DailyChallenge, Race, RaceEntry, SyncToken, SyncedResult]
)

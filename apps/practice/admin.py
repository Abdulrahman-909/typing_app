from django.contrib import admin
from .models import Passage, Result, Report, TestSession
from apps.challenges.models import ModerationLog


@admin.register(Passage)
class PassageAdmin(admin.ModelAdmin):
    list_display = ["title", "language", "difficulty", "active", "review_status"]
    list_filter = ["language", "difficulty", "active", "review_status"]
    search_fields = ["title", "text"]
    list_editable = ["active", "review_status"]


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ["owner", "language", "wpm", "accuracy", "review_status", "created_at"]
    list_filter = ["review_status", "language", "mode"]
    readonly_fields = ["metrics", "session", "owner", "wpm", "accuracy", "ranked", "source"]
    actions = ["approve", "reject"]

    @admin.action(description="Approve flagged online ranked results")
    def approve(self, request, qs):
        for result in qs.filter(ranked=True, source="web", review_status="pending"):
            result.review_status = "approved"
            result.save(update_fields=["review_status"])
            ModerationLog.objects.create(moderator=request.user, result=result, action="approved")

    @admin.action(description="Reject results from ranking")
    def reject(self, request, qs):
        for result in qs:
            result.review_status = "rejected"
            result.save(update_fields=["review_status"])
            ModerationLog.objects.create(moderator=request.user, result=result, action="rejected")


admin.site.register(Report)
admin.site.register(TestSession)

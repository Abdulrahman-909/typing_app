from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta
from apps.practice.models import Result


def leaderboard(request):
    language = request.GET.get("language", "en")
    amount = request.GET.get("amount", "30")
    difficulty = request.GET.get("difficulty", "easy")
    mode = request.GET.get("mode", "time")
    qs = Result.objects.filter(
        ranked=True,
        source="web",
        review_status="approved",
        language=language,
        mode=mode,
        difficulty=difficulty,
    )
    qs = qs.filter(amount=int(amount)) if amount.isdigit() else qs.none()
    if request.GET.get("window") == "week":
        qs = qs.filter(created_at__gte=timezone.now() - timedelta(days=7))
    return render(
        request,
        "leaderboard.html",
        {"leaders": qs.select_related("owner").order_by("-wpm", "-accuracy")[:50]},
    )

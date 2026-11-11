from datetime import timedelta
from collections import Counter, defaultdict
from zoneinfo import ZoneInfo
from django.conf import settings
from django.db.models import Avg, Max
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from apps.practice.models import Result


def owned(request):
    if settings.DESKTOP:
        return Result.objects.filter(
            local_profile_id=request.session.get("local_profile"), local_profile__isnull=False
        )
    return (
        Result.objects.filter(owner=request.user)
        if request.user.is_authenticated
        else Result.objects.none()
    )


def dashboard(request):
    if not settings.DESKTOP and not request.user.is_authenticated:
        return redirect("login")
    all_results = owned(request)
    results = all_results
    for field in ["language", "mode", "difficulty"]:
        if request.GET.get(field):
            results = results.filter(**{field: request.GET[field]})
    if request.GET.get("amount", "").isdigit():
        results = results.filter(amount=int(request.GET["amount"]))
    for param, lookup in [("from", "local_date__gte"), ("to", "local_date__lte")]:
        try:
            from datetime import date

            if request.GET.get(param):
                results = results.filter(**{lookup: date.fromisoformat(request.GET[param])})
        except ValueError:
            pass
    totals = all_results.aggregate(best=Max("wpm"), accuracy=Avg("accuracy"))
    minutes = defaultdict(float)
    goals = {}
    errors = Counter()
    for r in all_results:
        goals.setdefault(r.local_date, r.goal_minutes)
        minutes[r.local_date] += r.metrics.get("elapsed", 0) / 60
        errors.update(r.errors)
    goal = request.user.daily_goal if request.user.is_authenticated else 5
    zone = request.user.timezone if request.user.is_authenticated else "Asia/Kabul"
    today = timezone.now().astimezone(ZoneInfo(zone)).date()
    day = today
    if minutes[day] < goals.get(day, goal):
        day -= timedelta(days=1)
    streak = 0
    while minutes[day] >= goals.get(day, goal):
        streak += 1
        day -= timedelta(days=1)
    badges = []
    if all_results.exists():
        badges.append("First steps")
    if streak >= 7:
        badges.append("Seven-day rhythm")
    for speed in [40, 60, 80]:
        if all_results.filter(wpm__gte=speed, accuracy__gte=95).exists():
            badges.append(str(speed) + " WPM club")
    chart = [{"t": i + 1, "wpm": r.wpm} for i, r in enumerate(reversed(list(results[:30])))]
    return render(
        request,
        "dashboard.html",
        {
            "results": results[:100],
            "total": all_results.count(),
            "totals": totals,
            "streak": streak,
            "today_minutes": round(minutes[today], 1),
            "goal": goal,
            "badges": badges,
            "weak": errors.most_common(8),
            "chart": chart,
        },
    )


def detail(request, pk):
    result = get_object_or_404(owned(request), pk=pk)
    return render(request, "result.html", {"result": result, "chart": result.samples})

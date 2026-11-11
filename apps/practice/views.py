import json
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from .services import issue, finish, clean_custom
from .models import Report, Passage
from apps.lessons.models import Lesson


def practice(request):
    return render(request, "practice.html")


@require_POST
def start(request):
    try:
        data = json.loads(request.body)
        if data.get("challenge"):
            from apps.community.models import DailyChallenge
            from django.utils import timezone

            challenge = get_object_or_404(
                DailyChallenge, pk=data["challenge"], date=timezone.now().date()
            )
            data.update(custom=challenge.passage, language=challenge.language, ranked=False)
        lesson = None
        if data.get("lesson"):
            lesson = get_object_or_404(Lesson, pk=data["lesson"])
            previous = Lesson.objects.filter(language=lesson.language, order__lt=lesson.order)
            from apps.lessons.services import completed_lessons

            completed = completed_lessons(request)
            if previous.exclude(pk__in=completed).exists():
                raise ValueError("Complete the earlier lessons first.")
        return JsonResponse(issue(request, data, lesson))
    except (ValueError, TypeError, KeyError, AttributeError) as e:
        return JsonResponse({"error": str(e)}, status=400)


@require_POST
def submit(request):
    try:
        return JsonResponse(finish(request, json.loads(request.body)))
    except (ValueError, TypeError, KeyError, AttributeError, OverflowError) as e:
        return JsonResponse({"error": str(e)}, status=400)


@require_POST
def upload(request):
    try:
        f = request.FILES.get("file")
        if not f or not f.name.lower().endswith(".txt") or f.size > 102400:
            raise ValueError("Choose a UTF-8 .txt file up to 100 KB.")
        return JsonResponse({"text": clean_custom(f.read().decode("utf-8-sig"))})
    except (ValueError, UnicodeError) as e:
        return JsonResponse({"error": str(e)}, status=400)


@login_required
def report(request, pk):
    passage = get_object_or_404(Passage, pk=pk)
    if request.method == "POST":
        reason = request.POST.get("reason", "").strip()
        if reason:
            Report.objects.create(passage=passage, reporter=request.user, reason=reason[:500])
            return redirect("practice")
    return render(request, "report.html", {"passage": passage})

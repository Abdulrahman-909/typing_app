import hashlib
import json
import secrets
import uuid
import math
from datetime import timedelta, date
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseBadRequest
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from apps.practice.services import make_target
from apps.lessons.models import Lesson, LessonProgress
from .models import (
    Classroom,
    Enrollment,
    Assignment,
    DailyChallenge,
    SyncToken,
    SyncedResult,
    Race,
    RaceEntry,
)


def is_teacher(user):
    return user.is_staff or user.groups.filter(name="teacher").exists()


@login_required
def classes(request):
    error = ""
    if request.method == "POST":
        if request.POST.get("title"):
            if not is_teacher(request.user):
                return HttpResponseForbidden("Teacher permission required.")
            classroom = Classroom.objects.create(
                teacher=request.user, title=request.POST["title"][:100]
            )
            return redirect("classroom", classroom.pk)
        classroom = Classroom.objects.filter(code=request.POST.get("code", "").strip()).first()
        if classroom and request.POST.get("consent") == "yes":
            Enrollment.objects.get_or_create(classroom=classroom, student=request.user)
            return redirect("classroom", classroom.pk)
        error = "Check the join code and consent to share your assigned lesson progress."
    return render(
        request,
        "classes.html",
        {
            "teaching": Classroom.objects.filter(teacher=request.user),
            "enrollments": Enrollment.objects.filter(student=request.user).select_related(
                "classroom"
            ),
            "teacher": is_teacher(request.user),
            "error": error,
        },
    )


@login_required
def classroom(request, pk):
    room = get_object_or_404(Classroom, pk=pk)
    teacher = room.teacher_id == request.user.pk
    if not teacher and not Enrollment.objects.filter(classroom=room, student=request.user).exists():
        return HttpResponseForbidden("You are not enrolled in this class.")
    if request.method == "POST":
        if request.POST.get("leave") and not teacher:
            Enrollment.objects.filter(classroom=room, student=request.user).delete()
            return redirect("classes")
        if not teacher:
            return HttpResponseForbidden("Only this class teacher can assign lessons.")
        try:
            lesson = Lesson.objects.get(pk=request.POST.get("lesson"))
            due = date.fromisoformat(request.POST.get("due", ""))
        except (Lesson.DoesNotExist, ValueError, TypeError):
            return HttpResponseBadRequest("Choose a lesson and due date.")
        Assignment.objects.create(classroom=room, lesson=lesson, due=due)
        return redirect("classroom", pk)
    assignments = Assignment.objects.filter(classroom=room).select_related("lesson")
    progress = []
    if teacher:
        for enrollment in Enrollment.objects.filter(classroom=room).select_related("student"):
            completed = LessonProgress.objects.filter(
                user=enrollment.student,
                completed=True,
                lesson_id__in=assignments.values_list("lesson_id", flat=True),
            ).count()
            progress.append({"name": enrollment.student.username, "completed": completed})
    return render(
        request,
        "classroom.html",
        {
            "room": room,
            "teacher": teacher,
            "assignments": assignments,
            "progress": progress,
            "lessons": Lesson.objects.all(),
        },
    )


def daily(request):
    language = request.GET.get("language", "en")
    if language not in ["en", "fa", "ps"]:
        language = "en"
    challenge, _ = DailyChallenge.objects.get_or_create(
        date=timezone.now().date(),
        language=language,
        defaults={"passage": make_target(language, "easy", 25)},
    )
    return render(request, "daily.html", {"challenge": challenge})


@login_required
def sync_settings(request):
    token = None
    if request.method == "POST":
        SyncToken.objects.filter(owner=request.user).delete()
        if request.POST.get("action") == "create":
            token = secrets.token_urlsafe(40)
            SyncToken.objects.create(
                owner=request.user,
                digest=hashlib.sha256(token.encode()).hexdigest(),
                expires=timezone.now() + timedelta(days=30),
            )
    return render(
        request,
        "sync.html",
        {
            "token": token,
            "imports": SyncedResult.objects.filter(owner=request.user).order_by("-received_at")[
                :50
            ],
        },
    )


@csrf_exempt
@require_POST
def sync_upload(request):
    # Token-only endpoint: no cookie authentication, so CSRF exemption is intentional.
    if settings.DESKTOP:
        return HttpResponseForbidden()
    token = request.headers.get("Authorization", "").removeprefix("Bearer ")
    record = (
        SyncToken.objects.filter(
            digest=hashlib.sha256(token.encode()).hexdigest(), expires__gt=timezone.now()
        )
        .select_related("owner")
        .first()
    )
    if not record:
        return HttpResponseForbidden("Invalid or expired sync token.")
    try:
        data = json.loads(request.body)
        items = data["results"]
        if not isinstance(items, list) or len(items) > 100:
            raise ValueError("Send at most 100 records.")
        normalized = []
        for item in items:
            identity = uuid.UUID(item["id"])
            wpm = float(item["wpm"])
            accuracy = float(item["accuracy"])
            if (
                not math.isfinite(wpm)
                or not 0 <= wpm <= 10000
                or not math.isfinite(accuracy)
                or not 0 <= accuracy <= 100
            ):
                raise ValueError("Invalid score")
            if item["language"] not in ["en", "fa", "ps"]:
                raise ValueError("Invalid language")
            normalized.append(
                (
                    identity,
                    {
                        "id": str(identity),
                        "wpm": wpm,
                        "accuracy": accuracy,
                        "language": item["language"],
                        "source": "desktop_offline",
                        "ranked": False,
                    },
                )
            )
        count = 0
        for identity, payload in normalized:
            _, created = SyncedResult.objects.get_or_create(
                owner=record.owner, client_id=identity, defaults={"payload": payload}
            )
            count += created
        return JsonResponse({"created": count, "accepted": len(items)})
    except (ValueError, TypeError, KeyError):
        return JsonResponse({"error": "Invalid sync payload"}, status=400)


@login_required
def races(request):
    if request.method == "POST":
        language = request.POST.get("language", "en")
        if language not in ["en", "fa", "ps"]:
            return HttpResponseBadRequest()
        race = Race.objects.create(
            host=request.user, target=make_target(language, "easy", 10), language=language
        )
        RaceEntry.objects.create(race=race, user=request.user)
        return redirect("race", race.pk)
    return render(
        request,
        "races.html",
        {
            "races": Race.objects.filter(
                created_at__gt=timezone.now() - timedelta(hours=1), starts_at__isnull=True
            )
        },
    )


@login_required
def race(request, pk):
    room = get_object_or_404(Race, pk=pk, created_at__gt=timezone.now() - timedelta(hours=1))
    if room.starts_at is None:
        RaceEntry.objects.get_or_create(race=room, user=request.user)
    if not RaceEntry.objects.filter(race=room, user=request.user).exists():
        return HttpResponseForbidden("This race has already started.")
    return render(
        request,
        "race.html",
        {
            "race": room,
            "race_config": {
                "id": str(room.id),
                "target": room.target,
                "host": room.host_id == request.user.pk,
            },
        },
    )

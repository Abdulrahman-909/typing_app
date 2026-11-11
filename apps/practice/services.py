import random
import unicodedata
import uuid
from zoneinfo import ZoneInfo
from django.utils import timezone
from django.conf import settings
from django.core import signing
from django.db import transaction
from .models import Passage, TestSession, Result
from apps.lessons.models import LocalProfile, LessonProgress
from typing_engine.scoring import replay, units


def clean_custom(text):
    if not isinstance(text, str) or len(text.encode("utf-8")) > 102400:
        raise ValueError("Text must be at most 100 KB.")
    if "\x00" in text:
        raise ValueError("Binary content is not supported.")
    text = unicodedata.normalize("NFC", text)
    text = "".join(
        c for c in text if not unicodedata.category(c).startswith("C") or c in "\n\t\u200c\u200d"
    )
    text = " ".join(text.split())
    if not 5 <= len(text) <= 12000:
        raise ValueError("Use between 5 and 12,000 characters.")
    return text


def make_target(language, difficulty, count, punctuation=False, numbers=False):
    passages = Passage.objects.filter(language=language, active=True, difficulty=difficulty)
    if not passages.exists():
        raise ValueError("No passages are available for these settings.")
    words = " ".join(passages.values_list("text", flat=True)).split()
    rng = random.Random(uuid.uuid4().int)
    selected = [rng.choice(words) for _ in range(count)]
    if punctuation:
        for i in range(4, len(selected), 6):
            selected[i] += "," if language == "en" else "،"
    if numbers:
        for i in range(7, len(selected), 10):
            selected[i] = str(rng.randint(1, 999))
    return " ".join(selected)


def issue(request, data, lesson=None):
    language = data.get("language", "en")
    mode = data.get("mode", "time")
    difficulty = data.get("difficulty", "easy")
    try:
        amount = int(data.get("amount", 30))
    except (ValueError, TypeError):
        raise ValueError("Invalid duration or word count.")
    if language not in ["en", "fa", "ps"] or difficulty not in ["easy", "medium", "hard"]:
        raise ValueError("Invalid settings.")
    if mode not in ["time", "words"] or amount not in (
        [15, 30, 60, 120] if mode == "time" else [10, 25, 50, 100]
    ):
        raise ValueError("Invalid test length.")
    ranked = bool(data.get("ranked"))
    if ranked and (not request.user.is_authenticated or settings.DESKTOP):
        raise ValueError("Ranked tests require an online account.")
    custom = data.get("custom", "")
    if data.get("weak") and request.user.is_authenticated:
        from collections import Counter

        counts = Counter()
        for previous in Result.objects.filter(owner=request.user, language=language)[:100]:
            counts.update(previous.errors)
        weak = {char for char, n in counts.most_common(5)}
        words = " ".join(
            Passage.objects.filter(language=language, active=True).values_list("text", flat=True)
        ).split()
        selected = [word for word in words if any(char in word for char in weak)]
        if not selected:
            raise ValueError("Complete a test with some mistakes first to build targeted practice.")
        custom = " ".join(random.choices(selected, k=25))
        ranked = False
    if ranked and (data.get("punctuation") or data.get("numbers")):
        raise ValueError("Ranked tests use plain words so results stay comparable.")
    if ranked and (custom or lesson):
        raise ValueError("Custom text and lessons are practice only.")
    if not request.session.session_key:
        request.session.create()
    target = (
        clean_custom(custom)
        if custom
        else make_target(
            language,
            difficulty,
            2000 if mode == "time" else amount,
            bool(data.get("punctuation")),
            bool(data.get("numbers")),
        )
    )
    if lesson:
        target = lesson.text
        language = lesson.language
        mode = "words"
        amount = len(target.split())
    if custom:
        mode = "words"
        amount = len(target.split())
    if data.get("retry"):
        try:
            old = TestSession.objects.get(id=data["retry"], browser_key=request.session.session_key)
        except (TestSession.DoesNotExist, ValueError):
            raise ValueError("Previous session not found.")
        if not ranked and not custom and not lesson:
            target = old.target
            language = old.language
            mode = old.mode
            amount = old.amount
            difficulty = old.difficulty
    s = TestSession.objects.create(
        owner=request.user if request.user.is_authenticated else None,
        browser_key=request.session.session_key,
        target=target,
        language=language,
        mode=mode,
        amount=amount,
        difficulty=difficulty,
        ranked=ranked,
        lesson=lesson,
    )
    token = signing.dumps({"id": str(s.id), "browser": s.browser_key}, salt="typing-session")
    return {
        "id": str(s.id),
        "token": token,
        "target": target,
        "language": language,
        "mode": mode,
        "amount": amount,
        "ranked": ranked,
    }


@transaction.atomic
def finish(request, data):
    try:
        token = signing.loads(data.get("token", ""), salt="typing-session", max_age=7200)
        s = TestSession.objects.select_for_update().get(
            id=token["id"], browser_key=request.session.session_key
        )
    except (signing.BadSignature, TestSession.DoesNotExist, KeyError, ValueError):
        raise ValueError("Session expired or invalid. Start another test.")
    if s.consumed:
        raise ValueError("This test was already submitted.")
    uid = request.user.pk if request.user.is_authenticated else None
    if s.owner_id != uid:
        raise ValueError("Session account changed. Start another test.")
    elapsed = float(data.get("elapsed", 0))
    events = data.get("events", [])
    if not events:
        raise ValueError("Type at least one character.")
    if s.mode == "time" and abs(elapsed - s.amount) > 0.15:
        raise ValueError("Timed test duration mismatch.")
    if s.mode == "words" and (
        events[-1].get("v") != s.target or abs(events[-1].get("t", 0) / 1000 - elapsed) > 0.15
    ):
        raise ValueError("Complete the passage before finishing.")
    metrics = replay(s.target, events, elapsed)
    observed = (timezone.now() - s.created_at).total_seconds()
    if elapsed > observed + 2:
        raise ValueError("Submitted duration exceeds session age.")
    errors = {}
    prev = []
    target_units = units(s.target)
    for e in events:
        current = units(e["v"])
        i = 0
        while i < min(len(prev), len(current)) and prev[i] == current[i]:
            i += 1
        for j, c in enumerate(current[i:], i):
            if j < len(target_units) and c != target_units[j]:
                errors[target_units[j]] = errors.get(target_units[j], 0) + 1
        prev = current
    # Derive the chart from replayed input, never trust client scores or samples.
    samples = []
    for second in range(1, int(elapsed) + 1):
        batch = [e for e in events if e["t"] <= second * 1000]
        m = replay(s.target, batch, float(second))
        samples.append({"t": second, "wpm": m["wpm"]})
    profile = None
    if settings.DESKTOP:
        profile = LocalProfile.objects.filter(pk=request.session.get("local_profile")).first()
    zone = request.user.timezone if uid else profile.timezone if profile else "UTC"
    flags = []
    if s.ranked:
        gaps = [
            b["t"] - a["t"]
            for a, b in zip(events, events[1:])
            if b["kind"] != "deleteContentBackward"
        ]
        if metrics["wpm"] > 250:
            flags.append("Speed requires review")
        if len(gaps) > 20 and sum(g < 8 for g in gaps) / len(gaps) > 0.5:
            flags.append("Unusually rapid input")
    s.consumed = True
    s.save(update_fields=["consumed"])
    result = None
    if uid or profile:
        local_day = timezone.now().astimezone(ZoneInfo(zone)).date()
        daily = Result.objects.filter(local_date=local_day)
        daily = daily.filter(owner=request.user) if uid else daily.filter(local_profile=profile)
        earlier = daily.order_by("created_at").first()
        goal = earlier.goal_minutes if earlier else (request.user.daily_goal if uid else 5)
        result = Result.objects.create(
            owner=request.user if uid else None,
            local_profile=profile,
            session=s,
            language=s.language,
            mode=s.mode,
            amount=s.amount,
            difficulty=s.difficulty,
            wpm=metrics["wpm"],
            accuracy=metrics["accuracy"],
            metrics=metrics,
            samples=samples,
            errors=errors,
            local_date=local_day,
            goal_minutes=goal,
            source="desktop_offline" if settings.DESKTOP else "web",
            ranked=s.ranked,
            review_status=("pending" if flags else "approved") if s.ranked else "unranked",
            flag_reason="; ".join(flags),
        )
        if s.lesson and (uid or profile):
            progress, _ = LessonProgress.objects.get_or_create(
                **({"local_profile": profile} if settings.DESKTOP else {"user": request.user}),
                lesson=s.lesson,
            )
            progress.attempts += 1
            progress.completed = progress.completed or (
                metrics["accuracy"] >= s.lesson.min_accuracy and metrics["wpm"] >= s.lesson.min_wpm
            )
            progress.save()
    else:
        # Guest session rows contain temporary test state only; delete after scoring.
        s.delete()
    return {
        "metrics": metrics,
        "samples": samples,
        "saved": bool(result),
        "result_id": str(result.id) if result else None,
        "review": result.review_status if result else "unranked",
    }

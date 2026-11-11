from django.shortcuts import render
from .models import Lesson


def lessons(request):
    language = request.GET.get("language", "en")
    from .services import completed_lessons

    completed = completed_lessons(request)
    cards = []
    unlocked = True
    for lesson in Lesson.objects.filter(language=language):
        cards.append({"lesson": lesson, "done": lesson.pk in completed, "unlocked": unlocked})
        unlocked = unlocked and lesson.pk in completed
    return render(request, "lessons.html", {"cards": cards, "language": language})

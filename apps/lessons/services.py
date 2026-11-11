from django.conf import settings
from .models import LessonProgress, LocalProfile


def progress_owner(request):
    if settings.DESKTOP:
        profile = LocalProfile.objects.filter(pk=request.session.get("local_profile")).first()
        return {"local_profile": profile} if profile else None
    return {"user": request.user} if request.user.is_authenticated else None


def completed_lessons(request):
    owner = progress_owner(request)
    return (
        set(
            LessonProgress.objects.filter(**owner, completed=True).values_list(
                "lesson_id", flat=True
            )
        )
        if owner
        else set()
    )

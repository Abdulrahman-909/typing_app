import pytest
from apps.lessons.models import Lesson, LocalProfile, LessonProgress
from apps.lessons.services import completed_lessons

pytestmark = pytest.mark.django_db


def test_local_progress_isolation(rf, settings):
    settings.DESKTOP = True
    a = LocalProfile.objects.create(name="A")
    b = LocalProfile.objects.create(name="B")
    lesson = Lesson.objects.create(title="Home", text="asdf")
    LessonProgress.objects.create(local_profile=a, lesson=lesson, completed=True)
    request = rf.get("/")
    request.session = {"local_profile": a.pk}
    assert completed_lessons(request) == {lesson.pk}
    request.session = {"local_profile": b.pk}
    assert completed_lessons(request) == set()

from django.contrib import admin
from .models import Lesson, LessonProgress, LocalProfile

admin.site.register([Lesson, LessonProgress, LocalProfile])

from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from apps.practice import views as p
from apps.accounts import views as a
from apps.dashboard import views as d
from apps.lessons import views as l
from apps.challenges import views as c

urlpatterns = [
    path("", p.practice, name="practice"),
    path("health/", lambda r: JsonResponse({"ok": True})),
    path("api/start/", p.start),
    path("api/submit/", p.submit),
    path("api/upload/", p.upload),
    path("passages/<int:pk>/report/", p.report, name="report"),
    path("dashboard/", d.dashboard, name="dashboard"),
    path("results/<uuid:pk>/", d.detail, name="result"),
    path("lessons/", l.lessons, name="lessons"),
    path("leaderboard/", c.leaderboard, name="leaderboard"),
    path("accounts/register/", a.register, name="register"),
    path("accounts/profile/", a.profile, name="profile"),
    path("accounts/", include("django.contrib.auth.urls")),
]
if not settings.DESKTOP:
    urlpatterns += [path("admin/", admin.site.urls)]
else:
    from desktop import views

    urlpatterns += [path("local/profiles/", views.profiles, name="local_profiles")]

if not settings.DESKTOP:
    from apps.community import views as community

    urlpatterns += [
        path("classes/", community.classes, name="classes"),
        path("classes/<int:pk>/", community.classroom, name="classroom"),
        path("daily/", community.daily, name="daily"),
        path("sync/", community.sync_settings, name="sync_settings"),
        path("api/sync/", community.sync_upload),
        path("races/", community.races, name="races"),
        path("races/<uuid:pk>/", community.race, name="race"),
    ]

from django.conf import settings


def brand(request):
    return {"project_name": settings.PROJECT_NAME, "desktop_mode": settings.DESKTOP}

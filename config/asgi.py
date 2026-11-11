import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
from django.core.asgi import get_asgi_application

django_asgi = get_asgi_application()
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
from django.urls import path
from apps.community.consumers import RaceConsumer

application = ProtocolTypeRouter(
    {
        "http": django_asgi,
        "websocket": AllowedHostsOriginValidator(
            AuthMiddlewareStack(URLRouter([path("ws/race/<uuid:pk>/", RaceConsumer.as_asgi())]))
        ),
    }
)

import os
from .base import *
from desktop.paths import data_dir
import secrets

DESKTOP = True
DEBUG = False
SECRET_FILE = data_dir() / "secret.key"
if not SECRET_FILE.exists():
    SECRET_FILE.write_text(secrets.token_urlsafe(64))
    SECRET_FILE.chmod(0o600)
SECRET_KEY = SECRET_FILE.read_text()
DATABASES = {
    "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": data_dir() / "data.sqlite3"}
}
DESKTOP_PORT = int(os.environ.get("DESKTOP_PORT", "0"))
DESKTOP_TOKEN = os.environ.get("DESKTOP_TOKEN", "")
if not DESKTOP_TOKEN:
    raise ValueError("Use python -m desktop to launch the desktop edition.")
ALLOWED_HOSTS = ["127.0.0.1"]
SESSION_COOKIE_SAMESITE = "Strict"
SESSION_COOKIE_NAME = "typeatlas_desktop_" + str(DESKTOP_PORT)
MIDDLEWARE.insert(
    MIDDLEWARE.index("django.contrib.sessions.middleware.SessionMiddleware") + 1,
    "desktop.middleware.LocalGate",
)
WHITENOISE_USE_FINDERS = True

import time
from django.core.cache import cache
from django.http import HttpResponse


class SecurityHeaders:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        r = self.get_response(request)
        r["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; font-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; form-action 'self'; base-uri 'self'"
        )
        r["Referrer-Policy"] = "same-origin"
        return r


class Throttle:
    """Single-process baseline; deploy a shared cache/edge limiter for multiple workers."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method == "POST" and request.path in [
            "/accounts/login/",
            "/accounts/password_reset/",
            "/accounts/register/",
        ]:
            key = "auth:" + request.META.get("REMOTE_ADDR", "") + ":" + str(int(time.time() // 300))
            hits = cache.get(key, 0)
            if hits >= 20:
                return HttpResponse("Too many attempts. Try again in five minutes.", status=429)
            cache.set(key, hits + 1, 300)
        return self.get_response(request)

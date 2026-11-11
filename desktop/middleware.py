import hmac
from django.conf import settings
from django.http import HttpResponseForbidden


class LocalGate:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.META.get("HTTP_HOST") != "127.0.0.1:" + str(settings.DESKTOP_PORT):
            return HttpResponseForbidden("Invalid local host")
        if request.path == "/local/bootstrap/" and request.method == "POST":
            token = request.POST.get("token", "")
            if hmac.compare_digest(token, settings.DESKTOP_TOKEN):
                request.session.cycle_key()
                request.session["desktop_access"] = settings.DESKTOP_TOKEN
                from django.shortcuts import redirect

                return redirect("/")
            return HttpResponseForbidden("Invalid local token")
        if not hmac.compare_digest(
            str(request.session.get("desktop_access", "")), settings.DESKTOP_TOKEN
        ):
            return HttpResponseForbidden("Open this application from its desktop window.")
        return self.get_response(request)

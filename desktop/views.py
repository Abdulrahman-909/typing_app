from django.shortcuts import render, redirect
from django.http import HttpResponseBadRequest
from apps.lessons.models import LocalProfile


def profiles(request):
    if request.method == "POST":
        if request.POST.get("rename"):
            profile = LocalProfile.objects.filter(pk=request.POST["rename"]).first()
            new = request.POST.get("new_name", "").strip()
            if (
                profile
                and new
                and len(new) <= 60
                and not LocalProfile.objects.filter(name=new).exclude(pk=profile.pk).exists()
            ):
                profile.name = new
                profile.save()
            return redirect("local_profiles")
        if request.POST.get("delete"):
            if request.POST.get("confirm") != "yes":
                return HttpResponseBadRequest("Confirm profile deletion first.")
            from .backup import backup
            from .paths import data_dir
            import time

            backup(
                data_dir() / "data.sqlite3", data_dir() / f"pre-profile-delete-{time.time_ns()}.zip"
            )
            LocalProfile.objects.filter(pk=request.POST["delete"]).delete()
            request.session.pop("local_profile", None)
            return redirect("local_profiles")
        if request.POST.get("select"):
            profile = LocalProfile.objects.filter(pk=request.POST["select"]).first()
            if profile:
                request.session["local_profile"] = profile.pk
                return redirect("dashboard")
        name = request.POST.get("name", "").strip()
        if not 1 <= len(name) <= 60:
            return HttpResponseBadRequest("Use a profile name of 1–60 characters.")
        profile, _ = LocalProfile.objects.get_or_create(name=name)
        request.session["local_profile"] = profile.pk
        return redirect("practice")
    return render(request, "profiles.html", {"profiles": LocalProfile.objects.all()})

from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import RegisterForm, ProfileForm


def register(request):
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect("practice")
    return render(
        request,
        "form.html",
        {
            "form": form,
            "heading": "Make progress your habit",
            "subtitle": "Create an account to keep your results.",
            "button": "Create account",
        },
    )


@login_required
def profile(request):
    form = ProfileForm(request.POST or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Preferences saved.")
        return redirect("profile")
    return render(
        request,
        "form.html",
        {
            "form": form,
            "heading": "Your preferences",
            "subtitle": "Your timezone defines your practice day.",
            "button": "Save preferences",
        },
    )

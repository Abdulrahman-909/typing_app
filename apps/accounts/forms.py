from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["display_name", "timezone", "preferred_language", "daily_goal"]
        widgets = {
            "preferred_language": forms.Select(
                choices=[("en", "English"), ("fa", "Dari"), ("ps", "Pashto")]
            )
        }

    def clean_timezone(self):
        value = self.cleaned_data["timezone"]
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError):
            raise forms.ValidationError("Use an IANA timezone such as Asia/Kabul.")
        return value

    def clean_daily_goal(self):
        value = self.cleaned_data["daily_goal"]
        if not 1 <= value <= 120:
            raise forms.ValidationError("Choose 1–120 minutes.")
        return value

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from apps.lessons.models import LocalProfile


class Command(BaseCommand):
    help = "Create a desktop local profile (desktop settings required)."

    def add_arguments(self, parser):
        parser.add_argument("name")

    def handle(self, *args, **kwargs):
        if not settings.DESKTOP:
            raise CommandError(
                "Local profiles belong to the desktop edition. Use its Profiles screen."
            )
        p, _ = LocalProfile.objects.get_or_create(name=kwargs["name"][:60])
        self.stdout.write(str(p.pk))

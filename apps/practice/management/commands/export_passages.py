import json
from django.core.management.base import BaseCommand
from apps.practice.models import Passage


class Command(BaseCommand):
    help = "Export passage metadata and text as JSON to stdout."

    def handle(self, *args, **kwargs):
        self.stdout.write(
            json.dumps(
                list(
                    Passage.objects.values(
                        "title",
                        "text",
                        "language",
                        "difficulty",
                        "source",
                        "license",
                        "review_status",
                    )
                ),
                ensure_ascii=False,
                indent=2,
            )
        )

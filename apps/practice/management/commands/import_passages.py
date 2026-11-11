import json
from django.core.management.base import BaseCommand, CommandError
from apps.practice.models import Passage
from apps.practice.services import clean_custom


class Command(BaseCommand):
    help = "Import a JSON list of passages after validating the entire file."

    def add_arguments(self, parser):
        parser.add_argument("file")

    def handle(self, *args, **options):
        try:
            from pathlib import Path

            source = Path(options["file"])
            if source.stat().st_size > 1_000_000:
                raise ValueError("Maximum 1 MB")
            entries = json.loads(source.read_text("utf-8"))
            validated = []
            if not isinstance(entries, list):
                raise ValueError("Expected a list")
            for item in entries:
                if item.get("language") not in ["en", "fa", "ps"] or item.get("difficulty") not in [
                    "easy",
                    "medium",
                    "hard",
                ]:
                    raise ValueError("Invalid language/difficulty")
                validated.append(
                    Passage(
                        title=str(item["title"])[:120],
                        text=clean_custom(item["text"]),
                        language=item["language"],
                        difficulty=item["difficulty"],
                        source=str(item.get("source", "Imported"))[:200],
                        license=str(item.get("license", "Unknown — review required"))[:60],
                        review_status="unreviewed",
                    )
                )
            Passage.objects.bulk_create(validated)
            self.stdout.write(f"Imported {len(validated)} passages for review.")
        except (ValueError, KeyError, TypeError, OSError) as e:
            raise CommandError(str(e))

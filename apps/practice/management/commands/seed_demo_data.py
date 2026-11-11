import json
from django.conf import settings
from django.core.management.base import BaseCommand
from apps.practice.models import Passage
from apps.lessons.models import Lesson


class Command(BaseCommand):
    help = "Seed original starter content without creating accounts or passwords."

    def handle(self, *args, **kwargs):
        data = json.loads((settings.BASE_DIR / "data/passages.json").read_text(encoding="utf-8"))
        for language, levels in data.items():
            for difficulty, text in levels.items():
                Passage.objects.get_or_create(
                    title=f"{language} {difficulty} starter",
                    defaults={
                        "language": language,
                        "difficulty": difficulty,
                        "text": text,
                        "review_status": "reviewed" if language == "en" else "unreviewed",
                    },
                )
            texts = (
                [
                    "asdf jkl asdf jkl sad lad ask fall",
                    "qwer tyui op we type quite well",
                    "zxcv bnm mix calm next move",
                    "one small step each day makes a change",
                ]
                if language == "en"
                else [levels["easy"], levels["medium"], levels["hard"]]
            )
            names = (
                ["Home row", "Top row", "Bottom row", "Words and rhythm"]
                if language == "en"
                else ["First words", "Steady practice", "Longer passages"]
            )
            for i, (title, text) in enumerate(zip(names, texts), 1):
                Lesson.objects.get_or_create(
                    language=language,
                    order=i,
                    defaults={
                        "title": title,
                        "text": text,
                        "instruction": "Keep a relaxed posture. Type slowly and correct mistakes with Backspace. Complete this passage with at least 90% accuracy.",
                        "review_status": "reviewed" if language == "en" else "unreviewed",
                    },
                )
        self.stdout.write(
            self.style.SUCCESS("Seeded 9 passages and 10 lessons; no accounts created.")
        )

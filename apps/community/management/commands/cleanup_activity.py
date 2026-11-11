from datetime import timedelta
from django.utils import timezone
from django.core.management.base import BaseCommand
from apps.practice.models import TestSession
from apps.community.models import Race, SyncToken


class Command(BaseCommand):
    help = "Remove abandoned test sessions, expired race rooms, and expired sync tokens."

    def handle(self, *args, **kwargs):
        now = timezone.now()
        TestSession.objects.filter(
            created_at__lt=now - timedelta(hours=2), result__isnull=True
        ).delete()
        Race.objects.filter(created_at__lt=now - timedelta(hours=1)).delete()
        SyncToken.objects.filter(expires__lt=now).delete()
        self.stdout.write("Expired transient records removed.")

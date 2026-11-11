import time
from datetime import timedelta
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from django.db import transaction
from typing_engine.scoring import replay
from .models import Race, RaceEntry


class RaceConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.race_id = self.scope["url_route"]["kwargs"]["pk"]
        self.group = "race_" + str(self.race_id)
        if not self.scope["user"].is_authenticated or not await self.member():
            await self.close(code=4403)
            return
        self.last_message = 0
        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()
        await self.send_json(await self.snapshot())

    @database_sync_to_async
    def member(self):
        return RaceEntry.objects.filter(
            race_id=self.race_id,
            user=self.scope["user"],
            race__created_at__gt=timezone.now() - timedelta(hours=1),
        ).exists()

    @database_sync_to_async
    def snapshot(self):
        race = Race.objects.get(pk=self.race_id)
        return {
            "type": "state",
            "starts_at": race.starts_at.isoformat() if race.starts_at else None,
            "server_now": timezone.now().isoformat(),
            "players": [
                {
                    "name": e.user.username,
                    "progress": e.progress,
                    "finished": e.finished,
                    "wpm": e.result.get("wpm"),
                }
                for e in RaceEntry.objects.filter(race=race).select_related("user")
            ],
        }

    async def disconnect(self, code):
        if hasattr(self, "group"):
            await self.channel_layer.group_discard(self.group, self.channel_name)

    async def receive_json(self, content, **kwargs):
        if time.monotonic() - self.last_message < 0.15:
            return
        self.last_message = time.monotonic()
        try:
            await self.update(content)
        except (ValueError, KeyError, TypeError) as e:
            await self.send_json({"type": "error", "message": str(e)})
            return
        await self.channel_layer.group_send(self.group, {"type": "race.state"})

    @database_sync_to_async
    def update(self, data):
        with transaction.atomic():
            race = Race.objects.select_for_update().get(pk=self.race_id)
            if data.get("type") == "start":
                if race.host_id != self.scope["user"].pk or race.starts_at:
                    raise ValueError("Only the host can start once.")
                race.starts_at = timezone.now() + timedelta(seconds=3)
                race.save(update_fields=["starts_at"])
                return
            if not race.starts_at or timezone.now() < race.starts_at:
                raise ValueError("Wait for the start.")
            entry = RaceEntry.objects.select_for_update().get(race=race, user=self.scope["user"])
            if entry.finished:
                return
            elapsed = float(data.get("elapsed", 0))
            observed = (timezone.now() - race.starts_at).total_seconds()
            if elapsed > observed + 1 or elapsed <= 0:
                raise ValueError("Invalid race clock")
            events = data.get("events", [])
            if len(events) > 1500:
                raise ValueError("Too many events")
            metrics = replay(race.target, events, elapsed)
            text = events[-1]["v"] if events else ""
            entry.progress = min(100, len(text) / len(race.target) * 100)
            if text == race.target:
                entry.finished = True
                entry.result = metrics
            entry.save()

    async def race_state(self, event):
        await self.send_json(await self.snapshot())

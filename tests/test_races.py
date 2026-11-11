import asyncio
from datetime import timedelta
import pytest
from django.utils import timezone
from channels.testing import WebsocketCommunicator
from channels.db import database_sync_to_async
from apps.community.models import Race, RaceEntry
from apps.community.consumers import RaceConsumer


@pytest.mark.django_db(transaction=True)
def test_two_race_clients(django_user_model):
    host = django_user_model.objects.create_user("host")
    guest = django_user_model.objects.create_user("guest")
    race = Race.objects.create(host=host, target="hi")
    RaceEntry.objects.create(race=race, user=host)
    RaceEntry.objects.create(race=race, user=guest)

    async def scenario():
        clients = []
        for user in [host, guest]:
            c = WebsocketCommunicator(RaceConsumer.as_asgi(), "/ws/race/")
            c.scope["user"] = user
            c.scope["url_route"] = {"kwargs": {"pk": race.pk}}
            assert (await c.connect())[0]
            await c.receive_json_from()
            clients.append(c)
        await clients[0].send_json_to({"type": "start"})
        for c in clients:
            assert (await c.receive_json_from())["starts_at"]
        await database_sync_to_async(
            lambda: Race.objects.filter(pk=race.pk).update(
                starts_at=timezone.now() - timedelta(seconds=3)
            )
        )()
        # Rate limiter uses monotonic time; wait only the documented 150 ms interval.
        await asyncio.sleep(0.16)
        for c in clients:
            await c.send_json_to(
                {
                    "type": "progress",
                    "elapsed": 2,
                    "events": [
                        {"t": 100, "v": "h", "kind": "insertText"},
                        {"t": 2000, "v": "hi", "kind": "insertText"},
                    ],
                }
            )
            for receiver in clients:
                await receiver.receive_json_from()
        for c in clients:
            await c.disconnect()

    asyncio.run(scenario())
    assert RaceEntry.objects.filter(race=race, finished=True).count() == 2

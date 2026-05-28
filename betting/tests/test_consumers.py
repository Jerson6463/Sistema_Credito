import pytest
from channels.testing import WebsocketCommunicator
from decimal import Decimal

from betting.consumers import EventOddsConsumer
from betting.models import Event, EventStatus, Market, MarketType, Selection
from betting.realtime import broadcast_odds_update
from django.utils import timezone


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_event_odds_consumer_receives_broadcast():
    event = Event.objects.create(
        name='WS Test',
        start_time=timezone.now(),
        status=EventStatus.LIVE,
    )
    market = Market.objects.create(event=event, type=MarketType.MATCH_RESULT)
    selection = Selection.objects.create(
        market=market,
        name='Local',
        current_odds=Decimal('2.0000'),
    )

    communicator = WebsocketCommunicator(
        EventOddsConsumer.as_asgi(),
        f'/ws/events/{event.id}/',
    )
    connected, _ = await communicator.connect()
    assert connected

    welcome = await communicator.receive_json_from()
    assert welcome['type'] == 'connection.established'

    broadcast_odds_update(
        event_id=str(event.id),
        selection_id=str(selection.id),
        market_id=str(market.id),
        current_odds=Decimal('2.5000'),
        previous_odds=Decimal('2.0000'),
        is_active=True,
        previous_is_active=True,
    )

    message = await communicator.receive_json_from()
    assert message['type'] == 'odds_update'
    assert message['current_odds'] == '2.5000'

    await communicator.disconnect()

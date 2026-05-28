import pytest
from decimal import Decimal

from betting.models import Bet, Event, EventStatus, Market, MarketType, Selection
from betting.services import settle_market
from django.contrib.auth import get_user_model
from django.utils import timezone


@pytest.fixture(autouse=True)
def in_memory_channel_layer(settings):
    settings.CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels.layers.InMemoryChannelLayer',
        },
    }


@pytest.fixture
def demo_market(db):
    user = get_user_model().objects.create_user(username='bettor', password='test-pass-123')
    event = Event.objects.create(
        name='Test Event',
        start_time=timezone.now(),
        status=EventStatus.LIVE,
    )
    market = Market.objects.create(event=event, type=MarketType.MATCH_RESULT, is_active=True)
    home = Selection.objects.create(market=market, name='Local', current_odds=Decimal('2.5000'))
    draw = Selection.objects.create(market=market, name='Empate', current_odds=Decimal('3.0000'))
    away = Selection.objects.create(market=market, name='Visitante', current_odds=Decimal('2.8000'))
    Bet.objects.create(
        user=user,
        selection=home,
        stake=Decimal('10.0000'),
        locked_odds=Decimal('2.5000'),
    )
    Bet.objects.create(
        user=user,
        selection=away,
        stake=Decimal('5.0000'),
        locked_odds=Decimal('2.8000'),
    )
    return market, home, draw, away

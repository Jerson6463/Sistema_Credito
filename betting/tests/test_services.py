import pytest

from betting.models import Bet, Event, EventStatus, Market, MarketType, Selection
from betting.services import settle_market
from django.utils import timezone


def test_settle_market_pending_without_wallet(demo_market):
    market, home, _, _ = demo_market

    result = settle_market(market.id, home.id)

    assert result['status'] == 'pending'
    assert result['settled_count'] == 0
    assert result['pending_wallet'] == 2
    assert Bet.objects.filter(status=Bet.Status.ACCEPTED).count() == 2


def test_settle_market_rejects_foreign_selection(demo_market):
    market, _, _, _ = demo_market
    other_event = Event.objects.create(
        name='Otro',
        start_time=timezone.now(),
        status=EventStatus.SCHEDULED,
    )
    other_market = Market.objects.create(event=other_event, type=MarketType.MATCH_RESULT)
    other_selection = Selection.objects.create(
        market=other_market,
        name='X',
        current_odds='2.0000',
    )

    with pytest.raises(ValueError):
        settle_market(market.id, other_selection.id)


def test_settle_market_completes_when_wallet_ready(demo_market, mocker):
    market, home, _, _ = demo_market
    mocker.patch('betting.services.settle_bet_won')
    mocker.patch('betting.services.settle_bet_lost')

    result = settle_market(market.id, home.id)

    assert result['status'] == 'completed'
    assert result['settled_count'] == 2
    assert Bet.objects.filter(status=Bet.Status.WON).count() == 1
    assert Bet.objects.filter(status=Bet.Status.LOST).count() == 1

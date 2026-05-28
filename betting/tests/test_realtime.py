from decimal import Decimal

from betting.realtime import broadcast_odds_update


def test_broadcast_odds_update_skips_when_nothing_changed(mocker):
    group_send = mocker.patch('betting.realtime._group_send')

    sent = broadcast_odds_update(
        event_id='event-1',
        selection_id='sel-1',
        market_id='market-1',
        current_odds=Decimal('2.5000'),
        previous_odds=Decimal('2.5000'),
        is_active=True,
        previous_is_active=True,
    )

    assert sent is False
    group_send.assert_not_called()


def test_broadcast_odds_update_emits_when_odds_changed(mocker):
    group_send = mocker.patch('betting.realtime._group_send')

    sent = broadcast_odds_update(
        event_id='event-1',
        selection_id='sel-1',
        market_id='market-1',
        current_odds=Decimal('2.1000'),
        previous_odds=Decimal('2.5000'),
        is_active=True,
        previous_is_active=True,
    )

    assert sent is True
    group_send.assert_called_once()
    args = group_send.call_args[0]
    assert args[0] == 'event-1'
    assert args[1] == 'odds_update'
    assert args[2]['current_odds'] == '2.1000'


def test_broadcast_odds_update_emits_when_market_deactivated(mocker):
    group_send = mocker.patch('betting.realtime._group_send')

    sent = broadcast_odds_update(
        event_id='event-1',
        selection_id='sel-1',
        market_id='market-1',
        current_odds=Decimal('2.5000'),
        previous_odds=Decimal('2.5000'),
        is_active=False,
        previous_is_active=True,
    )

    assert sent is True
    group_send.assert_called_once()

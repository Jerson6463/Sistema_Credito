from betting.tasks import ping_task, settle_market_bets_task


def test_ping_task_returns_ok():
    result = ping_task()
    assert result == {'status': 'ok', 'service': 'betting'}


def test_settle_market_bets_task_pending_without_wallet(db, demo_market):
    market, home, _, _ = demo_market
    result = settle_market_bets_task(str(market.id), str(home.id))
    assert result['status'] == 'pending'
    assert result['pending_wallet'] >= 1

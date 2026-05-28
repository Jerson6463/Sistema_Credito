"""
Tareas Celery del Integrante 3.

Las tareas que mueven dinero delegan en betting.services.settle_market,
que a su vez llama wallet.services (Integrante 1).
"""
from __future__ import annotations

import logging
from uuid import UUID

from celery import shared_task
from django.conf import settings

from betting.realtime import broadcast_market_resumed, broadcast_market_suspended
from betting.services import set_market_active, settle_market

logger = logging.getLogger(__name__)


@shared_task(name='betting.ping')
def ping_task() -> dict[str, str]:
    """Tarea de prueba para verificar que el worker Celery está operativo."""
    return {'status': 'ok', 'service': 'betting'}


@shared_task(
    bind=True,
    name='betting.settle_market_bets',
    max_retries=3,
    default_retry_delay=5,
)
def settle_market_bets_task(
    self,
    market_id: str,
    winning_selection_id: str,
) -> dict:
    """Liquida apuestas accepted cuando el operador marca resultado."""
    try:
        result = settle_market(
            market_id=UUID(market_id),
            winning_selection_id=UUID(winning_selection_id),
        )
    except ValueError as exc:
        logger.warning('Liquidación inválida: %s', exc)
        return {'status': 'error', 'detail': str(exc)}

    if result['status'] == 'pending':
        return result

    if result['errors']:
        raise self.retry(exc=RuntimeError('; '.join(result['errors'])))

    return result


@shared_task(name='betting.suspend_market')
def suspend_market_task(
    event_id: str,
    market_id: str,
    reason: str = 'critical_event',
    suspension_seconds: int | None = None,
) -> dict:
    """Suspende mercado in-play y notifica clientes por WebSocket."""
    seconds = suspension_seconds or settings.INPLAY_MARKET_SUSPENSION_SECONDS

    set_market_active(market_id=UUID(market_id), is_active=False)

    broadcast_market_suspended(
        event_id=event_id,
        market_id=market_id,
        reason=reason,
        suspension_seconds=seconds,
    )

    resume_market_task.apply_async(
        args=[event_id, market_id],
        countdown=seconds,
    )

    return {
        'status': 'suspended',
        'event_id': event_id,
        'market_id': market_id,
        'suspension_seconds': seconds,
        'reason': reason,
    }


@shared_task(name='betting.resume_market')
def resume_market_task(event_id: str, market_id: str) -> dict:
    """Reactiva mercado tras la suspensión in-play."""
    set_market_active(market_id=UUID(market_id), is_active=True)
    broadcast_market_resumed(event_id=event_id, market_id=market_id)

    return {
        'status': 'resumed',
        'event_id': event_id,
        'market_id': market_id,
    }

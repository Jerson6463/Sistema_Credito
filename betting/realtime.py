"""
Utilidades para emitir mensajes WebSocket solo cuando hay cambios reales.
Evita saturar Redis con ticks repetidos (ADR 0007).
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings


def _normalize_odds(value: Decimal | str | float) -> str:
    return str(Decimal(str(value)).quantize(Decimal('0.0001')))


def broadcast_odds_update(
    event_id: str,
    selection_id: str,
    market_id: str,
    current_odds: Decimal | str,
    previous_odds: Decimal | str | None,
    is_active: bool,
    previous_is_active: bool | None = None,
) -> bool:
    """
    Emite actualización de cuota solo si odds o is_active cambiaron.
    Retorna True si se envió el mensaje, False si no hubo cambio.
    """
    odds_changed = previous_odds is None or _normalize_odds(current_odds) != _normalize_odds(
        previous_odds
    )
    active_changed = previous_is_active is None or is_active != previous_is_active

    if not odds_changed and not active_changed:
        return False

    payload: dict[str, Any] = {
        'type': 'odds_update',
        'event_id': event_id,
        'selection_id': selection_id,
        'market_id': market_id,
        'current_odds': _normalize_odds(current_odds),
        'is_active': is_active,
    }

    _group_send(event_id, 'odds_update', payload)
    return True


def broadcast_market_suspended(
    event_id: str,
    market_id: str,
    reason: str,
    suspension_seconds: int | None = None,
) -> None:
    seconds = suspension_seconds or settings.INPLAY_MARKET_SUSPENSION_SECONDS
    payload = {
        'type': 'market_suspended',
        'event_id': event_id,
        'market_id': market_id,
        'reason': reason,
        'suspension_seconds': seconds,
    }
    _group_send(event_id, 'market_suspended', payload)


def broadcast_market_resumed(event_id: str, market_id: str) -> None:
    payload = {
        'type': 'market_resumed',
        'event_id': event_id,
        'market_id': market_id,
    }
    _group_send(event_id, 'market_resumed', payload)


def _group_send(event_id: str, message_type: str, payload: dict[str, Any]) -> None:
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return

    async_to_sync(channel_layer.group_send)(
        f'event_{event_id}',
        {
            'type': message_type,
            'payload': payload,
        },
    )

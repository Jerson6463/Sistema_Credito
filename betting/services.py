"""Orquestación de betting para tareas Celery y endpoints del operador."""

from __future__ import annotations

import logging
from decimal import Decimal
from uuid import UUID

from django.apps import apps
from django.db import transaction

from wallet.services import WalletNotReady, settle_bet_lost, settle_bet_won

logger = logging.getLogger(__name__)


def set_market_active(market_id: UUID, is_active: bool) -> None:
    Market = apps.get_model('betting', 'Market')
    updated = Market.objects.filter(pk=market_id).update(is_active=is_active)
    if updated == 0:
        raise ValueError(f'Market {market_id} no encontrado')


def update_selection_odds(
    selection_id: UUID,
    current_odds: Decimal,
    *,
    is_active: bool | None = None,
) -> dict:
    """
    Actualiza cuota en BD; signals emiten WebSocket solo si hubo cambio real.
    """
    Selection = apps.get_model('betting', 'Selection')
    selection = Selection.objects.select_related('market__event').get(pk=selection_id)
    market = selection.market
    previous_odds = selection.current_odds

    if is_active is not None and market.is_active != is_active:
        market.is_active = is_active
        market.save(update_fields=['is_active'])

    selection.current_odds = current_odds
    selection.save(update_fields=['current_odds'])

    return {
        'selection_id': str(selection.id),
        'event_id': str(market.event_id),
        'market_id': str(market.id),
        'previous_odds': str(previous_odds),
        'current_odds': str(current_odds),
        'is_active': market.is_active,
    }


def settle_market(market_id: UUID, winning_selection_id: UUID) -> dict:
    """
    Liquida apuestas accepted de un mercado vía Celery.
    Delega movimientos contables a wallet.services; actualiza FSM de Bet aquí.
    """
    Market = apps.get_model('betting', 'Market')
    BetModel = apps.get_model('betting', 'Bet')

    market = Market.objects.get(pk=market_id)
    if not market.selections.filter(pk=winning_selection_id).exists():
        raise ValueError(
            f'Selección ganadora {winning_selection_id} no pertenece al mercado {market_id}'
        )

    settled_count = 0
    pending_wallet = 0
    errors: list[str] = []

    bets = (
        BetModel.objects.filter(selection__market_id=market_id, status=BetModel.Status.ACCEPTED)
        .select_related('selection')
        .order_by('created_at')
    )

    for bet in bets:
        try:
            with transaction.atomic():
                bet = BetModel.objects.select_for_update().get(pk=bet.pk)
                if bet.status != BetModel.Status.ACCEPTED:
                    continue

                if bet.selection_id == winning_selection_id:
                    settle_bet_won(bet)
                    bet.mark_won()
                else:
                    settle_bet_lost(bet)
                    bet.mark_lost()
                bet.save()
                settled_count += 1
        except WalletNotReady as exc:
            pending_wallet += 1
            logger.warning('Wallet no listo para bet %s: %s', bet.id, exc)
        except Exception as exc:
            errors.append(f'{bet.id}: {exc}')
            logger.exception('Error liquidando bet %s', bet.id)

    status = 'completed'
    if pending_wallet and settled_count == 0:
        status = 'pending'
    elif pending_wallet:
        status = 'partial'

    return {
        'status': status,
        'market_id': str(market_id),
        'winning_selection_id': str(winning_selection_id),
        'settled_count': settled_count,
        'pending_wallet': pending_wallet,
        'errors': errors,
    }

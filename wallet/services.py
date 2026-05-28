"""
Contrato de servicios financieros para Integrante 3.

Integrante 1 debe implementar los movimientos de partida doble aquí.
Las tareas Celery de liquidación llaman settle_bet_won / settle_bet_lost.
"""


class WalletNotReady(Exception):
    """El motor de wallet aún no implementó movimientos de ledger."""


def settle_bet_won(bet) -> None:
    """
    Acredita payout = stake × locked_odds desde apuestas_pendientes al wallet del usuario.

    Integrante 1: reemplazar el raise por entradas LedgerEntry balanceadas.
    """
    raise WalletNotReady(
        'settle_bet_won pendiente: implementar partida doble en wallet/services.py'
    )


def settle_bet_lost(bet) -> None:
    """
    Libera stake perdido desde apuestas_pendientes hacia la cuenta casa.

    Integrante 1: reemplazar el raise por entradas LedgerEntry balanceadas.
    """
    raise WalletNotReady(
        'settle_bet_lost pendiente: implementar partida doble en wallet/services.py'
    )

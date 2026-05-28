# Contexto

Al marcar resultado, pueden existir cientos de apuestas. Procesar payout en el hilo HTTP bloquea al operador.

# Opciones consideradas

1. **Síncrono en la vista admin:** simple pero bloqueante y frágil bajo carga.
2. **Celery + Redis:** cola async; la vista responde 202 y el worker liquida.

# Decisión

Celery task `settle_market_bets_task` que llama `betting.services.settle_market`. Los movimientos contables delegan en `wallet.services` (Integrante 1).

# Consecuencias

- Endpoint operador: `POST /api/admin/markets/{id}/settle/`.
- Sin wallet listo, la tarea retorna `pending_wallet` sin corromper estado de Bet.
- Reintentos Celery solo ante errores no relacionados con wallet pendiente.

# Fecha y autor

27 de mayo de 2026 — Integrante 3

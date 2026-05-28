# Integrante 3 — Channels, Celery y tiempo real

## Levantar stack (datos en D:\Docker\fairbet)

```powershell
cd D:\Sistema_Apuestas\Sistema_Apuestas
docker compose up --build
```

En otra terminal:

```powershell
docker compose exec web python manage.py migrate
docker compose exec web python manage.py seed_demo
docker compose exec web python manage.py createsuperuser
```

## Probar WebSocket

```powershell
# Tras seed_demo, copia el Event ID
pip install websockets
python scripts/ws_listen.py <EVENT_UUID>
```

En otra terminal (como admin autenticado vía sesión o token):

```powershell
# Actualizar cuota → debe aparecer en ws_listen
curl -X PATCH http://localhost:8000/api/admin/selections/<SELECTION_UUID>/odds/ ^
  -H "Content-Type: application/json" ^
  -u admin:password ^
  -d "{\"current_odds\": \"2.7500\"}"
```

## Probar Celery

```powershell
curl http://localhost:8000/api/celery/ping/
curl http://localhost:8000/api/celery/result/<task_id>/

# Liquidar mercado (wallet pendiente hasta Integrante 1)
curl -X POST http://localhost:8000/api/admin/markets/<MARKET_UUID>/settle/ ^
  -H "Content-Type: application/json" ^
  -u admin:password ^
  -d "{\"winning_selection_id\": \"<SELECTION_UUID>\"}"

# Suspensión in-play (30 s por defecto)
curl -X POST http://localhost:8000/api/admin/events/<EVENT_UUID>/critical-event/ ^
  -H "Content-Type: application/json" ^
  -u admin:password ^
  -d "{\"market_id\": \"<MARKET_UUID>\", \"reason\": \"goal\"}"
```

## Contrato para Integrante 1

Implementar en `wallet/services.py`:

- `settle_bet_won(bet)` — payout = stake × locked_odds
- `settle_bet_lost(bet)` — stake a cuenta casa

Cuando estén listos, `settle_market_bets_task` liquidará apuestas y actualizará FSM automáticamente.

## Tests

```powershell
docker compose exec web pytest betting/tests/ -q
```

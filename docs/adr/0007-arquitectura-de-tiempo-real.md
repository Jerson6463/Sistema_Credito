# Contexto

Las cuotas deben actualizarse en pantalla sin recargar. El reto exige Django Channels con canal por evento.

# Opciones consideradas

1. **SSE:** unidireccional, más simple, sin bidireccionalidad.
2. **WebSockets + Channels + Redis:** canal por evento, escalable en el ecosistema Django.

# Decisión

WebSockets con Django Channels y Redis Channel Layer. Un group `event_{uuid}` por partido.

# Consecuencias

- Emisión condicionada: solo si `current_odds` o `is_active` cambian (`betting/realtime.py`).
- Despliegue ASGI con Daphne en docker-compose.
- Integrante 2 actualiza modelos; signals en `betting/signals.py` disparan broadcast.

# Fecha y autor

27 de mayo de 2026 — Integrante 3

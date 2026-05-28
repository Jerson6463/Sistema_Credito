#!/usr/bin/env python3
"""
Cliente WebSocket de prueba para Integrante 3.

Uso:
  pip install websockets
  python scripts/ws_listen.py <event_uuid>

Ejemplo tras seed_demo:
  python scripts/ws_listen.py <event_id>
"""
from __future__ import annotations

import asyncio
import json
import sys

try:
    import websockets
except ImportError:
    print('Instala dependencia: pip install websockets')
    sys.exit(1)


async def listen(event_id: str) -> None:
    url = f'ws://localhost:8000/ws/events/{event_id}/'
    print(f'Conectando a {url} ...')
    async with websockets.connect(url) as websocket:
        print('Conectado. Esperando mensajes (Ctrl+C para salir)...')
        async for message in websocket:
            try:
                payload = json.loads(message)
            except json.JSONDecodeError:
                payload = message
            print(json.dumps(payload, indent=2, ensure_ascii=False))


def main() -> None:
    if len(sys.argv) != 2:
        print('Uso: python scripts/ws_listen.py <event_uuid>')
        sys.exit(1)
    asyncio.run(listen(sys.argv[1]))


if __name__ == '__main__':
    main()

import json

from channels.generic.websocket import AsyncJsonWebsocketConsumer


class EventOddsConsumer(AsyncJsonWebsocketConsumer):
    """Canal WebSocket por evento: recibe actualizaciones de cuotas y suspensiones."""

    async def connect(self):
        self.event_id = self.scope['url_route']['kwargs']['event_id']
        self.group_name = f'event_{self.event_id}'

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.send_json(
            {
                'type': 'connection.established',
                'event_id': self.event_id,
                'message': 'Suscrito a actualizaciones en vivo del evento.',
            }
        )

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def odds_update(self, event):
        await self.send_json(event['payload'])

    async def market_suspended(self, event):
        await self.send_json(event['payload'])

    async def market_resumed(self, event):
        await self.send_json(event['payload'])

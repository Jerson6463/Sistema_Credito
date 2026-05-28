from django.core.management.base import BaseCommand
from django.utils import timezone

from betting.models import Event, EventStatus, Market, MarketType, Selection


class Command(BaseCommand):
    help = 'Carga un evento demo 1X2 para probar WebSocket y Celery (Integrante 3).'

    def handle(self, *args, **options):
        event, created = Event.objects.get_or_create(
            name='Perú vs Brasil — Demo',
            defaults={
                'start_time': timezone.now() + timezone.timedelta(hours=2),
                'status': EventStatus.LIVE,
            },
        )
        if not created:
            event.status = EventStatus.LIVE
            event.save(update_fields=['status'])

        market, _ = Market.objects.get_or_create(
            event=event,
            type=MarketType.MATCH_RESULT,
            defaults={'is_active': True},
        )

        selections_data = [
            ('Gana Perú', '3.5000'),
            ('Empate', '3.2000'),
            ('Gana Brasil', '2.1000'),
        ]
        selections = []
        for name, odds in selections_data:
            selection, _ = Selection.objects.update_or_create(
                market=market,
                name=name,
                defaults={'current_odds': odds},
            )
            selections.append(selection)

        self.stdout.write(self.style.SUCCESS('Seed demo cargado.'))
        self.stdout.write(f'Event ID:   {event.id}')
        self.stdout.write(f'Market ID:  {market.id}')
        for selection in selections:
            self.stdout.write(f'  {selection.name}: {selection.id} @ {selection.current_odds}')
        self.stdout.write('')
        self.stdout.write(f'WebSocket: ws://localhost:8000/ws/events/{event.id}/')
        self.stdout.write(
            f'Actualizar odds: PATCH /api/admin/selections/<id>/odds/ '
            f'{{"current_odds": "2.5000"}}'
        )

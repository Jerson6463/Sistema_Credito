import uuid

from django.conf import settings
from django.db import models
from django_fsm import FSMField, transition


class EventStatus(models.TextChoices):
    SCHEDULED = 'programado', 'Programado'
    LIVE = 'en_vivo', 'En vivo'
    FINISHED = 'finalizado', 'Finalizado'
    SUSPENDED = 'suspendido', 'Suspendido'
    CANCELLED = 'anulado', 'Anulado'


class Event(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    start_time = models.DateTimeField()
    status = models.CharField(
        max_length=20,
        choices=EventStatus.choices,
        default=EventStatus.SCHEDULED,
    )

    class Meta:
        ordering = ['start_time']

    def __str__(self) -> str:
        return self.name


class MarketType(models.TextChoices):
    MATCH_RESULT = '1X2', '1X2'


class Market(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='markets')
    type = models.CharField(
        max_length=32,
        choices=MarketType.choices,
        default=MarketType.MATCH_RESULT,
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = [('event', 'type')]

    def __str__(self) -> str:
        return f'{self.event.name} — {self.type}'


class Selection(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    market = models.ForeignKey(Market, on_delete=models.CASCADE, related_name='selections')
    name = models.CharField(max_length=100)
    current_odds = models.DecimalField(max_digits=18, decimal_places=4)

    class Meta:
        unique_together = [('market', 'name')]

    def __str__(self) -> str:
        return f'{self.name} @ {self.current_odds}'


class Bet(models.Model):
    class Status(models.TextChoices):
        ACCEPTED = 'accepted', 'Accepted'
        WON = 'won', 'Won'
        LOST = 'lost', 'Lost'
        REFUNDED = 'refunded', 'Refunded'
        CASHED_OUT = 'cashed_out', 'Cashed out'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bets')
    selection = models.ForeignKey(Selection, on_delete=models.PROTECT, related_name='bets')
    stake = models.DecimalField(max_digits=18, decimal_places=4)
    locked_odds = models.DecimalField(max_digits=18, decimal_places=4)
    status = FSMField(default=Status.ACCEPTED, choices=Status.choices, protected=True)
    transaction_id = models.UUIDField(default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'Bet {self.id} — {self.status}'

    @transition(field=status, source=Status.ACCEPTED, target=Status.WON)
    def mark_won(self) -> None:
        pass

    @transition(field=status, source=Status.ACCEPTED, target=Status.LOST)
    def mark_lost(self) -> None:
        pass

    @transition(field=status, source=Status.ACCEPTED, target=Status.REFUNDED)
    def mark_refunded(self) -> None:
        pass

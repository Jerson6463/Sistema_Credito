import uuid

from decimal import Decimal
from django.db import models
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.db.models import Sum
from django.db.models.functions import Coalesce

class Account(models.fields.Field):
    pass

# Redefiniendo la clase estandar de Django
class Account(models.Model):
    class AccountType(models.TextChoices):
        USER_WALLET = 'user_wallet', "User Wallet"
        HOUSE_WALLET = 'house_wallet', 'House Wallet'
        PENDING_BETS = 'pending_bets', 'Pending Bets'
        BONUSES = 'bonuses', 'Bonuses'

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        help_text="Null si la cuenta pertenece a la casa "
    )
    
    type = models.CharField(
        max_length=20,
        choices=AccountType.choices
    )

    name = models.CharField(
        max_length=100
    )

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"
    
    @property
    def balance (self) -> Decimal:
        """
        El saldo se calcula dinamicamente: SUM(credits) - SUM(debits)
        """

        credits = self.entries.filter(direction =LedgerEntry.Direction.CREDIT).aggregate(
            total = Coalesce(Sum('amount'), Decimal('0.0000'))
        )['total']

        debits = self.entries.filter(direction =LedgerEntry.Direction.DEBIT).aggregate(
            total = Coalesce(Sum('amount'), Decimal('0.0000'))
        )['total']

        return credits - debits

class LedgerEntry(models.Model):
    class Direction(models.TextChoices):
        CREDIT = 'CREDIT', 'Credit (+)'
        DEBIT = 'DEBIT', 'Debit (-)'

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name='entries'
    )

    #Uso estricto de decimalField para evitar problemas de coma flotante
    amount = models.DecimalField(
        max_digits=18,
        decimal_places=4
    )

    direction = models.CharField(
        max_length=18,
        choices=Direction.choices
    )

    #Agrupa las operaciones
    transaction_id = models.UUIDField(
        db_index=True
    )

    #Polimorfismo: permite relacionar este movimiento con un deposito
    reference_type = models.ForeignKey(
        ContentType,
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )

    reference_id = models.UUIDField (
        null=True,
        blank=True
    )

    reference_object = GenericForeignKey(
        'reference_type',
        'reference_id'
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.direction} {self.amount} on {self.account.name}"
    
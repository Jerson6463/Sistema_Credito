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
        BILLETERA_USUARIO = 'billetera_usuario', "Billetera del usuario"
        BILLETERA_CASA = 'billetera_casa', 'Billetera de la casa'
        APUESTA_PENDIENTE = 'apuesta_pendiente', 'Pending Bets'
        BONUS = 'bonus', 'Bonus'

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
    
    tipo = models.CharField(
        max_length=20,
        choices=AccountType.choices
    )

    nombre = models.CharField(
        max_length=100
    )

    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_displayy()})"
    
    @property
    def balance(self) -> Decimal:
        """
        El saldo se calcula dinamicamente: SUM(credits) - SUM(debits)
        """

        creditos = self.entries.filter(direccion=LedgerEntry.Direction.CREDITO).aggregate(
            total=Coalesce(Sum('monto'), Decimal('0.0000'))
        )['total']

        debitos = self.entries.filter(direccion=LedgerEntry.Direction.DEBITO).aggregate(
            total=Coalesce(Sum('monto'), Decimal('0.0000'))
        )['total']

        return creditos - debitos

class LedgerEntry(models.Model):
    class Direction(models.TextChoices):
        CREDITO = 'CREDITO', 'Credito (+)'
        DEBITO = 'DEBITO', 'Debito (-)'

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    cuenta = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name='entries'
    )

    #Uso estricto de decimalField para evitar problemas de coma flotante
    monto = models.DecimalField(
        max_digits=18,
        decimal_places=4
    )

    direccion = models.CharField(
        max_length=18,
        choices=Direction.choices
    )

    #Agrupa las operaciones
    transaccion_id = models.UUIDField(
        db_index=True
    )

    #Polimorfismo: permite relacionar este movimiento con un deposito
    tipo_referencia = models.ForeignKey(
        ContentType,
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )

    id_referencia = models.UUIDField (
        null=True,
        blank=True
    )

    referencia_objeto = GenericForeignKey(
        'tipo_referencia',
        'id_referencia'
    )

    creado_en = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.direccion} {self.monto} on {self.cuenta.nombre}"
    
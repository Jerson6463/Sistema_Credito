from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db.models import Sum
from hypothesis import given, settings
from hypothesis.strategies import decimals
from hypothesis.extra.django import TestCase

from wallet.models import Account, LedgerEntry
from wallet.services import ejecutar_transferencia

class TransferServiceTests(TestCase):
    def setUp(self):
        """Configuración inicial del entorno de pruebas."""
        self.billetera_casa = Account.objects.create(
            nombre="Billetera de la Casa",
            tipo=Account.AccountType.BILLETERA_CASA
        )
        self.billetera_usuario = Account.objects.create(
            nombre="Billetera del Usuario",
            tipo=Account.AccountType.BILLETERA_USUARIO
        )

    def test_transferencia_exitosa(self):
        """Valida una transferencia exitosa y la actualización dinámica de saldos."""
        ejecutar_transferencia(self.billetera_casa, self.billetera_usuario, Decimal('150.5000'))

        self.assertEqual(self.billetera_usuario.balance, Decimal('150.5000'))
        self.assertEqual(self.billetera_casa.balance, Decimal('-150.5000'))

    def test_fondos_insuficientes_billetera_usuario(self):
        """Valida la invariante: Ningún wallet de usuario termina con saldo negativo."""
        with self.assertRaisesMessage(ValidationError, "Saldo insuficiente para realizar la operacion."):
            ejecutar_transferencia(self.billetera_usuario, self.billetera_casa, Decimal('50.0000'))

    def test_transferencia_cero_o_negativa_falla(self):
        """Valida que el sistema rechace operaciones matemáticamente inválidas."""
        with self.assertRaisesMessage(ValidationError, "El monto a transferir debe ser estrictamente mayor a cero"):
            ejecutar_transferencia(self.billetera_casa, self.billetera_usuario, Decimal('-10.0000'))

    def test_transferencia_misma_cuenta_falla(self):
        """Valida que no se pueda simular movimiento de fondos hacia la misma cuenta."""
        with self.assertRaisesMessage(ValidationError, "No se puede transferir fondos a la misma cuenta"):
            ejecutar_transferencia(self.billetera_usuario, self.billetera_usuario, Decimal('100.0000'))

    @given(monto_prueba=decimals(min_value=Decimal('0.0001'), max_value=Decimal('100000.0000'), places=4))
    @settings(max_examples=50)
    def test_invariante_partida_doble_siempre_cuadra(self, monto_prueba):
        """
        Property-based test con Hypothesis.
        Inyecta decenas de montos aleatorios para asegurar que el sistema nunca rompe la partida doble.
        """
        ejecutar_transferencia(self.billetera_casa, self.billetera_usuario, monto_prueba)

        # Extraemos los totales usando tus nuevos nombres de campos ('monto' y 'direccion')
        total_creditos = LedgerEntry.objects.filter(direccion=LedgerEntry.Direction.CREDITO).aggregate(
            total=Sum('monto')
        )['total'] or Decimal('0.0000')

        total_debitos = LedgerEntry.objects.filter(direccion=LedgerEntry.Direction.DEBITO).aggregate(
            total=Sum('monto')
        )['total'] or Decimal('0.0000')

        # Invariante: La suma global de débitos y créditos siempre es cero
        self.assertEqual(total_creditos, total_debitos)
        self.assertEqual(total_creditos - total_debitos, Decimal('0.0000'))
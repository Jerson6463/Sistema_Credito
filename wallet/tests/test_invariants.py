from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db.models import Sum
from hypothesis import given, settings
from hypothesis import strategies as st
from hypothesis.extra.django import TestCase

from wallet.models import Account, LedgerEntry
from wallet.services import ejecutar_transferencia

class TestInvariantesFinancieros(TestCase):
    
    def setUp(self):
        """
        Configuración aislada. Hypothesis ejecutará este bloque ANTES de cada 
        uno de los ejemplos generados por @given, asegurando una base de datos limpia.
        """
        self.billetera_casa = Account.objects.create(
            nombre="Billetera de la Casa",
            tipo=Account.AccountType.BILLETERA_CASA
        )
        self.billetera_usuario = Account.objects.create(
            nombre="Billetera del Usuario",
            tipo=Account.AccountType.BILLETERA_USUARIO
        )

    @given(monto=st.decimals(min_value=Decimal('0.0001'), max_value=Decimal('1000000.0000'), places=4))
    @settings(max_examples=50)
    def test_suma_global_siempre_es_cero(self, monto):
        """
        Invariante 1: La suma total de créditos menos débitos en el sistema siempre debe ser 0.
        """
        ejecutar_transferencia(self.billetera_casa, self.billetera_usuario, monto)

        total_creditos = LedgerEntry.objects.filter(direccion=LedgerEntry.Direction.CREDITO).aggregate(
            total=Sum('monto')
        )['total'] or Decimal('0.0000')

        total_debitos = LedgerEntry.objects.filter(direccion=LedgerEntry.Direction.DEBITO).aggregate(
            total=Sum('monto')
        )['total'] or Decimal('0.0000')

        self.assertEqual(total_creditos, total_debitos)
        self.assertEqual(total_creditos - total_debitos, Decimal('0.0000'))

    @given(monto=st.decimals(min_value=Decimal('0.0001'), max_value=Decimal('500.0000'), places=4))
    @settings(max_examples=50)
    def test_ninguna_billetera_termina_con_saldo_negativo(self, monto):
        """
        Invariante 2: Ninguna billetera de usuario puede terminar con saldo negativo.
        """
        # Intentamos retirar dinero del usuario hacia la casa, pero el usuario acaba de ser creado
        # en el setUp (saldo 0). Por lo tanto, SIEMPRE debe lanzar la excepción de validación.
        with self.assertRaisesMessage(ValidationError, "Saldo insuficiente para realizar la operacion."):
            ejecutar_transferencia(self.billetera_usuario, self.billetera_casa, monto)
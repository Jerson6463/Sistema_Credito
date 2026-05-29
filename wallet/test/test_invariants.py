import pytest
from decimal import Decimal
from hypothesis import given, settings, strategies as st
from django.db.models import Sum

from wallet.models import Account, LedgerEntry
from wallet.services import transfer_funds

pytestmark = pytest.mark.django_db(transaction = True)

@pytest.fixture
def setup_accounts():
    """Fixture para crear las cuentas base necesar"""
    house_account = Account.objects.create(
        name = "Casa",
        type = "house_wallet"
    )
    
    user_account = Account.objects.create(
        name = "Usuario 1",
        type = "user_wallet"
    )

    return house_account, user_account

class TestFinancialInvariants:

    @given(amount=st.decimals(min_value=Decimal('0.0001'), max_value=Decimal('1000000.0000'), places=4))
    @settings(max_examples=50) # Hypothesis ejecutará este test 50 veces con montos aleatorios

    def test_global_sum_is_always_zero(self, setup_accounts, amount):
        """
        Prueba la invariate: "La suma global de debitos y creditos siempre es cero
        """
        house_account, user_account = setup_accounts

        #Ejecutar una transferencia simulada
        transfer_funds(
            from_account = house_account,
            to_account = user_account,
            amount = amount
        )

        #Verificamos que los creditos menos los debitos sumen exactamente 0 a nivel global
        credits = LedgerEntry.objects.filter(direction = 'CREDIT').aggregate(Sum('amount'))['amount__sum'] or Decimal('0.0000')
        debits = LedgerEntry.objects.filter(direction = 'DEBIT').aggregate(Sum('amount'))['amount__sum'] or Decimal('0.0000')

        assert credits - debits == Decimal('0.0000')

@given(amount = st.decimal(min_value = Decimal ('0.0001'), max_value = Decimal ('500.0000'), places = 4))
def test_no_wallet_ends_with_negative_balance(self, setup_accounts, amount):
    """
    Prueba la invariante: "Ningun wallet termina con saldo negativo"
    """
    house_account, user_account = setup_accounts

    # Le damos un saldo inicial
    transfer_funds (from_account = house_account, to_account = user_account, amount = Decimal('100.000'))

    # Intentamos hacer un retiro aleatorio
    try:
        transfer_funds (from_account = user_account, to_account = house_account, amount = amount)
    except ValueError:
        #Si el monto a retirar es mayor a 100, la funcion debe lanzar un error y abortar
        pass

    # El saldo final del usuario jamas debe ser menor a 0
    user_credits = LedgerEntry.objects.filter(account = user_account, direction = 'CREDIT').aggregate(Sum('amount'))['amount__sum'] or Decimal('0.0000')
    user_debits = LedgerEntry.objects.filter(account = user_account, direction = 'DEBIT').aggregate(Sum('amount'))['amount__sum'] or Decimal('0.0000')

    balance = user_credits - user_debits
    assert balance >= Decimal('0.0000')

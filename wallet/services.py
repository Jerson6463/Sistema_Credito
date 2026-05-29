import uuid
from decimal import Decimal
from django.db import transaction
from django.core.exceptions import ValidationError
from .models import Account, LedgerEntry

@transaction.atomic
def ejecutar_transferencia(cuenta_origen: Account, cuenta_destino: Account, monto: Decimal, objeto_referencia=None) -> uuid.UUID:
    """
    Ejecuta una transferencia de fondos entre dos cuentas garantizando la partida doble
    y el bloqueo de filas para evitar condiciones de carrera (doble gasto).
    """

    if monto <= Decimal('0.0000'):
        raise ValidationError("El monto a transferir debe ser estrictamente mayor a cero")
    
    if cuenta_origen.id == cuenta_destino.id:
        raise ValidationError("No se puede transferir fondos a la misma cuenta")
    
    # 1. Bloqueo pesimista (Prevencion de Doble Gasto y Deadlocks)
    # Se bloquean ambas filas en la BD hasya que termine la transaccion
    # Es VITAL ordenar por 'id' para evitar deadlocks si dos transacciones cruzadas ocurren al mismo tiempo
    cuentas = Account.objects.select_for_update().filter(
        id__in=[cuenta_origen.id, cuenta_destino.id]
    ).order_by('id')

    if cuentas.count() != 2:
        raise ValidationError("Una de las cuentas especificadas no existe.")
    
    # Refrescar las instancias con los datos bloqueados directamente desde la BD
    cuenta_origen = cuentas.get(id=cuenta_origen.id)
    cuenta_destino = cuentas.get(id=cuenta_destino.id)

    # 2. Validacion de Saldo
    # Verifiamos que el origen tenga fondos suficientes (las cuentas de la casa pueden
    # puede operar en negativo, pero los usuarios no)

    if cuenta_origen.tipo == Account.AccountType.BILLETERA_USUARIO and cuenta_origen.balance < monto:
        raise ValidationError("Saldo insuficiente para realizar la operacion.")
    
    # 3. Creacion de la partida doble
    id_transaccion = uuid.uuid4()

    #Debito a la cuenta origen(-)
    LedgerEntry.objects.create(
        cuenta = cuenta_origen,
        monto = monto,
        direccion = LedgerEntry.Direction.DEBITO,
        transaccion_id = id_transaccion,
        referencia_objeto = objeto_referencia
    )

    # Credito a la cuenta destino (+)
    LedgerEntry.objects.create(
        cuenta=cuenta_destino,
        monto=monto,
        direccion=LedgerEntry.Direction.CREDITO,
        transaccion_id=id_transaccion,
        referencia_objeto=objeto_referencia
    )

    return id_transaccion



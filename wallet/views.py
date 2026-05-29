from django.shortcuts import render, get_object_or_404

from decimal import Decimal
from django.core.exceptions import ValidationError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .models import Account
from .services import ejecutar_transferencia

class SaldoWalletAPIView(APIView):
    """
    Para consultar el saldo actual de la billetera del usuario autenticado
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        #Buscamos la billetera especifica del usuario que hace la peticion
        billetera = get_object_or_404(
            Account,
            user=request.user,
            tipo = Account.AccountType.BILLETERA_USUARIO
        )

        # Convertir el decimal a string en Json
        return Response({
            "billetera_id": billetera.id,
            "nombre_cuenta": billetera.nombre,
            "saldo": str(billetera.balance)
        }, status=status.HTTP_200_OK)
    
class TransaccionWalletAPIView(APIView):
    """Realizar depositos y retiros"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        tipo_operacion = request.data.get("tipo_operacion") # Espera: 'DEPOSITO' o 'RETIRO'
        monto_input = request.data.get("monto")

        # Validaciones preliminares de formato de API
        if tipo_operacion not in ['DEPOSITO', 'RETIRO']:
            return Response(
                {"error": "Tipo de operación inválido. Use 'DEPOSITO' o 'RETIRO'."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            monto = Decimal(str(monto_input))
        except (TypeError, ValueError):
            return Response(
                {"error": "El monto proporcionado no es un formato decimal válido."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Obtener las cuentas involucradas bajo el contexto de la transacción
        billetera_usuario = get_object_or_404(Account, user=request.user, tipo=Account.AccountType.BILLETERA_USUARIO)
        billetera_casa = get_object_or_404(Account, tipo=Account.AccountType.BILLETERA_CASA)

        try:
            if tipo_operacion == 'DEPOSITO':
                # El dinero se mueve desde la casa hacia el usuario
                id_transaccion = ejecutar_transferencia(
                    cuenta_origen=billetera_casa,
                    cuenta_destino=billetera_usuario,
                    monto=monto
                )
            else:
                # RETIRO: El dinero se mueve desde el usuario hacia la casa
                id_transaccion = ejecutar_transferencia(
                    cuenta_origen=billetera_usuario,
                    cuenta_destino=billetera_casa,
                    monto=monto
                )

            return Response({
                "mensaje": f"{tipo_operacion} ejecutado exitosamente.",
                "transaccion_id": id_transaccion,
                "nuevo_saldo": str(billetera_usuario.balance)
            }, status=status.HTTP_201_CREATED)

        except ValidationError as e:
            # Capturamos los errores lanzados por el servicio (ej. Saldo insuficiente)
            # y respondemos con un HTTP 400 Bad Request limpio.
            return Response({"error": e.message}, status=status.HTTP_400_BAD_REQUEST)






from django.urls import path
from .views import SaldoWalletAPIView, TransaccionWalletAPIView

urlpatterns = [
    path('saldo/', SaldoWalletAPIView.as_view(), name='wallet-saldo'),
    path('transaccion/', TransaccionWalletAPIView.as_view(), name='wallet-transaccion'),
]
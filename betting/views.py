from celery.result import AsyncResult
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from rest_framework import status
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from betting.models import Event, Market, Selection
from betting.serializers import CriticalEventSerializer, SettleMarketSerializer, UpdateOddsSerializer
from betting.services import update_selection_odds
from betting.tasks import ping_task, settle_market_bets_task, suspend_market_task


@require_GET
def health_check(request):
    """Comprueba que Django responde (HTTP + ASGI vía Daphne)."""
    return JsonResponse(
        {
            'status': 'ok',
            'asgi': True,
            'channels': True,
            'celery': True,
        }
    )


@require_GET
def celery_ping(request):
    """Encola ping_task y devuelve el task_id para verificar el worker."""
    result = ping_task.delay()
    return JsonResponse(
        {
            'status': 'queued',
            'task_id': result.id,
            'check_url': f'/api/celery/result/{result.id}/',
        }
    )


@require_GET
def celery_result(request, task_id: str):
    """Consulta el resultado de una tarea Celery por task_id."""
    result = AsyncResult(task_id)
    payload = {
        'task_id': task_id,
        'state': result.state,
    }
    if result.ready():
        payload['result'] = result.result
    return JsonResponse(payload)


class SettleMarketView(APIView):
    """Operador marca resultado y encola liquidación async (Integrante 3)."""

    permission_classes = [IsAdminUser]

    def post(self, request, market_id):
        serializer = SettleMarketSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        market = Market.objects.filter(pk=market_id).first()
        if market is None:
            return Response({'detail': 'Mercado no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        winning_selection_id = serializer.validated_data['winning_selection_id']
        if not market.selections.filter(pk=winning_selection_id).exists():
            return Response(
                {'detail': 'La selección ganadora no pertenece a este mercado.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        async_result = settle_market_bets_task.delay(str(market_id), str(winning_selection_id))
        return Response(
            {
                'status': 'queued',
                'task_id': async_result.id,
                'market_id': str(market_id),
                'winning_selection_id': str(winning_selection_id),
                'check_url': f'/api/celery/result/{async_result.id}/',
            },
            status=status.HTTP_202_ACCEPTED,
        )


class CriticalEventView(APIView):
    """Suspende mercado in-play ante gol/expulsión y programa reactivación."""

    permission_classes = [IsAdminUser]

    def post(self, request, event_id):
        serializer = CriticalEventSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        event = Event.objects.filter(pk=event_id).first()
        if event is None:
            return Response({'detail': 'Evento no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        market_id = serializer.validated_data['market_id']
        market = Market.objects.filter(pk=market_id, event_id=event_id).first()
        if market is None:
            return Response(
                {'detail': 'Mercado no encontrado para este evento.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        async_result = suspend_market_task.delay(
            event_id=str(event_id),
            market_id=str(market_id),
            reason=serializer.validated_data['reason'],
            suspension_seconds=serializer.validated_data.get('suspension_seconds'),
        )
        return Response(
            {
                'status': 'queued',
                'task_id': async_result.id,
                'event_id': str(event_id),
                'market_id': str(market_id),
                'check_url': f'/api/celery/result/{async_result.id}/',
            },
            status=status.HTTP_202_ACCEPTED,
        )


class UpdateOddsView(APIView):
    """Operador actualiza cuota; emite WebSocket solo si hubo cambio."""

    permission_classes = [IsAdminUser]

    def patch(self, request, selection_id):
        serializer = UpdateOddsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        selection = Selection.objects.filter(pk=selection_id).first()
        if selection is None:
            return Response({'detail': 'Selección no encontrada.'}, status=status.HTTP_404_NOT_FOUND)

        result = update_selection_odds(
            selection_id=selection.id,
            current_odds=serializer.validated_data['current_odds'],
            is_active=serializer.validated_data.get('is_active'),
        )
        return Response(result, status=status.HTTP_200_OK)

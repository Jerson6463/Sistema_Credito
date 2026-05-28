from decimal import Decimal

from rest_framework import serializers


class SettleMarketSerializer(serializers.Serializer):
    winning_selection_id = serializers.UUIDField()


class CriticalEventSerializer(serializers.Serializer):
    market_id = serializers.UUIDField()
    reason = serializers.ChoiceField(
        choices=['goal', 'red_card', 'critical_event'],
        default='critical_event',
    )
    suspension_seconds = serializers.IntegerField(required=False, min_value=1, max_value=300)


class UpdateOddsSerializer(serializers.Serializer):
    current_odds = serializers.DecimalField(max_digits=18, decimal_places=4, min_value=Decimal('1.0100'))
    is_active = serializers.BooleanField(required=False)

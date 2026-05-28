from django.contrib import admin, messages

from betting.models import Bet, Event, Market, Selection


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_time', 'status')
    list_filter = ('status',)
    search_fields = ('name',)


@admin.register(Market)
class MarketAdmin(admin.ModelAdmin):
    list_display = ('event', 'type', 'is_active')
    list_filter = ('type', 'is_active')
    actions = ['queue_settlement']

    @admin.action(description='Liquidar mercado (requiere selección ganadora en consola)')
    def queue_settlement(self, request, queryset):
        messages.warning(
            request,
            'Use POST /api/admin/markets/<id>/settle/ con winning_selection_id.',
        )


@admin.register(Selection)
class SelectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'market', 'current_odds')
    list_filter = ('market__event',)


@admin.register(Bet)
class BetAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'selection', 'stake', 'locked_odds', 'status', 'created_at')
    list_filter = ('status',)
    readonly_fields = ('transaction_id', 'created_at')

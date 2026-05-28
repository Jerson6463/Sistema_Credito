from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from betting.models import Market, Selection
from betting.realtime import broadcast_odds_update


@receiver(pre_save, sender=Selection)
def cache_selection_previous_odds(sender, instance: Selection, **kwargs):
    if not instance.pk:
        instance._previous_odds = None
        return
    previous = Selection.objects.filter(pk=instance.pk).values_list('current_odds', flat=True).first()
    instance._previous_odds = previous


@receiver(post_save, sender=Selection)
def broadcast_selection_odds_change(sender, instance: Selection, created: bool, **kwargs):
    if kwargs.get('raw'):
        return

    previous_odds = getattr(instance, '_previous_odds', None)
    if created:
        previous_odds = None

    market = instance.market
    broadcast_odds_update(
        event_id=str(market.event_id),
        selection_id=str(instance.id),
        market_id=str(market.id),
        current_odds=instance.current_odds,
        previous_odds=previous_odds,
        is_active=market.is_active,
        previous_is_active=market.is_active,
    )


@receiver(pre_save, sender=Market)
def cache_market_previous_active(sender, instance: Market, **kwargs):
    if not instance.pk:
        instance._previous_is_active = None
        return
    previous = Market.objects.filter(pk=instance.pk).values_list('is_active', flat=True).first()
    instance._previous_is_active = previous


@receiver(post_save, sender=Market)
def broadcast_market_active_change(sender, instance: Market, **kwargs):
    if kwargs.get('raw'):
        return

    previous_is_active = getattr(instance, '_previous_is_active', None)
    if previous_is_active is None or previous_is_active == instance.is_active:
        return

    selection = instance.selections.order_by('name').first()
    if selection is None:
        return

    broadcast_odds_update(
        event_id=str(instance.event_id),
        selection_id=str(selection.id),
        market_id=str(instance.id),
        current_odds=selection.current_odds,
        previous_odds=selection.current_odds,
        is_active=instance.is_active,
        previous_is_active=previous_is_active,
    )

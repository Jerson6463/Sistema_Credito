from django.urls import path

from betting import views

urlpatterns = [
    path('health/', views.health_check, name='health-check'),
    path('celery/ping/', views.celery_ping, name='celery-ping'),
    path('celery/result/<str:task_id>/', views.celery_result, name='celery-result'),
    path(
        'admin/markets/<uuid:market_id>/settle/',
        views.SettleMarketView.as_view(),
        name='admin-settle-market',
    ),
    path(
        'admin/events/<uuid:event_id>/critical-event/',
        views.CriticalEventView.as_view(),
        name='admin-critical-event',
    ),
    path(
        'admin/selections/<uuid:selection_id>/odds/',
        views.UpdateOddsView.as_view(),
        name='admin-update-odds',
    ),
]

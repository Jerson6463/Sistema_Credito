from django.urls import re_path

from betting import consumers

websocket_urlpatterns = [
    re_path(
        r'ws/events/(?P<event_id>[0-9a-f-]+)/$',
        consumers.EventOddsConsumer.as_asgi(),
    ),
]

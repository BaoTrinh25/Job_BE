from django.urls import path
from .consumers import ChatConsumer

websocket_urlpatterns = [
    path('ws/chat/<str:room_name>/', ChatConsumer.as_asgi()),
    path(r'ws/chat/(?P<room_name>\w+)/$', ChatConsumer.as_asgi()),
]

from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/activity/<int:activity_id>/', consumers.ChatConsumer.as_asgi(), name='chat_ws'),
]
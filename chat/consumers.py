import json
from logging import getLogger

from asgiref.sync import async_to_sync
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer, InMemoryChannelLayer
from django.db.models import Q
from django.urls import Resolver404

from gantt.models import Activity

logger = getLogger(__name__)
channel_layer: InMemoryChannelLayer = get_channel_layer()
GROUP_PREFIX = "activity_{}"


def send_comment_to_channel(activity_id: int, data: dict):
    group_name = GROUP_PREFIX.format(activity_id)
    logger.info(f'new comment sent to {group_name}')

    async_to_sync(channel_layer.group_send)(
        group_name, {"type": "chat_message",
                     "data": data}
    )


class ChatConsumer(AsyncWebsocketConsumer):
    async def dispatch(self, message):
        await super(ChatConsumer, self).dispatch(message)

    async def connect(self):
        activity_id = self.scope['url_route']['kwargs'].get('activity_id')

        if not self.can_connect(activity_id):
            logger.info(f'Not authorized user "{self.scope["user"]}"')
            raise Resolver404

        await self.accept()

        self.room_group_name = GROUP_PREFIX.format(activity_id)

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

    @database_sync_to_async
    def can_connect(self, activity_id) -> bool:
        user = self.scope["user"]

        return user.is_authenticated and Activity.objects.filter(
            Q(task__project__project_manager=user) |
            Q(task__project__team__teammember__user=user), id=activity_id).exists()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def chat_message(self, event):
        data: dict = event['data']
        author_id = data['author']

        if self.scope['user'].id != author_id:
            await self.send(text_data=json.dumps(data))

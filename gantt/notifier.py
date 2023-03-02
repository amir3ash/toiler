from json import dumps as json_dumps
from typing import Type, Union

from django.conf import settings
from redis import StrictRedis, Redis

_redis_cli = StrictRedis(host=settings.NOTIFIER['HOST'], port=settings.NOTIFIER['PORT'])
_EVENTS = {"added", "updated", "deleted"}
_TYPES = {"project", "task", "activity", "state", "assigned", "user"}


class RedisNotifier:
    _EVENTS = _EVENTS
    _TYPES = _TYPES

    def __init__(self, r: Redis = None, channel='changes'):
        if not r:
            r = _redis_cli

        self.redis = r
        self.channel = channel

    def _publish(self, event, obj_type, object_id, parent_id):
        data_capsule = {
            "event": event,
            "type": obj_type,
            "id": object_id,
            "parent": parent_id
        }

        str_json = json_dumps(data_capsule)
        self.redis.publish(self.channel, str_json)


class Notifier(RedisNotifier):
    def notify(self, event: str, obj_type: str, object_id: int, parent_id: Union[int, Type[int]]):
        """
            publish event to **"changes"** redis channel.

            :param parent_id:
            :param object_id:
            :param event: "added" or "updated" or "deleted"
            :param obj_type:
            :return: None
            """
        if event not in self._EVENTS:
            raise Exception(f"event is not in {self._EVENTS}")

        if obj_type not in self._TYPES:
            raise Exception(f'obj_type is not in {self._TYPES}')

        self._publish(event, obj_type, object_id, parent_id)


class BulkNotify(RedisNotifier):
    def __init__(self, event: str, obj_type: str, redis_client: Redis = None, channel='changes'):
        """
        publish event to **"changes"** redis channel via Pipeline.

        :param event: "added" or "updated" or "deleted"
        :param obj_type:
        """
        if event not in self._EVENTS:
            raise Exception(f"event not in {self._EVENTS}")

        if obj_type not in self._TYPES:
            raise Exception(f'obj_type is not in {self._TYPES}')

        super(BulkNotify, self).__init__(redis_client, channel)

        self.event = event
        self.obj_type = obj_type

    def __enter__(self):
        self.pipe = self.redis.pipeline(transaction=False)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.pipe.execute()

    def notify(self, object_id: int, parent_id: Union[int, Type[int]]):
        self._publish(self.event, self.obj_type, object_id, parent_id)


_notifier = Notifier()
notify = _notifier.notify

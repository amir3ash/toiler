from json import dumps as json_dumps
from typing import Type, Union
from redis import StrictRedis

red = StrictRedis(host='127.0.0.1', port=6379)

_EVENTS = {"added", "updated", "deleted"}


def notify(event: str, obj_type: str, object_id: int, parent_id: Union[int, Type[int]]):
    """
    publish event to **"changes"** redis channel.

    :param parent_id:
    :param object_id:
    :param event: "added" or "updated" or "deleted"
    :param obj_type:
    :return: None
    """
    if event not in _EVENTS:
        raise Exception(f"event not in {_EVENTS}")

    data_capsule = {
        "event": event,
        "type": obj_type,
        "id": object_id,
        "parent": parent_id
    }

    str_json = json_dumps(data_capsule)
    red.publish('changes', str_json)


class BulkNotify:
    def __init__(self, event: str, obj_type: str):
        """
        publish event to **"changes"** redis channel via Pipeline.

        :param event: "added" or "updated" or "deleted"
        :param obj_type:
        """
        if event not in _EVENTS:
            raise Exception(f"event not in {_EVENTS}")

        self.event = event
        self.obj_type = obj_type

    def __enter__(self):
        self.pipe = red.pipeline(transaction=False)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.pipe.execute()

    def notify(self, object_id: int, parent_id: Union[int, Type[int]]):
        data_capsule = {
            "event": self.event,
            "type": self.obj_type,
            "id": object_id,
            "parent": parent_id
        }

        str_json = json_dumps(data_capsule)
        self.pipe.publish('changes', str_json)

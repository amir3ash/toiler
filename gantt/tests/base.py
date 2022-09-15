import functools
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import ClassVar, Optional, Callable, Dict

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

Usr = get_user_model()
_PASSWORD = 'amir12345amir'


def _create_user(username: str) -> Usr:
    return Usr.objects.create_user(username, f'{username}@test.com', password=_PASSWORD)


class GanttMixin:
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.create_base_users()

    @classmethod
    def create_base_users(cls):
        """
        Create users {user, username1, username2, username3, username4}
        """
        cls.user = _create_user('username')
        cls.username1 = _create_user('username1')
        cls.username2 = _create_user('username2')
        cls.username3 = _create_user('username3')
        cls.username4 = _create_user('username4')

    def create_user(self, username: str):
        user = _create_user(username)
        setattr(self, username, user)


class GanttApiTestCase(APITestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        def login_wrapper(*wrapper_args, **wrapper_kwargs):
            def login(*rgs, **kws):
                self.client.login(*rgs, password=_PASSWORD, **kws)

            return login(*wrapper_args, **wrapper_kwargs)

        self.client.login = login_wrapper

    def test_a(self):
        self.client.login()


class TimerError(Exception):
    """A custom exception used to report errors in use of Timer class"""


@dataclass
class Timer:
    def __init__(self, text: Optional[str] = '"{}" elapsed time in {:f} seconds',
                 logger: Optional[Callable[[str], None]] = print):
        self._start_time = {}
        self.timers = defaultdict(float)
        self.text = text
        self.logger = logger

    def start(self, name: str) -> None:
        """Start a new timer"""
        if name in self._start_time:
            raise TimerError(f"Timer is running. Use .stop() to stop it")

        self._start_time[name] = time.perf_counter()

    def stop(self, name: str) -> float:
        """Stop the timer, and report the elapsed time"""
        stop_time = time.perf_counter()
        if self._start_time.get(name) is None:
            raise TimerError(f"Timer is not running. Use .start() to start it")

        # Calculate elapsed time
        elapsed_time = stop_time - self._start_time[name]
        del self._start_time[name]

        # Report elapsed time
        if self.logger:
            self.logger(self.text.format(name, elapsed_time))

        self.timers[name] += elapsed_time

        return elapsed_time

    def measure(self, name: str):
        return self.ContextManager(self, name)

    class ContextManager:
        def __init__(self, timer, name: str):
            self.timer = timer
            self.name = name

        def __enter__(self):
            self.timer.start(self.name)

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.timer.stop(self.name)

        def __call__(self, func):
            """Support using Timer as a decorator"""

            @functools.wraps(func)
            def wrapper_timer(*args, **kwargs):
                with self:
                    return func(*args, **kwargs)

            return wrapper_timer

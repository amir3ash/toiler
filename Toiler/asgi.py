"""
ASGI config for Toiler project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/howto/deployment/asgi/
"""

import os

from channels.auth import AuthMiddleware
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from channels.sessions import CookieMiddleware, SessionMiddleware
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Toiler.settings')

if os.getenv('DJANGO_SETTINGS_MODULE'):
    os.environ['DJANGO_SETTINGS_MODULE'] = os.getenv('DJANGO_SETTINGS_MODULE')

django_asgi_app = get_asgi_application()

from chat.middlewares import HandleRouteNotFoundMiddleware, CsrfTokenCheckMiddleware
from chat.urls import websocket_urlpatterns


def middleware_stack(inner):
    return AllowedHostsOriginValidator(
        CookieMiddleware(CsrfTokenCheckMiddleware(SessionMiddleware(AuthMiddleware(inner)))))


application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket":
        HandleRouteNotFoundMiddleware(
            middleware_stack(
                URLRouter(websocket_urlpatterns)
            )
        )
})

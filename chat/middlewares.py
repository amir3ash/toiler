import functools
from logging import getLogger
from urllib.parse import parse_qsl

from autobahn.websocket import ConnectionDeny
from channels.middleware import BaseMiddleware
from channels.security.websocket import WebsocketDenier
from daphne.ws_protocol import WebSocketProtocol
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.http.request import HttpHeaders
from django.middleware.csrf import CSRF_TOKEN_LENGTH, CSRF_SECRET_LENGTH, InvalidTokenFormat, REASON_INCORRECT_LENGTH, \
    invalid_token_chars_re, REASON_INVALID_CHARACTERS, _unmask_cipher_token, RejectRequest, REASON_NO_CSRF_COOKIE, \
    REASON_CSRF_TOKEN_MISSING, CSRF_SESSION_KEY
from django.urls import Resolver404
from django.utils.crypto import constant_time_compare

logger = getLogger(__name__)

CSRF_QUERY_NAME = 'csrftoken'


class CsrfTokenCheckMiddleware(BaseMiddleware):

    @staticmethod
    def _check_token_format(token):
        """
        Raise an InvalidTokenFormat error if the token has an invalid length or
        characters that aren't allowed. The token argument can be a CSRF cookie
        secret or non-cookie CSRF token, and either masked or unmasked.
        """
        if len(token) not in (CSRF_TOKEN_LENGTH, CSRF_SECRET_LENGTH):
            raise InvalidTokenFormat(REASON_INCORRECT_LENGTH)
        # Make sure all characters are in CSRF_ALLOWED_CHARS.
        if invalid_token_chars_re.search(token):
            raise InvalidTokenFormat(REASON_INVALID_CHARACTERS)

    @staticmethod
    def _does_token_match(request_csrf_token, csrf_secret):
        """
        Return whether the given CSRF token matches the given CSRF secret, after
        unmasking the token if necessary.

        This function assumes that the request_csrf_token argument has been
        validated to have the correct length (CSRF_SECRET_LENGTH or
        CSRF_TOKEN_LENGTH characters) and allowed characters, and that if it has
        length CSRF_TOKEN_LENGTH, it is a masked secret.
        """
        # Only unmask tokens that are exactly CSRF_TOKEN_LENGTH characters long.
        if len(request_csrf_token) == CSRF_TOKEN_LENGTH:
            request_csrf_token = _unmask_cipher_token(request_csrf_token)
        assert len(request_csrf_token) == CSRF_SECRET_LENGTH
        return constant_time_compare(request_csrf_token, csrf_secret)

    @staticmethod
    def _get_token(query_string: bytes):
        """ get token from query. it may raise `KeyError` if the parameter not found."""

        queries = parse_qsl(query_string.decode(), separator='&')
        for name, value in queries:
            if name == CSRF_QUERY_NAME:
                return value
        raise KeyError

    def _check_token(self, scope: dict):
        # Access csrf_secret via self._get_secret() as rotate_token() may have
        # been called by an authentication middleware during the
        # process_request() phase.
        try:
            csrf_secret = self._get_secret(scope)
        except InvalidTokenFormat as exc:
            raise RejectRequest(f"CSRF cookie {exc.reason}.")

        if csrf_secret is None:
            raise RejectRequest(REASON_NO_CSRF_COOKIE)

        # Check non-cookie token for match.

        try:
            # This can have length CSRF_SECRET_LENGTH or CSRF_TOKEN_LENGTH,
            # depending on whether the client obtained the token from
            # the DOM or the cookie (and if the cookie, whether the cookie
            # was masked or unmasked).

            request_csrf_token = self._get_token(scope['query_string'])

        except KeyError:
            raise RejectRequest(REASON_CSRF_TOKEN_MISSING)
        token_source = settings.CSRF_HEADER_NAME

        try:
            self._check_token_format(request_csrf_token)
        except InvalidTokenFormat as exc:
            reason = self._bad_token_message(exc.reason, token_source)
            raise RejectRequest(reason)

        if not self._does_token_match(request_csrf_token, csrf_secret):
            reason = self._bad_token_message("incorrect", token_source)
            raise RejectRequest(reason)

    @staticmethod
    def _bad_token_message(reason, token_source):
        if token_source != "POST":
            # Assume it is a settings.CSRF_HEADER_NAME value.
            header_name = HttpHeaders.parse_header_name(token_source)
            token_source = f"the {header_name!r} HTTP header"
        return f"CSRF token from {token_source} {reason}."

    def _get_secret(self, scope):
        """
        Return the CSRF secret originally associated with the request, or None
        if it didn't have one.

        If the CSRF_USE_SESSIONS setting is false, raises InvalidTokenFormat if
        the request's secret has invalid characters or an invalid length.
        """
        if settings.CSRF_USE_SESSIONS:
            try:
                csrf_secret = scope['session'].get(CSRF_SESSION_KEY)
            except AttributeError:
                raise ImproperlyConfigured(
                    "CSRF_USE_SESSIONS is enabled, but request.session is not "
                    "set. SessionMiddleware must appear before CsrfViewMiddleware "
                    "in MIDDLEWARE."
                )
        else:
            try:
                csrf_secret = scope['cookies'][settings.CSRF_COOKIE_NAME]
            except KeyError:
                csrf_secret = None
            else:
                # This can raise InvalidTokenFormat.
                self._check_token_format(csrf_secret)
        if csrf_secret is None:
            return None
        # Django versions before 4.0 masked the secret before storing.
        if len(csrf_secret) == CSRF_TOKEN_LENGTH:
            csrf_secret = _unmask_cipher_token(csrf_secret)
        return csrf_secret

    @staticmethod
    async def _reject(scope, reason, send, receive):
        logger.warning("Forbidden (%s): %s", reason, scope['path'])

        denier = WebsocketDenier(None)
        return await denier(scope, receive, send)

    async def __call__(self, scope, receive, send):
        if scope["type"] == 'websocket':
            try:
                self._check_token(scope)
            except RejectRequest as exc:
                return await self._reject(scope, exc.reason, send, receive)

        return await super().__call__(scope, receive, send)


class HandleRouteNotFoundMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send: functools.partial):

        try:
            # inner_instance = await self.inner(scope, receive, send)

            return await super().__call__(scope, receive, send)
        except (Resolver404, ValueError) as e:
            if 'No route found for path' not in str(e) and \
                    scope["type"] not in ['http', 'websocket']:
                raise e

            logger.warning(e)

            # raise Resolver404(e)

            try:
                if scope["type"] == "websocket":
                    if send.args:
                        ws_client: WebSocketProtocol = send.args[0]
                        ws_client.handshake_deferred.errback(
                            ConnectionDeny(code=404, reason="Not Found")
                        )

                    return await self.handle_ws_route_error(scope, receive, send)

            except Exception as e:
                logger.exception(e)
                raise e

    @staticmethod
    async def handle_ws_route_error(scope, receive, send):
        await send({"type": "websocket.close"})

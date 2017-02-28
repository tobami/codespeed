import logging
from functools import wraps
from django.contrib.auth import authenticate, login
from django.http import HttpResponse, HttpResponseForbidden
from django.conf import settings
from base64 import b64decode

__ALL__ = ['basic_auth_required']
logger = logging.getLogger(__name__)


def basic_auth_required(realm='default'):
    def _helper(func):
        @wraps(func)
        def _decorator(request, *args, **kwargs):
            allowed = False
            logger.info('request is secure? {}'.format(request.is_secure()))
            if settings.ALLOW_ANONYMOUS_POST:
                logger.debug('allowing anonymous post')
                allowed = True
            elif hasattr(request, 'user') and request.user.is_authenticated():
                allowed = True
            elif 'HTTP_AUTHORIZATION' in request.META:
                logger.debug('checking for http authorization header')
                if settings.REQUIRE_SECURE_AUTH and not request.is_secure():
                    return insecure_connection_response()
                http_auth = request.META['HTTP_AUTHORIZATION']
                authmeth, auth = http_auth.split(' ', 1)
                if authmeth.lower() == 'basic':
                    username, password = decode_basic_auth(auth)
                    user = authenticate(username=username, password=password)
                    if user is not None and user.is_active:
                        logger.info(
                            'Authentication succeeded for {}'.format(username))
                        login(request, user)
                        allowed = True
                    else:
                        logger.info(
                            'Failed auth for {}'.format(username))
                        return HttpResponseForbidden()
            if allowed:
                return func(request, *args, **kwargs)

            if settings.REQUIRE_SECURE_AUTH and not request.is_secure():
                logger.debug('not requesting auth over an insecure channel')
                return insecure_connection_response()
            else:
                res = HttpResponse()
                res.status_code = 401
                res.reason_phrase = 'Unauthorized'
                res['WWW-Authenticate'] = 'Basic realm="{}"'.format(realm)
                return res
        return _decorator

    return _helper


def insecure_connection_response():
    return HttpResponseForbidden('Secure connection required')


def decode_basic_auth(auth):
    authb = b64decode(auth.strip())
    auth = authb.decode()
    return auth.split(':', 1)

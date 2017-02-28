import logging
from functools import wraps
from django.contrib.auth import authenticate, login
from django.http import HttpResponse, HttpResponseForbidden
from django.conf import settings
from base64 import b64decode

__ALL__ = ['basic_auth_required']


def basic_auth_required(realm='default'):
    def _helper(func):
        @wraps(func)
        def _decorator(request, *args, **kwargs):
            allowed = False
            logging.info('request is secure? {}'.format(request.is_secure()))
            if settings.ALLOW_ANONYMOUS_POST:
                allowed = True
            elif 'HTTP_AUTHORIZATION' in request.META:
                if settings.REQUIRE_SECURE_AUTH and not request.is_secure():
                    return insecure_connection_response()
                http_auth = request.META['HTTP_AUTHORIZATION']
                authmeth, auth = http_auth.split(' ', 1)
                if authmeth.lower() == 'basic':
                    username, password = decode_basic_auth(auth)
                    user = authenticate(username=username, password=password)
                    if user is not None and user.is_active:
                        logging.info(
                            'Authentication succeeded for {}'.format(username))
                        login(request, user)
                        allowed = True
                    else:
                        return HttpResponseForbidden()
            if allowed:
                return func(request, *args, **kwargs)

            if settings.REQUIRE_SECURE_AUTH and not request.is_secure():
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

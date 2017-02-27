import logging
from functools import wraps
from django.contrib.auth import authenticate
from django.http import HttpResponse, HttpResponseForbidden
from base64 import b64decode


def basic_auth_required(realm='default'):
    def _helper(func):
        @wraps(func)
        def _decorator(request, *args, **kwargs):
            if 'HTTP_AUTHORIZATION' in request.META:
                http_auth = request.META['HTTP_AUTHORIZATION']
                authmeth, auth = http_auth.split(' ', 1)
                if authmeth.lower() == 'basic':
                    authb = b64decode(auth.strip())
                    auth = authb.decode()
                    username, password = auth.split(':', 1)
                    user = authenticate(username=username, password=password)
                    if user is not None:
                        logging.info(
                            'Authentication succeeded for {}'.format(username))
                        return func(request, *args, **kwargs)
                    else:
                        return HttpResponseForbidden()
            res = HttpResponse()
            res.status_code = 401
            res.reason_phrase = 'Unauthorized'
            res['WWW-Authenticate'] = 'Basic realm="{}"'.format(realm)
            return res
        return _decorator

    return _helper

# This is used for staging & production
import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "speed_pypy.settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

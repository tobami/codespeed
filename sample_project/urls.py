# -*- coding: utf-8 -*-

from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^', include('codespeed.urls'))
]

if settings.DEBUG:
    # needed for development server
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    urlpatterns += staticfiles_urlpatterns()

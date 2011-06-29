# -*- coding: utf-8 -*-

import os.path

from django.conf import settings
from django.conf.urls.defaults import patterns, include, handler404, handler500
from django.views.generic.simple import redirect_to
from django.core.urlresolvers import reverse
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
    (r'^admin/', include(admin.site.urls)),
)

urlpatterns += patterns(
    '',
    #('^$', redirect_to, {'url': '/speed/'}),
)

urlpatterns += patterns(
    '',
    (r'^', include('codespeed.urls')),
    #(r'^speed/', include('codespeed.urls')),
)

if settings.DEBUG:
    # needed for development server
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    urlpatterns += staticfiles_urlpatterns()

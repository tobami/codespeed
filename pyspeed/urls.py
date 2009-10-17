# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    (r'^trunk/', include('pyspeed.codespeed.urls')),
    (r'^admin/', include(admin.site.urls)),
)

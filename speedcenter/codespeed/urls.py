    # -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template, redirect_to
import settings

urlpatterns = patterns('',
    (r'^$', direct_to_template, {'template': 'home.html'}),
    (r'^about/$', direct_to_template, {'template': 'about.html'}),
)

urlpatterns += patterns('codespeed.views',
    (r'^overview/$', 'overview'),
    (r'^overview/table/$', 'getoverviewtable'),
    (r'^timeline/$', 'timeline'),
    (r'^timeline/json/$', 'gettimelinedata'),
)

urlpatterns += patterns('codespeed.views',
    # URL interface for adding results
    (r'^result/add/$', 'addresult'),
)

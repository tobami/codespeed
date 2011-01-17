# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template
from codespeed.feeds import LatestEntries

feeds = { 'latest': LatestEntries }


urlpatterns = patterns('',
    (r'^$', direct_to_template, {'template': 'home.html'}),
    (r'^about/$', direct_to_template, {'template': 'about.html'}),
    # RSS for reports
    (r'^feeds/(?P<url>.*)/$', 'django.contrib.syndication.views.feed', {'feed_dict': feeds}),
)

urlpatterns += patterns('codespeed.views',
    (r'^reports/$', 'reports'),
    (r'^changes/$', 'changes'),
    (r'^changes/table/$', 'getchangestable'),
    (r'^changes/logs/$', 'displaylogs'),
    (r'^timeline/$', 'timeline'),
    (r'^timeline/json/$', 'gettimelinedata'),
    (r'^comparison/$', 'comparison'),
    (r'^comparison/json/$', 'getcomparisondata'),
)

urlpatterns += patterns('codespeed.views',
    # URL interface for adding results
    (r'^result/add/$', 'addresult'),
)

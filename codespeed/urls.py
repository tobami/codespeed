# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from django.core.urlresolvers import reverse
from django.views.generic.simple import direct_to_template
from codespeed.feeds import LatestEntries

feeds = { 'latest': LatestEntries }


urlpatterns = patterns('',
    (r'^$', direct_to_template, {'template': 'home.html'}),
    (r'^about/$', direct_to_template, {'template': 'about.html'}),
    # RSS for reports
    (r'^feeds/(?P<url>.*)/$', LatestEntries()),
)

urlpatterns += patterns('codespeed.views',
    url(r'^reports/$', 'reports', name='reports'),
    url(r'^changes/$', 'changes', name='changes'),
    url(r'^changes/table/$', 'getchangestable', name='getchangestable'),
    url(r'^changes/logs/$', 'displaylogs', name='displaylogs'),
    url(r'^timeline/$', 'timeline', name='timeline'),
    url(r'^timeline/json/$', 'gettimelinedata', name='gettimelinedata'),
    url(r'^comparison/$', 'comparison', name='comparison'),
    url(r'^comparison/json/$', 'getcomparisondata', name='getcomparisondata'),
)

urlpatterns += patterns('codespeed.views',
    # URLs for adding results
    (r'^result/add/json/$', 'add_json_results'),
    (r'^result/add/$',      'add_result'),
)

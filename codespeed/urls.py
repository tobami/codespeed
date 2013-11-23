# -*- coding: utf-8 -*-
from django.conf.urls import patterns, include, url
from django.core.urlresolvers import reverse
from django.views.generic import TemplateView

from codespeed.feeds import LatestEntries

feeds = {'latest': LatestEntries}

urlpatterns = patterns('',
    (r'^$', TemplateView.as_view(template_name='home.html')),
    (r'^about/$', TemplateView.as_view(template_name='about.html')),
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
    (r'^result/add/$', 'add_result'),
)

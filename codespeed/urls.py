# -*- coding: utf-8 -*-
from django.conf.urls import patterns, url
from django.views.generic import TemplateView

from codespeed.feeds import LatestEntries, LatestSignificantEntries


urlpatterns = patterns('',
    url(r'^$', TemplateView.as_view(template_name='home.html'), name='home'),
    url(r'^about/$', TemplateView.as_view(template_name='about.html'), name='about'),
    # RSS for reports
    url(r'^feeds/latest/$', LatestEntries(), name='latest-results'),
    url(r'^feeds/latest_significant/$', LatestSignificantEntries(),
        name='latest-significant-results'),
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
    url(r'^makeimage/$', 'makeimage', name='makeimage'),
)

urlpatterns += patterns('codespeed.views',
    # URLs for adding results
    url(r'^result/add/json/$', 'add_json_results', name='add-json-results'),
    url(r'^result/add/$', 'add_result', name='add-result'),
)

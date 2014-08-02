from django.contrib.syndication.views import Feed
from codespeed.models import Report
from django.conf import settings
from django.db.models import Q

class ResultFeed(Feed):
    title = settings.WEBSITE_NAME
    link = "/changes/"

    def items(self):
        return Report.objects\
            .filter(self.result_filter())\
            .order_by('-revision__date')[:10]

    def item_title(self, item):
        return unicode(item.revision)

    def item_description(self, item):
        if item.summary:
            return item.summary
        else:
            return "No significant changes"

class LatestEntries(ResultFeed):
    description = "Last benchmark runs"

    def result_filter(self):
        return Q(revision__branch__name=settings.DEF_BRANCH)

class LatestSignificantEntries(ResultFeed):
    description = "Last significant benchmark runs"

    def result_filter(self):
        return Q(revision__branch__name=settings.DEF_BRANCH,
                 colorcode__in = ('red','green'))

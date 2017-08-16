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
        return "%s: %s" % (item.revision.get_short_commitid(),
                           item.item_description())

    description_template = "codespeed/changes_table.html"

    def get_context_data(self, **kwargs):
        report = kwargs['item']
        trendconfig = settings.TREND

        tablelist = report.get_changes_table(trendconfig)

        return {
            'tablelist': tablelist,
            'trendconfig': trendconfig,
            'rev': report.revision,
            'exe': report.executable,
            'env': report.environment,
        }


class LatestEntries(ResultFeed):
    description = "Last Results"

    def result_filter(self):
        return Q()


class LatestSignificantEntries(ResultFeed):
    description = "Last results with significant changes"

    def result_filter(self):
        return Q(colorcode__in=('red', 'green'))

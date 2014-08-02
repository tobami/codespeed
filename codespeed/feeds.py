from django.contrib.syndication.views import Feed
from codespeed.models import Report
from django.conf import settings


class LatestEntries(Feed):
    title = settings.WEBSITE_NAME
    link = "/changes/"
    description = "Last benchmark runs"

    def items(self):
        return Report.objects.filter(
            revision__branch__name=settings.DEF_BRANCH
        ).order_by('-revision__date')[:10]

class LatestSignificantEntries(Feed):
    title = settings.WEBSITE_NAME
    link = "/changes/"
    description = "Last significant benchmark runs"

    def items(self):
        return Report.objects.filter(
            revision__branch__name=settings.DEF_BRANCH,
            colorcode__in = ('red','green')
        ).order_by('-revision__date')[:10]

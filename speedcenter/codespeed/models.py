# -*- coding: utf-8 -*-
from django.db import models
from django.utils import simplejson as json
from codespeed import settings

class Project(models.Model):
    REPO_TYPES = (
        ('N', 'none'),
        ('G', 'git'),
        ('M', 'mercurial'),
        ('S', 'subversion'),
    )
    
    name = models.CharField(unique=True, max_length=30)
    repo_type = models.CharField("Repository type", max_length=1, choices=REPO_TYPES, default='N')
    repo_path = models.CharField("Repository URL", blank=True, max_length=200)
    repo_user = models.CharField("Repository username", blank=True, max_length=100)
    repo_pass = models.CharField("Repository password", blank=True, max_length=100)
    track = models.BooleanField("Track changes", default=False)
    
    def __unicode__(self):
        return str(self.name)


class Revision(models.Model):
    commitid = models.CharField(max_length=42)#git and mercurial's SHA-1 length is 40
    project = models.ForeignKey(Project)
    tag = models.CharField(max_length=20, blank=True)
    date = models.DateTimeField(null=True)
    message = models.TextField(blank=True)
    author = models.CharField(max_length=30, blank=True)
    
    def get_short_commitid(self):
        return self.commitid[:10]
    
    def __unicode__(self):
        return self.date.strftime("%h %d, %H:%M") + " - " + \
            self.get_short_commitid() + " " + self.tag
    
    class Meta:
        unique_together = ("commitid", "project")


class Executable(models.Model):
    name = models.CharField(unique=True, max_length=30)
    description = models.CharField(max_length=200, blank=True)
    project = models.ForeignKey(Project)
    
    def __unicode__(self):
        return str(self.name)


class Benchmark(models.Model):
    B_TYPES = (
        ('C', 'Cross-project'),
        ('O', 'Own-project'),
    )
    
    name = models.CharField(unique=True, max_length=30)
    benchmark_type = models.CharField(max_length=1, choices=B_TYPES, default='C')
    description = models.CharField(max_length=200, blank=True)
    units_title = models.CharField(max_length=30, default='Time')
    units = models.CharField(max_length=20, default='seconds')
    lessisbetter = models.BooleanField(default=True)
    
    def __unicode__(self):
        return str(self.name)


class Environment(models.Model):
    name = models.CharField(unique=True, max_length=30)
    cpu = models.CharField(max_length=30, blank=True)
    memory = models.CharField(max_length=30, blank=True)
    os = models.CharField(max_length=30, blank=True)
    kernel = models.CharField(max_length=30, blank=True)
    
    def __unicode__(self):
        return str(self.name)


class Result(models.Model):
    value = models.FloatField()
    std_dev = models.FloatField(blank=True, null=True)
    val_min = models.FloatField(blank=True, null=True)
    val_max = models.FloatField(blank=True, null=True)
    date = models.DateTimeField(blank=True, null=True)
    revision = models.ForeignKey(Revision)
    executable = models.ForeignKey(Executable)
    benchmark = models.ForeignKey(Benchmark)
    environment = models.ForeignKey(Environment)
    
    def __unicode__(self):
        return str(self.benchmark.name) + " " + str(self.value)
    
    class Meta:
        unique_together = ("revision", "executable", "benchmark", "environment")


class Report(models.Model):
    revision    = models.ForeignKey(Revision)
    environment = models.ForeignKey(Environment)
    executable  = models.ForeignKey(Executable)
    summary     = models.CharField(max_length=30, blank=True)
    colorcode   = models.CharField(max_length=10, default="none")
    _tablecache = models.TextField(blank=True)
    
    def __unicode__(self):
        return "Report for " + str(self.revision.commitid)
    
    class Meta:
        unique_together = ("revision", "executable", "environment")
    
    def save(self, *args, **kwargs):
        tablelist = self.get_changes_table(force_save=True)
        max_change, max_change_ben, max_change_color = 0, None, "none"
        max_trend, max_trend_ben, max_trend_color = 0, None, "none"
        average_change, average_change_units, average_change_color = 0, None, "none"
        average_trend, average_trend_units, average_trend_color = 0, None, "none"
        
        # Get default threshold values
        change_threshold = 3.0
        trend_threshold  = 5.0
        if hasattr(settings, 'change_threshold') and settings.change_threshold != None:
            change_threshold = settings.change_threshold
        if hasattr(settings, 'trend_threshold') and settings.trend_threshold:
            trend_threshold = settings.trend_threshold
        
        # Fetch big changes for each unit type and each benchmark
        for units in tablelist:
            # Total change
            val = units['totals']['change']
            if val == "-":
                continue
            color = self.getcolorcode(val, units['lessisbetter'], change_threshold)
            if self.is_big_change(val, color, average_change, average_change_color):
                # Do update biggest total change
                average_change       = val
                average_change_units = units['units_title']
                average_change_color = color
            # Total trend
            val = units['totals']['trend']
            if val != "-":
                color = self.getcolorcode(val, units['lessisbetter'], trend_threshold)
                if self.is_big_change(val, color, average_trend, average_trend_color):
                    # Do update biggest total trend change
                    average_trend       = val
                    average_trend_units = units['units_title']
                    average_trend_color = color
            for row in units['rows']:
                # Single change
                val = row['change']
                if val == "-":
                    continue
                color = self.getcolorcode(val, units['lessisbetter'], change_threshold)
                if self.is_big_change(val, color, max_change, max_change_color):
                    # Do update biggest single change
                    max_change       = val
                    max_change_ben   = row['bench_name']
                    max_change_color = color
                # Single trend
                val = row['trend']
                if val == "-":
                    continue
                color = self.getcolorcode(val, units['lessisbetter'], trend_threshold)
                if self.is_big_change(val, color, max_trend, max_trend_color):
                    # Do update biggest single trend change
                    max_trend       = val
                    max_trend_ben   = row['bench_name']
                    max_trend_color = color
        # Reinitialize
        self.summary = ""
        self.colorcode = "none"
        
        # Save summary in order of priority
        # Average change
        if average_change_color != "none":
            #Substitute plus/minus with up/down
            direction = average_change >= 0 and "+" or "-"
            self.summary = "Average %s %s%.1f%%" % (
                average_change_units.lower(),
                direction,
                round(abs(average_change), 1))
            self.colorcode = average_change_color
        # Single benchmark change
        if max_change_color != "none" and self.colorcode != "red":
            #Substitute plus/minus with up/down
            direction = max_change >= 0 and "+" or "-"
            self.summary = "%s %s%.1f%%" % (
                max_change_ben, direction, round(abs(max_change), 1))
            self.colorcode = max_change_color
        
        # Average trend
        if average_trend_color != "none" and self.colorcode == "none":
            #Substitute plus/minus with up/down
            direction = average_trend >= 0 and "+" or ""
            self.summary = "Average %s trend %s%.1f%%" % (
                average_trend_units.lower(), direction, round(average_trend, 1))
            self.colorcode = average_trend_color == "red"\
                and "yellow" or average_trend_color
        # Single benchmark trend
        if max_trend_color != "none" and self.colorcode != "red":
            if self.colorcode == "none" or (self.colorcode == "green" and "trend" not in self.summary):
                direction = max_trend >= 0 and "+" or ""
                self.summary = "%s trend %s%.1f%%" % (
                    max_trend_ben, direction, round(max_trend, 1))
                self.colorcode = max_trend_color == "red"\
                    and "yellow" or max_trend_color
        
        super(Report, self).save(*args, **kwargs)
    
    def is_big_change(self, val, color, current_val, current_color):
        if color == "red" and current_color != "red":
            return True
        elif color == "red" and abs(val) > abs(current_val):
            return True
        elif color == "green" and  current_color != "red" and \
            abs(val) > abs(current_val):
            return True
        else:
            return False
    
    def getcolorcode(self, val, lessisbetter, threshold):
        if lessisbetter:
            val = -val
        colorcode = "none"
        if val < -threshold:
            colorcode = "red"
        elif val > threshold:
            colorcode = "green"
        return colorcode;
    
    def get_changes_table(self, trend_depth=10, force_save=False):
        # Determine whether required trend value is the default one
        default_trend = 10
        if hasattr(settings, 'trend') and settings.trend:
            default_trend = settings.trend
        # If the trend is the default and a forced save is not required
        # just return the cached changes table
        if not force_save and trend_depth == default_trend:
            return self._get_tablecache()
        
        lastrevisions = Revision.objects.filter(
            project=self.executable.project
        ).filter(
            date__lte=self.revision.date
        ).order_by('-date')[:trend_depth+1]
        lastrevision = lastrevisions[0]#same as self.revision unless in a different branch
        
        change_list = []
        pastrevisions = []
        if len(lastrevisions) > 1:
            changerevision = lastrevisions[1]
            change_list = Result.objects.filter(
                revision=changerevision
            ).filter(
                environment=self.environment
            ).filter(
                executable=self.executable
            )
            pastrevisions = lastrevisions[trend_depth-2:trend_depth+1]
        
        result_list = Result.objects.filter(
            revision=lastrevision
        ).filter(
            environment=self.environment
        ).filter(
            executable=self.executable
        )
        
        tablelist = []
        for units in Benchmark.objects.all().values('units').distinct():
            currentlist = []
            units_title = ""
            hasmin = False
            hasmax = False
            has_stddev = False
            smallest = 1000
            totals = {'change': [], 'trend': [],}
            for bench in Benchmark.objects.filter(units=units['units']):
                units_title = bench.units_title
                lessisbetter = bench.lessisbetter
                resultquery = result_list.filter(benchmark=bench)
                if not len(resultquery): continue
                
                resobj = resultquery.filter(benchmark=bench)[0]
                
                std_dev = resobj.std_dev
                if std_dev is not None: has_stddev = True
                else: std_dev = "-"
                
                val_min = resobj.val_min
                if val_min is not None: hasmin = True
                else: val_min = "-"
                
                val_max = resobj.val_max
                if val_max is not None: hasmax = True
                else: val_max = "-"
                
                # Calculate percentage change relative to previous result
                result = resobj.value
                change = "-"
                if len(change_list):
                    c = change_list.filter(benchmark=bench)
                    if c.count() and c[0].value and result:
                        change = (result - c[0].value)*100/c[0].value
                        totals['change'].append(result / c[0].value)
                
                # Calculate trend:
                # percentage change relative to average of 3 previous results
                # Calculate past average
                average = 0
                averagecount = 0
                if len(pastrevisions):
                    for rev in pastrevisions:
                        past_rev = Result.objects.filter(
                            revision=rev
                        ).filter(
                            environment=self.environment
                        ).filter(
                            executable=self.executable
                        ).filter(benchmark=bench)
                        if past_rev.count():
                            average += past_rev[0].value
                            averagecount += 1
                trend = "-"
                if average:
                    average = average / averagecount
                    trend =  (result - average)*100/average
                    totals['trend'].append(result / average)
                
                # Retain lowest number different than 0
                # to be used later for calculating significant digits
                if result < smallest and result:
                    smallest = result
                
                currentlist.append({
                    'bench_name': bench.name,
                    'bench_description': bench.description,
                    'result': result,
                    'std_dev': std_dev,
                    'val_min': val_min,
                    'val_max': val_max,
                    'change': change,
                    'trend': trend
                })
            
            # Compute Arithmetic averages
            for key in totals.keys():
                if len(totals[key]):
                    totals[key] = float(sum(totals[key]) / len(totals[key]))
                else:
                    totals[key] = "-"
            
            if totals['change'] != "-":
                totals['change'] = (totals['change'] - 1) * 100#transform ratio to percentage
            if totals['trend'] != "-":
                totals['trend'] = (totals['trend'] - 1) * 100#transform ratio to percentage
            
            # Calculate significant digits
            digits = 2;
            while smallest < 1:
                smallest *= 10
                digits += 1
            
            tablelist.append({
                'units': units['units'],
                'units_title': units_title,
                'lessisbetter': lessisbetter,
                'has_stddev': has_stddev,
                'hasmin': hasmin,
                'hasmax': hasmax,
                'precission': digits,
                'totals': totals,
                'rows': currentlist
            })
        if force_save:
            self._save_tablecache(tablelist)
        return tablelist
    
    def get_absolute_url(self):
        return "/changes/?rev=%s&exe=%s&env=%s" % (
            self.revision.commitid, self.executable.id, self.environment.name)
    
    def _save_tablecache(self, data):
        self._tablecache = json.dumps(data)
    
    def _get_tablecache(self):
        if self._tablecache == '':
            return {}
        return json.loads(self._tablecache)

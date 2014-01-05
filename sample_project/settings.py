# -*- coding: utf-8 -*-
# Django settings for a speedcenter project.
import os

DEBUG = True
TEMPLATE_DEBUG = DEBUG

BASEDIR = os.path.abspath(os.path.dirname(__file__))
TOPDIR = os.path.split(BASEDIR)[1]

#: The directory which should contain checked out source repositories:
REPOSITORY_BASE_PATH = os.path.join(BASEDIR, "repos")

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASEDIR, 'data.db'),
    }
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/Chicago'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = False

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = os.path.join(BASEDIR, "media")

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/media/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/static/admin/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'as%n_m#)^vee2pe91^^@c))sl7^c6t-9r8n)_69%)2yt+(la2&'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    # 'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

if DEBUG:
    import traceback
    import logging

    # Define a class that logs unhandled errors
    class LogUncatchedErrors:
        def process_exception(self, request, exception):
            logging.error("Unhandled Exception on request for %s\n%s" %
                                 (request.build_absolute_uri(),
                                  traceback.format_exc()))
    # And add it to the middleware classes
    MIDDLEWARE_CLASSES += ('sample_project.settings.LogUncatchedErrors',)

    # set shown level of logging output to debug
    logging.basicConfig(level=logging.DEBUG)

ROOT_URLCONF = '{0}.urls'.format(TOPDIR)

TEMPLATE_DIRS = (
    os.path.join(BASEDIR, 'templates'),
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.contrib.messages.context_processors.messages',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.core.context_processors.request',
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.admin',
    'django.contrib.staticfiles',
    'codespeed',
    'south',
)
SOUTH_TESTS_MIGRATE = False

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASEDIR, "sitestatic")
STATICFILES_DIRS = (
    os.path.join(BASEDIR, 'static'),
)

# Codespeed settings that can be overwritten here.
from codespeed.settings import *

## General default options ##
WEBSITE_NAME = "MySpeedSite" # This name will be used in the reports RSS feed

#DEF_ENVIRONMENT = None #Name of the environment which should be selected as default


#DEF_BASELINE = None # Which executable + revision should be default as a baseline
                    # Given as the name of the executable and commitid of the revision
                    # Example: defaultbaseline = {'executable': 'myexe', 'revision': '21'}

#TREND = 10 # Default value for the depth of the trend
           # Used by reports for the latest runs and changes view

# Threshold that determines when a performance change over the last result is significant
#CHANGE_THRESHOLD = 3.0

# Threshold that determines when a performance change
# over a number of revisions is significant
#TREND_THRESHOLD  = 5.0

## Changes view options ##
#DEF_EXECUTABLE = None # Executable that should be chosen as default in the changes view
                      # Given as the name of the executable.
                      # Example: defaultexecutable = "myexe"

#SHOW_AUTHOR_EMAIL_ADDRESS = True # Whether to show the authors email address in the
                                 # changes log

## Timeline view options ##
#DEF_BENCHMARK = "grid" # Default selected benchmark. Possible values:
                       #   "grid": will show the grid of plots
                       #   "show_none": will just show a text message
                       #   "mybench": will select benchmark "mybench"

#DEF_TIMELINE_LIMIT = 50  # Default number of revisions to be plotted
                         # Possible values 10,50,200,1000

#TIMELINE_BRANCHES = True # NOTE: Only the default branch is currently shown
                         # Get timeline results for specific branches
                         # Set to False if you want timeline plots and results only for trunk.

## Comparison view options ##
#CHART_TYPE = 'normal bars' # The options are 'normal bars', 'stacked bars' and 'relative bars'

#NORMALIZATION = False # True will enable normalization as the default selection
                      # in the Comparison view. The default normalization can be
                      # chosen in the defaultbaseline setting

#CHART_ORIENTATION = 'vertical' # 'vertical' or 'horizontal can be chosen as
                              # default chart orientation

#COMP_EXECUTABLES = None  # Which executable + revision should be checked as default
                         # Given as a list of tuples containing the
                         # name of an executable + commitid of a revision
                         # An 'L' denotes the last revision
                         # Example:
                         # COMP_EXECUTABLES = [
                         #     ('myexe', '21df2423ra'),
                         #     ('myexe', 'L'),]

#DEF_BRANCH = "default" # Defines the default branch to be used.
                       # In git projects, this branch is usually be calles
                       # "master"

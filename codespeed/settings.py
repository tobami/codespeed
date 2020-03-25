# -*- coding: utf-8 -*-
"""Default settings for Codespeed"""

## General default options ##
WEBSITE_NAME = "MySpeedSite" # This name will be used in the reports RSS feed

DEF_ENVIRONMENT = None # Name of the environment which should be selected as default

DEF_BASELINE = None # Which executable + revision should be default as a baseline
                    # Given as the name of the executable and commitid of the revision
                    # Example: DEF_BASELINE = {'executable': 'baseExe', 'revision': '444'}

TREND = 10 # Default value for the depth of the trend
           # Used by reports for the latest runs and changes view

# Threshold that determines when a performance change over the last result is significant
CHANGE_THRESHOLD = 3.0

# Threshold that determines when a performance change
# over a number of revisions is significant
TREND_THRESHOLD = 5.0

## Home view options ##
SHOW_REPORTS = True # Show report tables
SHOW_HISTORICAL = False # Show historical graphs

## Changes view options ##
DEF_EXECUTABLE = None # Executable that should be chosen as default in the changes view
                      # Given as the name of the executable.
                      # Example: DEF_EXECUTABLE = "myexe O3 64bits"

SHOW_AUTHOR_EMAIL_ADDRESS = True # Whether to show the authors email address in the
                                 # changes log

## Timeline view options ##
DEF_BENCHMARK = None   # Default selected benchmark. Possible values:
                       #   None: will show a grid of plot thumbnails, or a
                       #       text message when the number of plots exceeds 30
                       #   "grid": will always show as default the grid of plots
                       #   "show_none": will show a text message (better
                       #       default when there are lots of benchmarks)
                       #   "mybench": will select benchmark named "mybench"

DEF_TIMELINE_LIMIT = 50  # Default number of revisions to be plotted
                         # Possible values 10,50,200,1000

TIMELINE_GRID_LIMIT = 30  # Number of benchmarks beyond which the timeline view
                          # is disabled as default setting. Too many benchmarks make
                          # the view slow, and put load on the database, which may be
                          # undeseriable.

TIMELINE_GRID_PAGING = 4   # Number of benchmarks to be send in one grid request
                           # May be adjusted to improve the performance of the timeline grid view.
                           # If a large number of benchmarks is in the system,
                           # and the database is not fast, it can take a long time
                           # to send all results.

#TIMELINE_BRANCHES = True # NOTE: Only the default branch is currently shown
                         # Get timeline results for specific branches
                         # Set to False if you want timeline plots and results only for trunk.

## Comparison view options ##
CHART_TYPE = 'normal bars' # The options are 'normal bars', 'stacked bars' and 'relative bars'

NORMALIZATION = False # True will enable normalization as the default selection
                      # in the Comparison view. The default normalization can be
                      # chosen in the defaultbaseline setting

CHART_ORIENTATION = 'vertical' # 'vertical' or 'horizontal can be chosen as
                              # default chart orientation

COMP_EXECUTABLES = None  # Which executable + revision should be checked as default
                         # Given as a list of tuples containing the
                         # name of an executable + commitid of a revision
                         # An 'L' denotes the last revision
                         # Example:
                         # COMP_EXECUTABLES = [
                         #     ('myexe', '21df2423ra'),
                         #     ('myexe', 'L'),]

COMPARISON_COMMIT_TAGS = None  # List of tag names which should be included in the executables list
                               # on the comparision page.
                               # This comes handy where project contains a lot of tags, but you only want
                               # to list subset of them on the comparison page.
                               # If this value is set to None (default value), all the available tags will
                               # be included.

TIMELINE_EXECUTABLE_NAME_MAX_LEN = 22  # Maximum length of the executable name used in the
                                       # Changes and Timeline view. If the name is longer, the name
                                       # will be truncated and "..." will be added at the end.

COMPARISON_EXECUTABLE_NAME_MAX_LEN = 20  # Maximum length of the executable name  used in the
                                         # Coomparison view. If the name is longer, the name

USE_MEDIAN_BANDS = True # True to enable median bands on Timeline view


ALLOW_ANONYMOUS_POST = True  # Whether anonymous users can post results
REQUIRE_SECURE_AUTH = True  # Whether auth needs to be over a secure channel

US_TZ_AWARE_DATES = False  # True to use timezone aware datetime objects with Github provider.
                           # NOTE: Some database backends may not support tz aware dates.

GITHUB_OAUTH_TOKEN = None  # Github oAuth token to use when using Github repo type. If not
                           # specified, it will utilize unauthenticated requests which have
                           # low rate limits.

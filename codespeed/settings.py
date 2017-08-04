# -*- coding: utf-8 -*-
"""Default settings for Codespeed"""

## General default options ##
WEBSITE_NAME = "MySpeedSite" # This name will be used in the reports RSS feed

DEF_ENVIRONMENT = None # Name of the environment which should be selected as default

DEF_BASELINE = None # Which executable + revision should be default as a baseline
                    # Given as the name of the executable and commitid of the revision
                    # Example: defaultbaseline = {'executable': 'myexe', 'revision': '21'}

TREND = 10 # Default value for the depth of the trend
           # Used by reports for the latest runs and changes view

# Threshold that determines when a performance change over the last result is significant
CHANGE_THRESHOLD = 3.0

# Threshold that determines when a performance change
# over a number of revisions is significant
TREND_THRESHOLD = 5.0

## Changes view options ##
DEF_EXECUTABLE = None # Executable that should be chosen as default in the changes view
                      # Given as the name of the executable.
                      # Example: defaultexecutable = "myexe"

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

USE_MEDIAN_BANDS = True # True to enable median bands on Timeline view


ALLOW_ANONYMOUS_POST = True  # Whether anonymous users can post results
REQUIRE_SECURE_AUTH = True  # Whether auth needs to be over a secure channel

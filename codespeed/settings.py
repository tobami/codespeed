# -*- coding: utf-8 -*-

"""
Default settings for Codespeed
"""

## General default options ##
WEBSITE_NAME = "MySpeedSite" # This name will be used in the reports RSS feed

DEF_ENVIRONMENT = None #Name of the environment which should be selected as default


DEF_BASELINE = None # Which executable + revision should be default as a baseline
                    # Given as the name of the executable and commitid of the revision
                    # Example: defaultbaseline = {'executable': 'myexe', 'revision': '21'}

TREND = 10 # Default value for the depth of the trend
           # Used by reports for the latest runs and changes view

# Threshold that determines when a performance change over the last result is significant
CHANGE_THRESHOLD = 3.0

# Threshold that determines when a performance change
# over a number of revisions is significant
TREND_THRESHOLD  = 5.0

## Changes view options ##
DEF_EXECUTABLE = None # Executable that should be chosen as default in the changes view
                      # Given as the name of the executable.
                      # Example: defaultexecutable = "myexe"

## Timeline view options ##
DEF_BENCHMARK = "grid" # Default selected benchmark. Possible values:
                       #   "grid": will show the grid of plots
                       #   "show_none": will just show a text message
                       #   "mybench": will select benchmark "mybench"

#timeline_branches = True # NOTE: Only the default branch is currently shown
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


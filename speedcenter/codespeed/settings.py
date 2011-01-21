# -*- coding: utf-8 -*-
## General default options ##
website_name = "MySpeedSite" # This name will be used in the reports RSS feed

def_environment = None #Name of the environment which should be selected as default


def_baseline = None # Which executable + revision should be default as a baseline
                    # Given as the name of the executable and commitid of the revision
                    # Example: defaultbaseline = {'executable': 'myexe', 'revision': '21'}

trend = 10 # Default value for the depth of the trend
           # Used by reports for the latest runs and changes view

# Threshold that determines when a performance change over the last result is significant
change_threshold = 3.0

# Threshold that determines when a performance change
# over a number of revisions is significant
trend_threshold  = 5.0

# Changes view options ##
def_executable = None # Executable that should be chosen as default in the changes view
                      # Given as the id of the executable.
                      # Example: defaultexecutable = "myexe"

## Comparison view options ##
chart_type = 'normal bars' # The options are 'normal bars', 'stacked bars' and 'relative bars'

normalization = False # True will enable normalization as the default selection
                      # in the Comparison view. The default normalization can be
                      # chosen in the defaultbaseline setting

chart_orientation = 'vertical' # 'vertical' or 'horizontal can be chosen as
                              # default chart orientation

comp_executables = None  # Which executable + revision should be checked as default
                         # Given as a list of tuples containing the
                         # name of an executable + commitid of a revision
                         # An 'L' denotes the last revision
                         # Example:
                         # comp_executables = [
                         #     ('myexe', '21df2423ra'),
                         #     ('myexe', 'L'),]

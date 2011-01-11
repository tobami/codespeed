# -*- coding: utf-8 -*-
## General default options ##
defaultenvironment = None #Name of the environment which should be selected as default


defaultbaseline = None # Which executable + revision should be default as a baseline
                       # Given as the name of the executable and commitid of the revision
                       # Example: defaultbaseline = {'executable': 'myexe', 'revision': '21'}

# Threshold that determines when a performance change over the last result is significant
changethreshold = 3.0

# Threshold that determines when a performance change
# over a number of revisions is significant
trendthreshold  = 3.0

# Changes view options ##
defaultexecutable = None # Executable that should be chosen as default in the changes view
                         # Given as the id of the executable.
                         # Example: defaultexecutable = "myexe"

## Comparison view options ##
charttype = 'normal bars' # The options are 'normal bars', 'stacked bars' and 'relative bars'

normalization = False # True will enable normalization as the default selection
                      # in the Comparison view. The default normalization can be
                      # chosen in the defaultbaseline setting

chartorientation = 'vertical' # 'vertical' or 'horizontal can be chosen as
                              # default chart orientation

comp_defaultexecutables = None  # Which executable + revision should be checked
                                # Given as a list of tuples containing the
                                # name of an executable + commitid of a revision
                                # An 'L' denotes the last revision
                                # Example:
                                # comp_defaultexecutables = [
                                #     ('myexe', '21df2423ra'),
                                #     ('myexe', 'L'),
                                #]

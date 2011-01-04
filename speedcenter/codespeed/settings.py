# -*- coding: utf-8 -*-
## General default options ##
defaultenvironment = None #Name of the environment which should be selected as default


defaultbaseline = None # Which executable + revision should be default as a baseline
                       # Given as the id of the executable + commitid of the revision
                       # Example: defaultbaseline = {'executable': 'myexe', 'revision': '21'}

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

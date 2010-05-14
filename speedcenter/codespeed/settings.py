# -*- coding: utf-8 -*-
## Define some default options here ##
defaultexecutable = None # Executable that should be chosen as default in the overview
                         # Given as the id of the executable.
                         # Example: defaultexecutable = 1

defaultbaseline = None # Which executable + revision should be default as a baseline
                       # Given as the id of the executable + commitid of the revision
                       # Example: defaultbaseline = {'executable': 4, 'revision': 262}
                       
baselinelist = None # Which executables + revisions should be listed as comparison options
                    # Example:defaultbaseline = [
                    #             {'executable': 4, 'revision': 262},
                    #             {'executable': 2, 'revision': 56565},
                    #]
defaultenvironment = None #Name of the environment which should be selected as default
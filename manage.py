#!/usr/bin/env python
import os
import sys

new_file = os.path.join(os.path.dirname(__file__), 'example', 'manage.py')
os.execl(sys.executable, sys.executable, new_file, *sys.argv[1:])

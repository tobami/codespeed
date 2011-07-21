# -*- coding: utf-8 -*-

from django.conf import global_settings  # needed for codespeed.__init__

def inject_app_defaults(application):
    """Inject an application's default settings"""

    try:
        __import__('%s.settings' % application)
        import sys

        # Import our defaults, project defaults, and project settings
        _app_settings = sys.modules['%s.settings' % application]
        _def_settings = sys.modules['django.conf.global_settings']
        _settings = sys.modules['django.conf'].settings

        # Add the values from the application.settings module
        for _k in dir(_app_settings):
            if _k.isupper():
                # Add the value to the default settings module
                setattr(_def_settings, _k, getattr(_app_settings, _k))

                # Add the value to the settings, if not already present
                if not hasattr(_settings, _k):
                    setattr(_settings, _k, getattr(_app_settings, _k))
    except ImportError:
        # Silently skip failing settings modules
        pass

inject_app_defaults(__name__)

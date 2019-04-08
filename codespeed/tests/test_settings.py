from django.conf import settings
from django.test import TestCase

from codespeed import settings as default_settings


class TestCodespeedSettings(TestCase):
    """Test codespeed.settings
    """

    def setUp(self):
        self.cs_setting_keys = [key for key in dir(default_settings) if key.isupper()]

    def test_website_name(self):
        """See if WEBSITENAME is set
        """
        self.assertTrue(default_settings.WEBSITE_NAME)
        self.assertEqual(default_settings.WEBSITE_NAME, 'MySpeedSite',
                         "Change codespeed settings in project.settings")

    def test_keys_in_settings(self):
        """Check that all settings attributes from codespeed.settings exist
        in django.conf.settings
        """
        for k in self.cs_setting_keys:
            self.assertTrue(hasattr(settings, k),
                            "Key {0} is missing in settings.py.".format(k))

    def test_settings_attributes(self):
        """Check if all settings from codespeed.settings equals
        django.conf.settings
        """
        for k in self.cs_setting_keys:
            self.assertEqual(getattr(settings, k), getattr(default_settings, k))

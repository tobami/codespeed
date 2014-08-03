from django.test import TestCase
from django.core.urlresolvers import reverse

from codespeed.models import Environment


class TestAddResult(TestCase):

    def setUp(self):
        self.path = reverse('codespeed.views.reports')
        self.e = Environment.objects.create(name='Dual Core', cpu='Core 2 Duo 8200')
        self.data = {
            'commitid': 'abcd1',
            'branch': 'default',
            'project': 'MyProject',
            'executable': 'myexe O3 64bits',
            'benchmark': 'float',
            'environment': 'Dual Core',
            'result_value': 200,
        }
        resp = self.client.post(reverse('codespeed.views.add_result'), self.data)
        self.assertEqual(resp.status_code, 202)
        self.data['commitid'] = "abcd2"
        self.data['result_value'] = 150
        self.client.post(reverse('codespeed.views.add_result'), self.data)
        self.assertEqual(resp.status_code, 202)

    def test_reports(self):
        response = self.client.get(self.path)

        self.assertEqual(response.status_code, 200)
        self.assertIn('Latest Results', response.content)
        self.assertIn('Latest Significant Results', response.content)
        self.assertIn(self.data['commitid'], response.content)

    def test_reports_post_returns_405(self):
        response = self.client.post(self.path, {})

        self.assertEqual(response.status_code, 405)

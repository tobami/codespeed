from datetime import datetime
from django.test import TestCase, override_settings
from mock import Mock, patch

from codespeed.commits.git import getlogs
from codespeed.models import Project, Revision, Branch, Environment


@override_settings(ALLOW_ANONYMOUS_POST=True)
class GitTest(TestCase):
    def setUp(self):
        self.env = Environment.objects.create(name='env')
        self.project = Project.objects.create(name='project',
                                              repo_path='path',
                                              repo_type=Project.GIT)
        self.branch = Branch.objects.create(name='default',
                                            project_id=self.project.id)
        self.revision = Revision.objects.create(
            **{
               'commitid': 'id1',
               'date': datetime.now(),
               'project_id': self.project.id,
               'branch_id': self.branch.id,
            }
        )

    @patch("codespeed.commits.git.Popen")
    def test_git_output_parsing(self, popen):
        # given
        outputs = {
            "log": b"id\x00long_id\x001583489681\x00author\x00email\x00msg\x00\x1e",
            "tag": b'tag',
        }

        def side_effect(cmd, *args, **kwargs):
            ret = Mock()
            ret.returncode = 0
            git_command = cmd[1] if len(cmd) > 0 else None
            output = outputs.get(git_command, b'')
            ret.communicate.return_value = (output, b'')
            return ret

        popen.side_effect = side_effect

        # when
        # revision doesn't matter here, git commands are mocked
        logs = getlogs(self.revision, self.revision)

        # then
        expected = {
            'date': '2020-03-06 04:14:41',
            'message': 'msg',
            'commitid': 'long_id',
            'author': 'author',
            'author_email': 'email',
            'body': '',
            'short_commit_id': 'id',
            'tag': 'tag',
        }
        self.assertEquals([expected], logs)

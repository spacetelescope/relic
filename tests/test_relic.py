import os
import unittest
import shutil
import relic
import relic.release
import relic.git
from subprocess import check_call, STDOUT
from tempfile import mkdtemp


def runner(command):
    with open(os.devnull, 'w') as devnull:
        check_call(command, shell=True, stdout=devnull, stderr=STDOUT)


class TestRepo(unittest.TestCase):
    def setUp(self):
        self.pwd = os.path.abspath(os.curdir)
        try:
            self.repo_path = mkdtemp()
        except (OSError, IOError, PermissionError):
            print('Cannot write to temporary storage directory. Aborting.')
            exit(1)

        try:
            os.chdir(self.repo_path)
        except (OSError, IOError, PermissionError):
            print('Could not change directory. Aborting.')
            exit(1)

        # Create a basic git repository.
        runner('git init')
        runner('touch testfile')
        runner('git add testfile')
        runner("git commit -m 'Initial commit'")


    def tearDown(self):
        os.chdir(self.pwd)
        if os.path.exists(self.repo_path):
            shutil.rmtree(self.repo_path)


class TestGit(TestRepo):
    def test_git_describe_not_a_repository(self):
        shutil.rmtree('.git')
        desc = relic.git.git_describe()
        self.assertIsNone(desc)


    def test_git_describe(self):
        runner('git tag -a 1.0.0 -m "test message"')
        desc = relic.git.git_describe()
        self.assertIsInstance(desc, str)


    def test_git_log_date_not_a_repository(self):
        shutil.rmtree('.git')
        date = relic.git.git_log_date()
        self.assertIsNone(date)


    def test_git_log_date(self):
        runner('git tag -a 1.0.0 -m "test message"')
        date = relic.git.git_log_date()
        self.assertIsInstance(date, str)
        self.assertGreater(len(date), 0)


    def test_git_version_info_not_a_repository(self):
        shutil.rmtree('.git')
        v = relic.git.git_version_info()
        self.assertIsNone(v)


    def test_git_version_info(self):
        runner('git tag -a 1.0.0 -m "test message"')
        v = relic.git.git_version_info()
        self.assertIsInstance(v, relic.git.GitVersion)



class TestRelease(TestRepo):
    def test_version_not_a_repository(self):
        shutil.rmtree('.git')
        v = relic.release.get_info()
        self.assertEqual(v.pep386, '0.0.0')
        self.assertLess(int(v.post), 0)


    def test_version_without_tag(self):
        v = relic.release.get_info()
        self.assertIsNotNone(v)
        self.assertIsInstance(v, relic.git.GitVersion)
        self.assertEqual(len(v.pep386), 8)
        self.assertEqual(v.pep386, v.short)
        try:
            self.assertLess(int(v.post), 0)
        except ValueError as e:
            self.fail(e)


    def test_version_pep386_release(self):
        runner('git tag -a 1.0.0 -m "test message"')
        v = relic.release.get_info()
        self.assertEqual(v.pep386, '1.0.0')
        self.assertFalse(v.dirty)
        self.assertEqual(v.post, '0')


    def test_version_pep386_dev(self):
        runner('git tag -a 1.0.0 -m "test message"')
        runner('touch testfile2')
        runner('git add testfile2')
        runner('git commit -m "add testfile2"')
        v = relic.release.get_info()
        self.assertIn('.dev', v.pep386)
        self.assertFalse(v.dirty)
        self.assertGreater(int(v.post), 0)


    def test_version_dirty_true_if_dirty(self):
        runner('touch testfile3')
        runner('git add testfile3')
        v = relic.release.get_info()
        self.assertIsInstance(v.dirty, bool)
        self.assertTrue(v.dirty)


    def test_version_dirty_false_if_not_dirty(self):
        v = relic.release.get_info()
        self.assertIsInstance(v.dirty, bool)
        self.assertFalse(v.dirty)


    def test_version_short_is_short(self):
        runner('git tag -a 1.0.0 -m "test message"')
        runner('touch testfile3')
        runner('git add testfile3')
        runner('git commit -m "add testfile"')
        v = relic.release.get_info()
        self.assertIsInstance(v.short, str)
        self.assertIn('.', v.short)
        self.assertNotIn('-', v.short)


    def test_version_long_is_long(self):
        runner('git tag -a 1.0.0 -m "test message"')
        runner('touch testfile3')
        runner('git add testfile3')
        runner('git commit -m "add testfile"')
        v = relic.release.get_info()
        self.assertIsInstance(v.long, str)
        self.assertIn('.', v.long)
        self.assertIn('-', v.long)


    def test_version_post_incremented_after_commit(self):
        runner('git tag -a 1.0.0 -m "test message"')
        runner('touch testfile3')
        runner('git add testfile3')
        runner('git commit -m "add testfile"')
        v = relic.release.get_info()
        self.assertIsInstance(v.post, str)
        try:
            post = int(v.post)
        except ValueError as e:
            self.fail(e)

        self.assertGreater(post, 0)


    def test_version_commit_not_a_repository(self):
        shutil.rmtree('.git')
        v = relic.release.get_info()
        self.assertEqual(v.commit, '')


    def test_version_commit(self):
        runner('git tag -a 1.0.0 -m "test message"')
        v = relic.release.get_info()
        self.assertNotEqual(v.commit, '')


    def test_version_date_not_a_repository(self):
        #Only check if date is populated with "something"
        shutil.rmtree('.git')
        v = relic.release.get_info()
        self.assertIsInstance(v.date, str)
        self.assertEqual(len(v.date), 0)


    def test_version_date(self):
        #Only check if date is populated with "something"
        runner('git tag -a 1.0.0 -m "test message"')
        v = relic.release.get_info()
        self.assertIsInstance(v.date, str)
        self.assertNotEqual(len(v.date), 0)


if __name__ == '__main__':
    unittest.main()
import os
import pytest
import relic
import relic.release
import relic.git
import shutil
import stat
import sys
from subprocess import check_call, STDOUT


WIN32 = True if sys.platform.startswith('win') else False


def runner(command):
    with open(os.devnull, 'w') as devnull:
        check_call(command, shell=True, stdout=devnull, stderr=STDOUT)


def touch(filename):
    with open(filename, 'a'):
        pass


onerror = None
if WIN32:
    # From: shutil.rmtree fails on Windows with 'Access is denied'
    # https://stackoverflow.com/q/1213706/1711764
    def onerror(func, path, exc_info):
        """
        Error handler for ``shutil.rmtree``.

        If the error is due to an access error (read only file)
        it attempts to add write permission and then retries.

        If the error is for another reason it re-raises the error.

        Usage : ``shutil.rmtree(path, onerror=onerror)``
        """
        if not os.access(path, os.W_OK):
            # Is the error an access error ?
            os.chmod(path, stat.S_IWUSR)
            func(path)
        else:
            raise


@pytest.fixture()
def _baserepo(tmpdir):
    repo_path = tmpdir.mkdir('repo')
    os.chdir(str(repo_path))

    # Create a basic git repository.
    runner('git init')
    runner('git config user.name nobody')
    runner('git config user.email nobody@nowhere')
    runner('git config commit.gpgsign false')
    touch('testfile')
    runner('git add testfile')
    runner("git commit -m 'Initial'")
    yield


@pytest.mark.usefixtures('_baserepo')
class TestGit(object):
    def test_git_describe_not_a_repository(self):
        shutil.rmtree('.git', onerror=onerror)
        desc = relic.git.git_describe()
        assert desc is None

    def test_git_describe(self):
        runner('git tag -a 1.0.0 -m "test message"')
        desc = relic.git.git_describe()
        assert isinstance(desc, str)

    def test_git_log_date_not_a_repository(self):
        shutil.rmtree('.git', onerror=onerror)
        date = relic.git.git_log_date()
        assert date is None

    def test_git_log_date(self):
        runner('git tag -a 1.0.0 -m "test message"')
        date = relic.git.git_log_date()
        assert isinstance(date, str)
        assert len(date) > 0

    def test_git_version_info_not_a_repository(self):
        shutil.rmtree('.git', onerror=onerror)
        v = relic.git.git_version_info()
        assert v is None

    def test_git_version_info(self):
        runner('git tag -a 1.0.0 -m "test message"')
        v = relic.git.git_version_info()
        assert isinstance(v, relic.git.GitVersion)


@pytest.mark.usefixtures('_baserepo')
class TestRelease(object):
    def test_version_not_a_repository(self):
        shutil.rmtree('.git', onerror=onerror)
        v = relic.release.get_info()
        assert v.pep386 == '0.0.0'
        assert int(v.post) < 0

    def test_version_without_tag(self):
        v = relic.release.get_info()
        assert v is not None
        assert isinstance(v, relic.git.GitVersion)
        assert '0.0.0.dev' in v.pep386
        assert '+' in v.pep386
        assert int(v.post) == 1

    def test_version_without_tag_autocount(self):
        count = 0x10
        for i in range(count):
            filename = 'file{}.txt'.format(i)
            touch(filename)
            runner('git add {}'.format(filename))
            runner('git commit -m "added {}"'.format(filename))

        v = relic.release.get_info()
        assert v is not None
        assert isinstance(v, relic.git.GitVersion)
        assert '0.0.0.dev' in v.pep386
        assert '+' in v.pep386
        assert int(v.post) == count + 1

    def test_version_pep386_release(self):
        runner('git tag -a 1.0.0 -m "test message"')
        v = relic.release.get_info()
        assert v.pep386 == '1.0.0'
        assert not v.dirty
        assert v.post == '0'

    def test_version_pep386_dev(self):
        runner('git tag -a 1.0.0 -m "test message"')
        touch('testfile2')
        runner('git add testfile2')
        runner('git commit -m "add testfile2"')
        v = relic.release.get_info()
        assert '.dev' in v.pep386
        assert not v.dirty
        assert int(v.post) > 0

    def test_version_dirty_true_if_dirty(self):
        touch('testfile3')
        runner('git add testfile3')
        v = relic.release.get_info()
        assert isinstance(v.dirty, bool)
        assert v.dirty

    def test_version_dirty_false_if_not_dirty(self):
        v = relic.release.get_info()
        assert isinstance(v.dirty, bool)
        assert not v.dirty

    def test_version_short_is_short(self):
        runner('git tag -a 1.0.0 -m "test message"')
        touch('testfile3')
        runner('git add testfile3')
        runner('git commit -m "add testfile"')
        v = relic.release.get_info()
        assert isinstance(v.short, str)
        assert '.' in v.short
        assert '-' not in v.short

    def test_version_long_is_long(self):
        runner('git tag -a 1.0.0 -m "test message"')
        touch('testfile3')
        runner('git add testfile3')
        runner('git commit -m "add testfile"')
        v = relic.release.get_info()
        assert isinstance(v.long, str)
        assert '.' in v.long
        assert '-' in v.long

    def test_version_post_incremented_after_commit(self):
        runner('git tag -a 1.0.0 -m "test message"')
        touch('testfile3')
        runner('git add testfile3')
        runner('git commit -m "add testfile"')
        v = relic.release.get_info()
        assert isinstance(v.post, str)
        post = int(v.post)
        assert post > 0

    def test_version_commit_not_a_repository(self):
        shutil.rmtree('.git', onerror=onerror)
        v = relic.release.get_info()
        assert not v.commit

    def test_version_commit(self):
        runner('git tag -a 1.0.0 -m "test message"')
        v = relic.release.get_info()
        assert v.commit

    def test_version_handle_v_prefix(self):
        runner('git tag -a v1.0.0 -m "test message"')
        v = relic.release.get_info()
        assert 'v' not in v.short
        assert v.short == '1.0.0'

    def test_version_handle_purge_release_prefix(self):
        runner('git tag -a release_1.0.0 -m "test message"')
        v = relic.release.get_info()
        assert 'release_' not in v.short
        assert v.short == '1.0.0'

    def test_version_handle_purge_v_and_release_prefix(self):
        runner('git tag -a release_v1.0.0 -m "test message"')
        v = relic.release.get_info()
        assert 'release_' not in v.short
        assert 'v' not in v.short
        assert v.short == '1.0.0'

    def test_version_handle_purge_nightmare_pattern(self):
        runner('git tag -a itsover9000-v1.0.0_codingaward -m "test message"')
        purge_pattern = ['itsover9000-', '_codingaward']
        v = relic.release.get_info(purge_pattern)
        for p in purge_pattern:
            assert p not in v.short

        # Should have been purged via regex
        assert not v.short.startswith('v')
        assert v.short == '1.0.0'

    def test_version_date_not_a_repository(self):
        # Only check if date is populated with "something"
        shutil.rmtree('.git', onerror=onerror)
        v = relic.release.get_info()
        assert isinstance(v.date, str)
        assert not v.date

    def test_version_date(self):
        # Only check if date is populated with "something"
        runner('git tag -a 1.0.0 -m "test message"')
        v = relic.release.get_info()
        assert isinstance(v.date, str)
        assert v.date

    def test_read_relic_info(self):
        runner('git tag -a 1.0.0 -m "test message"')
        # Generate RELIC-INFO
        relic.release.get_info()
        shutil.rmtree('.git', onerror=onerror)
        # Read it back without git
        v = relic.release.get_info()
        assert v.short == '1.0.0'

    def test_read_relic_info_no_git(self):
        shutil.rmtree('.git', onerror=onerror)
        v = relic.release.get_info()
        assert '+' not in v.pep386
        assert v.short == '0.0.0'
        assert not v.commit

# Copyright (c) 2016, Joseph Hunkeler
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import re
from collections import namedtuple
from subprocess import Popen, PIPE
from . import PY3
from . import ABBREV


RE_GIT_DESC = re.compile('(.+?)-(\d+)-g(\w+)-?(.+)?')
GitVersion = namedtuple('GitVersion', ['pep386', 'short', 'long', 'date', 'dirty', 'commit', 'post'])


def strip_dirty(tag):
    if tag.endswith('-dirty'):
        tag.replace('-dirty', '')
    return tag


def git(*commands):
    command = ['git'] + [c for c in commands]
    proc = Popen(command, stdout=PIPE, stderr=PIPE, stdin=PIPE)

    if PY3:
        outs, errs = proc.communicate()
        if isinstance(outs, bytes):
            outs = outs.decode()
        if isinstance(errs, bytes):
            errs = errs.decode()
    else:
        outs, errs = proc.communicate()

    outs = outs.strip()
    errs = errs.strip()

    returncode = proc.wait()

    if returncode or errs:
        # Return code 128 implies we are trying to use git outside of a git
        # repository. This is a standard mode of operation for relic.
        if returncode == 128:
            return None

        print('{0} (exit: {1})'.format(errs, returncode))
        return None

    return outs


def git_describe(abbrev=ABBREV):
    return git('describe', '--always', '--long', '--tags', '--dirty',
               '--abbrev={0}'.format(abbrev))


def git_log_date(tag='HEAD'):
    tag = strip_dirty(tag)
    return git('log', '-1', '--format=%ai', tag)


def git_version_info(remove_pattern=None):
    dirty = False
    commit = ''
    post = ''
    pep386 = ''
    version_short = ''
    version_long = git_describe()

    if not version_long:
        return None

    date = git_log_date(version_long)

    if isinstance(remove_pattern, str):
        if remove_pattern in version_long:
            version_long = version_long.replace(remove_pattern, '')
    elif isinstance(remove_pattern, list):
        for pattern in remove_pattern:
            version_long = version_long.replace(pattern, '')

    # Construct version data from repository
    match = RE_GIT_DESC.match(version_long)
    if match is not None:
        version_short, post, commit, dirty_check = match.groups()
        pep386 = version_short  # assume release version

        if dirty_check is not None:
            dirty = True

        if int(post):  # construct development version
            pep386 = '{}.dev{}+g{}'.format(version_short, post, commit)

    # No tag or not enough data to proceed
    else:
        if version_long.endswith('-dirty'):
            version_long = strip_dirty(version_long)
            dirty = True

        pep386 = version_short = commit = version_long
        post = '-1'

    data = dict(
        pep386=pep386,
        short=version_short,
        long=version_long,
        date=date,
        dirty=dirty,
        commit=commit,
        post=post,
    )

    return GitVersion(**data)

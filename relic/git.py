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


GitVersion = namedtuple('GitVersion', ['pep386', 'short', 'long', 'date', 'dirty', 'commit', 'post'])


def git_describe(abbrev=ABBREV):
    proc = Popen(['git', 'describe', '--always', '--long', '--tags', '--dirty', '--abbrev={0}'.format(abbrev)],
                 stdout=PIPE,
                 stderr=PIPE,
                 stdin=PIPE)
    if PY3:
        outs, errs = proc.communicate()
        if isinstance(outs, bytes):
            outs = outs.decode()
        if isinstance(errs, bytes):
            errs = errs.decode()
    else:
        outs, errs = proc.communicate()

    returncode = proc.wait()
    if returncode:
        # I am aware of return code 128. We don't care about it.
        if errs:
            print('{0} (exit: {1})'.format(errs.strip(), returncode))
        return None

    return outs.strip()


def git_log_date(tag='HEAD'):
    if 'dirty' in tag:
        tag = 'HEAD'

    proc = Popen(['git', 'log', '-1', '--format=%ai', tag],
                 stdout=PIPE,
                 stderr=PIPE,
                 stdin=PIPE)

    if PY3:
        outs, errs = proc.communicate()
        if isinstance(outs, bytes):
            outs = outs.decode()
        if isinstance(errs, bytes):
            errs = errs.decode()
    else:
        outs, errs = proc.communicate()

    returncode = proc.wait()
    if returncode:
        # I am aware of return code 128. We don't care about it.
        if errs:
            print('{0} (exit: {1})'.format(errs.strip(), returncode))
        return None

    return outs.strip()


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

    # Is this a post commit string? It should be considering '--long' usage
    prog = re.compile('.*-g([a-z]|[0-9]).*')
    match = re.match(prog, version_long)

    components = version_long.split('-')
    if 'dirty' in components:
        dirty = True
        components.pop()
    components.reverse()

    if match is not None:
        for idx, word in enumerate(components):
            if idx == 0:
                commit = word[1:]
            elif idx == 1:
                post = word
            else:
                hack = components[idx:]
                hack.reverse()
                version_short = '-'.join(hack)
                if post:
                    if int(post) > 0:
                        pep386 = ''.join([hack[0], '.dev', post])
                    else:
                        pep386 = version_long.split('-')[0]
                        break
                break
    else:
        #Worst case scenario: somehow we managed not to obtain a long tag description
        if '-' in version_long:
            version_short = version_long.split('-')[0]
        else:
            version_short = version_long
        pep386 = version_short

    if not commit and version_short:
        commit = version_short

    if not post:
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


if __name__ == '__main__':
    pass

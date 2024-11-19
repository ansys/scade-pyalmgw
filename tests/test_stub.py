# Copyright (C) 2023 - 2024 ANSYS, Inc. and/or its affiliates.
# SPDX-License-Identifier: MIT
#
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import difflib
from pathlib import Path

import ansys.scade.pyalmgw.stub as stub
from tests.conftest import load_project

_root_dir = Path(__file__).parent.parent
_test_dir = _root_dir / 'tests'
_ref_dir = _test_dir / 'ref'
_res_dir = _test_dir / 'res'


def cmp_file(reference: Path, result: Path, n=3, linejunk=None):
    """Return the differences between the reference and the result file."""
    with reference.open() as f1, result.open() as f2:
        if linejunk:
            ref_lines = [_ for _ in f1 if not linejunk(_)]
            res_lines = [_ for _ in f2 if not linejunk(_)]
        else:
            ref_lines = f1.read().split('\n')
            res_lines = f2.read().split('\n')

    diff = difflib.context_diff(ref_lines, res_lines, str(reference), str(result), n=n)
    return diff


def diff_files(ref: Path, dst: Path) -> bool:
    print('compare', str(ref), str(dst))
    diffs = cmp_file(ref, dst)
    failure = False
    for d in diffs:
        print(d.rstrip('\r\n'))
        failure = True
    return failure


def test_merge_stub(local_tmpdir):
    path = local_tmpdir / 'sub' / 'stub.vsp'
    path.parent.mkdir(exist_ok=True)
    # create an empty project
    with path.open('w'):
        pass
    # use the stub connector
    project = load_project(path)
    connector = stub.StubConnector('stub', project=project)
    # initialize a stub file
    stub_reqs = connector.get_stub_file()
    assert stub_reqs.exists()
    doc = stub.StubProject(stub_reqs)
    doc.read()
    links = _res_dir / 'stub.links.json'
    doc.merge_links(links)
    doc.write()
    #
    ref = _ref_dir / 'stub.almgw.xml'

    failure = diff_files(ref, stub_reqs)
    assert not failure
    # make sure get_stub_file does not overwrite an existing file
    stub_reqs = connector.get_stub_file()
    failure = diff_files(ref, stub_reqs)
    assert not failure


if __name__ == '__main__':
    # sometimes, debugging tests with PTVS fails:
    # following entry points are workarounds
    if True:
        test_merge_stub(Path(__file__).parent / 'tmp')

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

import pytest

import ansys.scade.pyalmgw.documents as doc


def cmp_file(fromfile: Path, tofile: Path, n=3, linejunk=None):
    """Return the differences between two files."""
    with fromfile.open() as fromf, tofile.open() as tof:
        if linejunk:
            fromlines = [line for line in fromf if not linejunk(line)]
            tolines = [line for line in tof if not linejunk(line)]
        else:
            fromlines, tolines = list(fromf), list(tof)

    diff = difflib.context_diff(fromlines, tolines, str(fromfile), str(tofile), n=n)
    return diff


@pytest.mark.parametrize(
    'name',
    [
        ('empty.xml'),
        ('empty_docs.xml'),
        ('empty_sections.xml'),
        ('requirements.xml'),
        ('links.xml'),
    ],
)
def test_load_save_req_document(name, local_tmpdir):
    """
    Use load-save to test the parsing and serialization of a document
    """
    res_dir = Path(__file__).parent / 'ref'
    path = res_dir / name
    dst = local_tmpdir / name
    project = doc.ReqProject(path)
    project.read()
    project.write(dst)
    print('compare', str(path), str(dst))
    diffs = cmp_file(path, dst)
    failure = False
    for d in diffs:
        print(d.rstrip('\r\n'))
        failure = True
    assert not failure


def test_factory(local_tmpdir):
    """
    Build manually the test file links.xml and make sure it is identical.
    """
    dst = local_tmpdir / 'links_manual.xml'
    project = doc.ReqProject(dst, identifier='xxx.xml', text='collection')

    d1 = doc.ReqDocument(project, file='stub_yyy', name='document')
    # test init vs get property
    assert d1.path == Path('stub_yyy')
    # set property tested on save + compare
    d1.path = Path('yyy')

    s1 = doc.Section(d1, number='stub_1', title='stub_One', description='one description')
    # test init vs get property
    assert s1.number == 'stub_1'
    # set property tested on save + compare
    s1.number = '1'
    # test init vs get property
    assert s1.title == 'stub_One'
    # set property tested on save + compare
    s1.title = 'One'

    s11 = doc.Section(s1, number='1.1', title='One dot one', description='1.1 description')

    r1 = doc.Requirement(s1, 'stub_REQ_1', 'first', 'first first')
    # test init vs get property
    assert r1.id == 'stub_REQ_1'
    # set property tested on save + compare
    r1.id = 'REQ_1'

    s2 = doc.Section(d1, number='2', title='empty two', description='two description')
    r2 = doc.Requirement(d1, 'REQ_2', 'second', 'second second')
    r21 = doc.Requirement(r2, 'REQ_2.1', 'sub', 'sub sub')
    d2 = doc.ReqDocument(project, file='zzz', name='other empty document')

    t1 = doc.TraceabilityLink(project, r1, source='!ed/1')
    t2 = doc.TraceabilityLink(project, r2, source='!ed/2')
    t3 = doc.TraceabilityLink(project, r21, source='!ed/3')

    # dynamic properties
    assert s1.level == 1
    assert s1.depth == 2
    assert s11.level == 2
    assert s11.depth == 1
    assert s2.level == 1
    assert s2.depth == 1

    for c in d2, s2, s11, r1, r21:
        print('empty', c.identifier)
        assert c.is_empty()
    for c in d1, s1, r2:
        print('not empty', c.identifier)
        assert not c.is_empty()

    # unused locals for linter
    assert d2 and t1 and t2 and t3

    project.write()

    src = Path(__file__).parent / 'ref' / 'links.xml'
    print('compare', str(src), str(dst))
    diffs = cmp_file(src, dst)
    failure = False
    for d in diffs:
        print(d.rstrip('\r\n'))
        failure = True
    assert not failure


def test_bind():
    """
    Use load-save to test the parsing and serialization of a document
    """
    res_dir = Path(__file__).parent / 'ref'
    path = res_dir / 'links.xml'
    project = doc.ReqProject(path)
    project.read()
    assert all((_.requirement is None for _ in project.traceability_links))
    unresolved = project.bind()
    assert not unresolved
    assert all((_.requirement.id == _.target for _ in project.traceability_links))
    # add a link to an unknown requirement
    t1 = doc.TraceabilityLink(project, None, source='!ed/1', target='<unknown>')
    unresolved = project.bind()
    assert unresolved == [t1]


if __name__ == '__main__':
    # p = doc.ReqProject(Path(__file__).parent / 'ref' / 'links.xml')
    # p.read()
    # for d in p.documents:
    #     print(d.path)
    # dst = Path(__file__).parent / 'tmp' / 'links.xml'
    # p.write(dst)
    # p.bind()

    # test_req_document({}, Path(__file__).parent)
    # test_load_save_req_document(Path('tests/ref/empty_doc.xml'), Path('tmp'))

    # x = doc.HierarchyElement(None, 'a', 'b', 'c')
    # print(x.attributes)

    test_factory(Path(__file__).parent / 'tmp')

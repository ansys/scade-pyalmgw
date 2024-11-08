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
from typing import Tuple

import pytest

# shall modify sys.path to access SCACE APIs
import ansys.scade.apitools  # noqa: F401

# isort: split
import scade.model.project.stdproject as std
import scade.model.suite as suite

from ansys.scade.pyalmgw.llrs import LLRExport, ScadeLLRS
from tests.conftest import load_project_session


@pytest.fixture(scope='session')
def eq_sets() -> Tuple[std.Project, suite.Session]:
    # unique model for these tests
    path = Path('tests/EqSets/EqSets.etp')
    project, session = load_project_session(path, path)
    return project, session


def cmp_file(fromfile: Path, tofile: Path, n=3, linejunk=None, root=''):
    """
    Return the differences between two files."""
    with fromfile.open() as fromf, tofile.open() as tof:
        if linejunk:
            fromlines = [line.replace(root, '') for line in fromf if not linejunk(line)]
            tolines = [line.replace(root, '') for line in tof if not linejunk(line)]
        else:
            fromlines = [line.replace(root, '') for line in fromf]
            tolines = [line.replace(root, '') for line in tof]
            fromlines, tolines = list(fromf), list(tof)

    diff = difflib.context_diff(fromlines, tolines, str(fromfile), str(tofile), n=n)
    return diff


class TestLLRExport(LLRExport):
    __test__ = False

    def __init__(self, project, session):
        self.session = session
        super().__init__(project)

    def get_export_classes(self, project: std.Project):
        # get_roots not available
        assert project == self.project
        llrs = []
        products = project.get_tool_prop_def('STUDIO', 'PRODUCT', [], None)
        # give SCADE Test the priority if mixed projects Test/Suite
        # if 'QTE' in products:
        #     llrs.append(QteLLRS(self, test.get_roots()[0]))
        if 'SC' in products:
            llrs.append(ScadeLLRS(self, self.session.model))
        # if 'SYSTEM' in products:
        #     llrs.append(SystemLLRS(self, system.get_roots()[0]))
        # if 'DISPLAY' in products:
        #     llrs.append(DisplayLLRs(self))
        return llrs


def test_eq_sets(local_tmpdir, eq_sets: Tuple[std.Project, suite.Session]):
    """
    Build manually the test file links.xml and make sure it is identical.
    """
    root_dir = Path(__file__).parent.parent
    schema = root_dir / 'src/ansys/scade/pyalmgw/res/schemas/eqsets.json'
    cls = TestLLRExport(*eq_sets)
    cls.read_schema(schema)
    d = cls.dump_model(diagrams=False)
    dst = local_tmpdir / 'eq_sets_llrs.json'
    cls.write(d, dst)
    ref = root_dir / 'tests' / 'ref' / 'eq_sets_llrs.json'
    print('compare', str(ref), str(dst))
    diffs = cmp_file(ref, dst, root=str(root_dir))
    failure = False
    for d in diffs:
        print(d.rstrip('\r\n'))
        failure = True
    assert not failure


if __name__ == '__main__':
    path = Path('tests/EqSets/EqSets.etp')
    project, session = load_project_session(path, path)
    test_eq_sets(Path(__file__).parent / 'tmp', (project, session))

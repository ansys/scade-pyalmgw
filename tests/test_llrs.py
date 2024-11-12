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
import os
from pathlib import Path
from typing import Tuple

import pytest

# shall modify sys.path to access SCACE APIs
from ansys.scade.apitools.info import get_scade_home

# isort: split
import scade.model.project.stdproject as std
import scade.model.suite as suite
import scade.model.testenv as qte

from ansys.scade.pyalmgw.llrs import LLRExport, QteLLRS, ScadeLLRS
from tests.conftest import load_project_session, load_project_test

root_dir = Path(__file__).parent.parent


@pytest.fixture(scope='session')
def eq_sets() -> Tuple[std.Project, suite.Session]:
    # unique model for these tests
    path = root_dir / 'tests/EqSets/EqSets.etp'
    project, session = load_project_session(path, path)
    return project, session


@pytest.fixture(scope='session')
def records() -> Tuple[std.Project, qte.TestApplication]:
    # unique model for these tests
    path = root_dir / 'tests/Records/Records.etp'
    project, application = load_project_test(path)
    return project, application


@pytest.fixture(scope='session')
def qte_llrs() -> Tuple[std.Project, qte.TestApplication]:
    # unique model for these tests
    path = root_dir / 'tests/QteLLRS/QteLLRS.etp'
    project, application = load_project_test(path)
    return project, application


@pytest.fixture(scope='session')
def scade_llrs() -> Tuple[std.Project, suite.Session]:
    # unique model for these tests
    path = root_dir / 'tests/ScadeLLRS/ScadeLLRS.etp'
    project, session = load_project_session(path, path)
    return project, session


def cmp_file(reference: Path, result: Path, n=3, linejunk=None):
    """Return the differences between the reference and the result file."""
    # reference: replace $(ROOT) and $(SCADE) with runtime data
    ref_lines = reference.open().read().split('\n')
    root = root_dir.as_posix()
    scade_home = get_scade_home().as_posix()
    ref_lines = [_.replace('$(ROOT)', root).replace('$(SCADE)', scade_home) for _ in ref_lines]
    with result.open() as f:
        if linejunk:
            res_lines = [_ for _ in f if not linejunk(_)]
        else:
            res_lines = f.read().split('\n')

    diff = difflib.context_diff(ref_lines, res_lines, str(reference), str(result), n=n)
    return diff


class TestLLRExportSuite(LLRExport):
    __test__ = False

    def __init__(self, project, session: suite.Session):
        self.session = session
        super().__init__(project)

    def get_export_classes(self, project: std.Project):
        # get_roots not available
        assert project == self.project
        assert 'SC' in project.get_tool_prop_def('STUDIO', 'PRODUCT', [], None)
        return [ScadeLLRS(self, self.session.model)]


class TestLLRExportTest(LLRExport):
    __test__ = False

    def __init__(self, project, application: qte.TestApplication):
        self.application = application
        super().__init__(project)

    def get_export_classes(self, project: std.Project):
        # get_roots not available
        assert project == self.project
        assert 'QTE' in project.get_tool_prop_def('STUDIO', 'PRODUCT', [], None)
        return [QteLLRS(self, self.application)]


def _call_export(cls, ref, tmp, diagrams=False) -> bool:
    """Export the llrs and print the differences."""
    dst = tmp / ref.name
    dump = cls.dump_model(diagrams=diagrams)
    cls.write(dump, dst)
    print('compare', str(ref), str(dst))
    diffs = cmp_file(ref, dst)
    failure = False
    for d in diffs:
        print(d.rstrip('\r\n'))
        failure = True
    return failure


def test_eq_sets(local_tmpdir, eq_sets: Tuple[std.Project, suite.Session]):
    """Test esqets.json schema."""
    schema = root_dir / 'src/ansys/scade/pyalmgw/res/schemas' / 'eqsets.json'
    ref = root_dir / 'tests' / 'ref' / 'eq_sets_llrs.json'
    cls = TestLLRExportSuite(*eq_sets)
    cls.read_schema(schema)
    failure = _call_export(cls, ref, local_tmpdir)
    assert not failure


def test_scade_llrs(local_tmpdir, scade_llrs: Tuple[std.Project, suite.Session]):
    """Test ScadeLLRS."""
    schema = root_dir / 'tests' / 'ScadeLLRS' / 'scade_all.json'
    ref = root_dir / 'tests' / 'ref' / 'scade_llrs.json'
    cls = TestLLRExportSuite(*scade_llrs)
    cls.read_schema(schema)
    failure = _call_export(cls, ref, local_tmpdir, diagrams=True)
    assert not failure


def test_records(local_tmpdir, records: Tuple[std.Project, qte.TestApplication]):
    """Test esqets.json schema."""
    schema = root_dir / 'src/ansys/scade/pyalmgw/res/schemas' / 'records.json'
    ref = root_dir / 'tests' / 'ref' / 'records_llrs.json'
    cls = TestLLRExportTest(*records)
    cls.read_schema(schema)
    failure = _call_export(cls, ref, local_tmpdir)
    assert not failure


def test_qte_llrs(local_tmpdir, qte_llrs: Tuple[std.Project, qte.TestApplication]):
    """Test QteLLRS."""
    schema = root_dir / 'tests' / 'QteLLRS' / 'qte_all.json'
    ref = root_dir / 'tests' / 'ref' / 'qte_llrs.json'
    cls = TestLLRExportTest(*qte_llrs)
    cls.read_schema(schema)
    failure = _call_export(cls, ref, local_tmpdir)
    assert not failure


if __name__ == '__main__':
    if False:
        path = root_dir / 'tests/EqSets/EqSets.etp'
        project, session = load_project_session(path, path)
        test_eq_sets(Path(__file__).parent / 'tmp', (project, session))
    if True:
        os.environ['SCADE'] = str(get_scade_home() / 'SCADE')

        path = root_dir / 'tests/ScadeLLRS/ScadeLLRS.etp'
        project, session = load_project_session(path)
        test_scade_llrs(Path(__file__).parent / 'tmp', (project, session))
    if False:
        path = root_dir / 'tests/Records/Records.etp'
        project, application = load_project_test(path)
        test_records(Path(__file__).parent / 'tmp', (project, application))
    if False:
        path = root_dir / 'tests/QteLLRS/QteLLRS.etp'
        project, application = load_project_test(path)
        test_qte_llrs(Path(__file__).parent / 'tmp', (project, application))

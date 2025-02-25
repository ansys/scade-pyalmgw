# Copyright (C) 2024 - 2025 ANSYS, Inc. and/or its affiliates.
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

import filecmp
from pathlib import Path
import subprocess
import sys

import pytest

import ansys.scade.pyalmgw as pyalmgw
import ansys.scade.pyalmgw.connector as cnt
import ansys.scade.pyalmgw.llrs as llrs
import ansys.scade.pyalmgw.utils as utils
from conftest import load_project, load_project_session, std, suite

_pyalmgw_dir = Path(pyalmgw.__file__).parent
_test_dir = Path(__file__).parent.parent / 'tests'
_ref_dir = _test_dir / 'ref'
_settings_dir = _test_dir / 'LLRSettings'


class TestExecuteConnector(cnt.Connector):
    __test__ = False

    def __init__(self, return_code: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.return_code = return_code
        # callback hits assessment
        self.settings = False
        self.import_ = False
        self.file = None
        self.export = False
        self.links = None
        self.manage = False
        self.locate = False
        self.req = None
        self.pid = 0

    def on_settings(self, pid: int) -> int:
        self.settings = True
        self.pid = pid
        return self.return_code

    def on_import(self, file: Path, pid: int) -> int:
        self.import_ = True
        self.file = file
        self.pid = pid
        return self.return_code

    def on_export(self, links: Path, pid: int) -> int:
        self.export = True
        self.links = links
        self.pid = pid
        return self.return_code

    def on_manage(self, pid: int) -> int:
        self.manage = True
        self.pid = pid
        return self.return_code

    def on_locate(self, req: str, pid: int) -> int:
        self.locate = True
        self.req = req
        self.pid = pid
        return self.return_code


def test_execute_settings():
    code = 9
    connector = TestExecuteConnector(code, 'ut', None)
    return_code = connector.execute('settings', 5)
    assert connector.settings
    assert connector.pid == 5
    assert return_code == code


@pytest.mark.parametrize('file', ['connector_import.xml', 'unknown.xml'])
@pytest.mark.parametrize('code', [0, -1])
@pytest.mark.parametrize('trace', [True, False])
def test_execute_import(file, code, trace):
    save_trace = utils.traceon
    utils.traceon = trace
    connector = TestExecuteConnector(code, 'ut', None)
    req_file = _ref_dir / file
    trace_file = Path('c:/temp/req.xml')
    trace_file.unlink(missing_ok=True)
    return_code = connector.execute('import', str(req_file), 1)
    utils.traceon = save_trace
    assert connector.import_
    assert return_code == code
    assert connector.pid == 1
    if trace and code == 0 and req_file.stem != 'unknown':
        if Path('c:/temp').exists():
            assert trace_file.exists()
            assert filecmp.cmp(trace_file, req_file)
    else:
        assert not trace_file.exists()


@pytest.mark.parametrize('file', ['connector_export.json', 'unknown.json'])
@pytest.mark.parametrize('trace', [True, False])
def test_execute_export(file, trace):
    save_trace = utils.traceon
    utils.traceon = trace
    code = 31
    connector = TestExecuteConnector(code, 'ut', None)
    links_file = _ref_dir / file
    trace_file = Path('c:/temp/links.json')
    trace_file.unlink(missing_ok=True)
    return_code = connector.execute('export', str(links_file), 2)
    utils.traceon = save_trace
    assert connector.export
    assert connector.pid == 2
    assert return_code == code
    if trace and links_file.stem != 'unknown':
        if Path('c:/temp').exists():
            assert trace_file.exists()
            assert filecmp.cmp(trace_file, links_file)
    else:
        assert not trace_file.exists()


def test_execute_manage():
    code = 32
    connector = TestExecuteConnector(code, 'ut', None)
    return_code = connector.execute('manage', 3)
    assert connector.manage
    assert connector.pid == 3
    assert return_code == code


def test_execute_locate():
    code = 46
    req = 'REQ_081'
    connector = TestExecuteConnector(code, 'ut', None)
    return_code = connector.execute('locate', req, 4)
    assert connector.locate
    assert connector.req == req
    assert connector.pid == 4
    assert return_code == code


def test_execute_robustness():
    connector = TestExecuteConnector(0, 'ut', None)
    return_code = connector.execute('unknown', 'a', 'b', 'c', 9)
    assert connector.pid == 0
    assert return_code == -1


class TestLLRExport(llrs.LLRExport):
    __test__ = False

    def __init__(self, project, session):
        self.session = session
        super().__init__(project)

    def get_export_classes(self, project: std.Project):
        # get_roots not available
        assert project == self.project
        return [llrs.ScadeLLRS(self, self.session.model)]


class TestLLRConnector(cnt.Connector):
    __test__ = False

    def __init__(
        self, *args, llrs_file: Path | None = None, session: suite.Session | None = None, **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.llrs_file = llrs_file
        self.session = session

    def get_llrs_file(self) -> Path:
        return self.llrs_file if self.llrs_file else super().get_llrs_file()

    def get_export_class(self) -> llrs.LLRExport | None:
        if self.session:
            return TestLLRExport(self.project, self.session)
        else:
            return super().get_export_class()

    def on_settings(self, pid: int) -> int:
        assert False

    def on_import(self, file: Path, pid: int) -> int:
        assert False

    def on_export(self, links: Path, pid: int) -> int:
        assert False

    def on_manage(self, pid: int) -> int:
        assert False

    def on_locate(self, req: str, pid: int) -> int:
        assert False


def test_get_llr_diagram():
    project = load_project(_settings_dir / 'Default.etp')
    assert project
    connector = TestLLRConnector('ut', project)
    # Default.etp has the property set
    diagrams = connector.get_llr_diagrams()
    assert diagrams


@pytest.mark.parametrize(
    'products, expected',
    [
        ([], 'eqsets.json'),
        (['SC'], 'eqsets.json'),
        (['QTE'], 'records.json'),
        (['SC', 'QTE'], 'records.json'),
        (['QTE', 'SC'], 'records.json'),
        (['DISPLAY'], 'display.json'),
        (['SYSTEM'], 'system.json'),
    ],
)
def test_get_llr_default_schema(products, expected):
    project = load_project(_settings_dir / 'Default.etp')
    assert project
    project.set_tool_prop_def('STUDIO', 'PRODUCT', products, [], None)
    connector = TestLLRConnector('ut', project)
    schema = connector.get_llr_default_schema()
    assert schema.name == expected


@pytest.mark.parametrize(
    'project, expected',
    [
        (
            _settings_dir / 'Default.etp',
            _pyalmgw_dir / 'res/schemas' / 'eqsets.json',
        ),
        (_settings_dir / 'Relative.etp', _settings_dir / 'relative.json'),
        (_settings_dir / 'Absolute.etp', 'c:/absolute.json'),
    ],
)
def test_get_llr_schema(project, expected):
    project = load_project(project)
    assert project
    connector = TestLLRConnector('ut', project)
    schema = connector.get_llr_schema()
    assert schema == Path(expected)


def test_export_llrs_nominal(local_tmpdir):
    # @STUDIO:PRODUCT is not defined for this project
    path = _settings_dir / 'Default.etp'
    project, session = load_project_session(path, path)
    assert project
    assert session
    target_path = local_tmpdir / 'llrs_nominal.json'
    connector = TestLLRConnector('ut', project, session=session, llrs_file=target_path)
    path = connector.export_llrs()
    assert path == target_path


def test_export_llrs_robustness():
    # @STUDIO:PRODUCT is not defined for this project
    project = load_project(_settings_dir / 'Default.etp')
    assert project
    connector = TestLLRConnector('ut', project)
    path = connector.export_llrs()
    assert path is None


@pytest.mark.parametrize(
    'command, args, pid, expected',
    [
        # return code is expected to be unsigned: 4294967295 == -1
        ('settings', [], 9, 4294967295),
        ('manage', [], 12, 4294967295),
        ('locate', ['REQ_ID_031'], 32, 4294967295),
        ('locate', [], 46, 3),
        ('import', ['<tmp>/export.xml'], 65, 0),
        ('export', [str(Path(__file__).parent / 'res' / 'empty.json')], 81, 1),
        ('unknown', [], 82, 4294967295),
    ],
)
def test_main(local_tmpdir, command: str, args: list[str], pid: int, expected: int):
    # create an empty project
    path = local_tmpdir / ('main_' + command) / 'empty.vsp'
    path.parent.mkdir(exist_ok=True)
    with path.open('w'):
        pass
    # use the stub connector
    cmd = [
        sys.executable,
        '-m',
        'ansys.scade.pyalmgw.stub',
        '-' + command,
        Path(path),
    ]
    args = [_.replace('<tmp>', str(path.parent)) for _ in args]
    cmd.extend(args)
    cmd.append(str(pid))
    status = subprocess.run(cmd, capture_output=True)
    if status.stderr:
        print(status.stderr.decode('utf-8').strip('\n'))
        assert False
    out = status.stdout.decode('utf-8').strip('\n')
    print(out)
    assert command in out
    assert status.returncode == expected

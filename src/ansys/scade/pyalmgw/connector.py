# Copyright (C) 2024 ANSYS, Inc. and/or its affiliates.
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

# interfaces
from abc import ABCMeta, abstractmethod
from pathlib import Path
import shutil
import sys
from typing import Optional

# import scade_env through __init__ before importing any SCADE module
from ansys.scade.apitools import declare_project

# isort: split
from scade.model.project.stdproject import Project, get_roots as get_projects

from ansys.scade.pyalmgw.llrs import get_export_class
import ansys.scade.pyalmgw.utils as utils
from ansys.scade.pyalmgw.utils import traceln


class Connector(metaclass=ABCMeta):
    def __init__(self, id: str, project: Optional[Project] = None):
        self.project = project
        self.id = id

    # llrs
    def get_llrs_file(self) -> Path:
        assert self.project
        return Path(self.project.pathname).with_suffix('.' + self.id + '.llrs')

    def get_llr_schema(self) -> Optional[Path]:
        assert self.project
        file = self.project.get_scalar_tool_prop_def('ALMGW', 'LLRSCHEMA', '', None)
        if file:
            directory = Path(self.project.pathname).resolve().parent
            path = Path(file)
            if not path.is_absolute():
                path = directory.joinpath(path)
        else:
            path = self.get_llr_default_schema()
        return path

    def get_llr_default_schema(self) -> Path:
        assert self.project
        products = self.project.get_tool_prop_def('STUDIO', 'PRODUCT', [], None)
        # give SCADE Test the priority if mixed projects Test/Suite
        if 'QTE' in products:
            name = 'records.json'
        if 'SYSTEM' in products:
            name = 'system.json'
        if 'DISPLAY' in products:
            name = 'display.json'
        if 'SC' in products or not name:
            name = 'eqsets.json'
        return Path(__file__).parent / 'res' / 'schemas' / name

    def get_llr_diagrams(self) -> bool:
        assert self.project
        return self.project.get_bool_tool_prop_def('ALMGW', 'DIAGRAMS', False, None)

    def export_llrs(self):
        assert self.project
        # apply the script to the project
        pathname = self.get_llrs_file()
        schema = self.get_llr_schema()
        diagrams = self.get_llr_diagrams()
        cls = get_export_class(self.project)
        if cls is None:
            traceln('No export class available for this project')
            return None
        cls.read_schema(schema)
        data = cls.dump_model(diagrams=diagrams)
        cls.write(data, pathname)
        return pathname

    # ---------------------------------------------
    # virtuals
    # ---------------------------------------------

    @abstractmethod
    def on_settings(self) -> int:
        raise NotImplementedError('Abstract method call')

    @abstractmethod
    def on_import(self, file: Path) -> int:
        raise NotImplementedError('Abstract method call')

    @abstractmethod
    def on_export(self, links: Path) -> int:
        raise NotImplementedError('Abstract method call')

    @abstractmethod
    def on_manage(self) -> int:
        raise NotImplementedError('Abstract method call')

    @abstractmethod
    def on_locate(self, req: str) -> int:
        raise NotImplementedError('Abstract method call')

    # ---------------------------------------------
    # commands
    # ---------------------------------------------

    # return value:
    # -1 if an error occurs, therefore previous settings information is kept
    # 0 set settings information is OK
    # 1 ALM Gateway project is removed, i.e., ALM connection is reset
    def _cmd_settings(self) -> int:
        # virtual call
        code = self.on_settings()
        return code

    # return value:
    # -1 if an error occurs, therefore previous export status and requirement tree is kept
    # 0 requirements and traceability links are correctly imported
    def _cmd_import(self, req_file: Path) -> int:
        # virtual call
        code = self.on_import(req_file)

        if code == 0 and utils.traceon:
            # save a copy for debug purposes
            try:
                shutil.copyfile(req_file, 'c:/temp/req.xml')
            except BaseException:
                pass
        return code

    # return value:
    # -1: if an error occurs, therefore previous export status and requirement tree is kept
    # 0: traceability links are not exported
    # 1: traceability links are exported
    # 2: previous export status and requirement tree is kept; XML file is not returned on the given <XML Requirements Path>
    def _cmd_export(self, links: Path) -> int:
        if utils.traceon:
            # save a copy for debug purposes
            try:
                shutil.copyfile(links, 'c:/temp/links.json')
            except BaseException:
                pass
        # virtual call
        code = self.on_export(links)

        return code

    # return value:
    # -1: if an error occurs launching the command
    # 0: if ‘Management’ window of the customized ALM connection is successfully launched
    # 1: : to clean requirement list on the 'Requirement' window
    def _cmd_manage(self) -> int:
        code = self.on_manage()
        return code

    # return value:
    # -1: if an error occurs executing the command
    # 0: if the command is successfully executed
    def _cmd_locate(self, req: str) -> int:
        code = self.on_locate(req)
        return code

    def execute(self, command, *args) -> int:
        if command == 'settings':
            code = self._cmd_settings()
        elif command == 'manage':
            code = self._cmd_manage()
        elif command == 'locate':
            code = self._cmd_locate(args[0])
        elif command == 'import':
            code = self._cmd_import(Path(args[0]))
        elif command == 'export':
            code = self._cmd_export(Path(args[0]))
        else:
            print('%s: Unknown command' % command)
            code = -1
        return code

    def main(self) -> int:
        """Package entry point."""
        # the possible command lines are referenced in SC-IRS-040
        # generic pattern: -<command> <project> <arg>* <pid>
        # note: the syntax of the various command lines does not favor the usage of ArgumentParser
        command = sys.argv[1][1:]
        path = sys.argv[2]
        args = sys.argv[3:-1]
        # unused: pid = sys.argv[-1]

        assert declare_project
        declare_project(path)
        self.project = get_projects()[0]

        try:
            code = self.execute(command, *args)
        except BaseException:
            print('command', command, 'failed')
            code = -1
        exit(code)

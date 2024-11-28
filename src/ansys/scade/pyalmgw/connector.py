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

"""
SCADE LifeCycle ALM Gateway Python interface for external connectors.

New connectors must derive the ``Connector`` class and implement the abstract methods.

The other methods can be also overridden to provide alternative implementations.
"""

from abc import ABCMeta, abstractmethod
from pathlib import Path
import shutil
import sys
from typing import Optional

# shall modify sys.path to access SCACE APIs
from ansys.scade.apitools import declare_project

# must be imported after apitools
# isort: split
from scade.model.project.stdproject import Project, get_roots as get_projects

import ansys.scade.pyalmgw as pyalmgw
from ansys.scade.pyalmgw.llrs import LLRExport, get_export_class
import ansys.scade.pyalmgw.utils as utils


class Connector(metaclass=ABCMeta):
    """Top-level class for an external ALM Gateway connector."""

    def __init__(self, id: str, project: Optional[Project] = None):
        self.project = project
        self.id = id

    # llrs
    def get_llrs_file(self) -> Path:
        """Return the default path of the file to contain the exported LLRS."""
        assert self.project
        return Path(self.project.pathname).with_suffix('.' + self.id + '.llrs')

    def get_llr_schema(self) -> Path:
        """
        Return the schema to be used for exporting the LLRS.

        By default, the information is expected to be persisted in the project as
        a tool property ``@ALMGW:LLRSCHEMA``. If the property is not defined, the
        method returns a default schema.
        """
        assert self.project
        file = self.project.get_scalar_tool_prop_def(
            pyalmgw.TOOL, pyalmgw.LLRSCHEMA, pyalmgw.LLRSCHEMA_DEFAULT, None
        )
        if file:
            directory = Path(self.project.pathname).resolve().parent
            path = Path(file)
            if not path.is_absolute():
                path = directory.joinpath(path)
        else:
            path = self.get_llr_default_schema()
        return path

    def get_llr_default_schema(self) -> Path:
        """
        Return a default schema to be used for exporting the surrogate model.

        The schema depends on the project's nature: SCADE Suite, Test, Display or Architect.
        """
        assert self.project
        products = self.project.get_tool_prop_def('STUDIO', 'PRODUCT', [], None)
        # give SCADE Test the priority if mixed projects Test/Suite
        name = ''
        if 'QTE' in products:
            name = 'records.json'
        elif 'SYSTEM' in products:
            name = 'system.json'
        elif 'DISPLAY' in products:
            name = 'display.json'
        else:
            # 'SC' or unknown:
            name = 'eqsets.json'
        return Path(__file__).parent / 'res' / 'schemas' / name

    def get_llr_diagrams(self) -> bool:
        """
        Return whether the surrogfate model should include images: diagrams or panels for example.

        By default, the information is expected to be persisted in the project as
        a tool property ``@ALMGW:DIAGRAMS`` (default: ``false``).
        """
        assert self.project
        return self.project.get_bool_tool_prop_def('ALMGW', 'DIAGRAMS', False, None)

    def export_llrs(self):
        """Generate the surrogate models."""
        assert self.project
        # apply the script to the project
        pathname = self.get_llrs_file()
        schema = self.get_llr_schema()
        diagrams = self.get_llr_diagrams()
        cls = self.get_export_class()
        if cls is None:
            print('No export class available for this project')
            return None
        cls.read_schema(schema)
        data = cls.dump_model(diagrams=diagrams)
        cls.write(data, pathname)
        return pathname

    def get_export_class(self) -> Optional[LLRExport]:
        """Return an instance of LLRExport."""
        return get_export_class(self.project)

    # ---------------------------------------------
    # abstract methods
    # ---------------------------------------------

    @abstractmethod
    def on_settings(self, pid: int) -> int:
        """Process the ``settings`` command."""
        raise NotImplementedError('Abstract method call')

    @abstractmethod
    def on_import(self, file: Path, pid: int) -> int:
        """Process the ``import`` command."""
        raise NotImplementedError('Abstract method call')

    @abstractmethod
    def on_export(self, links: Path, pid: int) -> int:
        """Process the ``export`` command."""
        raise NotImplementedError('Abstract method call')

    @abstractmethod
    def on_manage(self, pid: int) -> int:
        """Process the ``manage`` command."""
        raise NotImplementedError('Abstract method call')

    @abstractmethod
    def on_locate(self, req: str, pid: int) -> int:
        """Process the ``locate`` command."""
        raise NotImplementedError('Abstract method call')

    # ---------------------------------------------
    # ALM Gateway commands
    # ---------------------------------------------

    def _cmd_settings(self, pid: int) -> int:
        """
        Execute the command ``settings``.

        Parameters
        ----------
        pid : int
            SCADE product process ID.

        Returns
        -------
        int

            * -1: if an error occurs, therefore previous settings information shall be kept
            * 0: set settings information shall be OK
            * 1: ALM Gateway project shall be removed, i.e., ALM connection shall be reset
        """
        code = self.on_settings(pid)
        return code

    def _cmd_import(self, req_file: Path, pid: int) -> int:
        """
        Execute the command ``import``.

        Parameters
        ----------
        path : Path
            Absolute path where the XML requirements file is saved.
        pid : int
            SCADE product process ID.

        Returns
        -------
        int

            * -1: if an error occurs, therefore previous export status and requirement tree shall be kept
            * 0: requirements and traceability links shall be correctly imported
        """
        code = self.on_import(req_file, pid)

        if code == 0 and utils.traceon:
            # save a copy for debug purposes
            try:
                shutil.copyfile(req_file, 'c:/temp/req.xml')
            except BaseException:
                pass
        return code

    def _cmd_export(self, links: Path, pid: int) -> int:
        """
        Execute the command ``export``.

        Parameters
        ----------
        path : Path
            Path of a JSON file that contains the links to add and remove.
        pid : int
            SCADE product process ID.

        Returns
        -------
        int

            * -1: if an error occurs, therefore previous export status and requirement tree shall be kept
            * 0: requirements and traceability links shall not be exported
            * 1: requirements and traceability links shall be exported
            * 2: previous export status and requirement tree shall be kept
        """
        if utils.traceon:
            # save a copy for debug purposes
            try:
                shutil.copyfile(links, 'c:/temp/links.json')
            except BaseException:
                pass
        # virtual call
        code = self.on_export(links, pid)

        return code

    def _cmd_manage(self, pid: int) -> int:
        """
        Execute the command ``manage``.

        Parameters
        ----------
        pid : int
            SCADE product process ID.

        Returns
        -------
        int

            * -1: if an error occurs launching the command
            * 0: if ‘Management Requirements’ UI of ALM tool is successfully launched
            * 1: to clean requirement list on the SCADE IDE 'Requirements' window
        """
        code = self.on_manage(pid)
        return code

    def _cmd_locate(self, req: str, pid: int) -> int:
        """
        Execute the command ``locate``.

        Parameters
        ----------
        req : str
            Identifier of a requirement defined on the corresponding ALM tool.
        pid : int
            SCADE product process ID.

        Returns
        -------
        int

            * -1: if an error occurs executing the command
            * 0: if the command is successfully executed
        """
        code = self.on_locate(req, pid)
        return code

    def execute(self, command: str, *args: str) -> int:
        """
        Execute the ALM Gateway command.

        Parameters
        ----------
        command : str
            Input command, must be one of settings, manage, locate, import or export.
        *args : str
            Parameters of the command

        Returns
        -------
        int
            Return code of the executed command.
        """
        if command == 'settings':
            # <Process ID>
            code = self._cmd_settings(int(args[0]))
        elif command == 'manage':
            # <Process ID>
            code = self._cmd_manage(int(args[0]))
        elif command == 'locate':
            # <reqId> <Process ID>
            code = self._cmd_locate(args[0], int(args[1]))
        elif command == 'import':
            # <XML Requirements Path>  <Process ID>
            code = self._cmd_import(Path(args[0]), int(args[1]))
        elif command == 'export':
            # <Links Path> <Process ID>
            code = self._cmd_export(Path(args[0]), int(args[1]))
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
        args = sys.argv[3:]

        assert declare_project
        declare_project(path)
        self.project = get_projects()[0]

        try:
            code = self.execute(command, *args)
        except BaseException as e:
            print('command', command, 'failed with', str(e))
            code = 3
        return code

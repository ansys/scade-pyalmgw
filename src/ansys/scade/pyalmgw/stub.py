# -*- coding: utf-8 -*-

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

"""
Integration test.

This entry point can be registered to Ansys SCADE ALM Gateway to exercise
the commands and validate the format of the exchanged files.
"""

from pathlib import Path
import shutil
import sys

from ansys.scade.pyalmgw.connector import Connector
from ansys.scade.pyalmgw.documents import ReqProject, TraceabilityLink
from ansys.scade.pyalmgw.utils import read_json


class StubProject(ReqProject):
    """Stubs the ``ReqProject`` class for unit testing and example."""

    def merge_links(self, file: Path):
        """
        Merge the traceability deltas from a cache file (ALMGT).

        The links are either created or deleted.

        Parameters
        ----------
        file : Path
            Input ALMGT file.
        """
        deltas = read_json(file)

        # cache existing requirements
        requirements = {req.id: req for doc in self.documents for req in doc.iter_requirements()}
        # cache existing links
        links = {f'{link.source}{link.target}': link for link in self.traceability_links}
        for delta in deltas:
            oid = delta['source']['oid']
            req = delta['target']['req_id']
            action = delta['action']
            # action is either 'ADD' or 'REMOVE'
            add = action == 'ADD'

            key = oid + req
            link = links.get(key)
            if add:
                if not link:
                    requirement = requirements.get(req)
                    if not requirement:
                        print(f'add a link to an unexisting requirement: {oid} -> {req}')
                    else:
                        print(f'adding link {oid} -> {req}')
                    link = TraceabilityLink(self, requirement, oid, req)
                    links[key] = link
                else:
                    # error
                    print(f'link already present: {oid} -> {req}')
            else:
                if link:
                    print(f'removing link {oid} -> {req}')
                    self.traceability_links.remove(link)
                else:
                    # error
                    print(f'link not present: {oid} -> {req}')


class StubConnector(Connector):
    """Stubs the ``Connector`` class for unit testing and example."""

    def get_stub_file(self) -> Path:
        """
        Return a stub requirements file for ALM Gateway.

        The function makes a local copy of a resource file
        so that it can be modified by the ALMGW commands.

        Returns
        -------
        Path
            Path of the requirements file.
        """
        # self.project must have been set in main()
        assert self.project is not None  # nosec B101  # addresses linter
        local_stub = Path(self.project.pathname).with_suffix('.almgw.stub.xml')
        if not local_stub.exists():
            print('initializing stub file:', local_stub)
            ref_stub = Path(__file__).parent / 'res' / 'stub.xml'
            shutil.copyfile(ref_stub, local_stub)
        return local_stub

    def on_settings(self, pid: int) -> int:
        """Stub the command ``settings``."""
        print('settings (%d): command stubbed' % pid)
        return -1

    def on_import(self, file: Path, pid: int) -> int:
        """
        Import requirements and traceability links to ALM Gateway.

        The function copies the stub file to the provided path.

        Parameters
        ----------
        path : Path
            Absolute path where the XML requirements file is saved.
        pid : int
            SCADE product process ID.
        """
        stub = self.get_stub_file()
        print('import %s (%d): using stub file %s' % (file, pid, stub))
        shutil.copyfile(stub, file)
        return 0

    def on_export(self, links: Path, pid: int) -> int:
        """
        Export traceability links and Contributing Elements (surrogate model).

        Parameters
        ----------
        links : Path
            Path of a JSON file that contains the links to add and remove.
        pid : int
            SCADE product process ID.
        """
        # 1. merge the traceability deltas into the stub file
        stub = self.get_stub_file()
        print('export %s (%d): using stub file %s' % (links, pid, stub))
        copy = stub.with_name(links.with_suffix('.stub' + links.suffix).name)
        shutil.copyfile(links, copy)
        doc = StubProject(stub)
        doc.read()
        doc.merge_links(links)
        doc.write()
        # 2. export the LLRs using default schemas depending on the project's nature
        self.export_llrs()
        return 1

    def on_manage(self, pid: int) -> int:
        """Stub the command ``manage``."""
        print('manage (%d): command stubbed' % pid)
        return -1

    def on_locate(self, req: str, pid: int) -> int:
        """Stub the command ``locate``."""
        print('locate %s (%d): command stubbed' % (req, pid))
        return -1


def main():
    """Package integration test entry point."""
    print(' '.join(sys.argv))
    connector = StubConnector('stub')
    code = connector.main()
    return code


if __name__ == '__main__':
    code = main()
    print('done')
    sys.exit(code)

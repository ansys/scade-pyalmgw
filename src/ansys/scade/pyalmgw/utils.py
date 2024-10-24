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


import json
from pathlib import Path

# debug
traceon = False


def traceln(text: str):
    if traceon:
        print(text)


def read_json(path: Path):
    if traceon:
        # save a copy for debug purposes
        # shutil.copyfile(file, "c:/temp/json.txt")
        pass
    try:
        return json.load(path.open())
    except BaseException as e:
        print(e)
        return None


def write_json(object, path: Path) -> bool:
    if traceon:
        # save a copy for debug purposes
        # shutil.copyfile(file, "c:/temp/json.txt")
        pass
    try:
        with path.open('w') as f:
            json.dump(object, f, indent=4, sort_keys=True)
        return True
    except BaseException as e:
        print(e)
        return False

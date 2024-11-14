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

from abc import ABCMeta, abstractmethod
from argparse import ArgumentParser
from base64 import b64encode
import os
from pathlib import Path
from re import compile
from shutil import copyfile
import subprocess
import sys

# shall modify sys.path to access SCACE APIs
from ansys.scade.apitools import declare_project
from ansys.scade.apitools.info import get_scade_home

# isort: split

import _scade_api
import scade
import scade.model.display as sdy
import scade.model.project.stdproject as std
import scade.model.suite as suite
import scade.model.testenv as test

from ansys.scade.pyalmgw.utils import read_json, traceln, write_json

# make script's implementation directory visible
script_dir = Path(__file__).parent

if __name__ != '__main__':  # pragma: no cover
    import scade.model.architect as system

# -----------------------------------------------------------------------------
# llrs.py
# -----------------------------------------------------------------------------

# global variable used by filters: allow the usage of list comprehensions
# https://stackoverflow.com/questions/32763500/nameerror-using-eval-inside-dictionary-comprehension
child = None


def read_project_id(project):
    pathname = str(Path(project.pathname).with_suffix('.almgp'))
    try:
        f = open(pathname, 'r')
    except BaseException as e:
        print(str(e))
        return None

    re = compile(r'.*\s+id="([^"]*)"')
    for line in f:
        match = re.match(line)
        if match:
            return match.groups()[0]

    return None


class LLRExport:
    def __init__(self, project):
        self.schema = None
        self.project = project
        self.project_id = read_project_id(project)
        self.export_classes = self.get_export_classes(project)
        self.roots = [export_class.root for export_class in self.export_classes]
        if self.export_classes:
            # several roots, the first one provides the top-level name
            # self.root = self.roots[0]
            self.kind = self.export_classes[0].kind
            self.valid = True
        else:
            # self.root = None
            self.kind = None
            self.valid = False
        self.diagrams = False
        # index table on the schema
        self.classes = {}
        self.version = LLRS.VCUSTOM

    def read_schema(self, pathname):
        self.schema = read_json(pathname)
        if self.schema is not None:
            for element in self.schema:
                self.classes[element.get('class')] = element

    def get_url(self, oid):
        return 'http://localhost:8080/scade_provider/services/{0}/requirements/{1}'.format(
            self.project_id, b64encode(oid.encode()).decode()
        )

    # TODO VCUSTOM def dump_model(self, diagrams = False, version = VCUSTOM):
    def dump_model(self, diagrams: bool = False, version: int = 0, empty: str = '') -> dict:
        assert self.export_classes

        # main export class
        main = self.export_classes[0]

        self.diagrams = diagrams
        self.version = version
        self.empty = empty
        for export_class in self.export_classes:
            export_class.version = version

        elements = []
        section_oid = main.get_model_oid(main.root) + ':_'
        section = main.new_section(main.get_model_name(main.root), elements, section_oid)
        for export_class in self.export_classes:
            export_class.dump_children(
                elements,
                export_class.root,
                export_class.get_item_class(export_class.root),
                section_oid,
            )

        model = {
            'name': main.get_model_name(main.root),
            'type': self.kind,
            'path': Path(self.project.pathname).as_posix(),
            'elements': [section],
        }

        return model

    def write(self, llrs, pathname):
        write_json(llrs, pathname)

    def get_export_classes(self, project: std.Project):
        llrs = []
        products = project.get_tool_prop_def('STUDIO', 'PRODUCT', [], None)
        # give SCADE Test the priority if mixed projects Test/Suite
        if 'QTE' in products:
            llrs.append(QteLLRS(self, test.get_roots()[0]))
        if 'SC' in products:
            llrs.append(ScadeLLRS(self, suite.get_roots()[0].model))
        if 'SYSTEM' in products:
            llrs.append(SystemLLRS(self, system.get_roots()[0]))
        if 'DISPLAY' in products:
            llrs.append(DisplayLLRS(self))
        return llrs


class LLRS(metaclass=ABCMeta):
    # versions
    VCUSTOM = 0
    V194 = 4
    # other versions are deprecated and not supported anymore

    def __init__(self, llr_export: LLRExport, kind, root):
        self.llr_export = llr_export
        self.kind = kind
        self.root = root
        self.version = LLRS.VCUSTOM
        # regular expression for paths
        self.re_path = compile(r'^(\w+)(?:{(.*)})?$')

    def get_url(self, oid):
        return self.llr_export.get_url(oid)

    # -----------------------------------------------------------------------------
    # abstractions
    # -----------------------------------------------------------------------------

    @abstractmethod
    def get_model_name(self, model):
        raise NotImplementedError('Abstract method call: get_model_name')

    @abstractmethod
    def get_model_oid(self, model):
        raise NotImplementedError('Abstract method call: get_model_oid')

    @abstractmethod
    def get_item_class(self, item):
        raise NotImplementedError('Abstract method call: get_item_class')

    @abstractmethod
    def get_item_name(self, item):
        raise NotImplementedError('Abstract method call: get_item_name')

    @abstractmethod
    def get_item_pathname(self, item):
        raise NotImplementedError('Abstract method call: get_item_pathname')

    @abstractmethod
    def get_item_oid(self, item):
        raise NotImplementedError('Abstract method call: get_item_oid')

    @abstractmethod
    def get_item_links(self, item, role, sort):
        raise NotImplementedError('Abstract method call: get_item_links')

    @abstractmethod
    def get_item_attribute(self, item, name):
        raise NotImplementedError('Abstract method call: get_item_attribute')

    @abstractmethod
    def get_item_attributes(self, item):
        raise NotImplementedError('Abstract method call: get_item_attributes')

    def get_item_image(self, item):
        return None

    # -----------------------------------------------------------------------------
    # schema based visit
    # -----------------------------------------------------------------------------

    def new_section(self, name: str, elements: list, oid: str) -> dict:
        section = {
            'name': name,
            'almtype': 'section',
            'oid': oid,
            'elements': elements,
        }
        return section

    def dump_sub_elements(self, container, item, cls, flatten, parent_oid):
        global child

        if cls is None:
            return []
        schema = self.llr_export.classes.get(cls)
        if schema is None:
            return []
        parent = schema.get('parent')
        structure = schema.get('structure', [])
        for entry in structure:
            folder = entry.get('folder')
            flags = entry.get('flags', [])
            content = entry.get('content', [])
            sort = 'sort' in flags
            sibling = 'sibling' in flags
            if sibling:
                pass
            if (not flatten and sibling) or (flatten and not sibling):
                continue
            if folder is not None:
                subelements = []
                section_oid = parent_oid + ':' + folder
                section = self.new_section(folder, subelements, section_oid)
                new_parent_oid = section_oid
            else:
                section = None
                subelements = container
                new_parent_oid = parent_oid

            for composition in content:
                role = composition.get('role')
                if role is None:
                    continue
                kind = composition.get('kind')
                class_ = composition.get('class')
                filter = composition.get('filter')
                # if kind is specified as empty, get the last role of the path
                if kind == '':
                    kind, _ = self.decompose_role(item, role.split('.')[-1])
                for child in self.get_links(item, role, sort):
                    # deprecated
                    if class_ is not None and self.get_item_class(child) != class_:
                        continue
                    if filter is not None and not eval(filter):
                        continue
                    self.dump_item(subelements, child, kind, new_parent_oid)

            if section is not None and len(subelements) != 0:
                container.append(section)

        self.dump_sub_elements(container, item, parent, flatten, parent_oid)

    def decompose_role(self, item, role_expression: str):
        m = self.re_path.match(role_expression)
        if not m:
            raise PathError(
                self.get_item_pathname(item),
                "Invalid role '{0}' for class {1}".format(
                    role_expression, self.get_item_class(item)
                ),
            )
        role, classes = m.groups()
        names = [_.strip() for _ in classes.split(',')] if classes else None
        return role, names

    def get_attribute(self, item, path):
        path_elements = path.split('.')
        dstitem = item
        for role in path_elements[:-1]:
            try:
                items = self.get_item_links(dstitem, role, False)
            except BaseException:
                raise PathError(
                    path,
                    "Invalid role '{0}' for class {1}".format(role, self.get_item_class(dstitem)),
                )
            if len(items) == 0:
                # for example type.name and type is None
                return ''
            if len(items) != 1:
                # error, access to a collection
                return None
            dstitem = items[0]

        try:
            value = self.get_item_attribute(dstitem, path_elements[-1])
        except BaseException:
            raise PathError(
                path,
                "Invalid attribute '{0}' for class {1}".format(
                    path_elements[-1], self.get_item_class(dstitem)
                ),
            )
        return value

    def get_links(self, item, path, sort):
        roles = path.split('.')
        items = [item]
        for role_expression in roles:
            role, names = self.decompose_role(item, role_expression)
            dstitems = []
            for dstitem in items:
                try:
                    links = self.get_item_links(dstitem, role, sort)
                except BaseException:
                    raise PathError(
                        path,
                        "Invalid role '{0}' for class {1}".format(
                            role, self.get_item_class(dstitem)
                        ),
                    )
                dstitems += [_ for _ in links if not names or self.get_item_class(_) in names]
            items = dstitems
        return dstitems

    def dump_children(self, container, item, cls, parent_oid):
        self.dump_sub_elements(container, item, cls, False, parent_oid)

    def dump_siblings(self, container, item, cls, parent_oid):
        self.dump_sub_elements(container, item, cls, True, parent_oid)

    def dump_item(self, container, item, kind, parent_oid):
        cls = self.get_item_class(item)
        schema = self.llr_export.classes.get(cls) if cls is not None else None

        if schema is None:
            isllr = True
            folder = None
            properties = []
        else:
            isllr = schema.get('isllr', False)
            folder = schema.get('folder')
            properties = schema.get('properties', [])
        if kind is None:
            kind = self.get_item_class(item)

        if not isllr and folder is None:
            # when the item is neither a requirement or a section, traverse only
            # the composition without any additional node in the hierarchy
            self.dump_children(container, item, cls, parent_oid)
            self.dump_siblings(container, item, cls, parent_oid)
            return

        item_oid = self.get_item_oid(item)
        if not item_oid:
            item_oid = parent_oid + self.get_item_name(item)

        if folder is not None:
            subelements = []
            section_name = folder + ' ' if folder != '' else ''
            section_oid = item_oid + ':_'
            section = self.new_section(
                section_name + self.get_item_name(item), subelements, section_oid
            )
        else:
            section = None
            subelements = container

        if isllr:
            oid = self.get_item_oid(item)
            element = {
                'oid': oid,
                'pathname': self.get_item_pathname(item),
                'name': self.get_item_name(item),
                'scadetype': kind,
                'almtype': 'req',
            }
            if self.version == LLRS.VCUSTOM:
                # for custom connectors
                element['url'] = self.get_url(oid)
                iconfile = script_dir / 'res' / self.kind / (kind + '.png')
                if not iconfile.exists():
                    # icon not available locally, try in the product
                    almicondir = (
                        get_scade_home() / 'SCADE LifeCycle' / 'ALM Gateway' / 'reqtifygw' / 'icons'
                    )
                    iconfile = almicondir / self.kind / (kind + '.png')
                if iconfile.exists():
                    element['icon'] = iconfile.as_posix()

            if self.llr_export.diagrams:
                path = self.get_item_image(item)
                if path is not None:
                    element['image'] = path

            # attributes
            attributes = self.get_item_attributes(item)
            for property in properties:
                name = property.get('name')
                if not name:
                    continue
                path = property.get('path')
                if not path:
                    continue
                value = self.get_attribute(item, path)
                if not value:
                    # may happen if the attribute is a null reference object w/o # or @
                    # some ALM tools raise exceptions with empty values
                    value = self.llr_export.empty
                elif name[0] == '@':
                    # value is expected to be a reference
                    value = self.get_item_pathname(value)
                elif name[0] == '#':
                    # value is expected to be a reference
                    value = self.get_item_oid(value)
                attributes.append({'name': name, 'value': str(value)})

            if len(attributes) != 0:
                element['attributes'] = attributes
            subelements.append(element)
            if section is not None:
                # add content as sibling of item's llr
                children = subelements
            else:
                # llr has children, although this is not advised
                children = []
        else:
            children = subelements

        self.dump_children(children, item, cls, item_oid)

        self.dump_siblings(subelements, item, cls, parent_oid)

        if section is not None:
            if len(subelements) != 0:
                container.append(section)
        else:
            assert isllr
            if len(children) != 0:
                element['elements'] = children


# -----------------------------------------------------------------------------
# specializations
# -----------------------------------------------------------------------------


class StdLLRS(LLRS):
    def __init__(self, llr_export: LLRExport, kind, root):
        return super().__init__(llr_export, kind, root)

    def get_item_class(self, item):
        return item._class_

    def get_item_links(self, item, role, sort):
        items = _scade_api.get(item, role)
        if items is None:
            return []
        if not isinstance(items, list):
            items = [items]
        if sort:
            # new 2019 R1
            items = items.copy()
            items.sort(key=lambda elem: self.get_item_name(elem).lower())
        return items

    def get_item_attribute(self, item, name):
        value = _scade_api.get(item, name)
        return value


class AnnotatedLLRS(StdLLRS):
    def __init__(self, llr_export: LLRExport, kind, root, note_types):
        super().__init__(llr_export, kind, root)
        self.note_types = note_types
        self.llr_fields = {}
        self.gather_llr_fields()

    # helper for suite/system
    def gather_llr_fields(self):
        for type in self.note_types:
            attributes = []
            for att in type.ann_att_definitions:
                # ann_properties for scade and something different for system:
                # -> let's use the original one
                for prop in _scade_api.get(att, 'annProperty'):
                    if prop.name == 'LLR_PROP':
                        attributes.append([prop.value, att.name])
                        break

            if len(attributes) != 0:
                # register the note type and its attributes
                self.llr_fields[type] = attributes

    def get_item_attributes(self, item):
        attributes = []
        try:
            notes = item.ann_notes
        except BaseException:
            notes = []
        for note in notes:
            type = note.ann_note_type
            pairs = self.llr_fields.get(type)
            if pairs is None:
                continue
            for kind, attribute in pairs:
                value = self.get_note_value(note, attribute)
                if not value:
                    # some ALM tools raise exceptions with empty values
                    value = self.llr_export.empty
                attributes.append({'name': kind, 'value': value})

        return attributes

    @abstractmethod
    def get_note_value(self, note, attribute):
        raise NotImplementedError('Abstract method call: get_note_value')


class ScadeLLRS(AnnotatedLLRS):
    def __init__(self, llr_export: LLRExport, root):
        return super().__init__(llr_export, 'suite', root, root.ann_note_types)

    def get_model_name(self, model):
        return model.name

    def get_model_oid(self, model):
        return model.name

    def get_item_name(self, item):
        try:
            return item.name
        except BaseException:
            pass
        # return path without named owner's prefix
        owner = item.owner
        name = None
        # top most owner must have a name
        while name is None:
            try:
                name = owner.name
            except BaseException:
                owner = owner.owner
        owner_path = owner.get_full_path()
        item_path = item.get_full_path()
        name = item_path.replace(owner_path, '', 1).strip(':')
        return name

    def get_item_pathname(self, item):
        return item.get_full_path()

    def get_item_oid(self, item):
        return item.get_oid()

    def get_note_value(self, note, attribute):
        value = note.get_ann_att_value_by_name(attribute)
        text = value.to_string()
        return text

    def get_item_image(self, item):
        if not isinstance(item, suite.NetDiagram) and not isinstance(item, suite.EquationSet):
            return None
        path = Path(self.llr_export.project.pathname).parent / 'img'
        if not os.access(path.as_posix(), os.F_OK):
            os.mkdir(path.as_posix())
        path = (path / (item.name + '.png')).as_posix()
        scade.print(item, path, 'png')
        return path


class QteLLRS(StdLLRS):
    def __init__(self, llr_export: LLRExport, root):
        return super().__init__(llr_export, 'test', root)

    def get_model_name(self, model):
        return Path(self.llr_export.project.pathname).stem

    def get_model_oid(self, model):
        return Path(self.llr_export.project.pathname).name

    def get_item_name(self, item):
        if isinstance(item, test.Scenario):
            return Path(item.pathname).name
        return item.name

    def get_item_pathname(self, item):
        if isinstance(item, test.Scenario):
            return Path(item.pathname).as_posix()
        return self.get_item_name(item)

    def get_item_oid(self, item):
        return item.oid

    def get_item_attributes(self, item):
        return []


class SystemLLRS(AnnotatedLLRS):
    def __init__(self, llr_export: LLRExport, root):
        # dict oid -> FileRef
        self.ids = {}
        # dict FileRef -> prefix
        self.prefixes = {}
        self.cache_ids(llr_export.project)
        return super().__init__(
            llr_export, 'architect', root, root.annotations.schema.ann_note_types
        )

    def get_model_name(self, model):
        return model.name

    def get_model_oid(self, model):
        return self.get_item_oid(model)

    def get_item_name(self, item):
        return item.name

    def get_item_pathname(self, item):
        try:
            return item.qualified_name
        except BaseException:
            # diagrams, tables, etc...
            # TODO: what shall be the pathname?
            return item.name

    def get_item_oid(self, item):
        try:
            # recent version of SCADE?
            oid = scade.model.architect.get_oid(item)
        except BaseException:
            oid = None

        if oid is None:
            try:
                oid = item.oid
            except BaseException:
                # TODO: what shall be the oid?
                return item.name

        file = self.ids[oid]
        if file is None:
            traceln(oid + ': undefined in the current project')
            return oid
        prefix = self.prefixes[file].replace(' ', '%20')
        return 'platform:/resource/' + prefix + '#' + oid

    def get_note_value(self, note, attribute):
        value = _scade_api.call(note, 'getAnnAttValueByName', attribute)
        text = _scade_api.call(value, 'toString')
        return text

    def filter_file_name(self, name: str) -> str:
        if name.isidentifier():
            return name
        filter = ''
        for c in name:
            filter += '_' if not c.isalnum() and c != '_' else c
        return filter

    def get_item_image(self, item):
        if not isinstance(item, scade.model.architect.Diagram):
            return None
        # R2019 R2a bug: cannot generate the diagram in a subdirectory
        #                --> generate in temp then copy the file
        temp = Path(os.environ['TEMP']) / (self.filter_file_name(item.name) + '.png')
        path = Path(self.llr_export.project.pathname).parent / 'llr_img'
        if os.path.basename(sys.executable).lower() != 'stdtcl.exe':
            # R2019 R2a: crash, do not print the item
            return path.as_posix()
        scade.print(item, str(temp), 'png')
        if not os.access(path.as_posix(), os.F_OK):
            os.mkdir(path.as_posix())
        path = path / (item.name + '.png')
        copyfile(str(temp), str(path))
        return path.as_posix()

    def cache_ids(self, project):
        files = project.file_refs
        re = compile(r'.*\s+xmi:id="([^"]*)"')
        for file in files:
            # 'grep' all oids
            for line in open(file.pathname, 'r', encoding='utf-8'):
                match = re.match(line)
                if match:
                    oid = match.groups()[0]
                    if oid in self.ids:
                        traceln(oid + ': Duplicate id')
                    else:
                        self.ids[oid] = file
            # get file prefix
            prefix = Path(file.pathname).name
            folder = file.folder
            while folder is not None:
                prefix = folder.name + '/' + prefix
                folder = folder.folder
            prefix = Path(project.pathname).stem + '/' + prefix
            self.prefixes[file] = prefix


# -----------------------------------------------------------------------------
# SCADE Display API has a different design: introduce methods so that we can
# reuse the schema based engine developed for the other APIs.
# -----------------------------------------------------------------------------


class DisplayApp:
    def __init__(self, project):
        self.name = Path(project.pathname).stem
        self.qualified_name = ''
        self.files = []
        self.owner = None
        for file in project.file_refs:
            path = Path(file.pathname)
            pathname = path.as_posix()
            if path.suffixes[-1].lower() == '.sgfx':
                file = sdy.load_sgfx(pathname)
            elif path.suffixes[-1].lower() == '.ogfx':
                file = sdy.load_ogfx(pathname)
            else:
                continue
            file.pathname = pathname
            file.name = path.name
            self.files.append(file)
            for file in self.files:
                self.cache_properties(file, self, file)

    def cache_properties(self, file, owner, item, link=''):
        item.owner = owner
        item.file = file
        item.qualified_name = (
            item.name
            if owner.qualified_name == ''
            else owner.qualified_name + '/' + link + item.name
        )
        if isinstance(item, sdy.Specification):
            item.qualified_name = ''
            for layer in item.layers:
                self.cache_properties(file, item, layer)
        elif isinstance(item, sdy.AContainer):
            for child in item.children:
                self.cache_properties(file, item, child)
        elif isinstance(item, sdy.ReferenceObject):
            item.qualified_name = ''
            self.cache_properties(file, item, item.children)
        if (
            isinstance(item, sdy.Layer)
            or isinstance(item, sdy.ReferenceObject)
            and item.declaration is not None
        ):
            declaration = item.declaration
            for role in ['input', 'output', 'constant', 'local', 'local_constant', 'probe']:
                link = role + '/'
                for child in declaration.__dict__[role]:
                    self.cache_properties(file, item, child, link)


class DisplayLLRS(LLRS):
    def __init__(self, llr_export: LLRExport):
        self.app = DisplayApp(llr_export.project)
        super().__init__(llr_export, 'display', self.app)

        self.img_dir = Path(llr_export.project.pathname).parent / 'img'
        self.img_dir.mkdir(exist_ok=True)
        # cache of specifications for which the images have been generated
        self.generated_specs = set()
        # scade display exe
        self.sdyexe = get_scade_home() / 'SCADE Display' / 'bin' / 'ScadeDisplayConsole.exe'

    def get_model_name(self, model):
        return model.name

    def get_model_oid(self, model):
        return model.name

    def get_item_name(self, item):
        return item.name

    def get_item_pathname(self, item):
        return item.qualified_name

    def get_item_class(self, item):
        return item.__class__.__name__

    def get_item_links(self, item, role, sort):
        items = item.__dict__[role]
        if items is None:
            return []
        if not isinstance(items, list):
            items = [items]
        if sort:
            items = items.copy()
            items.sort(key=lambda elem: self.get_item_name(elem).lower())
        return items

    def get_item_oid(self, item):
        # prefix = self.prefixes[item.file.pathname].replace(' ', '%20')
        if isinstance(item, sdy.Specification):
            return item.name
        else:
            try:
                # prefix = Path(item.file.pathname).name
                # return prefix + ':' + item.oid.oid
                return item.oid.oid
            except BaseException:
                return ''

    def get_item_attribute(self, item, name):
        value = getattr(item, name, '')
        return value

    def get_item_attributes(self, item):
        return []

    def get_item_image(self, item):
        # only containers can have images
        if not isinstance(item, sdy.AContainer):
            return None
        # make sure the images are generated
        self.export_images(item.file)
        path = Path(self.img_dir) / (self.get_item_oid(item) + '.bmp')
        return path.as_posix() if path.exists() else None

    def export_images(self, spec: sdy.Specification):
        if spec in self.generated_specs:
            # already generated
            return
        # update the cache, whether the generation succeeds or not
        self.generated_specs.add(spec)
        # call scadedisplayconsole
        cmd = [
            str(self.sdyexe),
            'batch',
            'exportOidSnapshots',
            self.llr_export.project.pathname,
            '-source',
            # spec.pathname,
            Path(spec.pathname).name,
            '-outdir',
            str(self.img_dir),
        ]
        try:
            traceln(' '.join(cmd))
            out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
            out = out.decode('utf-8')
            traceln(out)
        except subprocess.CalledProcessError as e:
            out = e.output.decode('utf-8')
            code = e.returncode
            traceln('exec error {0}: {1}'.format(code, out))


# -----------------------------------------------------------------------------
# exceptions
# -----------------------------------------------------------------------------


class PathError(BaseException):
    def __init__(self, path, message, **kwargs):
        super().__init__(**kwargs)
        self.path = path
        self.message = message

    def __str__(self):
        return '{0}: {1}'.format(self.path, self.message)


# -----------------------------------------------------------------------------
# interface for custom connectors
# -----------------------------------------------------------------------------


def get_export_class(project: std.Project):
    # backward compatibility
    export_class = LLRExport(project)
    return export_class if export_class.valid else None


# -----------------------------------------------------------------------------
# interface for almgw
# -----------------------------------------------------------------------------


def main(file, *cmd_line, version=LLRS.V194):
    project = std.get_roots()[0]
    project_path = Path(project.pathname)

    parser = ArgumentParser()
    parser.add_argument(
        '-s', '--schema', metavar='<schema>', help='json export schema', required=True
    )
    parser.add_argument('-i', '--images', action='store_true', help='export images', required=False)
    parser.add_argument(
        '-e', '--empty', metavar='<empty value>', help='placeholder for empty values', default=''
    )
    # for now, applies only to V194
    parser.add_argument('-v', '--version', choices=['V194'], help='version', required=False)

    try:
        args = parser.parse_args(cmd_line)
    except BaseException as e:
        print(e)
        return
    if args.version == 'V194':
        version = LLRS.V194
    # make the path relative to the project , when not absolute
    schema = project_path.parent.joinpath(args.schema)

    cls = get_export_class(project)
    if cls:
        cls.read_schema(schema)
        try:
            d = cls.dump_model(diagrams=args.images, version=version, empty=args.empty)
            cls.write(d, Path(file))
        except PathError as e:
            print(str(e))
    else:
        print('%s: This kind of project is not supported' % project.pathname)


# -----------------------------------------------------------------------------
# unit test
# -----------------------------------------------------------------------------

if __name__ == '__main__':  # pragma: no cover
    # usage python.exe script <project> <file> <schema> <option>*
    declare_project(sys.argv[1])
    import scade.model.architect as system

    main(sys.argv[2], '-s', *sys.argv[3:])
    print('done')

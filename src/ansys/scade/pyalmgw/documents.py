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


from pathlib import Path
from typing import Any, Dict, Generator, List, Optional

from lxml import etree


class ReqObject:
    """
    Top level class for Requirements Document.

    Defines the interface for XML serialization and parsing.
    """

    scade_req_ns = 'http://www.esterel-technologies.com/scade/lifecycle/almgateway/scade_req/1'
    ns = {'': scade_req_ns}

    def __init__(self, owner: Optional['ReqObject']):
        self.owner = owner
        # serialization
        self.xml_tag = ''

    # add the element to the dom
    def serialize(self, parent=None) -> Any:
        # attributes
        if parent is None:
            elem = etree.Element(self.xml_tag, self.attributes, {}, xmlns=self.scade_req_ns)
        else:
            elem = etree.SubElement(parent, self.xml_tag, self.attributes, None)
        # hierarchy
        for tag, collections in self.children.items():
            # {{ 2024R2 and prior releases hang if some empty tags are missing
            force = (
                tag == 'traceabilityLinks'
                or tag == 'documents'
                or (tag == 'children' and isinstance(self, ReqDocument))
            )
            # }}
            if force or (collections and any((_ for _ in collections))):
                collection = etree.SubElement(elem, tag, {}, None)
                for children in collections:
                    for child in children:
                        child.serialize(collection)
        return elem

    def parse(self, elem: Any):
        # assert elem.tag == self.xml_tag
        pass

    @property
    def attributes(self) -> Dict[str, str]:
        return {}

    @property
    def children(self) -> Dict[str, List[List['Element']]]:
        return {}


class Element(ReqObject):
    def __init__(self, owner: Optional['Element'], identifier: str = '', text: str = ''):
        super().__init__(owner)
        self.identifier = identifier
        self.text = text

    def parse(self, elem: Any):
        super().parse(elem)
        self.identifier = elem.get('identifier')
        self.text = elem.get('text')

    @property
    def attributes(self) -> Dict[str, str]:
        attributes_ = super().attributes
        attributes_.update({'identifier': self.identifier, 'text': self.text})
        return attributes_


class TraceabilityLink(ReqObject):
    def __init__(
        self,
        owner: 'ReqProject',
        requirement: Optional['Requirement'] = None,
        source: str = '',
        target: str = '',
    ):
        super().__init__(owner)
        self.source = source
        self.target = target
        self.requirement = requirement
        self.xml_tag = 'TraceabilityLink'
        owner.traceability_links.append(self)

    def parse(self, elem: Any):
        super().parse(elem)
        self.source = elem.get('source')
        self.target = elem.get('target')
        self.requirement = None

    @property
    def attributes(self) -> Dict[str, str]:
        attributes_ = super().attributes
        target = self.requirement.id if self.requirement else self.target
        attributes_.update(
            {'type': 'Covering:trace', 'local': 'true', 'source': self.source, 'target': target}
        )
        return attributes_


class Container(Element):
    """
    Abstraction for Document, Section and Requirement.

    Container of hierarchical elements.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sections: List['Section'] = []
        self.requirements: List['Requirement'] = []

    @property
    def children(self) -> Dict[str, List[List[Element]]]:
        children_ = super().children
        children_.setdefault('children', []).extend([self.sections, self.requirements])
        return children_

    def iter_requirements(self) -> Generator['Requirement', Any, Any]:
        for requirement in self.requirements:
            yield requirement
            yield from requirement.iter_requirements()
        for section in self.sections:
            yield from section.iter_requirements()

    def is_empty(self) -> bool:
        return not self.requirements and all([_.is_empty() for _ in self.sections])

    def parse(self, tree: Any):
        super().parse(tree)
        children = tree.find('children', self.ns)
        if children is not None:
            for elem in children.findall('Section', self.ns):
                section = Section(self)
                section.parse(elem)
            for elem in children.findall('Requirement', self.ns):
                requirement = Requirement(self)
                requirement.parse(elem)


class HierarchyElement(Container):
    """Abstraction for Section and Requirement."""

    def __init__(self, owner, identifier: str = '', text: str = '', description: str = ''):
        super().__init__(owner, identifier, text)
        self.description = description

    @property
    def attributes(self) -> Dict[str, str]:
        attributes_ = super().attributes
        attributes_.update({'description': self.description})
        return attributes_

    def parse(self, tree: Any):
        super().parse(tree)
        self.description = tree.get('description')


class Requirement(HierarchyElement):
    # anonymous_req_count = 0

    def __init__(self, owner: Container, id: str = '', *args, **kwargs):
        super().__init__(owner, id, *args, **kwargs)
        self.xml_tag = 'Requirement'
        owner.requirements.append(self)

    @property
    def id(self) -> str:
        # semantic of base classs' identifier
        return self.identifier

    @id.setter
    def id(self, id: str):
        # semantic of base classs' identifier
        self.identifier = id

    # @classmethod
    # def valid_id(cls, id: str) -> str:
    #     if id is None or id == '':
    #         Requirement.anonymous_req_count += 1
    #         id = '<Missing Requirement ID>_{0}'.format(Requirement.anonymous_req_count)
    #     return id

    def parse(self, tree: Any):
        super().parse(tree)
        # self.xxx = tree.get('xxx')


class Section(HierarchyElement):
    """
    Level of the a document hierarchy.

    Persistence:

    * ``number`` maps to ``identifier``. For example ``1``, ``2.3.4``...
    * ``title`` maps to ``text``. For example ``1``, ``2.3.4``...
    """

    def __init__(self, owner: Container, number: str = '', title: str = '', description: str = ''):
        super().__init__(owner, identifier=number, text=title, description=description)
        self.xml_tag = 'Section'
        owner.sections.append(self)

    @property
    def number(self) -> str:
        # semantic of base classs' identifier
        return self.identifier

    @number.setter
    def number(self, number: str):
        # semantic of base classs' identifier
        self.identifier = number

    @property
    def title(self) -> str:
        # semantic of base classs' text
        return self.text

    @title.setter
    def title(self, title: str):
        # semantic of base classs' text
        self.text = title

    @property
    def level(self) -> int:
        """Number of owners."""
        return (self.owner.level + 1) if type(self.owner) is Section else 1

    @property
    def depth(self) -> int:
        return 1 + max([_.depth for _ in self.sections], default=0)


class ReqDocument(Container):
    r"""
    Persistence.

    * ``file`` maps to ``identifier``.

      For example ``C:\Program Files\ANSYS Inc\examples\CruiseControl\CruiseControl.docx``...
    * ``file.name`` maps to ``text``.

      For example ``CruiseControl.docx``...
    """

    def __init__(self, owner: 'ReqProject', file: str = '', name: str = ''):
        name = name if name or not file else Path(file).name
        super().__init__(owner, identifier=file, text=name)
        self.xml_tag = 'Document'
        owner.documents.append(self)

    @property
    def path(self) -> Path:
        return Path(self.identifier)

    @path.setter
    def path(self, path: Path):
        self.identifier = str(path)


class ReqProject(Element):
    """Provides an implementation of a Requirement File."""

    def __init__(self, path: Path, *args, **kwargs) -> None:
        # root of the hierarchy: no owner
        super().__init__(None, *args, **kwargs)
        self.path = path
        self.documents: List[ReqDocument] = []
        self.traceability_links: List[TraceabilityLink] = []
        self.xml_tag = 'ReqProject'

    def bind(self) -> List[TraceabilityLink]:
        """Bind the traceability links."""
        cache = {_.id: _ for doc in self.documents for _ in doc.iter_requirements()}
        unresolved: List[TraceabilityLink] = []
        for link in self.traceability_links:
            link.requirement = cache.get(link.target)
            if not link.requirement:
                unresolved.append(link)
        return unresolved

    @property
    def children(self) -> Dict[str, List[List[Element]]]:
        children_ = super().children
        children_.setdefault('traceabilityLinks', []).append(self.traceability_links)
        children_.setdefault('documents', []).append(self.documents)
        return children_

    def parse(self, root: Any):
        super().parse(root)
        documents = root.find('documents', self.ns)
        if documents is not None:
            for elem in documents.findall('Document', self.ns):
                document = ReqDocument(self)
                document.parse(elem)
        links = root.find('traceabilityLinks', self.ns)
        if links is not None:
            for elem in links.findall('TraceabilityLink', self.ns):
                link = TraceabilityLink(self)
                link.parse(elem)

    def write(self, path: Optional[Path] = None):
        if path:
            # save as...
            self.path = path
        root = self.serialize()

        # requirements file
        tree = etree.ElementTree(element=root)
        tree.write(self.path, pretty_print=True, encoding='utf-8')

    def read(self):
        tree = etree.parse(str(self.path), etree.XMLParser())
        self.parse(tree.getroot())

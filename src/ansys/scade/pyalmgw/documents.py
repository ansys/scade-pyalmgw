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
Provides means to create a Requirements Document for ALM Gateway.

The classes defined by the module correspond to the XML schema
of a Requirements Document.
"""

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

    def serialize(self, parent=None) -> Any:
        """
        Add the element to the XML DOM.

        Parameters
        ----------
        parent : Any
            Parent element or None if the element to create is the root element.

        Returns
        -------
        Any
            Corresponding XML element.
        """
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
        """
        Parse the current object from an XML element.

        Parameters
        ----------
        elem : Any
            XML element to parse.
        """
        # assert elem.tag == self.xml_tag
        pass

    @property
    def attributes(self) -> Dict[str, str]:
        """Return the attributes to be serialized as a dictionary."""
        return {}

    @property
    def children(self) -> Dict[str, List[List['ReqObject']]]:
        """
        Return the contained elements to be serialized as a dictionary.

        The entries are indexed by their tag, and contain the lists of child elements.
        """
        return {}


class Element(ReqObject):
    """Base class for ``ReqProject`` and ``Container`` classes."""

    def __init__(self, owner: Optional['Element'], identifier: str = '', text: str = ''):
        super().__init__(owner)
        self.identifier = identifier
        self.text = text

    def parse(self, elem: Any):
        """Parse the current object from an XML element."""
        super().parse(elem)
        self.identifier = elem.get('identifier')
        self.text = elem.get('text')

    @property
    def attributes(self) -> Dict[str, str]:
        """Return the attributes to be serialized as a dictionary."""
        attributes_ = super().attributes
        attributes_.update({'identifier': self.identifier, 'text': self.text})
        return attributes_


class TraceabilityLink(ReqObject):
    """Implements the ``TraceabilityLinkEntity`` complex type."""

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
        """Parse the current object from an XML element."""
        super().parse(elem)
        self.source = elem.get('source')
        self.target = elem.get('target')
        self.requirement = None

    @property
    def attributes(self) -> Dict[str, str]:
        """Return the attributes to be serialized as a dictionary."""
        attributes_ = super().attributes
        target = self.requirement.id if self.requirement else self.target
        attributes_.update(
            {'type': 'Covering:trace', 'local': 'true', 'source': self.source, 'target': target}
        )
        return attributes_


class Container(Element):
    """
    Base class for ``ReqDocument``, ``Section``, and ``Requirement`` classes.

    Container of hierarchical elements.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sections: List['Section'] = []
        self.requirements: List['Requirement'] = []

    @property
    def children(self) -> Dict[str, List[List[ReqObject]]]:
        """Return the contained elements to be serialized as a dictionary."""
        children_ = super().children
        children_.setdefault('children', []).extend([self.sections, self.requirements])
        return children_

    def iter_requirements(self) -> Generator['Requirement', Any, Any]:
        """Iterate through the contained requirements."""
        for requirement in self.requirements:
            yield requirement
            yield from requirement.iter_requirements()
        for section in self.sections:
            yield from section.iter_requirements()

    def is_empty(self) -> bool:
        """Return whether a container does not contain requirements."""
        return not self.requirements and all([_.is_empty() for _ in self.sections])

    def parse(self, tree: Any):
        """Parse the current object from an XML element."""
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
    """Base class for ``Section`` and ``Requirement`` classes."""

    def __init__(self, owner, identifier: str = '', text: str = '', description: str = ''):
        super().__init__(owner, identifier, text)
        self.description = description

    @property
    def attributes(self) -> Dict[str, str]:
        """Return the attributes to be serialized as a dictionary."""
        attributes_ = super().attributes
        attributes_.update({'description': self.description})
        return attributes_

    def parse(self, tree: Any):
        """Parse the current object from an XML element."""
        super().parse(tree)
        self.description = tree.get('description')


class Requirement(HierarchyElement):
    """Implements the ``Requirement`` complex type."""

    def __init__(self, owner: Container, id: str = '', *args, **kwargs):
        super().__init__(owner, id, *args, **kwargs)
        self.xml_tag = 'Requirement'
        owner.requirements.append(self)

    @property
    def id(self) -> str:
        """Return the ID of a requirement."""
        # semantic of base classs' identifier
        return self.identifier

    @id.setter
    def id(self, id: str):
        """Set the ID of a requirement."""
        # semantic of base classs' identifier
        self.identifier = id


class Section(HierarchyElement):
    """Implements the ``Section`` complex type.

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
        """Return the section number."""
        # semantic of base classs' identifier
        return self.identifier

    @number.setter
    def number(self, number: str):
        """Set the section number."""
        # semantic of base classs' identifier
        self.identifier = number

    @property
    def title(self) -> str:
        """Return the section title."""
        # semantic of base classs' text
        return self.text

    @title.setter
    def title(self, title: str):
        """Set the section title."""
        # semantic of base classs' text
        self.text = title

    @property
    def level(self) -> int:
        """Return the level of a section, defined as its number of owners."""
        return (self.owner.level + 1) if isinstance(self.owner, Section) else 1

    @property
    def depth(self) -> int:
        """Return the maximum depth of a section."""
        return 1 + max([_.depth for _ in self.sections], default=0)


class ReqDocument(Container):
    r"""
    Implements the ``Document`` complex type.

    Persistence.

    * ``file`` maps to ``identifier``.

      For example ``C:\Program Files\ANSYS Inc\examples\CruiseControl\CruiseControl.docx``.
    * ``file.name`` maps to ``text``.

      For example ``CruiseControl.docx``.
    """

    def __init__(self, owner: 'ReqProject', file: str = '', name: str = ''):
        name = name if name or not file else Path(file).name
        super().__init__(owner, identifier=file, text=name)
        self.xml_tag = 'Document'
        owner.documents.append(self)

    @property
    def path(self) -> Path:
        """Return the path of the document."""
        # semantic of base class' identifier
        assert isinstance(self.owner, ReqProject)
        return (
            (self.owner.path.parent / self.identifier) if self.owner.path else Path(self.identifier)
        )

    @path.setter
    def path(self, path: Path):
        """Set the path of the document."""
        # semantic of base class' identifier
        assert isinstance(self.owner, ReqProject)
        if self.owner.path:
            try:
                path = path.relative_to(self.owner.path.parent)
            except ValueError:
                pass
        self.identifier = path.as_posix()

    @property
    def depth(self) -> int:
        """Return the maximum depth of a section."""
        return 1 + max([_.depth for _ in self.sections], default=0)


class ReqProject(Element):
    """Provides an implementation of a Requirement File."""

    def __init__(self, path: Optional[Path] = None, **kwargs) -> None:
        # root of the hierarchy: no owner
        super().__init__(None, **kwargs)
        self.path = path
        self.documents: List[ReqDocument] = []
        self.traceability_links: List[TraceabilityLink] = []
        self.xml_tag = 'ReqProject'

    def bind(self) -> List[TraceabilityLink]:
        """
        Bind the traceability links.

        Returns
        -------
        List[TraceabilityLink]
            Traceability links that can't be resolved.
        """
        cache = {_.id: _ for doc in self.documents for _ in doc.iter_requirements()}
        unresolved: List[TraceabilityLink] = []
        for link in self.traceability_links:
            link.requirement = cache.get(link.target)
            if not link.requirement:
                unresolved.append(link)
        return unresolved

    @property
    def children(self) -> Dict[str, List[List[ReqObject]]]:
        """Return the contained elements to be serialized as a dictionary."""
        children_ = super().children
        children_.setdefault('traceabilityLinks', []).append(self.traceability_links)
        children_.setdefault('documents', []).append(self.documents)
        return children_

    def parse(self, root: Any):
        """
        Build the project structure from a Requirements Document XML file.

        Parameters
        ----------
        root : Any
            Root element of the XML DOM.
        """
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
        """
        Serialize the project to a Requirements Document XMl file.

        Parameters
        ----------
        path : Path
            Path of the output file. Whene none, the file is saved to
            current path of the project.
        """
        if path:
            # save as...
            self.path = path
        root = self.serialize()

        # requirements file
        tree = etree.ElementTree(element=root)
        tree.write(self.path, pretty_print=True, encoding='utf-8')

    def read(self):
        """Build the project structure from a Requirements Document XMl file."""
        tree = etree.parse(str(self.path), etree.XMLParser())
        self.parse(tree.getroot())

    @property
    def depth(self) -> int:
        """Return the maximum depth of a section."""
        return 1 + max([_.depth for _ in self.documents], default=0)

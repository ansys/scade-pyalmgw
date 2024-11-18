Traceable Elements Export Schema
================================

Purpose
-------
This customizable export schema, detailed below, defines the hierarchy of the document and the model items to be considered as traceable elements.
It is used to produce surrogate models for ALM tools.

The schema is a list of descriptions for all classes of the considered meta-model: ``suite``, ``testenv``, ``display``, etc.

**Important notice: The term ``LLR`` used in this document designates a model element to be exported to an external ALM tool.
These elements are not only ``Scade`` model elements but any element from the various ANSYS SCADE tools:
``SCADE Suite``, ``SCADE Display``, ``SCADE Architect``, ``SCADE Test``.**

Class attributes
----------------

Each class description has the following attributes:

* ``parent`` (default ``null``): Name of the parent class. For example, the parent class of ``Operator`` is ``DataDef``.
* ``isllr`` (default ``false``): ``true`` when the instances of the class are considered as requirements, ``false`` otherwise.
  For example, ``isllr`` can be set to ``false`` for a package and ``true`` for a state.
* ``folder`` (default ``null``): Name of the section to be created for each instance of the class, empty otherwise.
  When a section is created, its name is ``<section> <instance name>`` or ``<instance name>`` if ``<section>`` is an empty string.
  This is used to manage the hierarchy of the document and avoid having LLRs with child LLRs.

**Example 1:**

.. code-block:: json

    {
        "class": "Package",
        "folder": "Package",
        "isllr": false
    }

Each instance of ``Package`` leads to a new section in the document called ``Package <package name>``.
The instance itself is not a LLR.

**Example 2:**

.. code-block:: json

    {
        "class": "Operator",
        "parent": "DataDef",
        "folder": "Operator",
        "isllr": true
    }

The class ``Operator`` inherits from ``DataDef``. Each instance of ``Operator`` introduces a
``Operator <operator name>`` section, that contains a LLR for the operator and additional items if any,
like interface, diagrams, etc. If ``folder`` were left empty, the additional items would be children of the LLR itself,
leading to potential awkward title numbering when exporting to DOORS for example.

**Example 3:**

.. code-block:: json

    {
        "class": "MainTransition",
        "parent": "Transition",
        "isllr": true
    }

Each transition is a LLR but does not introduce a section. This is particularly useful for leaf items.

**Notes**:

* The classes not mentioned in the export schema have the implicit following definition:

  .. code-block:: json

      { "class": "<class>", "isllr": true }

* The fields ``isllr`` and ``folder`` are ignored for abstract classes.
* Refer to the *Composition* and *Inheritance* class diagrams of the from the documentation
  of the meta-models to customize the export schema:

  *Common Help Resources/SCADE Products API Resources/SCADE API Reference Cards* sections.

Class properties
----------------

Each class can have implicit properties through the annotation system, cf. the dedicated section of this document.
It is also possible to define new attributes by querying the model. This tool only accepts scalar values.
The properties of a class are described in the list ``properties``. Each property element has the following attributes:

* ``name``: Name of the property to be created. It is possible to declare associations by adding a prefix to the name:

  * ``#name``: The value is the oid of the entity accessed by the path or empty if the entity is optional.
  * ``@name``: The value is the pathname of the entity accessed by the path or empty if the entity is optional.

* ``path``: Path of the attribute in the model. It is possible to use roles thanks to a dotted notation provided there aren't any collections.

Prefixes allows declaring references that can be bound in the ALM tool.
For example, a DXL script can search for all properties starting by the prefix and create an internal link to ease the navigation.

**Example 1:**

.. code-block:: json

    {
        "class": "LocalVariable",
        "isllr": true,
        "properties": [
            { "name": "Type", "path": "type.name" }
        ]
    }

Each instance of ``LocalVariable`` leads to a new requirement in the document with
an additional property ``Type`` containing the name of the type.

**Example 2:**

.. code-block:: json

    {
        "class": "LocalVariable",
        "isllr": true,
        "properties": [
            { "name": "#Type", "path": "type" }
        ]
    }

Each instance of ``LocalVariable`` leads to a new requirement in the document
with an additional property ``#Type`` containing the oid of the type.

**Example 3:**

.. code-block:: json

    {
        "class": "LocalVariable",
        "isllr": true,
        "properties": [
            { "name": "@Type", "path": "type" }
        ]
    }

Each instance of ``LocalVariable`` leads to a new requirement in the document
with an additional property ``#Type`` containing the static path of the type.

Class content
-------------

The structure of a class is described in the list ``structure``. Each structure element has the following attributes:

* ``folder`` (default ``null``): Name of the folder to be created for this collection, empty otherwise. No folders are created for empty collections.
* ``flags`` (default ``[]``): List of options:

  * ``sibling``: The items of the collection shall be declared as sibling items instead of child items.
  * ``sort``: The collection shall be sorted by alphabetical order.
    When used with the option ``sibling``, there is only a partial order.

* ``content`` (default ``null``): List of associations to be traversed to gather new items

  * ``role``: Name of the role to be traversed. It is possible to chain several roles using a dotted notation.
    Each role name can be suffixed with a list of class names, enclosed by ``{}``, to filter the result.
  * ``kind`` (default ``null``): Kind of the child item, otherwise:

    * An empty string evaluates to the value of ``role``.
    * A null value evaluates to the name of the class of the child item.

  * ``filter`` (default ``null``): A Python expression where ``child`` designates the item.
    When not empty, child items for which the expression evaluates to ``False`` are filtered.
  * *DEPRECATED: ``class`` (default ``null``): Class of the child item, otherwise empty.
    When not empty, the child items that are not instances of the specified class are filtered.*

**Example 1:**

.. code-block:: json

    {
        "class": "Package",
        "folder": "Package",
        "isllr": false,
        "structure": [
            {
                "folder": "Constants",
                "flags": [ "sort" ],
                "content": [ { "role": "constant" } ]
            },
            {
                "folder": "Sensors",
                "flags": [ "sort" ],
                "content": [ { "role": "sensor" }]
            },
            {
                "folder": "Types",
                "flags": [ "sort" ],
                "content": [ { "role": "namedType", "kind": "type" } ]
            },
            {
                "folder": "Operators",
                "flags": [ "sort" ],
                "content": [ { "role": "operator" } ]
            },
            { "flags": [ "sort" ], "content": [ { "role": "package" } ] }
        ]
    }

Each instance of ``Package`` defines several folders called ``"Constants"``, ``"Sensors"``, etc.
The instances of ``NamedType`` are declared as ``"type"``.
The sub-packages are direct children of the folder ``"Package"``. All the collections are sorted alphabetically.

**Example 2:**

.. code-block:: json

    {
        "class": "Operator",
        "parent": "DataDef",
        "folder": "Operator",
        "isllr": true,
        "structure": [
            {
                "folder": "Interface",
                "content": [
                    { "role": "input" },
                    { "role": "hidden", "kind": "input" },
                    { "role": "output" }
                ]
            }
        ]
    }

Each instance of ``Operator`` defines a section called ``"Interface"`` that gathers three collections:
inputs, hidden inputs and outputs. Hidden inputs are declared as ``"input"``.

**Example 3:**

.. code-block:: json

    {
        "class": "Transition",
        "structure": [
            {
                "flags": [ "sibling" ],
                "content": [
                    { "role": "forkedTransition", "kind": "transition" }
                ]
            }
        ]
    },
    {
        "class": "MainTransition",
        "parent": "Transition",
        "isllr": true
    },
    {
        "class": "ForkedTransition",
        "parent": "Transition",
        "isllr": true
    }

Each instance of ``Transition`` is a LLR. Their children, e.g. forked transitions,
are added as sibling items, avoiding numbering issues or extra complexity.

**Example 4:**

.. code-block:: json

    {
        "class": "Folder",
        "isllr": false,
        "folder": "Folder",
        "structure": [
            {
                "flags": [ "sort" ],
                "content": [
                    { "role": "testElement{Folder}", "kind": "folder" },
                    { "role": "testElement{Record}", "kind": "record" }
                ]
            }
        ]
    }

In the SCADE Test meta-model, there is only one association to access both sub-folders and records of a folder or a procedure.
In this example, the association ``"testElement"`` is traversed twice and filtered:
The first iteration retrieves only the folders while the second one retrieves the records.

Annotations
-----------

The annotation values eligible for export, as LLR attributes, have to be annotated in the schema with the property ``LLR_PROP``.
The value of this property is the name of the attribute in the export file.

**Example:**

.. code-block:: text

    DiagramNature ::=
        SEQUENCE OF {
            SEQUENCE {
                annot_object OID,
                name STRING,
                information {
                    Nature ENUM {
                        NT_ENUM_VALUES {
                            "Architecture",
                            "LLR",
                            "Derived"
                        },
                        NT_DEFAULT_VALUE "LLR",
                        NT_FIELD_HEIGHT 1,
                        NT_FIELD_WIDTH  20,
                        LLR_PROP "Nature"
                    }
                }
            }
        }

The note type ``DiagramNature`` defines a standard enumeration attribute.
The presence of the new property ``LLR_PROP`` allows the values to be exported to an attribute named ``Nature``.

There is no limit to the amount of attributes to be exported.

Complete example
----------------

The following schema allows exporting all the equation sets and textual diagrams per operator:

.. code-block:: json

    [
        {
            "class": "Model",
            "structure": [
                {
                    "flags": [ "sort" ],
                    "content": [
                        { "role": "allOperator", "kind": "operator" }
                    ]
                }
            ]
        },
        {
            "class": "Operator",
            "parent": "DataDef",
            "folder": "Operator",
            "structure": [
                {
                    "content": [
                        { "role": "subDataDef", "kind": "" }
                    ]
                }
            ]
        },
        {
            "class": "DataDef",
            "folder": "n/a",
            "structure": [
                {
                    "content": [
                        { "role": "diagram", "kind": "" }
                    ]
                }
            ]
        },
        {
            "class": "Action",
            "parent": "DataDef",
        },
        {
            "class": "State",
            "parent": "DataDef",
        },
        {
            "class": "TextDiagram",
            "isllr": true
        },
        {
            "class": "NetDiagram",
            "structure": [
                {
                    "flags": [ "sort" ],
                    "content": [
                        { "role": "equationSet", "kind": "" }
                    ]
                }
            ]
        }
    ]

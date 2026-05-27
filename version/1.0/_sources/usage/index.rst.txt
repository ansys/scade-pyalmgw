Usage
=====

External connector
------------------

Ansys SCADE LifeCycle ALM Gateway integrates an external connector to an ALM tool using a command line interface.
The connector executable should implement 5 commands:

* ``settings``: Allow the end-user to specify options to use the connector.
  These settings are usually stored in the project file (ETP).
* ``import``: Import the requirements and traceability data from the ALM tool. The connector should deliver
  these data in an intermediate XML file.
* ``export``: Export the surrogate model and the updated traceability data to the ALM tool. The connector should
  read the traceability updates from an intermediate json file.
* ``manage``: Open the ALM tool user interface.
* ``locate``: Open the ALM tool user interface and display the specified requirement.

.. toctree::
    :maxdepth: 1

    implementation
    registration

You may refer to the following examples:

* :mod:`Stub <ansys.scade.pyalmgw.stub>`: used for unit testing.

.. link does exist yet::

    * `MS-Office connector for Ansys SCADE LifeCycle ALM Gateway <https://github.com/ansys/scade-almgw-msoffice>`_:
    used for demonstrating Ansys SCADE LifeCycle ALM Gateway.

Customized export
-----------------

The script ``ansys/scade/pyalmgw/llrs.py`` can be used as a customization script for exporting
the surrogate model. The script is generic and is parametrized by a json configuration file, called export schema,
that describes the model elements to export as well as an optional documentation structure.

The script accepts the following parameters:

* ``-s <schema>``, ``--schema <schema>``: path to the export schema, that can be relative to the project.
* ``-i``, ``--images`` (default ``false``): whether to add graphical images, for example for diagrams, equation sets, or panels.
* ``-e``, ``--empty <value>`` (default ``''``): placeholder value for empty attribute values. This is required for some target ALM tools,
  such as DOORS, for SCADE releases up to 2025 R1.

Refer to the SCADE LifeCycle ALM Gateway user documentation for details to register an
export customization script.

.. toctree::
    :maxdepth: 1

    schema
    tutorial

Registration
============

Executable
----------

Ansys SCADE ALM Gateway requires an executable for the interface.

Create a ``main`` function as follows to instantiate you connector class,
for example in ``__init__.py``::

    def main():
        """Package entry point."""
        connector = MyConnectorClass('my_connector_id')
        code = connector.main()
        return code

And register this function as a script entry, for example in ``pyproject.toml``:

.. code-block:: toml

    [project.scripts]
    my_connector = "my_package:main"

The installation of the package with ``pip`` produces ``my_connector.exe`` in the Python environment's ``Scripts`` directory.

Registration for SCADE LifeCycle ALM Gateway 2025 R1 and above
--------------------------------------------------------------

Create a function to retrieve the name of your connector and its executable path,
for example in ``__init__.py``::

    def exe() -> tuple[str, str]:
        # path to the connector's executable
        # the connector is either in Lib/site-packages/my_package
        #                      or in site-packages/my_package (when installed with --user)
        python_dir = Path(__file__).parent.parent.parent
        if python_dir.name.lower() == 'lib':
            python_dir = python_dir.parent
        # the exe is in Scripts
        return 'My Connector', str(python_dir / 'Scripts' / 'my_connector.exe')

And add an entry point, for example in ``pyproject.toml``:

.. code-block:: toml

    [project.entry-points."ansys.almgw.connector"]
    exe = "my_package:exe"

Once installed, the package is available for any installed version of SCADE LifeCycle ALM Gateway 2025 R1 or greater.

Manual registration for SCADE LifeCycle ALM Gateway
---------------------------------------------------

This registration mode is an alternative that applies to any version of SCADE LifeCycle ALM Gateway.

Once the package is installed, create a file called ``my_connector.properties`` in
``C:\Program Files\ANSYS Inc\<version>\SCADE\SCADE LifeCycle\ALM Gateway\external``,
with the following content:

.. code-block:: text

    externalConnName=My Connector
    externalBinPath=<path to your Python installation directory>/Scripts/my_connector.exe

*Note the usage of forward slash in the path.*

For example, if you have installed the package with the option ``--user``
and want to have it available for SCADE LifeCycle ALM Gateway 2024 R2, create the file
``C:\Program Files\ANSYS Inc\v422\SCADE\SCADE LifeCycle\ALM Gateway\external\my_connector.properties``
with the following content:

.. code-block:: text

    externalConnName=My Connector
    externalBinPath=C:/Users/mylogin/AppData/Roaming/Python/Python310/Scripts/my_connector.exe

Where ``C:/Users/mylogin/AppData/Roaming`` corresponds to ``%APPDATA%``.

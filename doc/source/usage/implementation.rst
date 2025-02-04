Implementation
==============

Create a Python package with a class that derives from :class:`Connector <ansys.scade.pyalmgw.connector.Connector>`
and implement the 5 abstract methods corresponding to ALM Gateway commands.

This documentation focuses on the import and export commands.

Import
------

The connector should provide the requirements and stored traceability links as an XML intermediate file,
which format is specified in ``ansys/scade/pyalmgw/res/schema.xsd``.

The module :mod:`ansys.scade.pyalmgw.documents` provides classes to create this file.

The following piece of code demonstrates the creation of a project with one document and a few elements::

    from pathlib import Path

    import ansys.scade.pyalmgw.documents as doc

    def on_import(self, file: Path, pid: int) -> int:
        project = doc.ReqProject(file, identifier='some uri', text='collection')

        d1 = doc.ReqDocument(project, file='my document', name='document')

        s1 = doc.Section(d1, number='1', title='Main title', description='1. description')
        r1 = doc.Requirement(s1, 'REQ_1', 'first', 'first requirement')
        s2 = doc.Section(d1, number='2', title='Second section', description='2. description')
        r2 = doc.Requirement(d1, 'REQ_2', 'second', 'second requirement')
        r21 = doc.Requirement(r2, 'REQ_2.1', 'sub', 'sub-requirement')

        t1 = doc.TraceabilityLink(project, r1, source='!ed/1')
        t2 = doc.TraceabilityLink(project, r2, source='!ed/2')

        project.write()
        return 0

Export
------

The connector should integrate the traceability changes provided as an intermediate JSON file.
The format of this file is not documented yet, you can replicate the following piece of code
and add your semantic actions::

    def on_export(self, links: Path, pid: int) -> int:
        deltas = json.load(file.open())
        for delta in deltas:
            oid = delta['source']['oid']
            req = delta['target']['req_id']
            action = delta['action']
            # action is either 'ADD' or 'REMOVE'
            add = action == 'ADD'

            if add:
                # TODO: create a new traceability link
                pass
            else:
                # TODO: delete an existing traceability link
                pass

        return 1

To export the surrogate model, create a dictionary using :class:`LLRExport <ansys.scade.pyalmgw.llrs.LLRExport>`::

    def on_export(self, links: Path, pid: int) -> int:
        ...
        # apply the script to the project with a schema stored in the project's directory
        schema = path(self.project.pathname).with_name('my_schema.json')
        cls = self.get_export_class()
        cls.read_schema(schema)
        data = cls.dump_model(diagrams=True)
        # TODO: export the dictionary to the ALM tool

        return 1

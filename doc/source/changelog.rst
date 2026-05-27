.. _ref_release_notes:

Release notes
#############

This document contains the release notes for the project.

.. vale off

.. towncrier release notes start

`1.2.1 <https://github.com/ansys/scade-pyalmgw/releases/tag/v1.2.1>`_ - May 27, 2026
====================================================================================

.. tab-set::


  .. tab-item:: Fixed

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - Do not raise an exception for incorrect properties.
          - `#60 <https://github.com/ansys/scade-pyalmgw/pull/60>`_

        * - Provide a workaround for identifier/text mismatch when importing requirements documents
          - `#61 <https://github.com/ansys/scade-pyalmgw/pull/61>`_


  .. tab-item:: Dependencies

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - Bump the dependencies group with 2 updates
          - `#55 <https://github.com/ansys/scade-pyalmgw/pull/55>`_

        * - Bump build from 1.4.1 to 1.4.4 in the dependencies group
          - `#58 <https://github.com/ansys/scade-pyalmgw/pull/58>`_


  .. tab-item:: Maintenance

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - Bump actions/download-artifact from 7.0.0 to 8.0.1 in the actions group
          - `#54 <https://github.com/ansys/scade-pyalmgw/pull/54>`_

        * - Bump pypa/gh-action-pypi-publish from 1.13.0 to 1.14.0 in the actions group
          - `#57 <https://github.com/ansys/scade-pyalmgw/pull/57>`_


`1.2.0 <https://github.com/ansys/scade-pyalmgw/releases/tag/v1.2.0>`_ - March 18, 2026
======================================================================================

.. tab-set::


  .. tab-item:: Fixed

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - ci: Fix update changelog action
          - `#20 <https://github.com/ansys/scade-pyalmgw/pull/20>`_

        * - Maintenance missing or outdated check-vulnerabilities and check-actions-security ansys actions
          - `#45 <https://github.com/ansys/scade-pyalmgw/pull/45>`_

        * - Suppress useless zizmor configuration file
          - `#49 <https://github.com/ansys/scade-pyalmgw/pull/49>`_

        * - Restore license information
          - `#52 <https://github.com/ansys/scade-pyalmgw/pull/52>`_


  .. tab-item:: Dependencies

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - build(deps): Bump the dependencies group with 2 updates
          - `#25 <https://github.com/ansys/scade-pyalmgw/pull/25>`_

        * - Bump the dependencies group across 1 directory with 4 updates
          - `#47 <https://github.com/ansys/scade-pyalmgw/pull/47>`_


  .. tab-item:: Miscellaneous

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - Build(deps): bump numpydoc from 1.8.0 to 1.9.0 in the dependencies group
          - `#28 <https://github.com/ansys/scade-pyalmgw/pull/28>`_

        * - Ci: bump ansys/actions from 9 to 10 in the actions group
          - `#29 <https://github.com/ansys/scade-pyalmgw/pull/29>`_

        * - Fix: enhance robustness
          - `#30 <https://github.com/ansys/scade-pyalmgw/pull/30>`_

        * - Docs: update ``contributors.md`` with the latest contributors
          - `#31 <https://github.com/ansys/scade-pyalmgw/pull/31>`_

        * - Build(deps): bump build from 1.2.2.post1 to 1.3.0 in the dependencies group
          - `#34 <https://github.com/ansys/scade-pyalmgw/pull/34>`_

        * - Ci: bump the actions group with 2 updates
          - `#35 <https://github.com/ansys/scade-pyalmgw/pull/35>`_

        * - Chore: Update missing or outdated files
          - `#40 <https://github.com/ansys/scade-pyalmgw/pull/40>`_

        * - Ci: bump the actions group across 1 directory with 5 updates
          - `#41 <https://github.com/ansys/scade-pyalmgw/pull/41>`_

        * - Chore: Update license headers
          - `#44 <https://github.com/ansys/scade-pyalmgw/pull/44>`_


  .. tab-item:: Documentation

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - chore: update CHANGELOG for v1.1.0
          - `#16 <https://github.com/ansys/scade-pyalmgw/pull/16>`_

        * - chore: update CHANGELOG for v1.1.2
          - `#18 <https://github.com/ansys/scade-pyalmgw/pull/18>`_

        * - chore: update CHANGELOG for v1.1.3
          - `#22 <https://github.com/ansys/scade-pyalmgw/pull/22>`_

        * - chore: update CHANGELOG for v1.1.4
          - `#24 <https://github.com/ansys/scade-pyalmgw/pull/24>`_


  .. tab-item:: Maintenance

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - ci: Fix release action
          - `#19 <https://github.com/ansys/scade-pyalmgw/pull/19>`_

        * - ci: Bump ansys/actions from 8 to 9 in the actions group
          - `#26 <https://github.com/ansys/scade-pyalmgw/pull/26>`_

        * - Bump actions/download-artifact from 6.0.0 to 7.0.0 in the actions group
          - `#46 <https://github.com/ansys/scade-pyalmgw/pull/46>`_

        * - Bump Python and SCADE versions
          - `#51 <https://github.com/ansys/scade-pyalmgw/pull/51>`_


  .. tab-item:: Test

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - test: Fix typo for image directory
          - `#27 <https://github.com/ansys/scade-pyalmgw/pull/27>`_


`1.1.4 <https://github.com/ansys/scade-pyalmgw/releases/tag/v1.1.4>`_ - March 31, 2025
======================================================================================

Fixed
^^^^^

- fix: Replace illegal filename characters `#23 <https://github.com/ansys/scade-pyalmgw/pull/23>`_

`1.1.3 <https://github.com/ansys/scade-pyalmgw/releases/tag/v1.1.3>`_ - March 26, 2025
======================================================================================

Documentation
^^^^^^^^^^^^^

- chore: Enable Python 3.12 and greater `#21 <https://github.com/ansys/scade-pyalmgw/pull/21>`_

`1.1.2 <https://github.com/ansys/scade-pyalmgw/releases/tag/v1.1.2>`_ - March 12, 2025
======================================================================================

Fixed
^^^^^

- fix: limit flit version `#17 <https://github.com/ansys/scade-pyalmgw/pull/17>`_

`1.1.0 <https://github.com/ansys/scade-pyalmgw/releases/tag/v1.1.0>`_ - March 12, 2025
======================================================================================

Added
^^^^^

- feat: tech review `#12 <https://github.com/ansys/scade-pyalmgw/pull/12>`_


Fixed
^^^^^

- fix: cleanup `#14 <https://github.com/ansys/scade-pyalmgw/pull/14>`_
- fix: Correct the import of conftest in test files `#15 <https://github.com/ansys/scade-pyalmgw/pull/15>`_


Dependencies
^^^^^^^^^^^^

- build(deps): Bump the dependencies group with 3 updates `#9 <https://github.com/ansys/scade-pyalmgw/pull/9>`_
- build(deps): Bump the dependencies group with 2 updates `#13 <https://github.com/ansys/scade-pyalmgw/pull/13>`_


Documentation
^^^^^^^^^^^^^

- chore: update CHANGELOG for v1.0.0 `#6 <https://github.com/ansys/scade-pyalmgw/pull/6>`_
- docs: documentation only changes `#10 <https://github.com/ansys/scade-pyalmgw/pull/10>`_


Maintenance
^^^^^^^^^^^

- build(deps): Bump codecov/codecov-action from 4 to 5 in the actions group `#2 <https://github.com/ansys/scade-pyalmgw/pull/2>`_


Test
^^^^

- build(deps): Bump the dependencies group across 1 directory with 5 updates `#8 <https://github.com/ansys/scade-pyalmgw/pull/8>`_

`1.0.0 <https://github.com/ansys/scade-pyalmgw/releases/tag/v1.0.0>`_ - 2024-11-28
==================================================================================

Added
^^^^^

- feat: Migration to GitHub `#1 <https://github.com/ansys/scade-pyalmgw/pull/1>`_
- feat: Tune the implementation `#5 <https://github.com/ansys/scade-pyalmgw/pull/5>`_


Dependencies
^^^^^^^^^^^^

- build(deps): Bump the dependencies group with 6 updates `#3 <https://github.com/ansys/scade-pyalmgw/pull/3>`_


Maintenance
^^^^^^^^^^^

- ci: Restore doc-style action `#4 <https://github.com/ansys/scade-pyalmgw/pull/4>`_

.. vale on

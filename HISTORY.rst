#######
History
#######

.. |dob| replace:: ``dob``
.. _dob: https://github.com/hotoffthehamster/dob

.. |nark| replace:: ``nark``
.. _nark: https://github.com/hotoffthehamster/nark

.. |nark-pypi| replace:: nark
.. _nark-pypi: https://pypi.org/project/nark/

.. |config-decorator| replace:: ``config-decorator``
.. _config-decorator: https://github.com/hotoffthehamster/config-decorator

.. |hamster-lib| replace:: ``hamster-lib``
.. _hamster-lib: https://github.com/projecthamster/hamster-lib

.. |legacy-hamster| replace:: Legacy Hamster
.. _legacy-hamster: https://github.com/projecthamster/hamster

.. :changelog:

3.1.0 (2020-01-16)
==================

- Documentation improvements.

- Bugfixes and enhancements to support |dob|_ development.

- (Re)moved user settings modules to new project, |config-decorator|_.

3.0.0a35 (2019-02-24)
=====================

- Hamster Renascence: Total Metempsychosis.

  - Refactor modules and code into smaller modules and methods
    (ideally one class per module).

  - Bugfixes and features to support |dob|_ development.

3.0.0.beta.1 (2018-06-09)
=========================

- Fork from :doc:`hamster-lib <history-hamster-lib>`,
  rename, and release on PyPI as |nark-pypi|_.

- Rewrite *factoid* (Fact-encoded string) parser.

  - More regex.

  - Offload ``datetime`` parsing to ``iso8601``.

- Add database migration framework.

  - Including legacy database migration support.


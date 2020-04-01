#######
History
#######

.. |dob| replace:: ``dob``
.. _dob: https://github.com/hotoffthehamster/dob

.. |config-decorator| replace:: ``config-decorator``
.. _config-decorator: https://github.com/hotoffthehamster/config-decorator

.. |nark-pypi| replace:: nark
.. _nark-pypi: https://pypi.org/project/nark/

.. :changelog:

3.0.2 (2020-04-01)
==================

- Fix issue sometimes emitting incorrect version information.

3.0.1 (2020-03-30)
==================

- Documentation improvements.

- Developer Experience [DX] enhancements.

- Fix issue processing certain error messages.

3.0.0 (2020-01-19)
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

3.0.0a1 (2018-06-09)
====================

- Fork from :doc:`hamster-lib <history-hamster-lib>`,
  rename, and release on PyPI as |nark-pypi|_.

- Rewrite *factoid* (Fact-encoded string) parser.

  - More regex.

  - Offload ``datetime`` parsing to ``iso8601``.

- Add database migration framework.

  - Including legacy database migration support.


#######
History
#######

.. |dob| replace:: ``dob``
.. _dob: https://github.com/tallybark/dob

.. |config-decorator| replace:: ``config-decorator``
.. _config-decorator: https://github.com/hotoffthehamster/config-decorator

.. |nark-pypi| replace:: nark
.. _nark-pypi: https://pypi.org/project/nark/

.. :changelog:

3.2.3 (2020-07-02)
==================

- Change ownership to ``github.com/tallybark``.

- Bugfix: Correct problems with Tags query.

  - Cannot sort by Activity or Category on Tags query.

  - Issues ordering by and grouping by Tags.

- Tests: Improve coverage (to > 90%).

3.2.2 (2020-06-18)
==================

- Feature: Useful Reporting.

  - Extend search options to produce interesting reports.

  - Add grouping, all the ways.

    - For instance, group by Activity, Category, and Day to see
      how much time was spent on each Activity@Category each day.

  - Add multi-column sorting.

    - For instance, group by Activity, Category, and Day, and sort
      by day and usage to see results ordered by which tasks had the
      most time spent on them recently.

  - Add search on Fact description.

    - For instance, find all Facts whose description contains one
      or more search terms.

  - Add tag frequency distributions.

     - Show the number of times each tag was used in a result group.

- Feature: JSON output format.

   - Use case: To prepare data to transmit elsewhere, such as <third-
     party timesheet server>.

- Improve: Support human-friendly relative dates (like '1 day ago').

   - E.g., ``dob find --since yesterday``.

- Improve: Add since/until options to activity, category, and tag searches.

- Improve: Add max-width option to Fact.friendly_str.

  - It previously applied to just the description, but now can be applied
    to the complete friendly string.

  - Also make ANSI-aware, so that strings with colors or ornamentation
    are not truncated prematurely.

- Improve: Use 'at ...' syntax for Factoid with no end, not ' to <now>'.

   - So that the active Fact writ as a Factoid is parsable on import.

- Restrict: Raise error on search if SQLite is not the engine.

  - This conflicts with the goal (set by hamster-lib, and loftily sought
    by nark) to support any DBMS, but the necessary SQL aggregate functions
    are DBMS-specific, and SQLite is all that's been plumbed in this release.

    However, SQLite has been the only back end under test, so nark should
    probably not claim to support other DBMSes without also testing them.

    Which is to say, nark now only truly supports SQLite. (Although other
    DBMS support could be wired without too much code disruption.)

- Bugfix: Aggregate results for Facts with two or more tags is incorrect.

- Bugfix: Both ``antecedent`` and ``subsequent`` mishandle momentaneous Facts.

3.2.1 (2020-04-26)
==================

- Bugfix: Additional SQLAlchemy 1.3 support.

3.2.0 (2020-04-26)
==================

- Bugfix: Windows support, aka upgrade to SQLAlchemy 1.3.

3.1.1 (2020-04-25)
==================

- Bugfix: Config created by ``dob init`` crashes subsequent dob commands.

3.1.0 (2020-04-20)
==================

- API: De-scope function for broader usage.

- API: Rename function: oid_colorize → oid_stylize.

3.0.8 (2020-04-15)
==================

- Improve: Let caller set pedantic timedelta precision.

3.0.7 (2020-04-14)
==================

- Bugfix: Validate clock time components in range (0..23 or 0..59).

3.0.6 (2020-04-13)
==================

- API: New method to refresh "now".

3.0.5 (2020-04-09)
==================

- Bugfix: Interactive editor ``gg`` (jump to first Fact) fails.

3.0.4 (2020-04-08)
==================

- Bugfix: Update/save Fact broken.

- Docs: Clarify concepts terminology.

3.0.3 (2020-04-01)
==================

- Improve: Update get_version to accept package name.

3.0.2 (2020-04-01)
==================

- Bugfix: Sometimes emitting incorrect version information.

3.0.1 (2020-03-30)
==================

- Docs: General improvements.

- DX: General enhancements.

- Bugfix: Fix issue processing certain error messages.

3.0.0 (2020-01-19)
==================

- Docs: Some improvements.

- Bugfixes and enhancements to support |dob|_ development.

- Refactor: (Re)moved user settings modules to new project, |config-decorator|_.

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


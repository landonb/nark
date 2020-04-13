# History

[comment]: # DEV: release-ghub-pypi scrapes Markdown from the first section below for the GitHub release.

## 3.0.6 (2020-04-13)

- API: New method to refresh "now".

## 3.0.5 (2020-04-09)

- Bugfix: Interactive editor `gg` (jump to first Fact) fails.

## 3.0.4 (2020-04-08)

- Bugfix: Update/save Fact broken.

- Docs: Clarify concepts terminology.

## 3.0.3 (2020-04-01)

- Improve: Update get_version to accept package name.

## 3.0.2 (2020-04-01)

- Bugfix: Sometimes emitting incorrect version information.

## 3.0.1 (2020-03-30)

- Docs: General improvements.

- DX: General enhancements.

- Bugfix: Fix issue processing certain error messages.

## 3.0.0 (2020-01-19)

- Docs: Some improvements.

- Bugfixes and enhancements to support [dob](https://github.com/hotoffthehamster/dob) development.

- Refactor: (Re)moved user settings modules to new project, [config-decorator](https://github.com/hotoffthehamster/config-decorator).

## 3.0.0a35 (2019-02-24)

- Hamster Renascence: Total Metempsychosis.

  - Refactor modules and code into smaller modules and methods
    (ideally one class per module).

  - Bugfixes and features to support
    [dob](https://github.com/hotoffthehamster/dob)
    development.

## 3.0.0a1 (2018-06-09)

- Fork from
  [hamster-lib](https://nark.readthedocs.io/en/latest/history-hamster-lib.html),
  rename, and release on PyPI as
  [nark](https://pypi.org/project/nark).

- Rewrite *factoid* (Fact-encoded string) parser.

  - More regex.

  - Offload `datetime` parsing to `iso8601`.

- Add database migration framework.

  - Including legacy database migration support.


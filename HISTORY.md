# History

## 3.0.0 (2020-01-18)

- Documentation improvements.

- Bugfixes and enhancements to support
  [dob](https://github.com/hotoffthehamster/dob)
  development.

- (Re)moved user settings modules to new project,
  [config-decorator](https://github.com/hotoffthehamster/config-decorator)

## 3.0.0a35 (2019-02-24)

- Hamster Renascence: Total Metempsychosis.

  - Refactor modules and code into smaller modules and methods
    (ideally one class per module).

  - Bugfixes and features to support
    [dob](https://github.com/hotoffthehamster/dob)
    development.

## 3.0.0.beta.1 (2018-06-09)

- Fork from
  [hamster-lib](https://nark.readthedocs.io/en/latest/history-hamster-lib.html),
  rename, and release on PyPI as
  [nark](https://pypi.org/project/nark).

- Rewrite *factoid* (Fact-encoded string) parser.

  - More regex.

  - Offload `datetime` parsing to `iso8601`.

- Add database migration framework.

  - Including legacy database migration support.


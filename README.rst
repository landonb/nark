####
nark
####

.. image:: https://travis-ci.com/hotoffthehamster/nark.svg?branch=develop
  :target: https://travis-ci.com/hotoffthehamster/nark
  :alt: Build Status

.. image:: https://codecov.io/gh/hotoffthehamster/nark/branch/develop/graph/badge.svg
  :target: https://codecov.io/gh/hotoffthehamster/nark
  :alt: Coverage Status

.. image:: https://readthedocs.org/projects/nark/badge/?version=latest
  :target: https://nark.readthedocs.io/en/latest/
  :alt: Documentation Status

.. image:: https://img.shields.io/github/release/hotoffthehamster/nark.svg?style=flat
  :target: https://github.com/hotoffthehamster/nark/releases
  :alt: GitHub Release Status

.. image:: https://img.shields.io/pypi/v/nark.svg
  :target: https://pypi.org/project/nark/
  :alt: PyPI Release Status

.. image:: https://img.shields.io/github/license/hotoffthehamster/nark.svg?style=flat
  :target: https://github.com/hotoffthehamster/nark/blob/develop/LICENSE
  :alt: License Status

A time tracking, extreme-journaling back end for thrill-seeking interval travelers.

**NOTE:** You probably want to install the *client application*,
`dob <https://github.com/hotoffthehamster/dob>`__!
-- ``nark`` is a *back end* library.

Install with ``pip``::

    pip3 install nark

For more options, read the
`installation guide <https://nark.readthedocs.io/en/latest/installation.html>`__.

``nark`` is `Hamster <https://projecthamster.wordpress.com/>`__-compatible!

``nark`` is a completion of the tasty but green, modernized
`hamster-lib <https://github.com/projecthamster/hamster-lib>`__ rewrite.

``nark`` is simply a UX-agnostic Fact-tracking data storage library used by ``dob``
and other front end user interfaces [UX].

========
Features
========

* Compatible with all current Python releases.
* Naturally Unicode compatible -- spice up your notes!
* Fully Timezone-aware -- don't lose time when traveling!
* Migrates legacy Hamster databases.
* Excellent coverage.
* Decent documentation.
* Comfortable code base.
* Free and open source -- hack away!

See how you can
`contribute
<https://nark.readthedocs.io/en/latest/contributing.html>`__
to the project.

Simple example::

    $ python3
    >>> from nark.items import Fact
    >>> new_fact, err = Fact.create_from_factoid(
          '08:00 to 2019-02-16 10:00: act@cat: #tag1: Hello, nark!',
          time_hint='verify_both',
        )
    >>> new_fact
    # Fact(
    #   pk=None,
    #   deleted=False,
    #   split_from=None,
    #   _start='08:00',
    #   _end=datetime.datetime(2019, 2, 16, 10, 0),
    #   _description='Hello, nark!',
    #   activity=Activity(
    #     pk=None
    #     deleted=False,
    #     hidden=False,
    #     _name='act',
    #     category=Category(
    #       pk=None,
    #       deleted=False,
    #       hidden=False,
    #       _name='cat',
    #     ),
    #   ),
    #   tags=[Tag(
    #     pk=None,
    #     deleted=False,
    #     hidden=False,
    #     _name='tag1',
    #   )],
    # )

|

.. image:: https://github.com/hotoffthehamster/nark/raw/develop/docs/_static/images/information-cat.png
   :align: center
   :alt: "Information Cat"


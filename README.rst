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

.. |dob| replace:: ``dob``
.. _dob: https://github.com/hotoffthehamster/dob

.. |nark| replace:: ``nark``
.. _nark: https://github.com/hotoffthehamster/nark

.. |hamster-lib| replace:: ``hamster-lib``
.. _hamster-lib: https://github.com/projecthamster/hamster-lib

.. |pip| replace:: ``pip``
.. _pip: https://pip.pypa.io/en/stable/

Some might call it timesheet software, or dismiss it as simply time tracking,
but I call it extreme-journaling, a back end framework for thrill-seeking, time
travelling interval junkies, a/k/a *dobbers*.

**NOTE:** You probably want to install the *client application*,
`dob <https://github.com/hotoffthehamster/dob>`__!
-- Nark is a *support library*.

Install with |pip|_::

    pip3 install nark

For more options, read the
`installation guide <https://nark.readthedocs.io/en/latest/installation.html>`__.

=====
Ethos
=====

|nark|_ is inspired by
`Hamster <https://projecthamster.wordpress.com/>`__,
a beloved but aged time tracking application for
`GNOME <https://en.wikipedia.org/wiki/GNOME>`__.

|nark|_ is
`Hamster <https://github.com/projecthamster/hamster>`__-compatible.
Grab your existing Hamster database and start using |nark|_ today!

|nark|_ is a fork of the sensible but incomplete
modern |hamster-lib|_ code rewrite. Now it's done?

|nark|_ is plainly a database-agnostic *Fact* storage API.
It does one thing, (hopefully) well!

As developers, our goal with |nark|_ is naturally to provide stable,
reliable code. But we also want to provide easily hackable code. Code
that is approachable to any Python developer with a few extra minutes
and a sense of adventure. Code that is welcoming, so that a developer
who wants to incorporate this tool into their daily workflow will not
be afraid to bang on it when it breaks, or to patch a new limb on it
when then see a place for improvement. Or to just trust that it works.

========
Features
========

* Compatible with all current Python releases (3.5, 3.6, and 3.7).
* Naturally Unicode compatible -- spice up your notes!
* Fully Timezone-aware -- don't lose time traveling!
* Can migrate legacy Hamster databases (and fix integrity issues, too).
* Excellent coverage (to give you comfort knowing your Facts are safe).
* Decent documentation (though really you should learn by doing).
* Comfortable code base (focus on the feature, not on the format).
* Free and open source -- hack away!

See how you can
`contribute
<https://nark.readthedocs.io/en/latest/contributing.html>`__
to the project.

=======
Example
=======

Create a *Fact* instance from a *Factoid* string::

    $ python3
    >>> from nark.items import Fact
    >>> factoid = '08:00 to 2019-02-16 10:00: act@cat: #tag1: Hello, nark!'
    >>> fact, err = Fact.create_from_factoid(factoid, time_hint='verify_both')
    >>> fact
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

.. image:: https://raw.githubusercontent.com/hotoffthehamster/nark/develop/docs/_static/images/information-cat.png
   :target: https://nark.readthedocs.io/en/latest/authors.html#information-cat
   :align: center
   :alt: "Information Cat"


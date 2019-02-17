############
Installation
############

To install system-wide, run as superuser::

    $ pip3 install nark

To install user-local, simply run::

    $ pip3 install -U nark

To install within a ``virtualenv``, try::

    $ mkvirtualenv nark
    $ pip3 install nark

To develop on the project, link to the source files instead::

    $ deactivate
    $ rmvirtualenv nark
    $ git clone git@github.com:hotoffthehamster/nark.git
    $ cd nark
    $ mkvirtualenv -a $(pwd) --python=/usr/bin/python3.6 nark
    $ make develop

To start developing from a fresh terminal, run ``workon``::

    $ workon nark


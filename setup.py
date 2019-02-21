#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of 'nark'.
#
# 'nark' is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# 'nark' is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with 'nark'.  If not, see <http://www.gnu.org/licenses/>.

"""
Packaging instruction for setup tools.

Refs:

  https://setuptools.readthedocs.io/

  https://packaging.python.org/en/latest/distributing.html

  https://github.com/pypa/sampleproject
"""

import os
import re
# Because runtime import, else:
#   NameError: name 'time' is not defined
# F401 '...' imported but unused
import time  # noqa: F401
# Because exec(init_py) import _.
from gettext import gettext as _  # noqa: F401

try:
    from setuptools import find_packages, setup
except ImportError:
    from distutils.core import setup


requirements = [
    # "Very simple Python library for color and formatting in terminal."
    # Forked (for italic "support") to:
    #  https://github.com/hotoffthehamster/ansi-escape-room
    # Forked from:
    #  https://gitlab.com/dslackw/colored
    'ansi-escape-room',
    # Platform-specific directory magic.
    #  https://github.com/ActiveState/appdirs
    'appdirs',
    # Basic INI parser.
    #  https://pypi.org/project/configparser/
    #  https://docs.python.org/3/library/configparser.html
    'configparser >= 3.5.0b2',
    # https://github.com/scrapinghub/dateparser
    'dateparser',
    # Py2/3 support shim. (Higher-level than `six`.)
    #  https://pypi.org/project/future/
    #  https://python-future.org/
    'future',
    # Elapsed timedelta formatter, e.g., "1.25 days".
    'human-friendly_pedantic-timedelta >= 0.0.5',
    # https://github.com/collective/icalendar
    'icalendar',
    # https://bitbucket.org/micktwomey/pyiso8601
    'iso8601',
    # https://github.com/mnmelo/lazy_import
    'lazy_import',
    # Daylight saving time-aware timezone library.
    #  https://pythonhosted.org/pytz/
    'pytz',
    # For testing with dateparser,
    #   https://bitbucket.org/mrabarnett/mrab-regex
    #   https://pypi.org/project/regex/
    # FIXME/2019-02-19 18:13: Latest regex is broken.
    #   https://pypi.org/project/regex/2019.02.20/
    #   https://bitbucket.org/mrabarnett/mrab-regex/commits/
    #       5d8b8bb2b64b696cdbaa7bdc0dce4b462d311134#Lregex_3/regex.pyF400
    # Because of recent change to import line (was made self-referential):
    #      .tox/py37/lib/python3.7/site-packages/regex.py:400: in <module>
    #          import regex._regex_core as _regex_core
    #      E   ModuleNotFoundError: No module named 'regex._regex_core';
    #       'regex' is not a package
    'regex == 2019.02.18',
    # https://pythonhosted.org/six/
    'six',
    # https://www.sqlalchemy.org/
    'sqlalchemy',
    # Database gooser/versioner.
    #  https://pypi.org/project/sqlalchemy-migrate/
    #  https://sqlalchemy-migrate.readthedocs.io/en/latest/
    'sqlalchemy-migrate',
    # https://github.com/regebro/tzlocal
    'tzlocal',
]


# *** Boilerplate setuptools helper fcns.

# Source values from the top-level {package}/__init__.py,
# to avoid hardcoding herein.

# (lb): I was inspired by PPT's get_version() to write this mess.
# Thank you, PPT!

def top_level_package_file_path(package_dir):
    """Return path of {package}/__init__.py file, relative to this module."""
    path = os.path.join(
        os.path.dirname(__file__),
        package_dir,
        '__init__.py',
    )
    return path


def top_level_package_file_read(path):
    """Read the file at path, and decode as UTF-8."""
    with open(path, 'rb') as f:
        init_py = f.read().decode('utf-8')
    return init_py


def looks_like_app_code(line):
    """Return True if the line looks like `key = ...`."""
    matches = re.search("^\S+ = \S+", line)
    return matches is not None


def top_level_package_file_strip_imports(init_py):
    """Stip passed array of leading entries not identified as `key = ...` code."""
    # Expects comments, docstrings, and imports up top; ``key = val`` lines below.
    culled = []
    past_imports = False
    for line in init_py.splitlines():
        if not past_imports:
            past_imports = looks_like_app_code(line)
        if past_imports:
            culled.append(line)
    return "\n".join(culled)


def import_business_vars(package_dir):
    """Source the top-level __init__.py file, minus its import statements."""
    pckpath = top_level_package_file_path(package_dir)
    init_py = top_level_package_file_read(pckpath)
    source = top_level_package_file_strip_imports(init_py)
    exec(source)
    cfg = {key: val for (key, val) in locals().items() if key.startswith('__')}
    return cfg


# Import variables from nark/__init__.py,
# without triggering that files' imports.
cfg = import_business_vars('nark')

# *** Local file content.

long_description = open(
    os.path.join(
        os.path.dirname(__file__),
        'README.rst'
    )
).read()

# *** Package definition.

setup(
    name=cfg['__pipname__'],
    version=cfg['__version__'],
    author=cfg['__author__'],
    author_email=cfg['__author_email__'],
    url=cfg['__projurl__'],
    description=cfg['__briefly__'],
    long_description=long_description,
    long_description_content_type="text/x-rst",
    packages=find_packages(),
    install_requires=requirements,
    license='GPLv3',
    zip_safe=False,
    keywords=cfg['__keywords__'],
    classifiers=[
        # FIXME/2018-06-13: (lb): So, like, yeah, we'll get to Stable, even'ch.
        # 'Development Status :: 2 - Pre-Alpha',
        'Development Status :: 3 - Alpha',
        # 'Development Status :: 4 - Beta',
        # 'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)


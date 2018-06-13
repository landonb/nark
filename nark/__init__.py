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

"""nark provides generic time tracking functionality."""

from __future__ import absolute_import, unicode_literals

from gettext import gettext as _

# Export classes from here for other application to more easily import.
from .control import REGISTERED_BACKENDS, HamsterControl  # noqa: F401
from .items.activity import Activity  # noqa: F401
from .items.category import Category  # noqa: F401
from .items.fact import Fact  # noqa: F401
from .items.tag import Tag  # noqa:


# SYNC_UP: nark/__init__.py <=> dob/__init__.py
__author__ = 'HotOffThe Hamster'
__author_email__ = 'hotoffthehamster+nark@gmail.com'
__version__ = '3.0.0.a1'
__appname__ = 'nark'
__pipname__ = __appname__
__briefly__ = _(
    'Robot backend for personal journaling and professional time tracking software (like `dob`).'
)
__projurl__ = 'https://github.com/hotoffthehamster/nark'
__keywords__ = ' '.join([
    'journal',
    'diary',
    'timesheet',
    'timetrack',
    'jrnl',
    'rednotebook',
    'todo.txt',
    'prjct',
    'hamster',
    'fact',
])


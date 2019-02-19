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

import time
from gettext import gettext as _

__PROFILING__ = True
# DEVS: Comment this out to see load times summary.
__PROFILING__ = False
__time_0__ = time.time()


__all__ = (
    '__version__',
)


# SYNC_UP: nark/__init__.py <=> dob/__init__.py
__author__ = 'HotOffThe Hamster'
__author_email__ = 'hotoffthehamster+nark@gmail.com'
__version__ = '3.0.0a30'
__appname__ = 'nark'
__pipname__ = __appname__
__briefly__ = _(
    'Robot backend for personal journaling and professional time tracking software'
    ' (like `dob`).'
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


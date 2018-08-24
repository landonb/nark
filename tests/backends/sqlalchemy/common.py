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
Provide a central global Session-object.

This way it can be referencecd by fixtures and factories.
[Details](http://factoryboy.readthedocs.org/en/latest/orms.html#sqlalchemy)
"""

from sqlalchemy import orm

# (lb): Haha, here's what factoryboi says about this putrid global:
#   "A global (test-only?) file holds the scoped_session"
# test-only? Sure, why not. Anything goes in testland.
Session = orm.scoped_session(orm.sessionmaker())


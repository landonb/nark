# -*- coding: utf-8 -*-

# This file is part of 'hamster-lib'.
#
# 'hamster-lib' is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# 'hamster-lib' is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with 'hamster-lib'.  If not, see <http://www.gnu.org/licenses/>.

"""
Provide a central global Session-object.

This way it can be referencecd by fixtures and factories.
[Details](http://factoryboy.readthedocs.org/en/latest/orms.html#sqlalchemy)
"""

from sqlalchemy import orm

Session = orm.scoped_session(orm.sessionmaker())


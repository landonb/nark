# This file exists within 'nark':
#
#   https://github.com/hotoffthehamster/nark
#
# Copyright © 2018-2020 Landon Bouma
# Copyright © 2015-2016 Eric Goller
# All  rights  reserved.
#
# 'nark' is free software: you can redistribute it and/or modify it under the terms
# of the GNU General Public License  as  published by the Free Software Foundation,
# either version 3  of the License,  or  (at your option)  any   later    version.
#
# 'nark' is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY  or  FITNESS FOR A PARTICULAR
# PURPOSE.  See  the  GNU General Public License  for  more details.
#
# You can find the GNU General Public License reprinted in the file titled 'LICENSE',
# or visit <http://www.gnu.org/licenses/>.

"""
Provide a central global Session-object.

This way it can be referencecd by fixtures and factories.
[Details](http://factoryboy.readthedocs.org/en/latest/orms.html#sqlalchemy)
"""

from sqlalchemy import orm

# (lb): Haha, here's what factoryboi says about this global:
#   "A global (test-only?) file holds the scoped_session"
# This session is so the Alchemy item factories all deposit
# their items in the same backend.
Session = orm.scoped_session(orm.sessionmaker())

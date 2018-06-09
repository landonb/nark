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

from __future__ import unicode_literals

from future.utils import python_2_unicode_compatible
from migrate.versioning.api import db_version

from ....managers.migrate import BaseMigrationsManager


@python_2_unicode_compatible
class MigrationsManager(BaseMigrationsManager):
    def downgrade(self):
        """Downgrade the database according to its migration version."""
        raise 'FIXME!'

    def upgrade(self):
        """Upgrade the database according to its migration version."""
        raise 'FIXME!'

    def version(self):
        """Returns the migration version of the database indicated by the config."""
        url = self._get_db_url()
        return db_version(url)


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

from __future__ import absolute_import, unicode_literals
from future.utils import python_2_unicode_compatible

import os
from migrate.exceptions import DatabaseAlreadyControlledError
from migrate.exceptions import DatabaseNotControlledError
from migrate.versioning.api import db_version, downgrade, upgrade, version_control
from migrate.versioning.api import version as migrate_version

from ....managers.migrate import BaseMigrationsManager


__all__ = ['MigrationsManager']


@python_2_unicode_compatible
class MigrationsManager(BaseMigrationsManager):
    def control(self):
        """Mark a database as under version control."""
        current_ver = self.version()
        if current_ver is None:
            url = self.store.get_db_url()
            try:
                version_control(url, self.migration_repo(), version=None)
                return True
            except DatabaseAlreadyControlledError:
                return False
        elif current_ver == 0:
            return False
        else:
            return None

    def downgrade(self):
        """Downgrade the database according to its migration version."""
        current_ver = self.version()
        if current_ver is None:
            return None
        latest_ver = migrate_version(self.migration_repo())
        if not latest_ver:
            return None
        assert current_ver <= latest_ver
        if current_ver > 0:
            next_version = current_ver - 1
            url = self.store.get_db_url()
            downgrade(url, self.migration_repo(), version=next_version)
            return True
        else:
            return False

    def upgrade(self):
        """Upgrade the database according to its migration version."""
        current_ver = self.version()
        if current_ver is None:
            return None
        latest_ver = migrate_version(self.migration_repo())
        if not latest_ver:
            return None
        assert current_ver <= latest_ver
        if current_ver < latest_ver:
            next_version = current_ver + 1
            url = self.store.get_db_url()
            upgrade(url, self.migration_repo(), version=next_version)
            return True
        else:
            return False

    def version(self):
        """Returns the migration version of the database indicated by the config."""
        url = self.store.get_db_url()
        try:
            return db_version(url, self.migration_repo())
        except DatabaseNotControlledError:
            return None

    def latest_version(self):
        """Returns the latest version of the database as used by the application."""
        try:
            return int(migrate_version(self.migration_repo()).value)
        except DatabaseNotControlledError:
            return None

    # ***

    def migration_repo(self):
        # (lb): This is a little awkward. But there's not
        # another convenient way to do this, is there?
        path = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                '../../../../migrations',
            )
        )
        return path


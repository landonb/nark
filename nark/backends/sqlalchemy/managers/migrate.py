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

import os

import lazy_import
from future.utils import python_2_unicode_compatible

from ....helpers.legacy_db import upgrade_legacy_db_hamster_applet
from ....managers.migrate import BaseMigrationsManager

# Profiling: Loading `migrate` takes ~ 0.090 seconds.
migrate_exceptions = lazy_import.lazy_module('migrate.exceptions')
migrate_versioning_api = lazy_import.lazy_module('migrate.versioning.api')

__all__ = ('MigrationsManager', )


@python_2_unicode_compatible
class MigrationsManager(BaseMigrationsManager):
    def control(self, version=None):
        """Mark a database as under version control."""
        current_ver = self.version()
        if current_ver is None:
            url = self.store.get_db_url()
            try:
                migrate_versioning_api.version_control(
                    url, self.migration_repo(), version=version,
                )
                return True
            except migrate_exceptions.DatabaseAlreadyControlledError:
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
        latest_ver = migrate_versioning_api.version(self.migration_repo())
        if not latest_ver:
            return None
        assert current_ver <= latest_ver
        if current_ver > 0:
            next_version = current_ver - 1
            url = self.store.get_db_url()
            migrate_versioning_api.downgrade(
                url, self.migration_repo(), version=next_version,
            )
            return True
        else:
            return False

    def upgrade(self):
        """Upgrade the database according to its migration version."""
        current_ver = self.version()
        if current_ver is None:
            return None
        latest_ver = migrate_versioning_api.version(self.migration_repo())
        if not latest_ver:
            return None
        assert current_ver <= latest_ver
        if current_ver < latest_ver:
            next_version = current_ver + 1
            url = self.store.get_db_url()
            migrate_versioning_api.upgrade(
                url, self.migration_repo(), version=next_version,
            )
            return True
        else:
            return False

    def version(self):
        """Returns the current migration of the active database."""
        url = self.store.get_db_url()
        try:
            return migrate_versioning_api.db_version(url, self.migration_repo())
        except migrate_exceptions.DatabaseNotControlledError:
            return None

    def latest_version(self):
        """Returns the latest version defined by the application."""
        try:
            return int(migrate_versioning_api.version(self.migration_repo()).value)
        except migrate_exceptions.DatabaseNotControlledError:
            return None

    # ***

    def migration_repo(self):
        # (lb): This is a little awkward. But there's not
        # another convenient way to do this, is there?
        path = os.path.abspath(
            os.path.join(
                # Meh. We could also do dirname(nark.__file__) and use fewer ..'s.
                os.path.dirname(__file__),
                '../../../../migrations',
            )
        )
        return path

    # ***

    def legacy_upgrade_from_hamster_applet(self, db_path):
        upgrade_legacy_db_hamster_applet(db_path)

    def legacy_upgrade_from_hamster_lib(self):
        # (lb): I'm not sure how much traction hamster-lib had.
        #  So I'm not sure this function is needed.
        #  And hamster-libbers out there need a hand?
        #  You'll need to rename 3 things is all, I'm sure:
        #    Table renamed: facttags → fact_tags
        #    Cols renamed: facts.start_time/end_time → facts.start/end
        #  Please open a ticket if you really want this feature!
        raise NotImplementedError


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

from __future__ import absolute_import, unicode_literals
from future.utils import python_2_unicode_compatible

from . import BaseManager


@python_2_unicode_compatible
class BaseMigrationsManager(BaseManager):
    """Base class defining the minimal API for a MigrationsManager implementation."""

    def downgrade(self):
        """Downgrade the database according to its migration version."""
        raise NotImplementedError

    def upgrade(self):
        """Upgrade the database according to its migration version."""
        raise NotImplementedError

    def version(self):
        """Returns the migration version of the database indicated by the config."""
        raise NotImplementedError

    def latest_version(self):
        """Returns the latest version of the database as used by the application."""
        raise NotImplementedError




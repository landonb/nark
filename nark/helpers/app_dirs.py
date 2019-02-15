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

import appdirs

__all__ = (
    'NarkAppDirs',
)


class NarkAppDirs(appdirs.AppDirs):
    """Custom class that ensure appdirs exist."""

    def __init__(self, *args, **kwargs):
        """Add create flag value to instance."""
        super(NarkAppDirs, self).__init__(*args, **kwargs)
        # FIXME: (lb): I'm not super cool with this side-effect:
        #          Calling any property herein will cause its
        #          directory path to be created! Creating paths
        #          should be a deliberate action and not a side effect
        #          of just asking for a path. In any case, it currently
        #          works this way, so just rolling with the flow, for now.
        #        See Click: it has concept of lazy-creating paths, i.e.,
        #          only create path when a file therein opened for write.
        self.create = True

    @property
    def user_data_dir(self):
        """Return ``user_data_dir``."""
        directory = appdirs.user_data_dir(
            self.appname,
            self.appauthor,
            version=self.version,
            roaming=self.roaming,
        )
        if self.create:
            self._ensure_directory_exists(directory)
        return directory

    @property
    def site_data_dir(self):
        """Return ``site_data_dir``."""
        directory = appdirs.site_data_dir(
            self.appname,
            self.appauthor,
            version=self.version,
            multipath=self.multipath,
        )
        if self.create:
            self._ensure_directory_exists(directory)
        return directory

    @property
    def user_config_dir(self):
        """Return ``user_config_dir``."""
        directory = appdirs.user_config_dir(
            self.appname,
            self.appauthor,
            version=self.version,
            roaming=self.roaming,
        )
        if self.create:
            self._ensure_directory_exists(directory)
        return directory

    @property
    def site_config_dir(self):
        """Return ``site_config_dir``."""
        directory = appdirs.site_config_dir(
            self.appname,
            self.appauthor,
            version=self.version,
            multipath=self.multipath,
        )
        if self.create:
            self._ensure_directory_exists(directory)
        return directory

    @property
    def user_cache_dir(self):
        """Return ``user_cache_dir``."""
        directory = appdirs.user_cache_dir(
            self.appname, self.appauthor, version=self.version,
        )
        if self.create:
            self._ensure_directory_exists(directory)
        return directory

    @property
    def user_log_dir(self):
        """Return ``user_log_dir``."""
        directory = appdirs.user_log_dir(
            self.appname, self.appauthor, version=self.version,
        )
        if self.create:
            self._ensure_directory_exists(directory)
        return directory

    def _ensure_directory_exists(self, directory):
        """Ensure that the passed path exists."""
        if not os.path.lexists(directory):
            os.makedirs(directory)
        return directory


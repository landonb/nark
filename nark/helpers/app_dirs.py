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

import os

import appdirs

from .singleton import Singleton

__all__ = (
    'NarkAppDirs',
)


class NarkAppDirs(appdirs.AppDirs, metaclass=Singleton):
    """Application-specific AppDirs interface.

    Note: This class is a Singleton, because its data is immutable, and it
    represents global data (that's generated from the user name and
    application details) that goes unchanged throughout the application
    lifetime. *So it's appropriate and defensible to declare this class
    as a Singleton (ALIMHO, -lb).*

    (lb): One Pythonic alternate, if you're anti the Singleton pattern, is to
    do away with the class and just have this be a simple module, i.e., expose
    user_data_dir(), etc., as module-scope functions. But that's not really
    that different, and then you end up with module-scope semi-global variables,
    anyway. And the user has to explicitly import each method, rather than just
    the class. It feels more simple, readable, and maintainable to encapsulate
    the methods in a class, and to make that class a singleton; half a dozen of
    one six of the other, if you ask me.

    For a good discussion on ways to implement Singleton in Python, and whether
    or not they're a good idea, read the classic *Creating a singleton in Python*:

        https://stackoverflow.com/questions/6760685/creating-a-singleton-in-python
    """

    # Although the class is a Singleton, nark needs to access the class
    # without actually creating it -- because the client (dob) needs to
    # create it (so it can set appname properly). So here's a (hacky)
    # class member to indicate when the singleton instance is prepared.
    APP_DIRS = None

    def __init__(self, *args, **kwargs):
        """Add create flag value to instance."""
        # The AppDirs takes a number of parameters:
        #   appname=None, appauthor=None, version=None,
        #   roaming=False, multipath=False,
        # but generally you just need to specify appname.
        super(NarkAppDirs, self).__init__(*args, **kwargs)

        # This constructor only called once, because Singleton.
        assert(NarkAppDirs.APP_DIRS is None)
        # A hacky class variable so nark knows when the instance is ready.
        NarkAppDirs.APP_DIRS = self

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


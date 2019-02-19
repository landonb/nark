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

import gettext
import importlib
import sys
from collections import namedtuple

from future.utils import python_2_unicode_compatible

from .helpers import logging as logging_helpers
from .helpers.dev.profiling import timefunc

BackendRegistryEntry = namedtuple(
    'BackendRegistryEntry', ('verbose_name', 'store_class'),
)


REGISTERED_BACKENDS = {
    'sqlalchemy': BackendRegistryEntry(
        'SQLAlchemy',
        'nark.backends.sqlalchemy.SQLAlchemyStore',
    ),
}


# See: https://wiki.python.org/moin/PortingToPy3k/BilingualQuickRef#gettext
# [FIXME]
# Is this correct?
#   http://www.wefearchange.org/2012/06/the-right-way-to-internationalize-your.html
# seems to use ``sys.version_info.major > 3``
kwargs = {}
if sys.version_info.major < 3:
    kwargs['unicode'] = True
gettext.install('nark', **kwargs)


@python_2_unicode_compatible
class NarkControl(object):
    """
    All mandatory config options are set as part of the controller setup.
    Any client may overwrite those values. but we can always asume that the
    controller does have a value set.

    We will try hard to get through with at least always returning the object.
    We should be able to change only the internal service code to then
    decompose it into its required weired format.

    We were compelled to make attach CRUD-methods to our activity, category
    and fact objects. But as all of those depend on access to the store
    anyway they seem to be best be placed here as a central hub.

    Generic CRUD-actions is to be delegated to our store. The Controller itself
    provides general timetracking functions so that our clients do not have to.
    """

    def __init__(self, config):
        self.config = config
        self.lib_logger = self._get_logger()
        # Profiling: _get_store(): Observed: ~ 0.136 to 0.240 secs.
        self.store = self._get_store()
        self.sql_logger = self._sql_logger()
        self.for_your_convenience()

    def standup_store(self):
        created_fresh = self.store.standup()
        return created_fresh

    def for_your_convenience(self):
        self.migrations = self.store.migrations
        self.categories = self.store.categories
        self.activities = self.store.activities
        self.tags = self.store.tags
        self.facts = self.store.facts

    def update_config(self, config):
        """Use a new config dictionary and apply its settings."""
        self.config = config
        self.store = self._get_store()

    @timefunc
    def _get_store(self):
        """
        Setup the store used by this controller.

        This method is in charge off figuring out the store type, its
        instantiation as well as all additional configuration.
        """

        backend = REGISTERED_BACKENDS.get(self.config['store'])
        if not backend:
            raise KeyError(_("No or invalid storage specified."))
        import_path, storeclass = tuple(backend.store_class.rsplit('.', 1))
        # Profiling: importlib.import_module: ~ 0.265 secs.
        backend_module = importlib.import_module(import_path)
        cls = getattr(backend_module, storeclass)
        store = cls(self.config)
        return store

    def _get_logger(self):
        """
        Setup and configure the main logger.

        As the docs suggest we setup just a pseudo handler. Any client that
        actually wants to use logging needs to setup its required handlers
        itself.
        """

        lib_log_level = self.config['lib_log_level']
        lib_logger = logging_helpers.set_logger_level(
            'nark.log', lib_log_level,
        )
        return lib_logger

    def _sql_logger(self):
        """
        Setup and configure the SQLAlchemy database store logger.

        As the docs suggest we setup just a pseudo handler. Any client that
        actually wants to use logging needs to setup its required handlers
        itself.
        """
        return self.store.logger


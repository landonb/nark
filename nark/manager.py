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
from datetime import datetime

from future.utils import python_2_unicode_compatible

from .helpers import logging as logging_helpers
from .helpers.app_dirs import NarkAppDirs
from .managers.activity import BaseActivityManager
from .managers.category import BaseCategoryManager
from .managers.fact import BaseFactManager
from .managers.tag import BaseTagManager

__all__ = ('BaseStore', )


@python_2_unicode_compatible
class BaseStore(object):
    """
    A controller store defines the interface to interact with stored entities,
    regardless of the backend being used.
    """

    def __init__(self, config):
        self.config = config
        self.init_config()
        self.init_logger()
        self._now = None
        self.add_pytest_managers()

    def add_pytest_managers(self):
        if not os.environ.get('PYTEST_CURRENT_TEST', None):
            return
        # The following intermediate classes are solely used for testing!
        self.categories = BaseCategoryManager(self)
        self.activities = BaseActivityManager(self)
        self.tags = BaseTagManager(self)
        localize = self.config['tz_aware']
        self.facts = BaseFactManager(self, localize=localize)

    def standup(self):
        """
        Any backend specific setup code that needs to be executed before
        the data store can be used (including creating the data store).
        """
        raise NotImplementedError

    def cleanup(self):
        """
        Any backend specific teardown code that needs to be executed before
        we shut down gracefully.
        """
        raise NotImplementedError

    def init_config(self):
        self.config.setdefault('store', 'sqlalchemy')
        self.config.setdefault('db_engine', 'sqlite')
        app_dirs = NarkAppDirs('nark')
        db_path = os.path.join(
            app_dirs.user_data_dir,
            # (lb): Whatever client is using the nark library
            # will generally setup db_path specially; this is
            # just a default filename for completeness.
            'dob.sqlite',
        )
        self.config.setdefault('db_path', db_path)
        self.config.setdefault('db_host', '')
        self.config.setdefault('db_port', '')
        self.config.setdefault('db_name', '')
        self.config.setdefault('db_user', '')
        self.config.setdefault('db_password', '')
        self.config.setdefault('allow_momentaneous', False)
        self.config.setdefault('day_start', '')
        self.config.setdefault('fact_min_delta', '0')
        self.config.setdefault('lib_log_level', 'WARNING')
        self.config.setdefault('sql_log_level', 'WARNING')
        self.config.setdefault('tz_aware', False)
        self.config.setdefault('default_tzinfo', '')

    def init_logger(self):
        sql_log_level = self.config['sql_log_level']
        self.logger = logging_helpers.set_logger_level(
            'nark.store', sql_log_level,
        )

    @property
    def now(self):
        # Use the same 'now' for all items that need it. 'Now' is considered
        # the run of the whole command, and not different points within it.
        # (lb): It probably doesn't matter either way what we do, but I'd
        # like all facts that use now to reflect the same moment in time,
        # rather than being microseconds apart from one another.
        # (lb): Also, we use @property to convey to the caller that this
        # is not a function; i.e., the value is static, not re-calculated.
        if self._now is None:
            self._now = self.now_tz_aware()
        return self._now

    def now_tz_aware(self):
        if self.config['tz_aware']:
            # FIXME/2018-05-23: (lb): Tests use utcnow(). Should they honor tz_aware?
            #   (Though if Freezegun being used, now() == utcnow().)
            # Clear microseconds to avoid six digits of noise, e.g., 12:34:56.789012.
            # (lb): I added seconds to hamster (was historically demarcated by minutes),
            # because I think seconds could be useful to a developer. But not no more.
            return datetime.utcnow().replace(microsecond=0)
        else:
            return datetime.now().replace(microsecond=0)


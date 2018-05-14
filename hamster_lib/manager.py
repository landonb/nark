# -*- encoding: utf-8 -*-

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

import logging

from future.utils import python_2_unicode_compatible

from .helpers import logging as logging_helpers

from .managers.activity import BaseActivityManager
from .managers.category import BaseCategoryManager
from .managers.fact import BaseFactManager
from .managers.tag import BaseTagManager


__all__ = ['BaseStore',]


@python_2_unicode_compatible
class BaseStore(object):
    """
    A controller store provides unified interfaces to interact with our stored entities.

    ``self.logger`` provides a dedicated logger instance for any storage related logging.
    If you want to make use of it, just setup and attach your handlers and you are ready to go.
    Be advised though, ``self.logger`` will be very verbose as on ``debug`` it will log any
    method call and often even their returned instances.
    """

    def __init__(self, config):
        self.config = config
        self.init_logger()
        self.categories = BaseCategoryManager(self)
        self.activities = BaseActivityManager(self)
        self.tags = BaseTagManager(self)
        self.facts = BaseFactManager(self)

    def cleanup(self):
        """
        Any backend specific teardown code that needs to be executed before
        we shut down gracefully.
        """
        raise NotImplementedError

    def init_logger(self):
        self.logger = logging.getLogger('hamster_lib.storage')
        self.logger.addHandler(logging.NullHandler())

        warn_name = False
        try:
            sql_log_level = self.config['sql_log_level']
            try:
                log_level = int(sql_log_level)
            except ValueError:
                log_level = logging.getLevelName(sql_log_level)
        except KeyError:
            log_level = logging.WARNING
        try:
            self.logger.setLevel(int(log_level))
        except ValueError:
            warn_name = True
            log_level = logging.WARNING

        stream_handler = logging.StreamHandler()
        formatter = logging_helpers.formatter_basic()
        formatter = logging_helpers.setupHandler(stream_handler, formatter, self.logger)

        if warn_name:
            self.logger.warning('Unknown sql_log_level specified: {}'.format(sql_log_level))


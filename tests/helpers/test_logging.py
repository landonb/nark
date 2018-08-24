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

import logging

from nark.helpers import logging as logging_helpers


class TestSetupHandler(object):
    def test_get_formatter_basic(self, mocker):
        """Test formatter fetcher."""
        formatter = logging_helpers.formatter_basic()
        # (lb): Is this legit, or a little too _intimate?
        expected = '[%(levelname)s] %(asctime)s %(name)s %(funcName)s: %(message)s'
        assert formatter._fmt == expected

    def test_setup_handler_stream_handler(self, mocker):
        """Test logging setup."""
        stream_handler = logging.StreamHandler()
        formatter = logging_helpers.formatter_basic()
        logger = mocker.MagicMock()
        logging_helpers.setup_handler(stream_handler, formatter, logger)
        logger.addHandler.assert_called_with(stream_handler)


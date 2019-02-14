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

import pytest
from nark.manager import BaseStore


class TestController:
    @pytest.mark.parametrize('storetype', ['sqlalchemy'])
    def test_get_store_valid(self, controller, storetype):
        """Make sure we recieve a valid ``store`` instance."""
        # [TODO]
        # Once we got backend registration up and running this should be
        # improved to check actual store type for that backend.
        controller.config['store'] = storetype
        assert isinstance(controller._get_store(), BaseStore)

    def test_get_store_invalid(self, controller):
        """Make sure we get an exception if store retrieval fails."""
        controller.config['store'] = None
        with pytest.raises(KeyError):
            controller._get_store()

    def test_update_config(self, controller, base_config, mocker):
        """Make sure we assign new config and get a new store."""
        controller._get_store = mocker.MagicMock()
        controller.update_config({})
        assert controller.config == {}
        assert controller._get_store.called

    def test_get_logger(self, controller):
        """Make sure we recieve a logger that maches our expectations."""
        logger = controller._get_logger()
        assert isinstance(logger, logging.Logger)
        assert logger.name == 'nark.log'
        # [FIXME]
        # assert len(logger.handlers) == 1
        assert isinstance(logger.handlers[0], logging.NullHandler)

    def test_sql_logger(self, controller):
        """Make sure we recieve a logger that maches our expectations."""
        logger = controller._sql_logger()
        assert isinstance(logger, logging.Logger)
        assert logger.name == 'nark.store'
        assert isinstance(logger.handlers[0], logging.NullHandler)


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

import logging
import sys

import pytest

from unittest.mock import patch

from nark.config.log_levels import get_log_level_safe, must_verify_log_level


class TestConfigLogLevels:
    def test_must_verify_log_level_valid(self, log_level_valid_parametrized):
        _log_level = must_verify_log_level(log_level_valid_parametrized)
        assert(isinstance(_log_level, int))

    def test_must_verify_log_level_invalid(self, log_level_invalid_parametrized):
        with pytest.raises(SyntaxError):
            must_verify_log_level(log_level_invalid_parametrized)

    def test_get_log_level_safe_valid(self, log_level_valid_parametrized):
        _log_level = get_log_level_safe(log_level_valid_parametrized)
        assert(isinstance(_log_level, int))

    def test_get_log_level_safe_invalid(self, log_level_invalid_parametrized):
        _log_level = get_log_level_safe(log_level_invalid_parametrized)
        assert(isinstance(_log_level, int))

    def test_get_log_level_on_completion(self):
        testargs = [
            "/home/user/.virtualenvs/dob/lib/python3.[5-7]/site-packages/pytest.py",
            "complete",
        ]
        with patch.object(sys, 'argv', testargs):
            _log_level = get_log_level_safe(logging.DEBUG)
            assert(_log_level == (logging.CRITICAL + 1))


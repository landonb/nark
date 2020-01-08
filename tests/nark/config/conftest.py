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

"""Fixtures that are of general use."""

from configobj import ConfigObj

import pytest

from nark.config.log_levels import LOG_LEVELS


@pytest.fixture(params=list(LOG_LEVELS.keys()))
def log_level_valid_parametrized(request):
    """Return each of the valid log level strings."""
    return request.param


@pytest.fixture(params=(None, 123, 'abc', ''))
def log_level_invalid_parametrized(request):
    """Return selection of invalid log level strings."""
    return request.param


@pytest.fixture
def configobj_instance(request):
    """Provide a ``ConfigObj`` instance and its expected config dict."""

    config = ConfigObj()
    config['db'] = {}
    config['db']['orm'] = 'sqlalchemy'
    config['db']['engine'] = 'sqlite'
    config['db']['path'] = '/tmp/hamster.db'
    config['db']['host'] = 'www.example.com'
    config['db']['port'] = 22
    config['db']['name'] = 'hamster'
    config['db']['user'] = 'hamster'
    config['db']['password'] = 'hamster'
    config['dev'] = {}
    config['dev']['lib_log_level'] = 'WARNING'
    config['dev']['sql_log_level'] = 'debug'
    config['time'] = {}
    config['time']['allow_momentaneous'] = False
    config['time']['day_start'] = '05:00:00'
    config['time']['fact_min_delta'] = 60
    config['time']['tz_aware'] = False
    config['time']['default_tzinfo'] = ''

    expectation = {
        'db': {
            'orm': 'sqlalchemy',
            'engine': 'sqlite',
            'path': '/tmp/hamster.db',
            'host': 'www.example.com',
            'port': '22',
            'name': 'hamster',
            'user': 'hamster',
            'password': 'hamster',
        },
        'dev': {
            'lib_log_level': 'WARNING',
            'sql_log_level': 'debug',
        },
        'time': {
            'allow_momentaneous': 'False',
            'day_start': '05:00:00',
            # day_start_time is an ephemeral setting; not included in as_dict().
            # (lb): Should we test for this another way? (Check coverage.)
            #   'day_start_time': datetime.datetime.strptime(
            #                       '05:00:00', '%H:%M:%S').time(),
            'fact_min_delta': '60',
            # MAYBE: (lb): Consider fiddling with day_start and fact_min_delta
            # in specific tests and leaving them set to factory defaults here:
            #   'day_start': '',
            #   'fact_min_delta': 0,
            'tz_aware': 'False',
            'default_tzinfo': '',
        },
    }

    return config, expectation


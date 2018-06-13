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

"""Fixtures needed to test helper submodule."""

from __future__ import absolute_import, unicode_literals

import codecs
import datetime
import fauxfactory
import os
import pytest
from configparser import SafeConfigParser
from six import text_type

from hamster_lib.helpers import config_helpers
#from hamster_lib.helpers.time import TimeFrame


@pytest.fixture
def filename():
    """Provide a filename string."""
    return fauxfactory.gen_utf8()


@pytest.fixture
def filepath(tmpdir, filename):
    """Provide a fully qualified pathame within our tmp-dir."""
    return os.path.join(tmpdir.strpath, filename)


@pytest.fixture
def appdirs(mocker, tmpdir):
    """Provide mocked version specific user dirs using a tmpdir."""
    def ensure_directory_exists(directory):
        if not os.path.lexists(directory):
            os.makedirs(directory)
        return directory

    config_helpers.HamsterAppDirs.user_config_dir = ensure_directory_exists(os.path.join(
        tmpdir.mkdir('config').strpath, 'hamster-lib/'))
    config_helpers.HamsterAppDirs.user_data_dir = ensure_directory_exists(os.path.join(
        tmpdir.mkdir('data').strpath, 'hamster-lib/'))
    config_helpers.HamsterAppDirs.user_cache_dir = ensure_directory_exists(os.path.join(
        tmpdir.mkdir('cache').strpath, 'hamster-lib/'))
    config_helpers.HamsterAppDirs.user_log_dir = ensure_directory_exists(os.path.join(
        tmpdir.mkdir('log').strpath, 'hamster-lib/'))
    return config_helpers.HamsterAppDirs


@pytest.fixture
def backend_config(appdirs):
    """Provide generic backend config."""
    appdir = appdirs(config_helpers.DEFAULT_APP_NAME)
    return config_helpers.get_default_backend_config(appdir)


@pytest.fixture
def configparser_instance(request):
    """Provide a ``ConfigParser`` instance and its expected config dict."""
    config = SafeConfigParser()
    config.add_section('Backend')
    config.set('Backend', 'store', 'sqlalchemy')
    config.set('Backend', 'day_start', '05:00:00')
    #config.set('Backend', 'day_start', '')
    config.set('Backend', 'fact_min_delta', '60')
    #config.set('Backend', 'fact_min_delta', '0')
    config.set('Backend', 'db_engine', 'sqlite')
    config.set('Backend', 'db_path', '/tmp/hamster.db')
    config.set('Backend', 'db_host', 'www.example.com')
    config.set('Backend', 'db_port', '22')
    config.set('Backend', 'db_name', 'hamster')
    config.set('Backend', 'db_user', 'hamster')
    config.set('Backend', 'db_password', 'hamster')
    config.set('Backend', 'sql_log_level', 'WARNING')

    expectation = {
        'store': text_type('sqlalchemy'),
#        'day_start': datetime.datetime.strptime('05:00:00', '%H:%M:%S').time(),
        'fact_min_delta': 0,
        'db_engine': text_type('sqlite'),
        'db_path': text_type('/tmp/hamster.db'),
        'db_host': text_type('www.example.com'),
        'db_port': 22,
        'db_name': text_type('hamster'),
        'db_user': text_type('hamster'),
        'db_password': text_type('hamster'),
        'sql_log_level': text_type('WARNING'),
    }

    return config, expectation


@pytest.fixture
def config_instance(request):
    """A dummy instance of ``SafeConfigParser``."""
    return SafeConfigParser()


@pytest.fixture
def config_file(backend_config, appdirs):
    """Provide a config file stored under our fake config dir."""
    with codecs.open(os.path.join(appdirs.user_config_dir, 'config.conf'),
            'w', encoding='utf-8') as fobj:
        config_helpers.backend_config_to_configparser(backend_config).write(fobj)
        config_instance.write(fobj)


@pytest.fixture(params=[
    ('foobar', {
#        'timeinfo': TimeFrame(None, None, None, None, None),
        'timeinfo': None,
        'activity': 'foobar',
        'category': None,
        'description': None,
    }),
    ('11:00 12:00 foo@bar', {
#        'timeinfo': TimeFrame(None, datetime.time(11), None, None, None),
        'timeinfo': '11:00',
        'activity': '12:00 foo',
        'category': 'bar',
        'description': None,
    }),
    ('rumpelratz foo@bar', {
#        'timeinfo': TimeFrame(None, None, None, None, None),
        'timeinfo': None,
        'start': None,
        'end': None,
        'activity': 'rumpelratz foo',
        'category': 'bar',
        'description': None,
    }),
    ('foo@bar', {
#        'timeinfo': TimeFrame(None, None, None, None, None),
        'timeinfo': '',
        'activity': 'foo',
        'category': 'bar',
        'description': None,
    }),
    ('foo@bar, palimpalum', {
#        'timeinfo': TimeFrame(None, None, None, None, None),
        'timeinfo': None,
        'activity': 'foo',
        'category': 'bar',
        'description': 'palimpalum',
    }),
    ('12:00 foo@bar, palimpalum', {
#        'timeinfo': TimeFrame(None, datetime.time(12), None, None, None),
        'timeinfo': '12:00',
        'activity': 'foo',
        'category': 'bar',
        'description': 'palimpalum',
    }),
    ('12:00 - 14:14 foo@bar, palimpalum', {
#        'timeinfo': TimeFrame(None, datetime.time(12), None, datetime.time(14, 14), None),
        'timeinfo': '12:00 to 14:14',
        'activity': 'foo',
        'category': 'bar',
        'description': 'palimpalum',
    }),
    # Missing whitespace around ``-`` will prevent timeinfo from being parsed.
    ('12:00-14:14 foo@bar, palimpalum', {
#        'timeinfo': TimeFrame(None, None, None, None, None),
        'timeinfo': '',
        'activity': '12:00-14:14 foo',
        'category': 'bar',
        'description': 'palimpalum',
    }),
])
def raw_fact_parametrized(request):
    """Provide a variety of raw facts as well as a dict of its proper components."""
    return request.param

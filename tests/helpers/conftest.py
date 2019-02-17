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
import os

import fauxfactory
import pytest
from configparser import ConfigParser
from nark.helpers import app_config
from nark.helpers.app_dirs import NarkAppDirs
from six import text_type


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

    NarkAppDirs.user_config_dir = ensure_directory_exists(os.path.join(
        tmpdir.mkdir('config').strpath, 'nark/'))
    NarkAppDirs.user_data_dir = ensure_directory_exists(os.path.join(
        tmpdir.mkdir('data').strpath, 'nark/'))
    NarkAppDirs.user_cache_dir = ensure_directory_exists(os.path.join(
        tmpdir.mkdir('cache').strpath, 'nark/'))
    NarkAppDirs.user_log_dir = ensure_directory_exists(os.path.join(
        tmpdir.mkdir('log').strpath, 'nark/'))
    return NarkAppDirs


@pytest.fixture
def backend_config(appdirs):
    """Provide generic backend config."""
    appdir = appdirs(app_config.DEFAULT_APP_NAME)
    return app_config.get_default_backend_config(appdir)


@pytest.fixture
def configparser_instance(request):
    """Provide a ``ConfigParser`` instance and its expected config dict."""
    config = ConfigParser()
    config.add_section('Backend')
    config.set('Backend', 'store', 'sqlalchemy')
    config.set('Backend', 'db_engine', 'sqlite')
    config.set('Backend', 'db_path', '/tmp/hamster.db')
    config.set('Backend', 'db_host', 'www.example.com')
    config.set('Backend', 'db_port', '22')
    config.set('Backend', 'db_name', 'hamster')
    config.set('Backend', 'db_user', 'hamster')
    config.set('Backend', 'db_password', 'hamster')
    config.set('Backend', 'day_start', '05:00:00')
    config.set('Backend', 'fact_min_delta', '60')
    config.set('Backend', 'lib_log_level', 'WARNING')
    config.set('Backend', 'sql_log_level', 'WARNING')
    # MAYBE: (lb): Consider fiddling with day_start and fact_min_delta
    # in specific tests and leaving them set to factory defaults here.
    #   config.set('Backend', 'day_start', '')
    #   config.set('Backend', 'fact_min_delta', '0')
    # Also consider the other settings not being set here.
    #   config.set('Backend', 'allow_momentaneous', 'False')
    #   config.set('Backend', 'tz_aware', 'False')
    #   config.set('Backend', 'default_tzinfo', '')

    expectation = {
        'store': text_type('sqlalchemy'),
        'db_engine': text_type('sqlite'),
        'db_path': text_type('/tmp/hamster.db'),
        'db_host': text_type('www.example.com'),
        'db_port': 22,
        'db_name': text_type('hamster'),
        'db_user': text_type('hamster'),
        'db_password': text_type('hamster'),
        'allow_momentaneous': False,
        'day_start': datetime.datetime.strptime('05:00:00', '%H:%M:%S').time(),
        'fact_min_delta': 60,
        # MAYBE: (lb): Consider fiddling with day_start and fact_min_delta
        # in specific tests and leaving them set to factory defaults here:
        #   'day_start': '',
        #   'fact_min_delta': 0,
        'lib_log_level': text_type('WARNING'),
        'sql_log_level': text_type('WARNING'),
        'tz_aware': False,
        'default_tzinfo': '',
    }

    return config, expectation


@pytest.fixture
def config_instance(request):
    """A dummy instance of ``ConfigParser``."""
    return ConfigParser()


@pytest.fixture
def config_file(backend_config, appdirs):
    """Provide a config file stored under our fake config dir."""
    config_conf = os.path.join(appdirs.user_config_dir, 'config.conf')
    with codecs.open(config_conf, 'w', encoding='utf-8') as fobj:
        app_config.backend_config_to_configparser(backend_config).write(fobj)
        config_instance.write(fobj)


@pytest.fixture(params=[
    ('foobar', {
        'timeinfo': None,
        'activity': 'foobar',
        'category': None,
        'description': None,
    }),
    ('11:00 12:00 foo@bar', {
        'timeinfo': '11:00',
        'activity': '12:00 foo',
        'category': 'bar',
        'description': None,
    }),
    ('rumpelratz foo@bar', {
        'timeinfo': None,
        'start': None,
        'end': None,
        'activity': 'rumpelratz foo',
        'category': 'bar',
        'description': None,
    }),
    ('foo@bar', {
        'timeinfo': '',
        'activity': 'foo',
        'category': 'bar',
        'description': None,
    }),
    ('foo@bar, palimpalum', {
        'timeinfo': None,
        'activity': 'foo',
        'category': 'bar',
        'description': 'palimpalum',
    }),
    ('12:00 foo@bar, palimpalum', {
        'timeinfo': '12:00',
        'activity': 'foo',
        'category': 'bar',
        'description': 'palimpalum',
    }),
    ('12:00 - 14:14 foo@bar, palimpalum', {
        'timeinfo': '12:00 to 14:14',
        'activity': 'foo',
        'category': 'bar',
        'description': 'palimpalum',
    }),
    # Missing whitespace around ``-`` will prevent timeinfo from being parsed.
    ('12:00-14:14 foo@bar, palimpalum', {
        'timeinfo': '',
        'activity': '12:00-14:14 foo',
        'category': 'bar',
        'description': 'palimpalum',
    }),
])
def raw_fact_parametrized(request):
    """Provide a variety of raw facts as well as a dict of its proper components."""
    return request.param


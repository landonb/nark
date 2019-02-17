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

import pytest
from configparser import ConfigParser
from nark.helpers import app_config
from nark.helpers.app_dirs import NarkAppDirs


class TestNarkAppDirs(object):
    """Make sure that our custom AppDirs works as intended."""

    def test_user_data_dir_returns_directoy(self, tmpdir, mocker):
        """Make sure method returns directory."""
        path = tmpdir.strpath
        mocker.patch('nark.helpers.app_dirs.appdirs.user_data_dir', return_value=path)
        appdir = NarkAppDirs('nark')
        assert appdir.user_data_dir == path

    @pytest.mark.parametrize('create', [True, False])
    def test_user_data_dir_creates_file(self, tmpdir, mocker, create, faker):
        """Make sure that path creation depends on ``create`` attribute."""
        path = os.path.join(tmpdir.strpath, '{}/'.format(faker.word()))
        mocker.patch('nark.helpers.app_dirs.appdirs.user_data_dir', return_value=path)
        appdir = NarkAppDirs('nark')
        appdir.create = create
        assert os.path.exists(appdir.user_data_dir) is create

    def test_site_data_dir_returns_directoy(self, tmpdir, mocker):
        """Make sure method returns directory."""
        path = tmpdir.strpath
        mocker.patch('nark.helpers.app_dirs.appdirs.site_data_dir', return_value=path)
        appdir = NarkAppDirs('nark')
        assert appdir.site_data_dir == path

    @pytest.mark.parametrize('create', [True, False])
    def test_site_data_dir_creates_file(self, tmpdir, mocker, create, faker):
        """Make sure that path creation depends on ``create`` attribute."""
        path = os.path.join(tmpdir.strpath, '{}/'.format(faker.word()))
        mocker.patch('nark.helpers.app_dirs.appdirs.site_data_dir', return_value=path)
        appdir = NarkAppDirs('nark')
        appdir.create = create
        assert os.path.exists(appdir.site_data_dir) is create

    def test_user_config_dir_returns_directoy(self, tmpdir, mocker):
        """Make sure method returns directory."""
        path = tmpdir.strpath
        mocker.patch(
            'nark.helpers.app_dirs.appdirs.user_config_dir',
            return_value=path,
        )
        appdir = NarkAppDirs('nark')
        assert appdir.user_config_dir == path

    @pytest.mark.parametrize('create', [True, False])
    def test_user_config_dir_creates_file(self, tmpdir, mocker, create, faker):
        """Make sure that path creation depends on ``create`` attribute."""
        path = os.path.join(tmpdir.strpath, '{}/'.format(faker.word()))
        mocker.patch('nark.helpers.app_dirs.appdirs.user_config_dir',
                     return_value=path)
        appdir = NarkAppDirs('nark')
        appdir.create = create
        assert os.path.exists(appdir.user_config_dir) is create

    def test_site_config_dir_returns_directoy(self, tmpdir, mocker):
        """Make sure method returns directory."""
        path = tmpdir.strpath
        mocker.patch('nark.helpers.app_dirs.appdirs.site_config_dir',
                     return_value=path)
        appdir = NarkAppDirs('nark')
        assert appdir.site_config_dir == path

    @pytest.mark.parametrize('create', [True, False])
    def test_site_config_dir_creates_file(self, tmpdir, mocker, create, faker):
        """Make sure that path creation depends on ``create`` attribute."""
        path = os.path.join(tmpdir.strpath, '{}/'.format(faker.word()))
        mocker.patch('nark.helpers.app_dirs.appdirs.site_config_dir',
                     return_value=path)
        appdir = NarkAppDirs('nark')
        appdir.create = create
        assert os.path.exists(appdir.site_config_dir) is create

    def test_user_cache_dir_returns_directoy(self, tmpdir, mocker):
        """Make sure method returns directory."""
        path = tmpdir.strpath
        mocker.patch('nark.helpers.app_dirs.appdirs.user_cache_dir',
                     return_value=path)
        appdir = NarkAppDirs('nark')
        assert appdir.user_cache_dir == path

    @pytest.mark.parametrize('create', [True, False])
    def test_user_cache_dir_creates_file(self, tmpdir, mocker, create, faker):
        """Make sure that path creation depends on ``create`` attribute."""
        path = os.path.join(tmpdir.strpath, '{}/'.format(faker.word()))
        mocker.patch('nark.helpers.app_dirs.appdirs.user_cache_dir',
                     return_value=path)
        appdir = NarkAppDirs('nark')
        appdir.create = create
        assert os.path.exists(appdir.user_cache_dir) is create

    def test_user_log_dir_returns_directoy(self, tmpdir, mocker):
        """Make sure method returns directory."""
        path = tmpdir.strpath
        mocker.patch('nark.helpers.app_dirs.appdirs.user_log_dir', return_value=path)
        appdir = NarkAppDirs('nark')
        assert appdir.user_log_dir == path

    @pytest.mark.parametrize('create', [True, False])
    def test_user_log_dir_creates_file(self, tmpdir, mocker, create, faker):
        """Make sure that path creation depends on ``create`` attribute."""
        path = os.path.join(tmpdir.strpath, '{}/'.format(faker.word()))
        mocker.patch('nark.helpers.app_dirs.appdirs.user_log_dir', return_value=path)
        appdir = NarkAppDirs('nark')
        appdir.create = create
        assert os.path.exists(appdir.user_log_dir) is create


class TestGetConfigPath(object):
    """Test config pathj retrieval."""

    def test_get_config_path(self, appdirs):
        """Make sure the config target path is constructed to our expectations."""
        expectation = os.path.join(
            appdirs.user_config_dir,
            app_config.DEFAULT_CONFIG_FILENAME,
        )
        result = app_config.get_config_path()
        assert result == expectation


class TestWriteConfigFile(object):
    """Make sure writing a config instance to disk works as expected."""

    def test_file_is_written(self, config_instance, appdirs):
        """
        Make sure the file is written.

        Note: Content is not checked, this is ConfigParsers job.
        """
        app_config.write_config_file(config_instance)
        expected_location = app_config.get_config_path()
        assert os.path.lexists(expected_location)

    def test_return_config_instance(self, config_instance, appdirs):
        """Make sure we return a ``ConfigParser`` instance."""
        result = app_config.write_config_file(config_instance)
        assert isinstance(result, ConfigParser)


class TestLoadConfigFile(object):
    """Make sure file retrival works as expected."""

    def test_no_file_present(self, appdirs, config_instance):
        """
        Make sure we return ``None``.

        Notw:
            We use the ``appdirs`` fixture to make sure the required dirs exist.
        """
        result = app_config.load_config_file(fallback_config_instance=config_instance)
        assert result == config_instance

    def test_file_present(self, config_instance, backend_config):
        """Make sure we try parsing a found config file."""
        result = app_config.load_config_file()
        assert isinstance(result, ConfigParser)


class TestConfigParserToBackendConfig(object):
    """Make sure that conversion works expected."""

    def test_regular_usecase(self, configparser_instance):
        """Make sure basic mechanics work and int/time types are created."""
        cp_instance, expectation = configparser_instance
        result = app_config.configparser_to_backend_config(cp_instance)
        assert result == expectation


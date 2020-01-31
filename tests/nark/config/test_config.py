# This file exists within 'nark':
#
#   https://github.com/hotoffthehamster/nark
#
# Copyright © 2018-2020 Landon Bouma
# Copyright © 2015-2016 Eric Goller
# All  rights  reserved.
#
# 'nark' is free software: you can redistribute it and/or modify it under the terms
# of the GNU General Public License  as  published by the Free Software Foundation,
# either version 3  of the License,  or  (at your option)  any   later    version.
#
# 'nark' is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY  or  FITNESS FOR A PARTICULAR
# PURPOSE.  See  the  GNU General Public License  for  more details.
#
# You can find the GNU General Public License reprinted in the file titled 'LICENSE',
# or visit <http://www.gnu.org/licenses/>.

import os

import pytest

from nark.config import decorate_config
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


class TestConfigObjToBackendConfig(object):
    """Make sure that conversion works expected."""

    def test_regular_usecase(self, configobj_instance):
        """Make sure basic mechanics work and int/time types are created."""
        configobj, expectation = configobj_instance
        result = decorate_config(configobj).as_dict(unmutated=True)
        assert result == expectation


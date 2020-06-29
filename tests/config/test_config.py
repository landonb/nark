# This file exists within 'nark':
#
#   https://github.com/tallybark/nark
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

import datetime
import os

import pytest

from nark.config import decorate_config, ConfigRoot
from nark.helpers.app_dirs import NarkAppDirs


@pytest.fixture
def config_root():
    config_root = ConfigRoot
    config_root.forget_config_values()
    return config_root


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

    def test_decorate_config_on_config(self, config_root):
        """Test that decorate_config given existing config returns that config."""
        assert decorate_config(config_root) is config_root


class TestNarkConfigurableDb(object):
    """Test NarkConfigurableDb ConfigRoot.section."""

    def test_db_path_with_appdirs(self, tmpdir, mocker):
        path = tmpdir.strpath
        mocker.patch('nark.helpers.app_dirs.appdirs.user_data_dir', return_value=path)
        # The ConfigRoot will already have been created without AppDirs setup,
        # so tell it to forget what it knows, and it'll scan defaults again.
        config_root = ConfigRoot
        config_root.forget_config_values()
        db_path = config_root['db']['path']
        assert db_path == os.path.join(path, 'dob.sqlite')


class TestNarkConfigurableTime(object):
    """Test NarkConfigurableTime ConfigRoot.section."""

    # *** nark.config._strptime_day_start

    # These tests implicitly test nark.config._strptime_day_start.

    def test_day_start_empty_string(self, config_root):
        config_root.asobj.time.day_start.value = ''
        assert config_root['time']['day_start'] == datetime.time(0, 0, 0)

    def test_day_start_datetime_time(self, config_root):
        time = datetime.time(23, 59, 44)
        config_root.asobj.time.day_start.value = time
        assert config_root['time']['day_start'] == time

    def test_day_start_from_text_valid(self, config_root):
        time = '21:34:56'
        config_root.asobj.time.day_start.value = time
        assert config_root['time']['day_start'] == datetime.time(21, 34, 56)

    def test_day_start_from_text_invalid(self, config_root):
        time = '25:66:67'
        with pytest.raises(ValueError) as excinfo:
            config_root.asobj.time.day_start.value = time
        assert str(excinfo.value).startswith('Unrecognized value for setting')

    # *** ephemeral settings

    def test_tz_aware_default(self, config_root):
        assert config_root['time']['tz_aware'] is False

    def test_default_tzinfo_default(self, config_root):
        assert config_root['time']['default_tzinfo'] == ''


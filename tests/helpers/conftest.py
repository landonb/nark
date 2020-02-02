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

"""Fixtures needed to test helper submodule."""

import os

import pytest

from nark.helpers.app_dirs import NarkAppDirs


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
# FIXME/2020-01-31: raw_fact_parametrized is not used.
def raw_fact_parametrized(request):
    """Provide a variety of raw facts as well as a dict of its proper components."""
    return request.param


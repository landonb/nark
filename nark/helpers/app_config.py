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

"""
Provide functions that provide common config related functionality.

This module provide easy to use convenience functions to handle common
configuration related tasks. Clients can use those to provide consistent
behaviour and focus on their specific requirements instead.

The easiest way to make use of those helpers is to call ``load_config_file``
(which will also handle creating a new one if none exists) and
``write_config_file``.

Clients may use ``backend_config_to_configparser`` and its counterpart
``configparser_to_backend_config`` to delegate conversion between a backend
config dict and a ``ConfigParser`` instance.

Note:
    Backend config key/value information:
        store: A ``string`` indicating which store to use.
            See: ``nark.REGISTERED_BACKENDS``

        db_engine: ``string`` indicating which db-engine to use.
            Options depend on store choice.

        db_path: ``string`` indicating where to save the db file if the
            selected db option saves to disk. Depends on store/engine choice.

        db_host: ``string`` indicating the host of the db server.
            Depends on store/engine choice.

        db_port: ``int`` indicating the port of the db server.
            Depends on store/engine choice.

        db_name: ``string`` indicating the db-name. Depends on store/engine choice.

        db_user: ``string`` indicating the username to access the db server.
            Depends on store/engine choice.

        db_password: ``string`` indicating the password to access the db server.
            Depends on store/engine choice.

        allow_momentaneous: ``bool`` indicting if 0-length duration Facts allowed,
            e.g., start == end. Here's a little vocabulary lesson:
                Fugacious: "lasting a short time"
                Evanescent: "tending to vanish like vapor"
                Momentaneous: "characterizing action begun, terminated in an instant"
                See also: Vacant, Fleeting, Transient.

        day_start: ``datetime.time`` cna be used to specify default start time.
            (Weird Legacy Hamster feature; now disabled by default.)

        fact_min_delta: ``int`` specifying minimal fact duration. Facts shorter
            than this will be rejected.

        lib_log_level: ``string`` indicating the nark library logging logger log level.

        sql_log_level: ``string`` indicating the SQLAlchemy logging logger log level.

        tz_aware: ``bool`` indicating if datetimes are relative UTC or not.

        default_tzinfo: ``string`` default Timezone to use when storing time.

    Please also note that a backend *config dict* does except ``None`` / ``empty``
    values, its ``ConfigParser`` representation does not include those however!
"""

from __future__ import absolute_import, unicode_literals

import datetime
import os

from configparser import NoOptionError, ConfigParser
from six import string_types, text_type

from ..control import REGISTERED_BACKENDS
from .app_dirs import NarkAppDirs

# NOTE: (lb): This file is unused by nark/dob.
#       It's used by hamster-gtk, which is broke
#       against nark because of so much refactoring.
# FIXME: Fix this file to work with hamster-gtk again?
#        (I'm not sure how much I care about the windowed app;
#         I'm pretty happy with just the CLI....)


DEFAULT_APP_NAME = 'nark'
DEFAULT_APPDIRS = NarkAppDirs(DEFAULT_APP_NAME)
DEFAULT_CONFIG_FILENAME = '{}.conf'.format(DEFAULT_APPDIRS.appname)


def get_config_path(appdirs=DEFAULT_APPDIRS, file_name=DEFAULT_CONFIG_FILENAME):
    """
    Return the path where the config file is stored.

    Args:
        app_name (text_type, optional): Name of the application, defaults to
        ``'projecthamster``. Allows you to use your own application specific
        namespace if you wish.
        file_name (text_type, optional): Name of the config file. Defaults to
        ``config.conf``.

    Returns:
        str: Fully qualified path (dir & filename) where we expect the config file.
    """
    if isinstance(appdirs, string_types):
        appdirs = NarkAppDirs(appdirs)
    return os.path.join(appdirs.user_config_dir, file_name)


def write_config_file(
    config_instance,
    appdirs=DEFAULT_APPDIRS,
    file_name=DEFAULT_CONFIG_FILENAME,
):
    """
    Write a ConfigParser instance to file at the correct location.

    Args:
        config_instance: Config instance to safe to file.
        appdirs (NarkAppDirs, optional): ``NarkAppDirs`` instance storing
            app/user specific path information.
        file_name (text_type, optional): Name of the config file. Defaults to
        ``DEFAULT_CONFIG_FILENAME``.

    Returns:
        ConfigParser: Instance written to file.
    """

    path = get_config_path(appdirs, file_name)
    with open(path, 'w') as fobj:
        config_instance.write(fobj)
    return config_instance


def load_config_file(
    appdirs=DEFAULT_APPDIRS,
    file_name=DEFAULT_CONFIG_FILENAME,
    fallback_config_instance=None,
):
    """
    Retrieve config information from file at default location.

    If no config file is found a new one will be created either with
        ``fallback_config_instance`` as content or if none is provided
        with the result of ``get_default_backend_config``.

    Args:
        appdirs (NarkAppDirs, optional): ``NarkAppDirs`` instance
            storing app/user specific path information.
        file_name (text_type, optional): Name of the config file.
            Defaults to ``DEFAULT_CONFIG_FILENAME``.
        fallback_config_instance (ConfigParser): Backend config that is
            to be used to populate the config file that is created if no
            pre-existing one can be found.

    Returns:
        ConfigParser: Config loaded from file, either from the the
            pre-existing config file or the one created with fallback values.
    """
    if not fallback_config_instance:
        fallback_config_instance = backend_config_to_configparser(
            get_default_backend_config(appdirs)
        )

    config = ConfigParser()
    path = get_config_path(appdirs, file_name)
    if not config.read(path):
        config = write_config_file(
            fallback_config_instance, appdirs=appdirs, file_name=file_name
        )
    return config


def get_default_backend_config(appdirs):
    """
    Return a default config dictionary.

    Args:
        appdirs (NarkAppDirs): ``NarkAppDirs`` instance encapsulating
            the apps details.

    Returns:
        dict: Dictionary with a default configuration.

    Note:
        Those defaults are independent of the particular config-store.
    """
    return {
        'store': 'sqlalchemy',
        'db_engine': 'sqlite',
        'db_path': os.path.join(
            appdirs.user_data_dir,
            '{}.sqlite'.format(appdirs.appname),
        ),
        # Skipping:
        #  'db_host': '',
        #  'db_port': '',
        #  'db_name': '',
        #  'db_user': '',
        #  'db_password': '',
        'allow_momentaneous': False,
        'day_start': '',
        'fact_min_delta': 0,
        'lib_log_level': 'WARNING',
        'sql_log_level': 'WARNING',
        'tz_aware': False,
        'default_tzinfo': '',
    }


# [TODO]
# Provide better error handling
def backend_config_to_configparser(config):
    """
    Return a ConfigParser instance representing a given backend config dictionary.

    Args:
        config (dict): Dictionary of config key/value pairs.

    Returns:
        ConfigParser: ConfigParser instance representing config.

    Note:
        We do not provide *any* validation about mandatory values whatsoever.
    """
    # NOTE: config.get(k) returns None on key miss; but config[k] would KeyError.
    def get_store():
        return config.get('store')

    def get_db_engine():
        return text_type(config.get('db_engine'))

    def get_db_path():
        return text_type(config.get('db_path'))

    def get_db_host():
        return text_type(config.get('db_host'))

    def get_db_port():
        return text_type(config.get('db_port'))

    def get_db_name():
        return text_type(config.get('db_name'))

    def get_db_user():
        return text_type(config.get('db_user'))

    def get_db_password():
        return text_type(config.get('db_password'))

    def get_allow_momentaneous():
        return text_type(bool(config.get('allow_momentaneous')))

    def get_day_start():
        day_start = config.get('day_start')
        if not day_start:
            return text_type('')
        return day_start.strftime('%H:%M:%S')

    def get_fact_min_delta():
        return text_type(config.get('fact_min_delta'))

    def get_lib_log_level():
        return text_type(config.get('lib_log_level'))

    def get_sql_log_level():
        return text_type(config.get('sql_log_level'))

    def get_tz_aware():
        # Convert to a string, e.g., True => 'True'.
        return text_type(bool(config.get('tz_aware')))

    def get_default_tzinfo():
        return text_type(config.get('default_tzinfo'))

    cp_instance = ConfigParser()
    cp_instance.add_section('Backend')
    cp_instance.set('Backend', 'store', get_store())
    cp_instance.set('Backend', 'db_engine', get_db_engine())
    cp_instance.set('Backend', 'db_path', get_db_path())
    cp_instance.set('Backend', 'db_host', get_db_host())
    cp_instance.set('Backend', 'db_port', get_db_port())
    cp_instance.set('Backend', 'db_name', get_db_name())
    cp_instance.set('Backend', 'db_user', get_db_user())
    cp_instance.set('Backend', 'db_password', get_db_password())
    cp_instance.set('Backend', 'allow_momentaneous', get_allow_momentaneous())
    cp_instance.set('Backend', 'day_start', get_day_start())
    cp_instance.set('Backend', 'fact_min_delta', get_fact_min_delta())
    cp_instance.set('Backend', 'lib_log_level', get_lib_log_level())
    cp_instance.set('Backend', 'sql_log_level', get_sql_log_level())
    cp_instance.set('Backend', 'tz_aware', get_tz_aware())
    cp_instance.set('Backend', 'default_tzinfo', get_default_tzinfo())

    return cp_instance


# [TODO]
# Provide better error handling
# Provide validation! For this it would probably be enough to validate a config
# dict. We do not actually need to validate a CP-instance but just its resulting
# dict.
def configparser_to_backend_config(cp_instance):
    """
    Return a config dict generated from a configparser instance.

    This functions main purpose is to ensure config dict values are properly typed.

    Note:
        This can be used with any ``ConfigParser`` backend instance not just
          the default one in order to extract its config.
        If a key is not found in ``cp_instance`` the resulting dict will have
          ``None`` assigned to this dict key.
    """
    def cp_instance_get(section, keyname, default=None):
        try:
            return cp_instance.get(section, keyname)
        except NoOptionError:
            return default

    def cp_instance_getboolean(section, keyname, default=None):
        try:
            return cp_instance.getboolean(section, keyname)
        except NoOptionError:
            return default

    def cp_instance_getint(section, keyname, default=None):
        try:
            return cp_instance.getint(section, keyname)
        except NoOptionError:
            return default

    # ***

    def get_store():
        # (lb): Here's a comment from hamster-lib:
        #     "This should be deligated to a dedicated validation function!"
        #   Though I'm not sure what's the ask. Should we
        #   check more than `store in REGISTERED_BACKENDS.keys`?
        # MAYBE: (lb): Use default 'sqlalchemy' if store not set?
        store = cp_instance_get('Backend', 'store')
        if store not in REGISTERED_BACKENDS.keys():
            raise ValueError(_("Unrecognized store option."))
        return store

    def get_db_engine():
        # (lb): Use default 'sqlite' if db_engine not set?
        return text_type(cp_instance_get('Backend', 'db_engine'))

    def get_db_path():
        return text_type(cp_instance_get('Backend', 'db_path'))

    def get_db_host():
        return text_type(cp_instance_get('Backend', 'db_host'))

    def get_db_port():
        return cp_instance_getint('Backend', 'db_port')

    def get_db_name():
        return text_type(cp_instance_get('Backend', 'db_name'))

    def get_db_user():
        return text_type(cp_instance_get('Backend', 'db_user'))

    def get_db_password():
        return text_type(cp_instance_get('Backend', 'db_password'))

    def get_allow_momentaneous():
        return cp_instance_getboolean('Backend', 'allow_momentaneous', False)

    def get_day_start():
        day_start = cp_instance_get('Backend', 'day_start')
        if not day_start:
            return ''
        try:
            day_start = datetime.datetime.strptime(day_start, '%H:%M:%S').time()
        except ValueError:
            raise ValueError(_(
                "We encountered an error when parsing config's 'day_start' value!"
                " Aborting ..."
            ))
        return day_start

    def get_fact_min_delta():
        return cp_instance_getint('Backend', 'fact_min_delta')

    def get_lib_log_level():
        return text_type(cp_instance_get('Backend', 'lib_log_level'))

    def get_sql_log_level():
        return text_type(cp_instance_get('Backend', 'sql_log_level'))

    def get_tz_aware():
        return cp_instance_getboolean('Backend', 'tz_aware', False)

    def get_default_tzinfo():
        return text_type(cp_instance_get('Backend', 'default_tzinfo', ''))

    result = {
        'store': get_store(),
        'db_engine': get_db_engine(),
        'db_path': get_db_path(),
        'db_host': get_db_host(),
        'db_port': get_db_port(),
        'db_name': get_db_name(),
        'db_user': get_db_user(),
        'db_password': get_db_password(),
        'allow_momentaneous': get_allow_momentaneous(),
        'day_start': get_day_start(),
        'fact_min_delta': get_fact_min_delta(),
        'lib_log_level': get_lib_log_level(),
        'sql_log_level': get_sql_log_level(),
        'tz_aware': get_tz_aware(),
        'default_tzinfo': get_default_tzinfo(),
    }

    return result


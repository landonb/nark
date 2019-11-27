# - coding: utf-8 -

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

"""Nark User Configurable Settings"""

from __future__ import absolute_import, unicode_literals

import datetime
import os

from gettext import gettext as _

from ..control import REGISTERED_BACKENDS
from ..helpers.app_dirs import NarkAppDirs

from .inify import section
from .log_levels import get_log_level_safe
from .subscriptable import Subscriptable

__all__ = (
    'ConfigRoot',
    # PRIVATE:
    # 'NarkConfigurableDb',
    # 'NarkConfigurableDev',
    # 'NarkConfigurableTime',
)


# ***
# *** Top-level, root config object.
# ***

@section(None)
class ConfigRoot(object):
    pass


# ***
# *** Backend (nark) Config.
# ***


@ConfigRoot.section('db')
class NarkConfigurableDb(Subscriptable):
    """"""

    def __init__(self, *args, **kwargs):
        # Cannot super because @section decorator makes NarkConfigurableDb
        # an object instance of a different class type, so there is really
        # no NarkConfigurableDb class. It's been replaced by/monkey patched
        # into an object instance of the decorator class. As such, calling
        # super here, without the correct class, would raise.
        # DEATH: super(NarkConfigurableDb, self).__init__(*args, **kwargs)
        pass

    # ***

    @property
    @ConfigRoot.setting(
        # Just showing off: How to deliberately specify the setting name,
        # otherwise it defaults to the function name.
        # (lb): Was called 'store' in hamster-lib, but 'orm' descriptiver.
        name='orm',  # I.e., instead if `def orm(self)`.
        choices=REGISTERED_BACKENDS,
    )
    def store_default(self):
        # HINT: The doc string here can be used in lieu of specifying in @setting.
        """ORM used by dob to interface with the DBMS. Most likely ‘sqlalchemy’."""
        # HINT: The property return value is the default for the setting.
        # HINT: The type of this value determines the setting type, too.
        return 'sqlalchemy'

    # ***

    @property
    @ConfigRoot.setting(
        _("Database management system used to manage your data."
            " Most likely ‘sqlite’."),
    )
    def engine(self):
        return 'sqlite'

    # ***

    @property
    @ConfigRoot.setting(
        _("Path to SQLite database file"
            " (for ‘sqlite’ db.engine)."),
        # The db.path only applies for 'sqlite' DBMS.
        # But we won't set ephemeral or hidden, because user should still see in
        # config, so they more easily understand how to change DBMS settings.
    )
    def path(self):
        if NarkAppDirs.APP_DIRS is None:
            # Happens when code is sourced, before NarkAppDirs() created.
            return ''
        return os.path.join(
            NarkAppDirs.APP_DIRS.user_data_dir,
            # MAYBE: Rename? 'nark.sqlite'?? or 'hamster.sqlite'??
            # FIXME: Make this a package const rather than inline literal.
            #        (Maybe on Config refactor how to do so will be evident.)
            'dob.sqlite',
        )

    # ***

    # The 5 settings -- db.host, db.port, db.name, db.user, and db.password --
    # apply when db.engine != 'sqlite'. Otherwise, if sqlite, only db.path used.

    @property
    @ConfigRoot.setting(
        _("Host name of the database server"
            " (for non-‘sqlite’ db.engine)."),
    )
    def host(self):
        return ''

    @property
    @ConfigRoot.setting(
        _("Port number on which the server is listening"
            " (for non-‘sqlite’ db.engine)."),
    )
    def port(self):
        return ''

    @property
    @ConfigRoot.setting(
        _("The database name (for non-‘sqlite’ db.engine)."),
    )
    def name(self):
        return ''

    @property
    @ConfigRoot.setting(
        _("The database user (for non-‘sqlite’ db.engine)."),
    )
    def user(self):
        return ''

    @property
    @ConfigRoot.setting(
        _("The database password (non-‘sqlite’)."
            " WARNING: This setting is potentially unsafe!"),
    )
    def password(self):
        return ''


# ***

@ConfigRoot.section('dev')
class NarkConfigurableDev(Subscriptable):
    """"""

    def __init__(self, *args, **kwargs):
        pass

    # ***

    @property
    @ConfigRoot.setting(
        _("The log level setting for library (nark) squaller"
            " (using Python logging library levels)"),
        validate=get_log_level_safe,
    )
    def lib_log_level(self):
        return 'WARNING'

    @property
    @ConfigRoot.setting(
        _("The log level setting for database (SQL) squaller"
            " (using Python logging library levels)"),
        validate=get_log_level_safe,
    )
    def sql_log_level(self):
        return 'WARNING'


# ***

@ConfigRoot.section('time')
class NarkConfigurableTime(Subscriptable):
    """"""

    def __init__(self, *args, **kwargs):
        pass

    # ***

    @property
    @ConfigRoot.setting(
        _("If True, lets you save Facts that start and end"
            " at the exact same time, i.e., zero-length Facts."),
        # FIXME/2019-11-18: (lb): Hidden for now. Still testing.
        # ! - Might be better to default True.
        hidden=True,
    )
    def allow_momentaneous(self):
        return False

    # ***

    # (lb): Seems like an abuse: Not a class method (no self),
    # but not a staticmethod either, so what is?
    def validate_day_start(day_start_text):
        def _get_day_start():
            day_start = None
            if day_start_text:
                try:
                    day_start = datetime.datetime.strptime(
                        day_start_text, '%H:%M:%S',
                    ).time()
                except ValueError:
                    warn_invalid(day_start_text)
            if not day_start:
                day_start = datetime.time(0, 0, 0)
            return day_start

        def warn_invalid(day_start_text):
            msg = _(
                'WARNING: Invalid "day_start" from config: {}'
            ).format(str(day_start_text))
            raise SyntaxError(msg)

        return _get_day_start()

    @property
    @ConfigRoot.setting(
        # FIXME/2019-11-18: Explain this option better.
        _("The time at which the day is considered started."),
        validate=validate_day_start,
    )
    def day_start(self):
        # (lb): Disable this by default; I've never liked this logic!
        #   In Legacy Hamster: '00:00:00'
        return ''

    # ***

    @property
    @ConfigRoot.setting(
        _("If nonzero, dob will not let you save a Fact"
            " with a duration less than this number of seconds."),
    )
    def fact_min_delta(self):
        # (lb): Disable this by default; I've never liked this logic!
        #   In Legacy Hamster: 60, i.e., facts must be 1 minute apart!
        #   In Modern Hamster (nark), you can make facts every seconds,
        #     or every millisecond, we don't care, so long as they do
        #     not overlap!
        return '0'

    # ***

    @property
    @ConfigRoot.setting(
        _("If True, makes it easier to travel across timezones"
            " and daylight savings with dob!"),
    )
    def tz_aware(self):
        # FIXME/2018-06-09: (lb): Implement tzawareness!
        #   Then maybe this should be default True?
        return False

    @property
    @ConfigRoot.setting(
        _("Default TimeZone when tz_aware is in effect."),
    )
    def default_tzinfo(self):
        return ''

# ***

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

"""This module provides nark raw fact parsing-related functions."""

from __future__ import absolute_import, unicode_literals

import re
from datetime import timedelta

import lazy_import
from six import text_type

from .fact_time import (
    RE_PATTERN_RELATIVE_CLOCK,
    RE_PATTERN_RELATIVE_DELTA,
    datetime_from_clock_prior
)
from .parse_errors import ParserInvalidDatetimeException

# Profiling: load iso8601: ~ 0.004 secs.
iso8601 = lazy_import.lazy_module('iso8601')

__all__ = (
    'HamsterTimeSpec',
    'parse_dated',
    'parse_clock_time',
    'parse_datetime_iso8601',
    'parse_relative_minutes',
)


# =================
# Notes on ISO 8601
# =================
#
# ASIDE: (lb): It's not my intent to write a datetime parser (there are plenty
# out there!), but our flexible factoid format lets the user specify datetimes
# in different, non-standard ways. E.g., the user can use relative time, which
# needs business logic to transform into a real datetime. So it's up to us to
# at least parse the datetime well enough to identify what type of format it's
# in, and then to either process it ourselves, or filter it through ``iso8601``
# or ``dateparser``.
#
# Some examples of ISO 8601 compliant datetimes
# ---------------------------------------------
#
#     ✓ 2018-05-14
#     ✓ 2018-05-14T22:29:24.123456+00:00
#     ✓ 2018-05-14T22:29:24+00:00
#     ✓ 2018-05-14T22:29:24Z
#     ✓ 20180514T222924Z
#
# Not all formats are supported by the ``iso8601`` parser
# -------------------------------------------------------
#
#     ✗ 2018-W20
#     ✗ 2018-W20-1
#     ✗ --05-14
#     ✗ 2018-134
#     ✓ 2018-12
#     ✗ 201805
#     ✓ 2018
#   __ ______________________________________________
#     ^ indicates if parse-worthy by iso8601 (✓ or ✗).
#
# And the ``iso8601`` parser also supports an extended format
# -----------------------------------------------------------
#
#   - The iso8601 parser allows ' ' in lieu of 'T'.
#
# The iso8601 parser format is: ``Date [Time [Timezone]]``
# --------------------------------------------------------
#
#   - Date and time are separated by ' ' or 'T'.
#
#   - Timezone immediately follow Time (no delimiter/space).
#
#   - Dates: YYYY-MM-DD | YYYYMMDD | YYYY-MM | YYYY
#
#   - Times: hh:mm:ss.nn | hhmmss.nn | hh:mm | hhmm | hh
#
#   - Time zones: <nothing> | Z | +/-hh:mm | +/-hhmm | +/-hh
#
#   - You can specify days or months without leading 0s [(lb): but why?].

class HamsterTimeSpec(object):
    """"""
    RE_HAMSTER_TIME = None

    def __init__(self):
        """Not implemented: Use class as static/global, not instantiated."""
        raise NotImplementedError

    @staticmethod
    def discern(hamster_time):
        """
        Check for magic datetimes:
          - '+/-n' relative;
          - 'nn:nn' clocktime;
          - ISO 8601 datetime.

        NOTE: This fcn. does not make datetime.datetime's; that's up to the caller.
        """
        dt, type_dt, sep, rest = None, None, None, None

        if HamsterTimeSpec.RE_HAMSTER_TIME is None:
            HamsterTimeSpec.setup_re()

        match = HamsterTimeSpec.RE_HAMSTER_TIME.match(hamster_time)
        if match is not None:
            say_what = match.groupdict()
            if say_what['relative']:
                assert dt is None
                dt = say_what['relative']
                type_dt = 'relative'
            if say_what['clock_time']:
                assert dt is None
                dt = say_what['clock_time']
                type_dt = 'clock_time'
            if say_what['datetime']:
                assert dt is None
                dt = say_what['datetime']
                type_dt = 'datetime'
            assert dt is not None
            sep = say_what['sep']
            rest = say_what['rest']

        return dt, type_dt, sep, rest

    @staticmethod
    def setup_re():
        # NOTE: This pattern isn't perfect; and that's why we use the
        #       iso8601.parse_date routine.
        #
        #       (lb): It's because we use the ()? optionals.
        #       If one of the optionals is formatted incorrectly,
        #       the pattern here happily ignores it, because ?
        #       For instance, this matches, but the microseconds has an error:
        #
        #           RE_HAMSTER_TIME.match('2018-05-14 22:29:24.123x456+00:02')

        # Never forget! Hamster allows relative time!
        pattern_relative = (
            '(?P<relative>([-+]?(\d+h)|[-+](\d+h)?\d+m?))'
        )

        pattern_just_clock = (
            '(?P<clock_time>\d{1,2}:?\d{2}(:\d{2})?)'
        )

        # (lb): Treat 4 digits as clock time, not year, i.e.,
        #   `2030` should be 10:30 PM, not Jan 01, 2030.
        # This steals colon-less clock times:
        #   '(?:(\d{8}|\d{4}|\d{4}-\d{1,2}(-\d{1,2})?))'
        pattern_date = (
            '(?:(\d{8}|\d{4}-\d{1,2}(-\d{1,2})?))'
        )
        pattern_time = (  # noqa: E131
            # (lb): We could allow 3-digit times... but, no.
            #   '(?:\d{1,2})'
            '(?:\d{2})'
            '(?::?\d{2}'
                '(?::?\d{2}'
                    '(?:\.\d+)?'
                ')?'
            ')?'
        )
        pattern_zone = (  # noqa: E131
            '(?:('
                'Z'
            '|'
                '[+-]\d{2}(:?\d{2})?'
            '))?'
        )
        pattern_datetime = (
            '(?P<datetime>{}([ T]{}{})?)'
            .format(pattern_date, pattern_time, pattern_zone)
        )

        hamster_pattern = (
            '(^|\s)({}|{}|{})(?P<sep>[,:]?)(?=\s|$)(?P<rest>.*)'
            .format(
                pattern_relative,
                pattern_just_clock,
                pattern_datetime,
            )
        )

        # Use re.DOTALL to match newlines, which might be part
        # of the <rest> of the factoid.
        HamsterTimeSpec.RE_HAMSTER_TIME = re.compile(hamster_pattern, re.DOTALL)

    @staticmethod
    def has_time_of_day(raw_dt):
        # Assuming format is year-mo-day separated from time of day by space or 'T'.
        parts = re.split(r' |T', raw_dt)
        if len(parts) != 2:
            return False
        assert re.match(RE_PATTERN_RELATIVE_CLOCK, parts[1]) is not None
        return True


# ***

# FIXME: Use this fcn. to support relative/clock-time --since/--until.
def parse_dated(dated, time_now, cruftless=False):
    """"""
    def _parse_dated():
        if not isinstance(dated, text_type):
            # Let BaseFactManager.get_all() process, if not already datetime.
            return dated
        dt, type_dt, sep, rest = HamsterTimeSpec.discern(dated)
        if cruftless and rest:
            msg = _('Found more than datetime in')
            plus_sep = sep and ' + ‘{}’'.format(sep) or ''
            raise ParserInvalidDatetimeException(
                '{} “{}”: ‘{}’{} + ‘{}’'
                .format(msg, dated, str(dt), plus_sep, rest)
            )
        if dt is None:
            raise ParserInvalidDatetimeException(
                '{}: “{}”'.format(_('Unparseable datetime'), dated)
            )
        return datetime_from_discerned(dated, dt, type_dt)

    def datetime_from_discerned(dated, dt, type_dt):
        if type_dt == 'datetime':
            # FIXME: (lb): Implement timezone/local_tz.
            dt_suss = parse_datetime_iso8601(dt, must=True, local_tz=None)
        # else, relative time, or clock time; let caller handle.
        elif type_dt == 'clock_time':
            clock_time = parse_clock_time(dt)
            dt_suss = datetime_from_clock_prior(time_now, clock_time)
        else:
            assert type_dt == 'relative'
            rel_mins, negative = parse_relative_minutes(dt)
            dt_suss = time_now + timedelta(minutes=rel_mins)
        return dt_suss

    return _parse_dated()


# ***

def parse_clock_time(clock_time):
    parsed_ct = None
    match = RE_PATTERN_RELATIVE_CLOCK.match(clock_time)
    if match:
        parts = match.groupdict()
        parsed_ct = (
            parts['hours'],
            parts['minutes'],
            parts['seconds'] or '0',
        )
    return parsed_ct


# ***

def parse_datetime_iso8601(datepart, must=False, local_tz=None):
    try:
        # NOTE: Defaults to datetime.timezone.utc.
        #       Uses naive if we set default_timezone=None.
        parsed = iso8601.parse_date(datepart, default_timezone=local_tz)
    except iso8601.iso8601.ParseError as err:
        parsed = None
        if must:
            raise ParserInvalidDatetimeException(_(
                'Unable to parse iso8601 datetime: {} [{}]'
                .format(datepart, str(err))
            ))
    return parsed


# ***

def parse_relative_minutes(rel_time):
    rel_mins = None
    negative = None
    match = RE_PATTERN_RELATIVE_DELTA.match(rel_time)
    if match:
        parts = match.groupdict()
        rel_mins = 0
        if parts['minutes']:
            rel_mins += int(parts['minutes'])
        if parts['hours']:
            rel_mins += int(parts['hours']) * 60
        if parts['signage'] == '-':
            negative = True  # Because there's no such thang as "-0".
            rel_mins *= -1
        else:
            negative = False
    return rel_mins, negative


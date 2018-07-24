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

"""This module provides several time-related convenience functions."""

from __future__ import absolute_import, unicode_literals

import datetime
import math
from six import text_type

import lazy_import
# Profiling: load pytz: ~ 0.002 secs.
pytz = lazy_import.lazy_module('pytz')


__all__ = [
    'day_end_datetime',
    'day_end_time',
    'must_be_datetime_or_relative',
    'must_not_start_after_end',
    'isoformat',
    'isoformat_tzinfo',
    'isoformat_tzless',
]


def day_end_datetime(end_date, start_time=None):
    """
    Convert a given end date to its proper datetime, based on a day start time.

    Args:
        end_date (datetime.date): Raw end date that is to be adjusted.
        start_time (string): Clock time of start of day.

    Returns:
        datetime.datetime: The adjusted end datetime for a given date,
          based on a specific start_time.

    Example:
        Given a ``start_time`` of ``5:30`` and an end date of ``2015-04-01``,
          the active end datetime is ``2015-04-02 5:29``, to account for an
          actual start datettime of ``2015-04-01 5:30``. The gist is that a
          *work day* does not match a *calendar* (24-hour) day; it depends on
          what the user considers their "daily start time". (Though for many
          users, they'll leave day_start untouched, in which case a single
          day covers a normal 24-hour span, i.e., from 00:00 to 23:59.

    Note:
        An alternative implementation can be found in legacy hamster:
          ``hamster.storage.db.Storage.__get_todays_facts``.
    """
    start_time = start_time or datetime.time(0, 0, 0)
    end_time = day_end_time(start_time)
    if start_time == datetime.time(0, 0, 0):
        # The start time is midnight, so the end time is 23:59:59
        # on the same day.
        assert end_time == datetime.time(23, 59, 59)
        end = datetime.datetime.combine(end_date, end_time)
    else:
        # The start time is not midnight, so the end time is
        # on the following day.
        end = datetime.datetime.combine(end_date, end_time)
        end += datetime.timedelta(days=1)
    return end


def day_end_time(start_time):
    """
    Get the day end time given the day start. This assumes full 24h day.

    Args:
        start_time (string): Clock time of start of day.
    """
    # NOTE: Because we're only returning the time, we don't need the
    #       static "now" from the controller.
    today_date = datetime.date.today()
    start_datetime = datetime.datetime.combine(today_date, start_time)
    end_datetime = start_datetime - datetime.timedelta(seconds=1)
    end_time = end_datetime.time()
    return end_time


def must_be_datetime_or_relative(dt):
    """FIXME: Document"""
    if not dt or isinstance(dt, datetime.datetime) or isinstance(dt, text_type):
        if isinstance(dt, datetime.datetime):
            # FIXME: (lb): I've got milliseconds in my store data!!
            #        So this little hack kludge-fixes the problem;
            #        perhaps someday I'll revisit this and really
            #        figure out what's going on.
            return dt.replace(microsecond=0)
        return dt
    raise TypeError(_(
        'Found {} rather than a datetime, string, or None, as expected.'
        .format(type=type(dt))
    ))


def must_not_start_after_end(range_tuple):
    """
    Perform basic sanity checks on a timeframe.

    Args:
        range_tuple (tuple): ``(start, end)`` tuple.

    Raises:
        ValueError: If start > end.

    Returns:
        tuple: ``(start, end)`` tuple that passed validation.

    Note:
        ``timeframes`` may be incomplete, e.g., end might not be set.
    """

    start, end = range_tuple

    if (
        isinstance(start, datetime.datetime)
        and isinstance(end, datetime.datetime)
        and start > end
    ):
        raise ValueError(_("Start after end!"))

    return range_tuple


def isoformat(dt, sep='T', timespec='auto', include_tz=False):
    """
    FIXME: Document

    Based loosely on
        datetime.isoformat(sep='T', timespec='auto')
    in Python 3.6 (which added timespec).

    The optional argument sep (default 'T') is a one-character separator,
    placed between the date and time portions of the result.

    The optional argument timespec specifies the number of additional components
    of the time to include (the default is 'auto'). It can be one of the following:

    'auto': Same as 'seconds' if microsecond is 0, same as 'microseconds' otherwise.
    'hours': Include the hour in the two-digit HH format.
    'minutes': Include hour and minute in HH:MM format.
    'seconds': Include hour, minute, and second in HH:MM:SS format.
    'milliseconds': Include full time, but truncate fractional second part
        to milliseconds. HH:MM:SS.sss format.
    'microseconds': Include full time in HH:MM:SS.mmmmmm format.

    Note: Excluded time components are truncated, not rounded.

    ValueError will be raised on an invalid timespec argument.

    """
    timecomp = _format_timespec(dt, timespec)

    tzcomp = ''
    if dt.tzinfo:
        if include_tz:
            tzcomp = '%z'
        else:
            dt = dt.astimezone(pytz.utc)
    # else, a naive datetime, we'll just have to assume it's UTC!

    return dt.strftime('%Y-%m-%d{}{}{}'.format(sep, timecomp, tzcomp))


def _format_timespec(dt, timespec):
    if timespec == 'auto':
        if not dt.microsecond:
            timespec = 'seconds'
        else:
            timespec = 'microseconds'

    if timespec == 'hours':
        return '%H'
    elif timespec == 'minutes':
        return '%H:%M'
    elif timespec == 'seconds':
        return '%H:%M:%S'
    elif timespec == 'milliseconds':
        msec = '{:03}'.format(math.floor(dt.microsecond / 1000))
        return '%H:%M:%S.{}'.format(msec)
    elif timespec == 'microseconds':
        return '%H:%M:%S.%f'
    else:
        raise ValueError('Not a valid `timespec`: {}'.format(timespec))


def isoformat_tzinfo(dt, sep='T', timespec='auto'):
    """FIXME: Document"""
    if isinstance(dt, datetime.datetime):
        return isoformat(dt, sep=sep, timespec=timespec, include_tz=True)
    else:
        return dt


def isoformat_tzless(dt, sep='T', timespec='auto'):
    """FIXME: Document"""
    if isinstance(dt, datetime.datetime):
        return isoformat(dt, sep=sep, timespec=timespec, include_tz=False)
    else:
        return dt


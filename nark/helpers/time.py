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
    'get_day_end',
    'end_day_to_datetime',
    'validate_start_end_range',
    'must_be_datetime_or_relative',
    'isoformat',
    'isoformat_tzinfo',
    'isoformat_tzless',
]


def get_day_end(config):
    """
    Get the day end time given the day start. This assumes full 24h day.

    Args:
        config (dict): Configdict. Needed to extract ``day_start``.

    Note:
        This is merely a convenience funtion so we do not have to deduct
        this from ``day_start`` by hand all the time.
    """
    day_start = config['day_start'] or '00:00'
    day_start_datetime = datetime.datetime.combine(
        datetime.date.today(), day_start,
    )
    day_end_datetime = day_start_datetime - datetime.timedelta(seconds=1)
    return day_end_datetime.time()


def end_day_to_datetime(end_day, config):
    """
    Convert a given end day to its proper datetime.

    This is non trivial because of variable ``day_start``. We want to make sure
    that even if an 'end day' is specified the actual point in time may reach
    into the following day.

    Args:
        end (datetime.date): Raw end date that is to be adjusted.
        config: Controller config containing information on when a workday starts.

    Returns:
        datetime.datetime: The endday as a adjusted datetime object.

    Example:
        Given a ``day_start`` of ``5:30`` and end date of ``2015-04-01`` we
        actually want to consider even points in time up to ``2015-04-02 5:29``.
        That is to represent that a *work day* does not match *calendar days*.

    Note:
        An alternative implementation for the similar problem in legacy hamster:
            ``hamster.storage.db.Storage.__get_todays_facts``.
    """
    day_start_time = config['day_start'] or '00:00'
    day_end_time = get_day_end(config)

    if day_start_time == datetime.time(0, 0, 0):
        end = datetime.datetime.combine(end_day, day_end_time)
    else:
        end = datetime.datetime.combine(end_day, day_end_time)
        end += datetime.timedelta(days=1)
    return end


def validate_start_end_range(range_tuple):
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


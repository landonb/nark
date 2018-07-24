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

import lazy_import
# Profiling: load pytz: ~ 0.002 secs.
pytz = lazy_import.lazy_module('pytz')


__all__ = [
    'isoformat',
    'isoformat_tzinfo',
    'isoformat_tzless',
]


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
    def _isoformat(dt, sep, timespec, include_tz):
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

    return _isoformat(dt, sep, timespec, include_tz)


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


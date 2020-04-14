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

"""This module provides several time-related convenience functions."""

from gettext import gettext as _

import datetime
import re


__all__ = (
    'datetime_from_clock_prior',
    'datetime_from_clock_after',
    'day_end_datetime',
    'day_end_time',
    'must_be_datetime_or_relative',
    'must_not_start_after_end',
    'parse_clock_time',
    'RE_PATTERN_RELATIVE_CLOCK',
    'RE_PATTERN_RELATIVE_DELTA',
)


# ***

def datetime_from_clock_prior(dt_relative, clock_time):
    # FIXME/MEH/2018-05-21 11:32: (lb): I'm guessing this doesn't work
    # across the "fold", e.g., 2 AM on daylight savings "fall back"
    # occurs twice, and in Python, the first time, fold=0, and the
    # second time, fold=1.
    new_dt = dt_relative.replace(
        hour=int(clock_time[0]),
        minute=int(clock_time[1]),
        second=int(clock_time[2]),
    )
    if new_dt > dt_relative:
        new_dt -= datetime.timedelta(days=1)
    return new_dt


def datetime_from_clock_after(dt_relative, clock_time):
    # FIXME/MEH/2018-05-21 11:32: (lb): Ignoring so-called "fold"/DST issue.
    new_dt = dt_relative.replace(
        hour=int(clock_time[0]),
        minute=int(clock_time[1]),
        second=int(clock_time[2]),
    )
    if new_dt < dt_relative:
        new_dt += datetime.timedelta(days=1)
    return new_dt


# ***

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


# ***

# (lb) See comment atop pattern_date in parse_time about allowing
#   \d{4} (without :colon). Here's the stricter pattern:
#    '^(?P<hours>\d{2}):(?P<minutes>\d{2})$'
# - Note that colons (':') are used to separate parts.
RE_PATTERN_RELATIVE_CLOCK = re.compile(
    '^(?P<hours>\d{1,2}):?(?P<minutes>\d{2})(:(?P<seconds>\d{2}))?$'
)


# HARDCODED: There's an 'h' and 'm' in this regex.
# FIXME: (lb): The 'h' and 'm' are not part of i18n, not l10n-friendly.
RE_PATTERN_RELATIVE_DELTA = re.compile(
    '^(?P<signage>[-+])?((?P<hours>\d+)h)?((?P<minutes>\d{1,2})m?)?$'
)


def must_be_datetime_or_relative(dt):
    """FIXME: Document"""
    if isinstance(dt, datetime.datetime):
        # FIXME: (lb): I've got milliseconds in my store data!!
        #        So this little hack kludge-fixes the problem;
        #        perhaps someday I'll revisit this and really
        #        figure out what's going on.
        return dt.replace(microsecond=0)
    elif not dt or isinstance(dt, str):
        if (
            dt and not (
                # NOTE: re.match checks for a match only at the beginning of the string.
                RE_PATTERN_RELATIVE_CLOCK.match(dt)
                or RE_PATTERN_RELATIVE_DELTA.match(dt)
            )
        ):
            raise TypeError(_(
                'Expected time entry to indicate relative time, not: {}'
            ).format(dt))
        return dt
    raise TypeError(_(
        "Time entry not `datetime`, relative string, or `None`, but: {}"
    ).format(type(dt)))


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
    if (
        not parsed_ct
        or (int(parsed_ct[0]) < 0 or int(parsed_ct[0]) > 24)
        or (int(parsed_ct[1]) < 0 or int(parsed_ct[1]) > 59)
        or (int(parsed_ct[2]) < 0 or int(parsed_ct[2]) > 59)
    ):
        parsed_ct = None
    return parsed_ct


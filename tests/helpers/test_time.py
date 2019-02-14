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

from __future__ import absolute_import, unicode_literals

import datetime

import pytest
from freezegun import freeze_time
from nark.helpers import fact_time, parse_time
from nark.helpers.parse_errors import ParserInvalidDatetimeException


class TestGetDayEnd(object):
    @pytest.mark.parametrize(('day_start', 'expectation'), [
        (datetime.time(0, 0, 0), datetime.time(23, 59, 59)),
        (datetime.time(5, 30, 0), datetime.time(5, 29, 59)),
        (datetime.time(23, 59, 59), datetime.time(23, 59, 58)),
        (datetime.time(14, 44, 23), datetime.time(14, 44, 22)),
    ])
    def test_various_day_start_times(self, base_config, day_start, expectation):
        """Ensure that resulting end times match our expectation given ``day_start``-"""
        base_config['day_start'] = day_start
        assert fact_time.day_end_time(day_start) == expectation


class TestEndDayToDatetime(object):
    @pytest.mark.parametrize(
        ('day_start', 'expectation'),
        [
            (datetime.time(0, 0, 0), datetime.datetime(2015, 4, 15, 23, 59, 59)),
            (datetime.time(5, 30, 0), datetime.datetime(2015, 4, 16, 5, 29, 59)),
            (datetime.time(23, 59, 59), datetime.datetime(2015, 4, 16, 23, 59, 58)),
            (datetime.time(14, 44, 23), datetime.datetime(2015, 4, 16, 14, 44, 22)),
        ],
    )
    def test_same_end_day_various_day_starts(self, day_start, expectation):
        """
        Ensure that resulting ``end datetimes`` match our expectation given ``day_end``
        """
        end_day = datetime.datetime(2015, 4, 15)
        assert fact_time.day_end_datetime(end_day, day_start) == expectation


@freeze_time('2015-12-10 12:30')
class TestParseTime(object):
    @pytest.mark.parametrize(('time', 'expectation'), [
        ('18:55', datetime.datetime(2015, 12, 9, 18, 55)),
        ('18:55:34', datetime.datetime(2015, 12, 9, 18, 55, 34)),
        ('2014-12-10', datetime.datetime(2014, 12, 10, 0, 0)),
        ('2015-10-02 18:12', datetime.datetime(2015, 10, 2, 18, 12)),
        ('2015-10-02 18:12:33', datetime.datetime(2015, 10, 2, 18, 12, 33)),
    ])
    def test_parse_dated_valid_times(self, time, expectation):
        """Make sure that given times are parsed as expected."""
        parsed = parse_time.parse_dated(time, time_now=datetime.datetime.now())
        assert parsed == expectation

    @pytest.mark.parametrize('time', ['18 55', '18:555', '2014 01 04 12:30'])
    def test_parse_dated_invalid_times(self, time):
        """Ensure that invalid times throw an exception."""
        with pytest.raises(ParserInvalidDatetimeException):
            # F841 local variable 'parsed_' is assigned to but never used
            parsed_ = parse_time.parse_dated(  # noqa: F841
                time, time_now=datetime.datetime.now(), cruftless=True,
            )
            assert False  # Unreachable.


class TestValidateStartEndRange(object):
    """Unittests for validation function."""

    @pytest.mark.parametrize('range', (
        (datetime.datetime(2016, 12, 1, 12, 30), datetime.datetime(2016, 12, 1, 12, 45)),
        (datetime.datetime(2016, 1, 1, 12, 30), datetime.datetime(2016, 12, 1, 12, 45)),
        (datetime.datetime(2016, 1, 1, 12, 30), datetime.datetime(2016, 12, 1, 1, 45)),
    ))
    def test_valid_ranges(self, range):
        """Make sure that ranges with end > start pass validation."""
        result = fact_time.must_not_start_after_end(range)
        assert result == range

    @pytest.mark.parametrize('range', (
        (datetime.datetime(2016, 12, 1, 12, 30), datetime.datetime(2016, 12, 1, 10, 45)),
        (datetime.datetime(2016, 1, 13, 12, 30), datetime.datetime(2016, 1, 1, 12, 45)),
    ))
    def test_invalid_ranges(self, range):
        """Make sure that ranges with start > end fail validation."""
        with pytest.raises(ValueError):
            fact_time.must_not_start_after_end(range)


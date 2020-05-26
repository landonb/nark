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

"""Fixtures that are of general use."""

import datetime

import pytest


# ***

# Fixture(s) for: tests/nark/test_reports.py.

@pytest.fixture
def list_of_facts(fact_factory):
    """
    Provide a factory that returns a list with given amount of Fact instances.

    The key point here is that these fact *do not overlap*!
    """
    def get_list_of_facts(number_of_facts):
        facts = []
        # MAYBE: Use controller.store.now ?
        old_start = datetime.datetime.utcnow().replace(microsecond=0)
        offset = datetime.timedelta(hours=4)
        for i in range(number_of_facts):
            start = old_start + offset
            facts.append(fact_factory(start=start))
            old_start = start
        return facts
    return get_list_of_facts


# ***

# (lb): Unused.

def convert_time_to_datetime(time_string):
    """
    Helper method.

    If given a %H:%M string, return a datetime.datetime object with todays
    date.
    """
    return datetime.datetime.combine(
        # MAYBE: Use controller.store.now ?
        datetime.datetime.utcnow().date(),
        datetime.datetime.strptime(time_string, "%H:%M").time()
    )


@pytest.fixture
def raw_fact_with_persistent_activity(persistent_activity):
    """A raw fact whichs 'activity' is already present in the db."""
    return (
        '12:00-14:14 {a.name}@{a.category.name}'.format(a=persistent_activity), {
            'start': convert_time_to_datetime('12:00'),
            'end': convert_time_to_datetime('14:14'),
            'activity': persistent_activity.name,
            'category': persistent_activity.category.name,
            'description': None,
        },
    )


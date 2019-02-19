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

"""Fixtures that are of general use."""

from __future__ import absolute_import, unicode_literals

import datetime

import faker as faker_
import pytest
from nark.control import NarkControl
from nark.manager import BaseStore
from pytest_factoryboy import register

from . import factories

register(factories.CategoryFactory)
register(factories.ActivityFactory)
register(factories.TagFactory)
register(factories.FactFactory)

faker = faker_.Faker()


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


# Controller


@pytest.yield_fixture
def controller(base_config):
    """Provide a basic controller."""
    # [TODO] Parametrize over all available stores.
    controller = NarkControl(base_config)
    yield controller
    controller.store.cleanup()


@pytest.fixture
def basestore(base_config):
    """Provide a generic ``storage.BaseStore`` instance using ``baseconfig``."""
    store = BaseStore(base_config)
    return store


# Categories
@pytest.fixture(params=(None, True,))
def category_valid_parametrized(
    request, category_factory, name_string_valid_parametrized,
):
    """Provide a variety of valid category fixtures."""
    if request.param:
        result = category_factory(name=name_string_valid_parametrized)
    else:
        result = None
    return result


@pytest.fixture
def category_valid_parametrized_without_none(
    request, category_factory, name_string_valid_parametrized,
):
    """
    Provide a parametrized category fixture but not ``None``.

    This fixuture will represent a wide array of potential name charsets as well
    but not ``category=None``.
    """
    return category_factory(name=name_string_valid_parametrized)


# Activities
@pytest.fixture
def activity_valid_parametrized(
    request,
    activity_factory,
    name_string_valid_parametrized,
    category_valid_parametrized,
    deleted_valid_parametrized,
):
    """Provide a huge array of possible activity versions. Including None."""
    return activity_factory(
        name=name_string_valid_parametrized,
        category=category_valid_parametrized,
        deleted=deleted_valid_parametrized,
    )


@pytest.fixture
def new_activity_values(category):
    """Return garanteed modified values for a given activity."""
    def modify(activity):
        return {
            'name': activity.name + 'foobar',
        }
    return modify


# Facts
@pytest.fixture
def fact_factory():
    """Return a factory class that generates non-persisting Fact instances."""
    return factories.FactFactory.build


@pytest.fixture
def fact():
    """Provide a randomized non-persistant Fact-instance."""
    return factories.FactFactory.build()


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


@pytest.fixture(params=('%M', '%H:%M', 'HHhMMm', ''))
def string_delta_style_parametrized(request):
    """Provide all possible format option for ``Fact().format_delta()``."""
    return request.param


@pytest.fixture
def today_fact(fact_factory):
    """Return a ``Fact`` instance that start and ends 'today'."""
    # MAYBE: Use controller.store.now ?
    start = datetime.datetime.utcnow()
    end = start + datetime.timedelta(minutes=30)
    return fact_factory(start=start, end=end)


@pytest.fixture
def not_today_fact(fact_factory):
    """Return a ``Fact`` instance that neither start nor ends 'today'."""
    # MAYBE: Use controller.store.now ?
    start = datetime.datetime.utcnow() - datetime.timedelta(days=2)
    end = start + datetime.timedelta(minutes=30)
    return fact_factory(start=start, end=end)


@pytest.fixture
def current_fact(fact_factory):
    """Provide a ``ongoing fact``. That is a fact that has started but not ended yet."""
    # MAYBE: Use controller.store.now ?
    return fact_factory(
        start=datetime.datetime.utcnow().replace(microsecond=0),
        end=None,
    )


@pytest.fixture(params=[
    '',
    '14:00 - 12:00 foo@bar',
    '12:00 - 14:00 @bar',
    '12:00:11 - 11:00:59 foo@bar',
])
def invalid_raw_fact_parametrized(request):
    """Return various invalid ``raw fact`` strings."""
    return request.param


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


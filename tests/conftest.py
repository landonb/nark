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

"""Global fixtures."""

from __future__ import absolute_import, unicode_literals

import datetime
import fauxfactory
import os.path
import pickle
import pytest
from pytest_factoryboy import register

from .nark import factories as lib_factories


register(lib_factories.CategoryFactory)
register(lib_factories.ActivityFactory)
register(lib_factories.TagFactory)
register(lib_factories.FactFactory)


## This fixture is used by ``test_helpers`` and ``test_storage``.
#@pytest.fixture
#def tmp_fact(base_config, fact_factory):
#    """Provide an existing 'ongoing fact'."""
#    # For reasons unknow ``fact.tags`` would be empty when using the ``fact``
#    # fixture.
#    fact = fact_factory()
#    fact.end = None
#    with open(base_config['tmpfile_path'], 'wb') as fobj:
#        pickle.dump(fact, fobj)
#    return fact


@pytest.fixture
def base_config(tmpdir):
    """Provide a generic baseline configuration."""
    return {
        'store': 'sqlalchemy',
        'day_start': datetime.time(hour=5, minute=30, second=0),
        #'day_start': '',
        'fact_min_delta': 60,
        #'fact_min_delta': 0,
        'db_engine': 'sqlite',
        'db_path': ':memory:',
        'sql_log_level': 'WARNING',
    }


# Helper fixtures
@pytest.fixture
def start_end_datetimes_from_offset():
    """Generate start/end datetime tuple with given offset in minutes."""
    def generate(offset):
        # MAYBE: Use controller.store.now ?
        #end = datetime.datetime.now()
        end = datetime.datetime.utcnow()
        start = end - datetime.timedelta(minutes=offset)
        return (start, end)
    return generate


@pytest.fixture(params=(True, False))
def bool_value_parametrized(request):
    """
    Return a parametrized boolean value.

    This is usefull to easily parametrize tests using flags.
    """
    return request.param


# Attribute fixtures (non-parametrized)
@pytest.fixture
def name():
    """Randomized, valid but non-parametrized name string."""
    return fauxfactory.gen_utf8()


@pytest.fixture
def start_end_datetimes(start_end_datetimes_from_offset):
    """Return a start/end-datetime-tuple."""
    return start_end_datetimes_from_offset(15)


@pytest.fixture
def start_datetime():
    """Provide an arbitrary datetime."""
    # [TODO]
    # Fixtures using this could propably be refactored using a cleaner way.
    # MAYBE: Use controller.store.now ?
    #return datetime.datetime.now()
    return datetime.datetime.utcnow()


@pytest.fixture
def description():
    """Return a generic text suitable to mimic a ``Fact.description``."""
    return fauxfactory.gen_iplum()


# New value generation
@pytest.fixture
def new_category_values():
    """Return garanteed modified values for a given category."""
    def modify(category):
        return {
            'name': category.name + 'foobar',
        }
    return modify


@pytest.fixture
def new_tag_values():
    """Return garanteed modified values for a given tag."""
    def modify(tag):
        return {
            'name': tag.name + 'foobar',
        }
    return modify


@pytest.fixture
def new_fact_values(tag_factory, activity_factory):
    """Provide guaranteed different Fact-values for a given Fact-instance."""
    def modify(fact):
        if fact.end:
            end = fact.end - datetime.timedelta(days=10)
        else:
            end = None
        return {
            'activity': activity_factory(),
            'start': fact.start - datetime.timedelta(days=10),
            'end': end,
            'description': fact.description + 'foobar',
            'tags': set([tag_factory() for i in range(5)])
        }
    return modify


# Valid attributes parametrized
@pytest.fixture(params='cyrillic utf8'.split())
def name_string_valid_parametrized(request):
    """Provide a variety of strings that should be valid *names*."""
    return fauxfactory.gen_string(request.param)


@pytest.fixture(params=(None, ''))
def name_string_invalid_parametrized(request):
    """Provide a variety of strings that should be valid *names*."""
    return request.param


@pytest.fixture(params=(
    fauxfactory.gen_string('numeric'),
    fauxfactory.gen_string('alphanumeric'),
    fauxfactory.gen_string('utf8'),
    None,
))
def pk_valid_parametrized(request):
    """Provide a variety of valid primary keys.

    Note:
        At our current stage we do *not* make assumptions about the type of primary key.
        Of cause, this may be a different thing on the backend level!
    """
    return request.param


@pytest.fixture(params=(True, False, 0, 1, '', 'foobar'))
def deleted_valid_parametrized(request):
    """Return various valid values for the ``deleted`` argument."""
    return request.param


@pytest.fixture(params='alpha cyrillic latin1 utf8'.split())
def description_valid_parametrized(request):
    """Provide a variety of strings that should be valid *descriptions*."""
    return fauxfactory.gen_string(request.param)


@pytest.fixture(params='alpha cyrillic latin1 utf8'.split())
def tag_list_valid_parametrized(request):
    """Provide a variety of strings that should be valid *descriptions*."""
    return set([fauxfactory.gen_string(request.param) for i in range(4)])

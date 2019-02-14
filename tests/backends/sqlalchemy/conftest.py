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

"""Fixtures in order to test the SQLAlchemy backend."""

from __future__ import absolute_import, unicode_literals

import datetime
import os

import fauxfactory
import pytest
from nark.backends.sqlalchemy import objects
from nark.backends.sqlalchemy.storage import SQLAlchemyStore
from nark.items.activity import Activity
from nark.items.category import Category
from nark.items.fact import Fact
from nark.items.tag import Tag
from pytest_factoryboy import register
from sqlalchemy import create_engine, event

from . import common, factories

register(factories.AlchemyCategoryFactory)
register(factories.AlchemyActivityFactory)
register(factories.AlchemyTagFactory)
register(factories.AlchemyFactFactory)


# *** SQLAlchemy fixtures


def implement_transactional_support_fully(engine):
    """
    (lb): A hack to make SQLite SAVEPOINTs work, so that
    session.begin_nested() works, so that if code under
    test calls session.commit(), we can still rollback().
    See the madness explained at:

      http://docs.sqlalchemy.org/en/rel_1_0/dialects/sqlite.html#pysqlite-serializable
    """

    @event.listens_for(engine, "connect")
    def do_connect(dbapi_connection, connection_record):
        # disable pysqlite's emitting of the BEGIN statement entirely.
        # also stops it from emitting COMMIT before any DDL.
        dbapi_connection.isolation_level = None

    @event.listens_for(engine, "begin")
    def do_begin(conn):
        # emit our own BEGIN
        conn.execute("BEGIN")


# (lb): Use 'module' scope so that the Session is only configured once
# for all tests. (Note: I also tried `scope='session'`, which seemed to
# work similarly.)
@pytest.fixture(scope='module')
def alchemy_runner(request):
    """
    Bind an in-memory mock-db to the session object.

    The session object, common.Session, is a global that this module-scoped
    function sets up just once. And then for each test, we'll create a clean
    session to use for testing that we clean up after.

    This is pretty much straight from the factoryboi docs:

      https://factoryboy.readthedocs.io/en/latest/orms.html#sqlalchemy

    """
    engine = create_engine('sqlite:///:memory:')
    implement_transactional_support_fully(engine)
    objects.metadata.bind = engine
    objects.metadata.create_all(engine)
    common.Session.configure(bind=engine)


@pytest.fixture
def alchemy_session(request):
    """
    Create a new session for each test.

    Reset the database and remove it after each test.

    As suggested by the docs:

        [Using factory_boy with ORMs](
            http://factoryboy.readthedocs.org/en/latest/orms.html#sqlalchemy
        )
    """
    # (lb): 2018-08-22: If we don't create a new Session() for each test,
    # there's one test that triggers a warning, TestFactManager.test_get_all:
    #   /home/user/.virtualenvs/dob/lib/python3.5/site-packages/
    #     sqlalchemy/orm/scoping.py:102: SAWarning: At least one scoped session
    #     is already present.  configure() can not affect sessions that have
    #     already been created.
    # Prepare a new, clean session for each test, lest SQLAlchemy complain.
    session = common.Session()

    # Rather than mock session.commit, use a nested transaction, otherwise
    # items' PK attrs will not be updated.
    # (lb): NOTE: I tried using subtransactions but those didn't work (albeit
    #   that was before I added the implement_transactional_support_fully hack).
    #       session.begin(subtransactions=True)  # (lb): Didn't work for me.
    # This works, but only after having hacked pysqlite to emit BEGIN ourselves.
    session.begin_nested()

    def fin():
        # "Rollback the session => no changes to the database."
        session.rollback()
        # (lb): Call rollback() twice. (For some reason one test,
        # TestFactManager.test_get_all, has five of each item in
        # the db after it runs, and after we can rollback once.
        # Which to me doesn't make sense. But whatever I'm only
        # human, I don't need to understand _everything_.)
        #
        # You can see for yourself with a conditional breakpoint, e.g.,
        #
        #   if session.query('name from categories;').all(): import pdb;pdb.set_trace()
        #
        # (lb): I'm not sure that we need to close, but so far hasn't hurt.
        session.close()
        # "Remove it, so that the next test gets a new Session()."
        common.Session.remove()

    request.addfinalizer(fin)

    return session


@pytest.fixture(params=[
    fauxfactory.gen_utf8(),
    fauxfactory.gen_alphanumeric(),
    ':memory:',
])
def db_path_parametrized(request, tmpdir):
    """Parametrized database paths."""
    if request.param == ':memory:':
        path = request.param
    else:
        path = os.path.join(tmpdir.strpath, request.param)
    return path


@pytest.fixture
def alchemy_config(request, base_config):
    """Provide a config that is suitable for sqlalchemy stores."""
    config = base_config.copy()
    config.update({
        'store': 'sqlalchemy',
        'db_engine': 'sqlite',
        'db_path': ':memory:',
    })
    return config


@pytest.fixture(
    params=(
        # SQLite
        {
            'db_engine': 'sqlite',
            'db_path': ':memory:',
        },
        # Non-SQLite
        {
            'db_engine': 'postgres',
            'db_host': fauxfactory.gen_ipaddr(),
            'db_port': fauxfactory.gen_integer(),
            'db_name': fauxfactory.gen_utf8(),
            'db_user': fauxfactory.gen_utf8(),
            'db_password': fauxfactory.gen_utf8(),
        },
        {
            'db_engine': 'postgres',
            'db_host': fauxfactory.gen_ipaddr(),
            'db_name': fauxfactory.gen_utf8(),
            'db_user': fauxfactory.gen_utf8(),
            'db_password': fauxfactory.gen_utf8(),
        },
    ),
)
def alchemy_config_parametrized(request, alchemy_config):
    """
    Provide a parametrized config that is suitable for sqlalchemy stores.

    We need to build our expectation dynamically if we want to use faked config values.
    """
    config = alchemy_config.copy()
    config.update(request.param)
    if request.param['db_engine'] == 'sqlite':
        expectation = '{engine}:///{path}'.format(
            engine=request.param['db_engine'], path=request.param['db_path'])
    else:
        port = request.param.get('db_port', '')
        if port:
            port = ':{}'.format(port)
        expectation = '{engine}://{user}:{password}@{host}{port}/{name}'.format(
            engine=request.param['db_engine'], user=request.param['db_user'],
            password=request.param['db_password'], host=request.param['db_host'],
            port=port, name=request.param['db_name'])
    return (config, expectation)


@pytest.fixture(params=(
    {'db_engine': None,
     'db_path': None},
    # sqlite
    {'db_engine': 'sqlite',
     'db_path': None},
    {'db_engine': 'sqlite',
     'db_path': ''},
    # Non-sqlite
    {'db_engine': 'postgres',
     'db_host': None,
     'db_name': fauxfactory.gen_utf8(),
     'db_user': fauxfactory.gen_utf8(),
     'db_password': fauxfactory.gen_alphanumeric()},
    {'db_engine': 'postgres',
     'db_host': fauxfactory.gen_ipaddr(),
     'db_name': '',
     'db_user': fauxfactory.gen_utf8(),
     'db_password': fauxfactory.gen_alphanumeric()},
    {'db_engine': 'postgres',
     'db_host': fauxfactory.gen_ipaddr(),
     'db_name': fauxfactory.gen_utf8(),
     'db_user': '',
     'db_password': fauxfactory.gen_alphanumeric()},
    {'db_engine': 'postgres',
     'db_host': fauxfactory.gen_ipaddr(),
     'db_name': fauxfactory.gen_utf8(),
     'db_user': fauxfactory.gen_utf8(),
     'db_password': ''}
))
def alchemy_config_missing_store_config_parametrized(request, alchemy_config):
    """
    Provide an alchemy config containing invalid key/value pairs for
    store initialization.
    """
    config = alchemy_config.copy()
    config.update(request.param)
    return config


@pytest.fixture
def alchemy_store(request, alchemy_config, alchemy_runner, alchemy_session):
    """
    Provide a SQLAlchemyStore that uses our test-session.

    Note:
        The engine created as part of the store.__init__() goes simply unused.
    """
    # (lb): There was a note from hamster-lib:
    #   "probably want this to autouse=True"
    # but after reviewing the docs, I'm guessing there's no point, because an
    # autouse fixture does not return a value, and the code we'd be replacing
    # -- alchemy_session -- creates the common.Session() object that each test
    # uses. So if we removed alchemy_session from the parameters for each test,
    # each test would still have to find the session object somehow.
    #   https://docs.pytest.org/en/latest/fixture.html#autouse-fixtures-xunit-setup-on-steroids
    store = SQLAlchemyStore(alchemy_config)
    store.standup(alchemy_session)
    return store


@pytest.fixture
def alchemy_activity_deleted(alchemy_activity_factory):
    alchemy_activity = alchemy_activity_factory()
    alchemy_activity.deleted = True
    return alchemy_activity


# Instance sets
# Convenience fixtures that provide multitudes of certain alchemy instances.
@pytest.fixture
def set_of_categories(alchemy_category_factory):
    """Provide a number of perstent facts at once."""
    return [alchemy_category_factory() for i in range(5)]


@pytest.fixture
def set_of_tags(alchemy_tag_factory):
    """Provide a number of perstent facts at once."""
    return [alchemy_tag_factory() for i in range(5)]


@pytest.fixture
def set_of_alchemy_facts(start_datetime, alchemy_fact_factory):
    """
    Provide a multitude of generic persistent facts.

    Facts have one day offset from each other and last 20 minutes each.
    """
    start = start_datetime
    result = []
    for i in range(5):
        end = start + datetime.timedelta(minutes=20)
        fact = alchemy_fact_factory(start=start, end=end)
        result.append(fact)
        start = start + datetime.timedelta(days=1)
    return result


# Fallback nark object and factory fixtures. Unless we know how factories
# interact.
@pytest.fixture
def category_factory(request, name):
    """Provide a ``nark.Category`` factory."""
    def generate():
        return Category(name, None)
    return generate


@pytest.fixture
def category(request, category_factory):
    """Provide a randomized ``nark.Category`` instance."""
    return category_factory()


@pytest.fixture
def tag_factory(request, name):
    """Provide a ``nark.Tag`` factory."""
    def generate():
        return Tag(name, None)
    return generate


@pytest.fixture
def tag(request, tag_factory):
    """Provide a randomized ``nark.Tag`` instance."""
    return tag_factory()


@pytest.fixture
def activity_factory(request, name, category_factory):
    """
    Provide a ``nark.Activity`` factory.

    Note:
        * The returned activity will have a *new* category associated as well.
        * Values are randomized but *not parametrized*.
    """
    def generate():
        category = category_factory()
        return Activity(name, pk=None, category=category, deleted=False)
    return generate


@pytest.fixture
def activity(request, activity_factory):
    """Provide a randomized ``nark.Activity`` instance."""
    return activity_factory()


@pytest.fixture
def fact_factory(
    request, activity_factory, tag_factory, start_end_datetimes, description,
):
    """
    Provide a ``nark.Fact`` factory.

    Note:
        * The returned fact will have a *new* activity (and by consequence category)
          associated as well.
        * Values are randomized but *not parametrized*.
    """
    def generate():
        activity = activity_factory()
        tags = set([tag_factory() for i in range(1)])
        start, end = start_end_datetimes
        fact = Fact(activity, start, end, pk=None, description=description, tags=tags)
        return fact
    return generate


@pytest.fixture
def fact(request, fact_factory):
    """Return a randomized ``nark.Fact`` instance."""
    return fact_factory()


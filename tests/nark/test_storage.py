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


# ***

class TestBaseStore():
    def test_cleanup(self, basestore):
        with pytest.raises(NotImplementedError):
            basestore.cleanup()


# ***

class TestCategoryManager():
    def test_add(self, basestore, category):
        with pytest.raises(NotImplementedError):
            basestore.categories._add(category)

    def test_update(self, basestore, category):
        with pytest.raises(NotImplementedError):
            basestore.categories._update(category)

    def test_remove(self, basestore, category):
        with pytest.raises(NotImplementedError):
            basestore.categories.remove(category)

    def test_get_invalid_pk(self, basestore):
        with pytest.raises(NotImplementedError):
            basestore.categories.get(12)

    def test_get_invalid_pk_type(self, basestore):
        with pytest.raises(NotImplementedError):
            basestore.categories.get_by_name('fooo')

    def test_save_wrong_type(self, basestore, category):
        with pytest.raises(TypeError):
            basestore.categories.save([])

    def test_save_new(self, basestore, category, mocker):
        """Make sure that saving an new category calls ``__add``."""
        basestore.categories._add = mocker.MagicMock(return_value=category)
        try:
            basestore.categories.save(category)
        except NotImplementedError:
            pass
        assert basestore.categories._add.called

    def test_save_existing(self, basestore, category, mocker):
        category.pk = 0
        basestore.categories._update = mocker.MagicMock(return_value=category)
        try:
            basestore.categories.save(category)
        except NotImplementedError:
            pass
        assert basestore.categories._update.called

    def test_get_or_create_existing(self, basestore, category, mocker):
        """Make sure the category is beeing looked up and no new one is created."""
        basestore.categories.get_by_name = mocker.MagicMock(return_value=category)
        basestore.categories._add = mocker.MagicMock(return_value=category)
        try:
            basestore.categories.get_or_create(category.name)
        except NotImplementedError:
            pass
        assert basestore.categories._add.called is False
        assert basestore.categories.get_by_name.called

    def test_get_or_create_new_category(self, basestore, category, mocker):
        """Make sure the category is beeing looked up and new one is created."""
        basestore.categories._add = mocker.MagicMock(return_value=category)
        basestore.categories.get_by_name = mocker.MagicMock(side_effect=KeyError)
        try:
            basestore.categories.get_or_create(category.name)
        except NotImplementedError:
            pass
        assert basestore.categories.get_by_name.called
        assert basestore.categories._add.called

    def test_get_all(self, basestore):
        with pytest.raises(NotImplementedError):
            basestore.categories.get_all()


# ***

class TestActivityManager:
    def test_save_new(self, basestore, activity, mocker):
        """Make sure that saving an new activity calls ``_add``."""
        basestore.activities._add = mocker.MagicMock(return_value=activity)
        try:
            basestore.activities.save(activity)
        except NotImplementedError:
            pass
        assert basestore.activities._add.called

    def test_save_existing(self, basestore, activity, mocker):
        """Make sure that saving an existing activity calls ``_update``."""
        activity.pk = 0
        basestore.activities._update = mocker.MagicMock(return_value=activity)
        try:
            basestore.activities.save(activity)
        except NotImplementedError:
            pass
        assert basestore.activities._update.called

    def test_get_or_create_existing(self, basestore, activity, mocker):
        basestore.activities.get_by_composite = mocker.MagicMock(return_value=activity)
        basestore.activities.save = mocker.MagicMock(return_value=activity)
        result = basestore.activities.get_or_create(activity)
        assert result.name == activity.name
        assert basestore.activities.save.called is False

    def test_get_or_create_new(self, basestore, activity, mocker):
        basestore.activities.get_by_composite = mocker.MagicMock(side_effect=KeyError())
        basestore.activities.save = mocker.MagicMock(return_value=activity)
        result = basestore.activities.get_or_create(activity)
        assert result.name == activity.name
        assert basestore.activities.save.called is True

    def test_add(self, basestore, activity):
        with pytest.raises(NotImplementedError):
            basestore.activities._add(activity)

    def test_update(self, basestore, activity):
        with pytest.raises(NotImplementedError):
            basestore.activities._update(activity)

    def test_remove(self, basestore, activity):
        with pytest.raises(NotImplementedError):
            basestore.activities.remove(activity)

    def test_get_by_composite(self, basestore, activity):
        with pytest.raises(NotImplementedError):
            basestore.activities.get_by_composite(activity.name, activity.category)

    def test_get(self, basestore):
        with pytest.raises(NotImplementedError):
            basestore.activities.get(12)

    def test_get_all(self, basestore):
        with pytest.raises(NotImplementedError):
            basestore.activities.get_all()


# ***

class TestTagManager():
    def test_add(self, basestore, tag):
        with pytest.raises(NotImplementedError):
            basestore.tags._add(tag)

    def test_update(self, basestore, tag):
        with pytest.raises(NotImplementedError):
            basestore.tags._update(tag)

    def test_remove(self, basestore, tag):
        with pytest.raises(NotImplementedError):
            basestore.tags.remove(tag)

    def test_get_invalid_pk(self, basestore):
        with pytest.raises(NotImplementedError):
            basestore.tags.get(12)

    def test_get_invalid_pk_type(self, basestore):
        with pytest.raises(NotImplementedError):
            basestore.tags.get_by_name('fooo')

    def test_save_wrong_type(self, basestore, tag):
        with pytest.raises(TypeError):
            basestore.tags.save([])

    def test_save_new(self, basestore, tag, mocker):
        """Make sure that saving an new tag calls ``__add``."""
        basestore.tags._add = mocker.MagicMock(return_value=tag)
        try:
            basestore.tags.save(tag)
        except NotImplementedError:
            pass
        assert basestore.tags._add.called

    def test_save_existing(self, basestore, tag, mocker):
        tag.pk = 0
        basestore.tags._update = mocker.MagicMock(return_value=tag)
        try:
            basestore.tags.save(tag)
        except NotImplementedError:
            pass
        assert basestore.tags._update.called

    def test_get_or_create_existing(self, basestore, tag, mocker):
        """Make sure the tag is beeing looked up and no new one is created."""
        basestore.tags.get_by_name = mocker.MagicMock(return_value=tag)
        basestore.tags._add = mocker.MagicMock(return_value=tag)
        try:
            basestore.tags.get_or_create(tag.name)
        except NotImplementedError:
            pass
        assert basestore.tags._add.called is False
        assert basestore.tags.get_by_name.called

    def test_get_or_create_new_tag(self, basestore, tag, mocker):
        """Make sure the tag is beeing looked up and new one is created."""
        basestore.tags._add = mocker.MagicMock(return_value=tag)
        basestore.tags.get_by_name = mocker.MagicMock(side_effect=KeyError)
        try:
            basestore.tags.get_or_create(tag.name)
        except NotImplementedError:
            pass
        assert basestore.tags.get_by_name.called
        assert basestore.tags._add.called

    def test_get_all(self, basestore):
        with pytest.raises(NotImplementedError):
            basestore.tags.get_all()


# ***

class TestFactManager:
    def test_save_endless_fact(self, basestore, fact, mocker):
        """
        Make sure that passing a fact without end (aka 'endless, ongoing fact')
        triggers the right method.
        """
        magic_fact = {}
        basestore.facts._add = mocker.MagicMock(return_value=magic_fact)
        fact.end = None
        new_fact = basestore.facts.save(fact)
        assert basestore.facts._add.called
        assert new_fact is magic_fact

    def test_save_to_brief_fact(self, basestore, fact):
        """Ensure that a fact with too small of a time delta raises an exception."""
        delta = datetime.timedelta(seconds=(basestore.config['fact_min_delta'] - 1))
        fact.end = fact.start + delta
        with pytest.raises(ValueError):
            basestore.facts.save(fact)

    def test_add(self, basestore, fact):
        with pytest.raises(NotImplementedError):
            basestore.facts._add(fact)

    def test_update(self, basestore, fact):
        with pytest.raises(NotImplementedError):
            basestore.facts._update(fact)

    def test_remove(self, basestore, fact):
        with pytest.raises(NotImplementedError):
            basestore.facts.remove(fact)

    def test_get(self, basestore):
        with pytest.raises(NotImplementedError):
            basestore.facts.get(12)

    @pytest.mark.parametrize(('since', 'until', 'filter_term', 'expectation'), [
        (None, None, '', {
            'since': None,
            'until': None}),
        # Various since info.
        (datetime.date(2014, 4, 1), None, '', {
            'since': datetime.datetime(2014, 4, 1, 5, 30, 0),
            'until': None}),
        (datetime.time(13, 40, 25), None, '', {
            'since': datetime.datetime(2015, 4, 1, 13, 40, 25),
            'until': None}),
        (datetime.datetime(2014, 4, 1, 13, 40, 25), None, '', {
            'since': datetime.datetime(2014, 4, 1, 13, 40, 25),
            'until': None}),
        # Various until info.
        (None, datetime.date(2014, 2, 1), '', {
            'since': None,
            'until': datetime.datetime(2014, 2, 2, 5, 29, 59)}),
        (None, datetime.time(13, 40, 25), '', {
            'since': None,
            'until': datetime.datetime(2015, 4, 1, 13, 40, 25)}),
        (None, datetime.datetime(2014, 4, 1, 13, 40, 25), '', {
            'since': None,
            'until': datetime.datetime(2014, 4, 1, 13, 40, 25)}),
    ])
    @freeze_time('2015-04-01 18:00')
    def test_get_all_various_since_and_until_times(
        self, basestore, mocker, since, until, filter_term, expectation,
    ):
        """Test that time conversion matches expectations."""
        basestore.facts._get_all = mocker.MagicMock()
        basestore.facts.get_all(since=since, until=until, search_term=filter_term)
        assert basestore.facts._get_all.called
        assert basestore.facts._get_all.call_args[1] == {
            'since': expectation['since'],
            'until': expectation['until'],
            'search_term': filter_term,
        }

    @pytest.mark.parametrize(
        ('since', 'until'),
        [
            (
                datetime.date(2015, 4, 5),
                datetime.date(2012, 3, 4),
            ),
            (
                datetime.datetime(2015, 4, 5, 18, 0, 0),
                datetime.datetime(2012, 3, 4, 19, 0, 0),
            ),
        ],
    )
    def test_get_all_until_before_since(self, basestore, mocker, since, until):
        """Test that we throw an exception if passed until time is before since time."""
        with pytest.raises(ValueError):
            basestore.facts.get_all(since, until)

    @pytest.mark.parametrize(('since', 'until'), [
        (datetime.date(2015, 4, 5), '2012-03-04'),
        ('2015-04-05 18:00:00', '2012-03-04 19:00:00'),
    ])
    def test_get_all_invalid_date_types(self, basestore, mocker, since, until):
        """Test that we throw an exception if we recieve invalid date/time objects."""
        with pytest.raises(TypeError):
            basestore.facts.get_all(since, until)

    @freeze_time('2015-10-03 14:45')
    def test_get_today(self, basestore, mocker):
        """Make sure that method uses apropiate timeframe."""
        basestore.facts.get_all = mocker.MagicMock(return_value=[])
        result = basestore.facts.get_today()
        assert result == []
        assert (
            basestore.facts.get_all.call_args[1] == {
                'since': datetime.datetime(2015, 10, 3, 5, 30, 0),
                'until': datetime.datetime(2015, 10, 4, 5, 29, 59),
            }
        )

    def test__get_all(self, basestore):
        with pytest.raises(NotImplementedError):
            basestore.facts._get_all()

    # FIXME: See comment in function docstring: there's a problem with Fact.start
    #   that's being masked -- for now -- with the (currently) future freeze_time.
    @freeze_time('2019-02-01 18:00')
    @pytest.mark.parametrize('hint', (
        None,
        datetime.timedelta(minutes=10),
        datetime.timedelta(minutes=300),
        datetime.timedelta(seconds=-10),
        datetime.timedelta(minutes=-10),
        datetime.datetime(2019, 2, 1, 19),
        datetime.datetime(2019, 2, 1, 17, 59),
    ))
    def test_stop_current_fact_with_hint(
        self, basestore, base_config, endless_fact, hint, mocker,
    ):
        """
        Make sure we can stop an 'ongoing fact' and that it will have an end set.

        Please note that ever so often it may happen that the factory generates
        a endless_fact with ``Fact.start`` after our mocked today-date. In order to avoid
        confusion the easies fix is to make sure the mock-today is well in the future.
        """
        # NOTE: The `fact` fixture simply adds a second Fact to the db, after
        #       having added the endless_fact Fact.
        if hint:
            if isinstance(hint, datetime.datetime):
                expected_end = hint
            else:
                expected_end = datetime.datetime(2019, 2, 1, 18) + hint
        else:
            # NOTE: Because freeze_time, datetime.now() === datetime.utcnow().
            expected_end = datetime.datetime.now().replace(microsecond=0)
        basestore.facts.endless = mocker.MagicMock(return_value=[endless_fact])
        basestore.facts._add = mocker.MagicMock()
        basestore.facts.stop_current_fact(hint)
        assert basestore.facts.endless.called
        assert basestore.facts._add.called
        fact_to_be_added = basestore.facts._add.call_args[0][0]
        assert fact_to_be_added.end == expected_end
        fact_to_be_added.end = None
        assert fact_to_be_added == endless_fact

    def test_stop_current_fact_invalid_offset_hint(
        self, basestore, endless_fact, mocker,
    ):
        """
        Make sure that stopping with an offset hint that results in end > start
        raises an error.
        """
        basestore.facts.endless = mocker.MagicMock(return_value=[endless_fact])
        now = datetime.datetime.now().replace(microsecond=0)
        offset = (now - endless_fact.start).total_seconds() + 100
        offset = datetime.timedelta(seconds=-1 * offset)
        with pytest.raises(ValueError):
            basestore.facts.stop_current_fact(offset)

    def test_stop_current_fact_invalid_datetime_hint(
        self, basestore, endless_fact, mocker,
    ):
        """
        Make sure that stopping with a datetime hint that results in end > start
        raises an error.
        """
        basestore.facts.endless = mocker.MagicMock(return_value=[endless_fact])
        with pytest.raises(ValueError):
            basestore.facts.stop_current_fact(
                endless_fact.start - datetime.timedelta(minutes=30),
            )

    def test_stop_current_fact_invalid_hint_type(
        self, basestore, endless_fact, mocker,
    ):
        """Make sure that passing an invalid hint type raises an error."""
        basestore.facts.endless = mocker.MagicMock(return_value=[endless_fact])
        with pytest.raises(TypeError):
            basestore.facts.stop_current_fact(str())

    def test_stop_current_fact_non_existing(self, basestore, mocker):
        """
        Make sure that trying to call stop when there is no 'endless fact'
        raises an error.
        """
        basestore.facts.endless = mocker.MagicMock(return_value=[])
        with pytest.raises(KeyError):
            basestore.facts.stop_current_fact()
            # KeyError: 'No ongoing Fact found.'

    def test_get_endless_fact_with_ongoing_fact(
        self, basestore, endless_fact, fact, mocker,
    ):
        """Make sure we return the 'ongoing_fact'."""
        basestore.facts.endless = mocker.MagicMock(return_value=[endless_fact])
        fact = basestore.facts.endless()
        assert fact == fact
        assert fact is fact

    def test_get_endless_fact_without_ongoing_fact(self, basestore, mocker):
        """Make sure that we raise a KeyError if ther is no 'ongoing fact'."""
        basestore.facts.endless = mocker.MagicMock(return_value=[])
        fact = basestore.facts.endless()
        assert fact == []

    def test_cancel_current_fact(self, basestore, endless_fact, fact, mocker):
        """Make sure we return the 'ongoing_fact'."""
        basestore.facts.endless = mocker.MagicMock(return_value=[endless_fact])
        basestore.facts.remove = mocker.MagicMock()
        result = basestore.facts.cancel_current_fact()
        assert basestore.facts.endless.called
        assert basestore.facts.remove.called
        assert result is endless_fact  # Because mocked.
        # FIXME: Where's the test that actually tests FactManager.endless()?

    def test_cancel_current_fact_without_endless_fact(self, basestore, mocker):
        """Make sure that we raise a KeyError if there is no 'ongoing fact'."""
        basestore.facts.endless = mocker.MagicMock(return_value=[])
        with pytest.raises(KeyError):
            basestore.facts.cancel_current_fact()
        assert basestore.facts.endless.called


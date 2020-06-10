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

import datetime

import pytest

from nark.backends.sqlalchemy.objects import AlchemyFact
from nark.backends.sqlalchemy.managers.fact import FactManager


class TestGatherFactManager():
    """"""

    def test_get_all(self, set_of_alchemy_facts, alchemy_store):
        results = alchemy_store.facts.get_all()
        assert len(results) == len(set_of_alchemy_facts)
        assert len(results) == alchemy_store.session.query(AlchemyFact).count()

    @pytest.mark.parametrize(('start_filter', 'end_filter'), (
        (10, 12),
        (10, None),
        (None, -12),
    ))
    def test_get_all_existing_facts_not_in_timerange(
        self,
        alchemy_store,
        alchemy_fact,
        bool_value_parametrized,
        start_filter,
        end_filter,
    ):
        """Make sure that a valid timeframe returns an empty list."""
        since, until = None, None
        if start_filter:
            since = alchemy_fact.start + datetime.timedelta(days=start_filter)
        if end_filter:
            until = alchemy_fact.start + datetime.timedelta(days=end_filter)

        results = alchemy_store.facts.get_all(
            since=since, until=until, partial=bool_value_parametrized,
        )
        assert results == []

    @pytest.mark.parametrize(('start_filter', 'end_filter'), (
        (-1, 5),
        (-1, None),
        (None, 5),
        (None, None),
    ))
    def test_get_all_existing_fact_fully_in_timerange(
        self,
        alchemy_store,
        alchemy_fact,
        bool_value_parametrized,
        start_filter,
        end_filter,
    ):
        """Ensure a fact fully within the timeframe is returned."""
        since, until = None, None
        if start_filter:
            since = alchemy_fact.start + datetime.timedelta(days=start_filter)
        if end_filter:
            until = alchemy_fact.start + datetime.timedelta(days=end_filter)

        results = alchemy_store.facts.get_all(
            since=since, until=until, partial=bool_value_parametrized,
        )
        # ANSWER/2018-05-05: (lb): This test is failing. When did it break?
        #                      assert results == [alchemy_fact]
        #                    - 2020-05-26: Probably when lazy_tags=False added.
        assert len(results) == 1
        assert str(results[0]) == str(alchemy_fact)

    @pytest.mark.parametrize(('start_filter', 'end_filter'), (
        # Fact.start is in time window.
        (None, 2),
        (-900, 2),
        # Fact.end is in time window.
        (5, None),
        (5, 900),
    ))
    def test_get_all_existing_fact_partialy_in_timerange(
        self,
        alchemy_store,
        alchemy_fact,
        bool_value_parametrized,
        start_filter,
        end_filter,
    ):
        """
        Test that a fact partially within timeframe is returned with
        ``partial=True`` only.
        """
        since, until = None, None
        if start_filter:
            since = alchemy_fact.start + datetime.timedelta(minutes=start_filter)
        if end_filter:
            until = alchemy_fact.start + datetime.timedelta(minutes=end_filter)
        results = alchemy_store.facts.get_all(
            since=since,
            until=until,
            partial=bool_value_parametrized,
            # Use lazy_tags=True, so that we can compare Fact objects.
            # - If lazy_tags=False, the query concatenates tag names to save
            #   time, and does not load Tag PKs, and each Fact object is setup
            #   with new Tags that do not have their PK set. As such, the
            #   comparison, `results == [alchemy_fact]`, won't work.
            #   (Alternatively, one could compare str(fact), which does not
            #   include IDs.)
            # - But when lazy_tags=True, this relies on SQLAlchemy magic that
            #   fetches a Fact's Tag items when the fact.tags attribute is read.
            #   It's slower (there's one additional SELECT for every fact.tags
            #   read) but more complete.
            lazy_tags=True,
        )
        if bool_value_parametrized:
            assert len(results) == 1
            assert str(results[0]) == str(alchemy_fact)
            assert results == [alchemy_fact]
        else:
            assert results == []

    def test_get_all_search_matches_description(
        self, alchemy_store, set_of_alchemy_facts,
    ):
        """Make sure facts with ``Fact.activity.name`` matching the term are returned."""
        assert len(set_of_alchemy_facts) == 5
        search_terms = [set_of_alchemy_facts[1].description]
        # Use lazy_tags=True so Tag.pk are set, and results == [...] works.
        results = alchemy_store.facts.get_all(
            search_terms=search_terms, lazy_tags=True,
        )
        assert len(results) == 1
        assert str(results[0]) == str(set_of_alchemy_facts[1])
        assert results == [set_of_alchemy_facts[1]]

    def test_get_all_search_matches_activity(self, alchemy_store, set_of_alchemy_facts):
        """Make sure facts with ``Fact.activity.name`` matching the term are returned."""
        assert len(set_of_alchemy_facts) == 5
        search_terms = [set_of_alchemy_facts[1].activity.name]
        # Use lazy_tags=True so Tag.pk are set, and results == [...] works.
        results = alchemy_store.facts.get_all(
            search_terms=search_terms, broad_match=True, lazy_tags=True,
        )
        assert len(results) == 1
        assert str(results[0]) == str(set_of_alchemy_facts[1])
        assert results == [set_of_alchemy_facts[1]]

    def test_get_all_search_matches_category(self, alchemy_store, set_of_alchemy_facts):
        """Make sure facts with ``Fact.category.name`` matching the term are returned."""
        assert len(set_of_alchemy_facts) == 5
        search_terms = [set_of_alchemy_facts[1].category.name]
        # Use lazy_tags=True so Tag.pk are set, and results == [...] works.
        results = alchemy_store.facts.get_all(
            search_terms=search_terms, broad_match=True, lazy_tags=True,
        )
        assert len(results) == 1
        assert str(results[0]) == str(set_of_alchemy_facts[1])
        assert results == [set_of_alchemy_facts[1]]

    # ***

    def test__get_all_no_query_terms_not_lazy(self, alchemy_store, set_of_alchemy_facts):
        """Verify basic FactManager.get_all finds the whole store."""
        assert len(set_of_alchemy_facts) == 5
        results = alchemy_store.facts.get_all(lazy_tags=False)
        assert len(results) == len(set_of_alchemy_facts)
        # (lb): The results list contain the same items, and the sort order is
        # the same, because the Fact.get_all sort defaults to 'start'. But the
        # lists are not equal, because the result Facts do not have the Tag PK.
        # That is, lazy_tags enables a quicker query that just concatenates tag
        # names, not bothering with the PK. So comparing lists will not work:
        #   assert results == set_of_alchemy_facts
        # but we can stringify and compare.
        assert str(results[0]) == str(set_of_alchemy_facts[0])
        # etc.

    def test__get_all_no_query_terms_yes_lazy(
        self, alchemy_store, set_of_alchemy_facts,
    ):
        """Verify basic FactManager.get_all finds the whole store."""
        assert len(set_of_alchemy_facts) == 5
        # Use lazy_tags=True so Tag.pk are set, and results == ... works.
        results = alchemy_store.facts.get_all(lazy_tags=True)
        # (lb): This is similar to the previous test, but now lazy_tags is True,
        # meaning, whenever we access a Tag item for the first time, SQLAlchemy
        # will fetch it from the database. But it also means that the Fact.tags
        # include PKs, so here, a direct list comparison is valid.
        assert len(results) == len(set_of_alchemy_facts)
        assert results == set_of_alchemy_facts

    def test__get_all_no_params_count(self, alchemy_store, set_of_alchemy_facts):
        """Verify FactManager.get_all count_results returns number of Facts."""
        assert len(set_of_alchemy_facts) == 5
        results = alchemy_store.facts.get_all(count_results=True)
        assert results == 5

    def test__get_all_include_stats_return_raw(
        self, alchemy_store, set_of_alchemy_facts,
    ):
        """Verify basic FactManager.get_all finds the whole store."""
        assert len(set_of_alchemy_facts) == 5
        results = alchemy_store.facts.get_all(
            include_stats=True,
            raw=True,
        )
        assert len(results) == 5
        # Each results is the Fact and the aggregate columns.
        fact_0, *cols_0 = results[0]
        assert len(cols_0) == len(FactManager.RESULT_GRP_INDEX)
        # Duration is days, and set_of_alchemy_facts are 20 mins. each.
        i_duration = FactManager.RESULT_GRP_INDEX['duration']
        # Ensure that the duration calculation is correct. (For instance,
        # if the SUM() aggregate happened before tags are coalesced, if a
        # Fact had three tags, the duration calculation would be three times
        # would it really should be.)
        assert round(cols_0[i_duration] * 24 * 60) == 20
        # The group_count when not grouping is 1. (And even if we did group,
        # faker seems to make it so all Activity, Category, and Tag names
        # are unique.)
        # FIXME/2020-05-25: Create Facts with the same Activity, and test aggregates.
        i_group_count = FactManager.RESULT_GRP_INDEX['group_count']
        assert cols_0[i_group_count] == 1
        # Because raw=True, the Tag objects were recreated, but without PKs.
        assert not fact_0.tags[0].pk

    def test__get_all_by_pk_with_stats_named(self, alchemy_store, set_of_alchemy_facts):
        """Verify QueryTerms.named_tuples returns attribute-accessible results."""
        assert len(set_of_alchemy_facts) == 5
        expect = set_of_alchemy_facts[3]
        results = alchemy_store.facts.get_all(
            named_tuples=True,
            include_stats=True,
            key=expect.pk,
        )
        assert len(results) == 1
        assert str(results[0].fact) == str(expect)
        assert results[0].group_count == 1
        # etc.

    def test__get_all_limit_offset(self, alchemy_store, set_of_alchemy_facts):
        """Verify FactManager.get_all count_results returns number of Facts."""
        assert len(set_of_alchemy_facts) == 5
        results = alchemy_store.facts.get_all(limit=2, offset=2, lazy_tags=True)
        assert len(results) == 2
        assert results == set_of_alchemy_facts[2:4]

    # ***

    def test__get_all_fails_on_unsupported_store(self, controller, alchemy_store):
        """Ensure get_all/GatherFactManager.gather raised on unsupported store type."""
        # MAYBE/2020-05-26: Add support for other data stores (other than SQLite),
        #   which requires using and wiring the appropriate DBMS-specific aggregate
        #   functions.
        #   - For now, dob is at least nice enough to print an error message.
        controller.store.config['db.engine'] += '_not'
        with pytest.raises(NotImplementedError) as excinfo:
            results = alchemy_store.facts.get_all()  # noqa: F841 local variable...
            assert False  # Unreachable.
        # See: must_support_db_engine_funcs.
        expect = 'This feature does not work with the current DBMS engine'
        assert str(excinfo.value).startswith(expect)


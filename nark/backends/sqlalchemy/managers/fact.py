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

from gettext import gettext as _

from datetime import datetime

from sqlalchemy import asc, case, desc, distinct, func
from sqlalchemy.sql.expression import and_, or_

from . import BaseAlchemyManager, query_apply_limit_offset, query_apply_true_or_not
from ....managers.fact import BaseFactManager
from ..objects import (
    AlchemyActivity,
    AlchemyCategory,
    AlchemyFact,
    AlchemyTag,
    fact_tags
)


class FactManager(BaseAlchemyManager, BaseFactManager):
    """
    """
    def __init__(self, *args, **kwargs):
        super(FactManager, self).__init__(*args, **kwargs)

    # ***

    def _timeframe_available_for_fact(self, fact, ignore_pks=[]):
        """
        Determine if a timeframe given by the passed fact is already occupied.

        This method takes also such facts into account that start before and end
        after the fact in question. In that regard it exceeds what ``_get_all``
        would return.

        Args:
            fact (Fact): The fact to check. Please note that the fact is expected to
                have a ``start`` and ``end``.

        Returns:
            bool: ``True`` if the timeframe is available, ``False`` if not.

        Note:
            If the given fact is the only fact instance within the given timeframe
            the timeframe is considered available (for this fact)!
        """
        # Use func.datetime and _get_sql_datetime to normalize time comparisons,
        # so that equivalent times that are expressed differently are evaluated
        # as equal, e.g., "2018-01-01 10:00" should match "2018-01-01 10:00:00".
        # FIXME: func.datetime is SQLite-specific: need to abstract for other DBMSes.

        start = self._get_sql_datetime(fact.start)
        query = self.store.session.query(AlchemyFact)

        # FIXME: Only use func.datetime on SQLite store.
        #
        #   (lb): SQLite stores datetimes as strings, so what's in the store
        #   might vary depending on, say, changes to this code. As such, some
        #   start and end times might include seconds, and some times might not.
        #   Here we use func.datetime and _get_sql_datetime to normalize the
        #   comparison. But this is SQLite-specific, so we should abstract
        #   the operation for other DBMSes (and probably do nothing, since most
        #   other databases have an actual datetime data type).
        condition = and_(func.datetime(AlchemyFact.end) > start)
        if fact.end is not None:
            end = self._get_sql_datetime(fact.end)
            condition = and_(condition, func.datetime(AlchemyFact.start) < end)
        else:
            # The fact is ongoing, so match the ongoing (active) Fact in the store.
            # E711: `is None` breaks Alchemy, so use `== None`.
            condition = or_(AlchemyFact.end == None, condition)  # noqa: E711

        if fact.pk:
            condition = and_(condition, AlchemyFact.pk != fact.pk)

        if fact.split_from:
            condition = and_(condition, AlchemyFact.pk != fact.split_from.pk)

        if ignore_pks:
            condition = and_(condition, AlchemyFact.pk.notin_(ignore_pks))

        condition = and_(condition, AlchemyFact.deleted == False)  # noqa: E712

        query = query.filter(condition)

        return not bool(query.count())

    # ***

    def _add(self, fact, raw=False, skip_commit=False, ignore_pks=[]):
        """
        Add a new fact to the database.

        Args:
            fact (nark.Fact): Fact to be added.
            raw (bool): If ``True`` return ``AlchemyFact`` instead.

        Returns:
            nark.Fact: Fact as stored in the database

        Raises:
            ValueError: If the passed fact has a PK assigned.
                New facts should not have one.

            ValueError: If the time window is already occupied.
        """
        self.adding_item_must_not_have_pk(fact)

        self.must_validate_datetimes(fact, ignore_pks=ignore_pks)

        alchemy_fact = AlchemyFact(
            pk=None,
            activity=None,
            # FIXME/2018-08-23 00:38: Is this still valid?
            # FIXME: mircoseconds are being stored...
            #        I modified fact_time.must_be_datetime_or_relative to strip
            #        milliseconds. but they're still being saved (just as six 0's).
            start=fact.start,
            end=fact.end,
            description=fact.description,
            deleted=bool(fact.deleted),
            split_from=fact.split_from,
        )
        get_or_create = self.store.activities.get_or_create
        alchemy_fact.activity = get_or_create(fact.activity, raw=True, skip_commit=True)
        tags = [
            self.store.tags.get_or_create(tag, raw=True, skip_commit=True)
            for tag in fact.tags
        ]
        alchemy_fact.tags = tags

        result = self.add_and_commit(
            alchemy_fact, raw=raw, skip_commit=skip_commit,
        )

        return result

    # ***

    def _update(self, fact, raw=False, ignore_pks=[]):
        """
        Update and existing fact with new values.

        Args:
            fact (nark.fact): Fact instance holding updated values.

            raw (bool): If ``True`` return ``AlchemyFact`` instead.
              ANSWER: (lb): "instead" of what? raw is not used by Fact...

        Returns:
            nark.fact: Updated Fact

        Raises:
            KeyError: if a Fact with the relevant PK could not be found.
            ValueError: If the the passed activity does not have a PK assigned.
            ValueError: If the time window is already occupied.
        """
        self.store.logger.debug(_("Received '{!r}', 'raw'={}.".format(fact, raw)))

        if not fact.pk:
            message = _(
                "{!r} does not seem to have a PK. We don't know"
                "which entry to modify.".format(fact)
            )
            self.store.logger.error(message)
            raise ValueError(message)

        self.must_validate_datetimes(fact, ignore_pks=ignore_pks)

        alchemy_fact = self.store.session.query(AlchemyFact).get(fact.pk)
        if not alchemy_fact:
            message = _("No fact with PK: {} was found.".format(fact.pk))
            self.store.logger.error(message)
            raise KeyError(message)

        if alchemy_fact.deleted:
            message = _('Cannot edit deleted Fact: {!r}'.format(fact))
            self.store.logger.error(message)
            raise ValueError(message)

        if (
            (
                (fact.deleted and (fact.end == alchemy_fact.end))
                or (fact.end and not alchemy_fact.end)
            )
            and fact.equal_sans_end(alchemy_fact)
        ):
            # Don't bother with split_from entry.
            # MAYBE: (lb): Go full wiki and store edit times? Ug...
            new_fact = alchemy_fact
            alchemy_fact.deleted = fact.deleted
            alchemy_fact.end = fact.end
        else:
            assert alchemy_fact.pk == fact.pk
            was_split_from = fact.split_from
            fact.split_from = alchemy_fact
            # Clear the ID so that a new ID is assigned.
            fact.pk = None
            new_fact = self._add(fact, raw=True, skip_commit=True, ignore_pks=ignore_pks)
            # NOTE: _add() calls:
            #       self.store.session.commit()
            # The fact being split from is deleted/historic.
            alchemy_fact.deleted = True
            assert new_fact.pk > alchemy_fact.pk
            # Restore the ID to not confuse the caller!
            # The caller will still have a handle on Fact. Rather than
            # change its pk to new_fact's, have it reflect its new
            # split_from status.
            fact.pk = alchemy_fact.pk
            fact.split_from = was_split_from
            # The `alchemy_fact` is what gets saved, but the `fact`
            # is what the caller passed us, so update it, too.
            fact.deleted = True

        self.store.session.commit()

        self.store.logger.debug(_("Updated {!r}.".format(fact)))

        if not raw:
            new_fact = new_fact.as_hamster(self.store)

        return new_fact

    # ***

    def must_validate_datetimes(self, fact, ignore_pks=[]):
        if not isinstance(fact.start, datetime):
            raise TypeError(_('Missing start time for “{!r}”.').format(fact))

        # Check for valid time range.
        invalid_range = False
        if fact.end is not None:
            if fact.start > fact.end:
                invalid_range = True
            else:
                # EXPERIMENTAL: Sneaky, "hidden", vacant, timeless Facts.
                allow_momentaneous = self.store.config['time.allow_momentaneous']
                if not allow_momentaneous and fact.start >= fact.end:
                    invalid_range = True

        if invalid_range:
            message = _('Invalid time range for “{!r}”.').format(fact)
            if fact.start == fact.end:
                assert False  # (lb): Preserved in case we revert == policy.
                message += _(' The start time cannot be the same as the end time.')
            else:
                message += _(' The start time cannot be after the end time.')
            self.store.logger.error(message)
            raise ValueError(message)

        if not self._timeframe_available_for_fact(fact, ignore_pks):
            msg = _(
                'One or more Facts already exist '
                'between the indicated start and end times. '
            )
            self.store.logger.error(msg)
            raise ValueError(msg)

    # ***

    def remove(self, fact, purge=False):
        """
        Remove a fact from our internal backend.

        Args:
            fact (nark.Fact): Fact to be removed

        Returns:
            bool: Success status

        Raises:
            ValueError: If fact passed does not have an pk.

            KeyError: If no fact with passed PK was found.
        """
        self.store.logger.debug(_("Received '{!r}'.".format(fact)))

        if not fact.pk:
            message = _(
                "The fact passed ('{!r}') does not seem to havea PK. We don't know"
                "which entry to remove.".format(fact)
            )
            self.store.logger.error(message)
            raise ValueError(message)

        alchemy_fact = self.store.session.query(AlchemyFact).get(fact.pk)
        if not alchemy_fact:
            message = _('No fact with given pk was found!')
            self.store.logger.error(message)
            raise KeyError(message)
        if alchemy_fact.deleted:
            message = _('The Fact is already marked deleted.')
            self.store.logger.error(message)
            # FIXME/2018-06-08: (lb): I think we need custom Exceptions...
            raise Exception(message)
        alchemy_fact.deleted = True
        if purge:
            self.store.session.delete(alchemy_fact)
        self.store.session.commit()
        self.store.logger.debug(_('{!r} has been removed.'.format(fact)))
        return True

    # ***

    def get(self, pk, deleted=None, raw=False):
        """
        Retrieve a fact based on its PK.

        Args:
            pk (int): PK of the fact to be retrieved.

            deleted (boolean, optional):
                False to restrict to non-deleted Facts;
                True to find only those marked deleted;
                None to find all.

            raw (bool): Return the AlchemyActivity instead.

        Returns:
            nark.Fact: Fact matching given PK

        Raises:
            KeyError: If no Fact of given key was found.
        """
        self.store.logger.debug(_("Received PK: {}', 'raw'={}.".format(pk, raw)))

        if deleted is None:
            query = self.store.session.query(AlchemyFact)
            result = query.get(pk)
        else:
            query = self.store.session.query(AlchemyFact)
            query = query.filter(AlchemyFact.pk == pk)
            query = query_apply_true_or_not(query, AlchemyFact.deleted, deleted)
            results = query.all()
            assert(len(results) <= 1)
            result = results[0] if results else None

        if not result:
            message = _("No fact with given PK found.")
            self.store.logger.error(message)
            raise KeyError(message)
        if not raw:
            # Explain: Why is as_hamster optionable, when act/cat/tag do it always?
            result = result.as_hamster(self.store)
        self.store.logger.debug(_("Returning {!r}.".format(result)))
        return result

    # ***

    def get_all(self, *args, **kwargs):
        return super(FactManager, self).get_all(*args, **kwargs)

    # ***

    RESULT_GRP_INDEX = {
        'duration': 0,
        'group_count': 1,
        'first_start': 2,
        'final_end': 3,
        'activities': 4,
        'actegories': 5,
        'categories': 6,
        'date_col': 7,
    }

    # ***

    def _get_all(
        self,

        # - If include_extras, returns a tuple for each result row: the Fact,
        #   and then any additional columns added to the select.
        include_extras=False,

        # - If count_results, returns just the count (an int) of results.
        count_results=False,

        # - Use since and/or until to find Facts within a specific time range.
        since=None,
        until=None,
        # - Use endless and partial to further influence the time range query.
        # - Set endless=True to include the final, active Fact, if one exists.
        endless=False,
        # - Use exclude_ongoing to omit the final, active Fact, if any,
        #   from the results.
        exclude_ongoing=None,
        # - Specify partial
        # - MAYBE/2020-05-09: (lb): I don't see partial ever being True.
        #   - Either add to a test, or remove it. (Or find a use for it.)
        partial=False,

        # - (lb): Note that 'deleted' is not super useful, given how 'deleted'
        #   is used in a haphazard way to retain a Fact's edit history (though
        #   really user's should use an external solution, like Git, and we
        #   should remove the 'deleted' construct from herein, because nothing
        #   actually does anything with deleted Facts (they just hang around
        #   the database but that's it).
        deleted=False,

        search_term='',

        # Leave activity=False or category=False to skip filtering on them.
        # Or, set activity=None to find Facts without an Activity; likewise
        # for category=None. Or set either to a string to do string matching
        # on the activity or category name(s). Or set activity to Activity
        # object, or category to Category object to match against exact item
        # (i.e., using its PK).
        activity=False,
        category=False,
        match_activities=[],
        match_categories=[],

        # - Use the group_* flags to GROUP BY specific attributes.
        group_activity=False,
        group_category=False,
        group_tags=False,
        group_days=False,

        # - The user can specify one or more columns on which to sort,
        #   and an 'asc' or 'desc' modifier for each column under sort.
        sort_cols=[],
        sort_orders=[],

        # - The user can restrict the results with basic SQL limit-offset.
        limit=None,
        offset=None,

        # - If raw, returns the SQLAlchemy result object, a first-class object
        #   with attributes (upon which the caller can use dot.notation).
        #   The first item in the object is an AlchemyFact object, and the
        #   remainder are the additional query columns.
        # - If not raw, converts each result into a tuple, and converts the
        #   AlchemyFact object into a proper Fact object. Note that the
        #   additional query columns are not themselves identified, so it's
        #   up to the caller to know what's in the tuple (which is at least
        #   always the same set of columns, regardless of the query params).
        raw=False,

        # - An option to lazy-load tags, but which should be avoided.
        # - (lb): IMPOSSIBLE_BRANCH: Nothing in the code sets lazy_tags.
        #   - It's here for the benefit of developers only.
        #   - We should always be able to preload tags (eager loading), which
        #     is a lot quicker than lazy-loading tags, especially when exporting
        #     all Facts. I.e., when eager loading, there's only one SELECT call;
        #     but if lazy loading, there's one SELECT to get all the Facts, and
        #     then one SELECT each to get the tags for each Fact; inefficient!).
        #     In any case, if there are problems with pre-loading, you can flip
        #     this switch to sample the other behavior, which is SQLAlchemy's
        #     "default", which is to lazy-load.
        lazy_tags=False,
    ):
        """
        Return all facts within a given timeframe that match given search terms.

        ``get_all`` already took care of any normalization required.

        If no timeframe is given, return all facts.

        Args:
            deleted (boolean, optional): False to restrict to non-deleted
                Facts; True to find only those marked deleted; None to find
                all.
            since (datetime.datetime, optional):
                Match Facts more recent than a specific dates.
            until (datetime.datetime, optional):
                Match Facts older than a specific dates.
            search_term (str):
                Case-insensitive strings to match ``Activity.name`` or
                ``Category.name``.
            deleted (boolean, optional): False to restrict to non-deleted
                Facts; True to find only those marked deleted; None to find
                all.
            partial (bool):
                If ``False`` only facts which start *and* end within the
                timeframe will be considered. If ``True`` facts with
                either ``start``, ``end`` or both within the timeframe
                will be returned.
            order (string, optional): 'asc' or 'desc'; re: Fact.start.

        Returns:
            list: List of ``nark.Facts`` instances.

        Note:
            This method will *NOT* return facts that start before and end after
            (e.g. that span more than) the specified timeframe.
        """
        magic_tag_sep = '%%%%,%%%%'

        is_grouped = (
            group_activity or group_category or group_tags or group_days
        )

        add_aggregates = (
            include_extras
            or is_grouped
            or set(sort_cols).intersection(('usage', 'time', 'day'))
        )

        i_duration = FactManager.RESULT_GRP_INDEX['duration']
        i_group_count = FactManager.RESULT_GRP_INDEX['group_count']
        # i_first_start = FactManager.RESULT_GRP_INDEX['first_start']
        # i_final_end = FactManager.RESULT_GRP_INDEX['final_end']
        i_activities = FactManager.RESULT_GRP_INDEX['activities']
        i_actegories = FactManager.RESULT_GRP_INDEX['actegories']
        i_categories = FactManager.RESULT_GRP_INDEX['categories']
        # i_date_col = FactManager.RESULT_GRP_INDEX['date_col']

        def _get_all_facts():
            message = _(
                'since: {} / until: {} / srch_term: {} / srt_cols: {} / srt_ordrz: {}'
                .format(since, until, search_term, sort_cols, sort_orders)
            )
            self.store.logger.debug(message)

            must_support_db_engine_funcs()

            query = self.store.session.query(AlchemyFact)

            query, span_cols = _get_all_prepare_span_cols(query)

            query, actg_cols = _get_all_prepare_actg_cols(query)

            query, date_col = _get_all_prepare_date_col(query)

            query, tags_col = _get_all_prepare_tags_col(query)

            query = _get_all_prepare_joins(query)

            query = self.query_filter_by_fact_times(
                query, since=since, until=until, endless=endless, partial=partial,
            )

            query = self._get_all_filter_by_activities(
                query, match_activities + [activity],
            )

            query = self._get_all_filter_by_categories(
                query, match_categories + [category],
            )

            query = _get_all_filter_by_search_term(query)

            query = query_apply_true_or_not(query, AlchemyFact.deleted, deleted)

            query = _get_all_filter_by_ongoing(query)

            query = _get_all_group_by(query)

            query = self._get_all_order_by(
                query, sort_cols, sort_orders, span_cols, date_col, tags_col,
            )

            query = query_apply_limit_offset(query, limit=limit, offset=offset)

            query = _get_all_with_entities(query, span_cols, actg_cols, date_col, tags_col)

            self._log_sql_query(query)

            if count_results:
                results = query.count()
            else:
                # Profiling: 2018-07-15: (lb): ~ 0.120 s. to fetch latest of 20K Facts.
                records = query.all()
                results = _process_results(records)

            return results

        # ***

        def must_support_db_engine_funcs():
            if self.store.config['db.engine'] == 'sqlite':
                return

            errmsg = _(
                'This feature does not work with the current DBMS engine: ‘{}’.'
                ' (Please tell the maintainers if you want this supported!'
                ' That, or switch to SQLite to use this feature.)'
                .format(self.store.config['db.engine'])
            )
            raise NotImplementedError(errmsg)

        # ***

        def _process_results(records):
            if (
                not records
                or (not include_extras and not add_aggregates and lazy_tags)
            ):
                return _process_records_facts_only(records)

            return _process_records_facts_and_aggs(records)

        # The list of results returned to the user is one of:
        # - A list of raw AlchemyFact objects;
        # - A list of hydrated Fact objects (or of a caller-specified subclass); or
        # - A list of tuples comprised of the AlchemyFact or Fact, followed by
        #   a number of calculated, aggregate columns (added when grouping).
        #   - The order of items in each tuple is determined by the function:
        #       _get_all_with_entities
        #     which calls query.with_entities with a list that starts with:
        #       AlchemyFact
        #     and then adds aggregate columns from the functions:
        #       _get_all_prepare_span_cols, and
        #       _get_all_prepare_actg_cols.
        #   - The order of aggregates is also reflected by RESULT_GRP_INDEX.
        # - The intermediate results might also end with a coalesced Tags value
        #   (see _get_all_prepare_tags_col), but the tags_col is pulled before
        #   the results are returned.

        def _process_records_facts_only(records):
            if raw:
                return records

            # Because not add_aggregates, each result is a single item, the
            # AlchemyFact; or a list containing a single item, if not lazy_tags.
            if not include_extras:
                records = [fact.as_hamster(self.store) for fact in records]
            else:
                # (lb): I doubt this path happens, and I also don't doubt that
                # it would be allowed, because include_extras is a method arg.
                assert(not records or len(records[0]) == 1)
                records = [
                    fact.as_hamster(self.store) for fact, *_cols in records
                ]
            return records

        def _process_records_facts_and_aggs(records):
            results = []
            # PROFILING: Here's a loop over all the results!
            # If the user didn't limit or restrict their query,
            # this could be all the Facts!
            for fact, *cols in records:
                fact_or_tuple = _process_record(fact, cols)
                results.append(fact_or_tuple)
            return results

        def _process_record(fact, cols):
            new_tags = _process_record_tags(cols)
            new_fact = _process_record_prepare_fact(fact, new_tags)
            _process_record_reduce_aggregates(cols)
            return _process_record_new_fact_or_tuple(new_fact, cols)

        # +++

        def _process_record_tags(cols):
            # If tags were fetched, they'll be coalesced in the final column.
            new_tags = None
            if cols and not lazy_tags:
                tags = cols.pop()
                new_tags = tags.split(magic_tag_sep) if tags else []
            return new_tags

        # +++

        def _process_record_prepare_fact(fact, new_tags):
            # Unless the caller wants raw results, create a Fact.
            if not raw:
                # Create a new, first-class Fact (or FactDressed). And if
                # the results are aggregate, create a frequency distribution,
                # or number of uses per tag (stored at tag.freq).
                return fact.as_hamster(
                    self.store, new_tags, set_freqs=is_grouped,
                )

            # Even if user wants raw results, still attach the tags.
            if new_tags:
                # Note that this is an AlchemyFact fact, and new_tags
                # is a list of AlchemyTag objects, so not calling
                # tags_replace.
                fact.tags = new_tags
            return fact

        # +++

        def _process_record_reduce_aggregates(cols):
            if not cols or not include_extras:
                return

            _process_record_reduce_aggregate_activities(cols)
            _process_record_reduce_aggregate_actegories(cols)
            _process_record_reduce_aggregate_categories(cols)

        def _process_record_reduce_aggregate_activities(cols):
            _process_record_reduce_aggregate_value(cols, i_activities)

        def _process_record_reduce_aggregate_actegories(cols):
            _process_record_reduce_aggregate_value(cols, i_actegories)

        def _process_record_reduce_aggregate_categories(cols):
            _process_record_reduce_aggregate_value(cols, i_categories)

        def _process_record_reduce_aggregate_value(cols, index):
            encoded_value = cols[index]
            # Note that group_concat generates None if all values were None.
            if encoded_value == 0:
                return

            if encoded_value:
                concated_values = encoded_value.split(magic_tag_sep)
                unique_values = set(concated_values)
            else:
                unique_values = ''
            cols[index] = unique_values

        # +++

        def _process_record_new_fact_or_tuple(new_fact, cols):
            # Make a tuple with the calculated and group-by aggregates,
            # if any, when requested by the caller.
            if include_extras:
                return new_fact, *cols
            return new_fact

        # ***

        def _get_all_prepare_tags_col(query):
            if lazy_tags:
                return query, None
            # (lb): Always include tags. We could let SQLAlchemy lazy load,
            # but this can be slow. E.g., on 15K Facts, calling fact.tags on
            # each -- triggering lazy load -- takes 7 seconds on my machine.
            # As opposed to 0 seconds (rounded down) when preloading tags.
            # - Note earlier must_support_db_engine_funcs() b/c SQLite-specific.
            tags_col = func.group_concat(
                AlchemyTag.name, magic_tag_sep,
            ).label("facts_tags")
            query = query.add_columns(tags_col)
            # (lb): Leaving this breadcrumb for now; feel free to delete later.
            # - sqlalchemy 1.2.x allowed ambiguous joins and would use the first
            #   instance of such a join for its ON clause. But sqlalchemy 1.3.x
            #   requires that you be more specific. Here's the original code:
            #       query = query.outerjoin(fact_tags)
            #   and following is (obviously) the new code. Note that this was
            #   the only place I found code that needed fixing, but I would not
            #   be surprised to find more. Hence this note-to-self, for later.
            query = query.outerjoin(
                fact_tags, AlchemyFact.pk == fact_tags.columns.fact_id,
            )
            query = query.outerjoin(AlchemyTag)
            # (lb): 2019-01-22: Old comment re: joinedload. Leaving here as
            # documentation in case I try using joinedload again in future.
            #   # FIXME/2018-06-25: (lb): Not quite sure this'll work...
            #   # http://docs.sqlalchemy.org/en/latest/orm/loading_relationships.html
            #   #   # joined-eager-loading
            #   from sqlalchemy.orm import joinedload
            #   # 2019-01-22: Either did not need, or did not work, !remember which!
            #   query = query.options(joinedload(AlchemyFact.tags))
            return query, tags_col

        # ***

        def _get_all_prepare_span_cols(query):
            if not add_aggregates:
                return query, None

            span_cols = []

            query, group_span_col = _get_all_prepare_span_cols_group_span(query)
            span_cols.append(group_span_col)

            query, group_count_col = _get_all_prepare_span_cols_group_count(query)
            span_cols.append(group_count_col)

            query, first_start_col = _get_all_prepare_span_cols_first_start(query)
            span_cols.append(first_start_col)

            query, final_end_col = _get_all_prepare_span_cols_final_end(query)
            span_cols.append(final_end_col)

            return query, span_cols

        def _get_all_prepare_span_cols_group_span(query):
            # For most Facts, we could calculate the time window span with
            # simple end-minus-start math, e.g.,
            #   func.julianday(AlchemyFact.end)
            #    - func.julianday(AlchemyFact.start)
            # But this would miss the final ongoing, active Fact. So check
            # first if end is None, and use the 'now' time if so.
            endornow_col = case(
                [(AlchemyFact.end != None, AlchemyFact.end)],  # noqa: E711
                else_=self._get_sql_datetime(self.store.now),
            )

            span_col = _get_all_prepare_span_cols_group_span_dbms_specific(endornow_col)

            group_span_col = func.sum(
                span_col
            ).label('duration')
            query = query.add_columns(group_span_col)
            return query, group_span_col

        def _get_all_prepare_span_cols_group_span_dbms_specific(endornow_col):
            # MAYBE/2020-05-15: Implement this feature for other DBMS engines.
            # - The julianday function is SQLite-specific.
            #   - A "pure" fix might mean doing the calculation after getting
            #     all the results (i.e., post-processing the SQL response).
            #   - (lb): But I like how easy julianday is. It works, and I personally
            #     have no stake in using another DBMS engine. We can add additional
            #     support as needed (i.e., as users' non-SQLite interests dictate).
            if self.store.config['db.engine'] == 'sqlite':
                return _get_all_prepare_span_cols_group_span_sqlite(endornow_col)
            else:
                # See exception thrown by must_support_db_engine_funcs() if not SQLite.
                assert(False)  # Not reachable.

        def _get_all_prepare_span_cols_group_span_sqlite(endornow_col):
            span_col = (
                func.julianday(endornow_col) - func.julianday(AlchemyFact.start)
            )
            return span_col

        def _get_all_prepare_span_cols_group_count(query):
            group_count_col = func.count(
                distinct(AlchemyFact.pk)
            ).label('group_count')
            query = query.add_columns(group_count_col)
            return query, group_count_col

        def _get_all_prepare_span_cols_first_start(query):
            first_start_col = func.min(
                AlchemyFact.start
            ).label('first_start')
            query = query.add_columns(first_start_col)
            return query, first_start_col

        def _get_all_prepare_span_cols_final_end(query):
            final_end_col = func.max(
                AlchemyFact.end
            ).label('final_end')
            query = query.add_columns(final_end_col)
            return query, final_end_col

        # ***

        # Note that grouping by Activity.pk inherently also groups by the
        # Category, because of the many-to-one relationship.
        # - The same is also true if grouping by Activity.pk and Category.pk,
        #   which is essentially no different than grouping by just Activity.pk.
        # - As such, we make the distinction between grouping by just Activity
        #   and by both Activity and Category by using the Activity name when
        #   grouping only by the Activity, but using the Activity ID when the
        #   Category is also involved.
        # - When we group by Activity name, it combines Facts from same-named
        #   Activities in different Categories. As an example, if a user has
        #   Email@Personal and Email@Work, grouping by Activity name will show
        #   overall time spent on Email (which they could also achieve with,
        #   say, an #Email tag).
        # - Also note that grouping by Category (but not Activity) will
        #   collapse one or more Activities, as will grouping by Tags.
        # - Depending on what's grouped -- Activity, Category, and/or Tags --
        #   we'll make a coalesced Activities or Act@gories column to combine
        #   all Activity names that are grouped, or a Categories column to
        #   report all the Categories of each set of grouped Facts (each row).

        def _get_all_prepare_actg_cols(query):
            actg_cols = None
            if not add_aggregates:
                return query, actg_cols

            # Use placeholder values -- may as well be zero -- for columns we do
            # not need for this query, so that the return tuple is always the same
            # size and always has the same layout as reflected by RESULT_GRP_INDEX.
            # Because the concatenated names columns are strings, the caller can
            # check if the value is not a string, but an integer (0) instead, to
            # help decide which columns to use in the report output.
            activities_col = '0'
            actegories_col = '0'
            categories_col = '0'

            if group_activity and group_category:
                # The Activity@Category for each result is unique/not an aggregate.
                pass
            elif group_activity:
                # One Activity per result, but one or more Categories were flattened.
                query, categories_col = _get_all_prepare_actg_cols_categories(query)
            elif group_category:
                # One Category per result, but one or more Activities were flattened.
                query, activities_col = _get_all_prepare_actg_cols_activities(query)
            elif group_tags or group_days:
                # When grouping by tags, both Activities and Categories are grouped.
                query, actegories_col = _get_all_prepare_actg_cols_actegories(query)

            actg_cols = [activities_col, actegories_col, categories_col]

            return query, actg_cols

        def _get_all_prepare_actg_cols_activities(query):
            activities_col = func.group_concat(
                AlchemyActivity.name, magic_tag_sep,
            ).label("facts_activities")
            query = query.add_columns(activities_col)
            return query, activities_col

        def _get_all_prepare_actg_cols_actegories(query):
            # SQLite supports column || concatenation, which is + in SQLAlchemy.
            # MAYBE/2020-05-18: Is there a config value that specs the '@' sep?
            # - I.e., replace the hardcoded '@' with a config value.
            actegory_col = AlchemyActivity.name + '@' + AlchemyCategory.name
            # SKIP/Not necessary:
            #   actegory_col.label("actegory")
            #   query = query.add_columns(actegory_col)
            #   actg_cols.append(actegory_col)
            actegories_col = func.group_concat(
                actegory_col, magic_tag_sep,
            ).label("facts_actegories")
            query = query.add_columns(actegories_col)
            return query, actegories_col

        def _get_all_prepare_actg_cols_categories(query):
            categories_col = func.group_concat(
                AlchemyCategory.name, magic_tag_sep,
            ).label("facts_categories")
            query = query.add_columns(categories_col)
            return query, categories_col

        # ***

        # MAYBE/2020-05-19: Splice Facts at midnight so that each
        # day is reported as 24 hours, rather than reported as the
        # sum of all the complete Facts that start on the day (in
        # which case, a Fact that starts the day before that runs
        # into the day will not be counted (undercount); and a Fact
        # that starts on the day by ends on the next will be have
        # all its time counted (over-count).

        def _get_all_prepare_date_col(query):
            # If we were not going to return the date_col with the results,
            # rather than checking `not add_aggregates`, we would instead
            # check `not group_days` and return if so.
            if not add_aggregates:
                return query, None

            # FIXME/MAYBE/2020-05-19: Prepare other time-grouped reports. See:
            #   https://www.sqlite.org/lang_datefunc.html
            # - MAYBE: Prepare monthly reports using 'start of month':
            #     SELECT date('now', 'start of month');
            #     if group_months: ...
            # - MAYBE: Prepare weekly reports using `weekday N` (0=Sunday);
            #     if group_weeks: ...
            # - MAYBE: Prepare Sprint reports using... not sure.
            #     if group_sprint???

            date_col = func.date(
                AlchemyFact.start,
            ).label("date_col")
            query = query.add_columns(date_col)
            if group_days:
                query = query.group_by(date_col)

            return query, date_col

        # ***

        def _get_all_prepare_joins(query):
            join_category = (
                group_activity  # b/c _get_all_prepare_actg_cols_categories
                or group_category
                or group_tags  # b/c _get_all_prepare_actg_cols_actegories
                or group_days  # b/c _get_all_prepare_actg_cols_actegories
                or (category is not False)
                or search_term
                or 'activity' in sort_cols
                or 'category' in sort_cols
            )
            if (
                add_aggregates
                or (activity is not False)
                or join_category
            ):
                # Equivalent: AlchemyFact.activity or AlchemyActivity.
                query = query.outerjoin(AlchemyFact.activity)
            if join_category:
                # Equivalent: AlchemyActivity.category or AlchemyCategory.
                query = query.outerjoin(AlchemyActivity.category)
            return query

        # ***

        def _get_all_filter_by_search_term(query):
            if search_term:
                query = _filter_search_term(query)
            return query

        # ***

        def _filter_search_term(query):
            """
            Limit query to facts that match the search terms.

            Terms are matched against ``Category.name`` and ``Activity.name``.
            The matching is not case-sensitive.
            """
            # FIXME/2018-06-09: (lb): Now with activity and category filters,
            #   search_term makes less sense. Unless we apply to all parts?
            #   E.g., match tags, and match description.
            query = query.filter(
                or_(
                    AlchemyActivity.name.ilike('%{}%'.format(search_term)),
                    AlchemyCategory.name.ilike('%{}%'.format(search_term)),
                )
            )

            return query

        # ***

        def _get_all_filter_by_ongoing(query):
            if not exclude_ongoing:
                return query
            if exclude_ongoing:
                query = query.filter(AlchemyFact.end != None)  # noqa: E711
            return query

        # ***

        def _get_all_group_by(query):
            if not is_grouped:
                # Need to group by Fact.pk because of Tags join table.
                return _get_all_group_by_pk(query)
            return _get_all_group_by_meta(query)

        def _get_all_group_by_pk(query):
            # Group by Fact.pk, as there might be "duplicate" Facts because
            # of the fact_tags join. The 'facts_tags' column coalesces Tags.
            query = query.group_by(AlchemyFact.pk)
            return query

        def _get_all_group_by_meta(query):
            query = _get_all_group_by_activity_and_category(query)
            query = _get_all_group_by_tags(query)
            return query

        def _get_all_group_by_activity_and_category(query):
            if group_activity and group_category:
                # NOTE:The wrong group-by returns 1 record:
                #        query = query.group_by(AlchemyFact.activity)
                #      generates:
                #         GROUP BY activities.id = facts.activity_id
                #      But we want more simply:
                #         GROUP BY activities.id
                query = query.group_by(AlchemyActivity.pk)
                # Each Activity is associated with exactly one Category,
                # so the group_by(AlchemyActivity.pk) is sufficient, but
                # for completeness, group on the Category, too.
                query = query.group_by(AlchemyCategory.pk)
            elif group_activity:
                # This is kinda smudgy. What does it mean to group by the Activity?
                # - Do you mean an Activity in the traditional sense, which is
                #   Activity@Category? (in which case, group-by the Activity.pk,
                #   and include the Category in the grouping).
                # - Or is this an Activity is a looser sense, as in an Activity
                #   name? (in which case, group by the Activity name, which means
                #   two Activities with the same name but in different Categories
                #   become grouped).
                # To be the most flexible, if the user wants to group by the
                # Activity but does not also specify the Category, then, sure,
                # group by the Activity name. They can add the Category grouping
                # if they want to group on the actual Activity@Category.
                query = query.group_by(AlchemyActivity.name)
            elif group_category:
                query = query.group_by(AlchemyCategory.pk)
            return query

        def _get_all_group_by_tags(query):
            if group_tags:
                query = query.group_by(AlchemyTag.pk)
            return query

        # ***

        def _get_all_with_entities(query, span_cols, actg_cols, date_col, tags_col):
            # Even if grouping, we still want to fetch all columns. For one,
            # _process_results expects a Fact object as leading item in each
            # result tuple, and also because as_hamster expects certain fields
            # (and in a specific order). We'd also have to at least specify
            # AlchemyFact.pk so that SQLAlchemy uses `FROM facts`, and not,
            # e.g., `FROM category`. So use all Fact cols to start the select.
            columns = [AlchemyFact]

            # The order of the columns added here is reflected by RESULT_GRP_INDEX.
            # - Note also if `add_aggregates` is True, then both span_cols and
            #   actg_cols should be not None. But we'll check for None-ness
            #   just to be safe.
            if span_cols is not None:
                columns.extend(span_cols)
            if actg_cols is not None:
                columns.extend(actg_cols)
            if add_aggregates:
                columns.append(date_col)

            # Ensure tags_col is last, because _process_record_tags expects (pops) it.
            if tags_col is not None:
                assert not lazy_tags
                columns.append(tags_col)

            query = query.with_entities(*columns)

            return query

        # ***

        return _get_all_facts()

    # ***

    def _get_all_order_by_col(
        self, query, sort_col, direction, span_cols, date_col, tags_col,
    ):
        if sort_col == 'start' or not sort_col:
            query = self.query_order_by_start(query, direction)
        elif sort_col == 'time':
            query = query.order_by(direction(span_cols[i_duration]))
        elif sort_col == 'day':
            assert(date_col is not None)
            query = query.order_by(direction(date_col))
        elif sort_col == 'activity':
            # If grouping by only category, this sort does not work: The
            # activity names are group_concat'enated into the 'activities'
            # column, which must be post-processed -- split on magic_tag_sep,
            # made unique, and sorted. Such a dob command might look like this:
            #   `dob list facts --group category --sort activity`
            # But if also grouping by activity, or tags, order-by here works.
            # So sorting activity when grouping category is done by caller.
            if group_activity or group_tags or group_days or not group_category:
                query = query.order_by(direction(AlchemyActivity.name))
        elif sort_col == 'category':
            # If sorting by category but grouping by activity (or tags), the
            # caller must sort during post-processing, after transforming the
            # categories aggregate (which get_all returns as a set) into an
            # alphabetically ordered string. (We could sort here, but it
            # would have no effect, so might as well not.)
            if group_category or group_tags or group_days or not group_activity:
                query = query.order_by(direction(AlchemyCategory.name))
        elif sort_col == 'tag' and tags_col is not None:
            # Don't sort by the aggregate column, because tags aren't
            # sorted in the aggregate (they're not even unique, it's
            # just a long string built from all the tags).
            # - So this won't sort the table:
            #     query = query.order_by(direction(tags_col))
            # But because we checked tags_col is not None, we know that
            # the Tag table is joined -- so we can sort by the tag name.
            # Except if grouping by activity or category, then the sort
            # won't stick, so skip it in that case.
            if not group_activity and not group_category:
                query = query.order_by(direction(AlchemyTag.name))
        elif sort_col == 'usage' and span_cols is not None:
            query = query.order_by(direction(span_cols[i_group_count]))
        elif sort_col == 'name':
            # It makes sense to sort Activities, Categories, and Tags by their
            # names, but a Fact does not have a name. So what does `--sort name`
            # mean to a Fact? 2020-05-19: This code had been ignoring --sort name
            # (all sort options are shared, so it's not considered wrong to
            # receive such a request), but we could treat `--sort name` as a
            # request to sort by description. There's not another mechanism to
            # sort by description, and it seems pretty useless, anyway, except
            # maybe to group Facts without a description. So we might as well wire
            # sorting by name to sorting be description, rather than ignoring it.
            query = query.order_by(direction(AlchemyFact.description))
        elif sort_col == 'fact':
            # (lb): There is (or at least should be) no meaning with Fact IDs,
            # i.e., you should think of them as UUID values, and not having any
            # relationship to one another, other than as an indicator of identity.
            # So ordering by the PK, just because it happens to be an integer
            # and can be compared against other PKs, is possible, but it also
            # doesn't accomplish much. I suppose you could sort by PK to ensure that
            # you can recreate a report in the same order as before, if that's your
            # thing. 2020-05-18: In any case, the `--sort fact` option has existed
            # in the CLI, but the code here has been ignoring it (and just treating
            # it like `--sort start`). But there are no reasons, other than perhaps
            # ideological, that we cannot at least wire it to the PK. So here ya go:
            query = query.order_by(direction(AlchemyFact.pk))
        else:
            self.store.logger.warn("Unknown sort_col: {}".format(sort_col))
        return query

    # ***

    def query_exclude_fact(self, query, fact=None):
        if fact and not fact.unstored:
            query = query.filter(AlchemyFact.pk != fact.pk)
        return query

    # ***

    def query_order_by_start(self, query, direction):
        # Include end so that momentaneous Facts are sorted properly.
        # - And add PK, too, so momentaneous Facts are sorted predictably.
        query = query.order_by(
            direction(AlchemyFact.start),
            direction(AlchemyFact.end),
            direction(AlchemyFact.pk),
        )
        return query

    # ***

    def starting_at(self, fact):
        """
        Return the fact starting at the moment in time indicated by fact.start.

        Args:
            fact (nark.Fact):
                The Fact to reference, with its ``start`` set.

        Returns:
            nark.Fact: The found Fact, or None if none found.

        Raises:
            ValueError: If more than one Fact found at given time.
        """
        query = self.store.session.query(AlchemyFact)

        if fact.start is None:
            raise ValueError('No `start` for starting_at(fact).')

        start_at = self._get_sql_datetime(fact.start)
        condition = and_(func.datetime(AlchemyFact.start) == start_at)

        # Excluded 'deleted' Facts.
        condition = and_(condition, AlchemyFact.deleted == False)  # noqa: E712
        query = query.filter(condition)
        # Exclude fact.pk from results.
        query = self.query_exclude_fact(query, fact)
        # Order by start time (end time, fact ID), ascending.
        query = self.query_order_by_start(query, asc)

        self.store.logger.debug(_('fact: {} / query: {}'.format(fact, str(query))))

        n_facts = query.count()
        if n_facts > 1:
            message = 'More than one fact found starting at "{}": {} facts found'.format(
                fact.start, n_facts
            )
            raise ValueError(message)

        found = query.one_or_none()
        found_fact = found.as_hamster(self.store) if found else None
        return found_fact

    # ***

    def ending_at(self, fact):
        """
        Return the fact ending at the moment in time indicated by fact.end.

        Args:
            fact (nark.Fact):
                The Fact to reference, with its ``end`` set.

        Returns:
            nark.Fact: The found Fact, or None if none found.

        Raises:
            ValueError: If more than one Fact found at given time.
        """
        query = self.store.session.query(AlchemyFact)

        if fact.end is None:
            raise ValueError('No `end` for ending_at(fact).')

        end_at = self._get_sql_datetime(fact.end)
        condition = and_(func.datetime(AlchemyFact.end) == end_at)

        # Excluded 'deleted' Facts.
        condition = and_(condition, AlchemyFact.deleted == False)  # noqa: E712
        query = query.filter(condition)
        # Exclude fact.pk from results.
        query = self.query_exclude_fact(query, fact)
        # Order by start time (end time, fact ID), descending.
        query = self.query_order_by_start(query, desc)

        self.store.logger.debug(_('fact: {} / query: {}'.format(fact, str(query))))

        n_facts = query.count()
        if n_facts > 1:
            message = 'More than one fact found ending at "{}": {} facts found'.format(
                fact.end, n_facts,
            )
            raise ValueError(message)

        found = query.one_or_none()
        found_fact = found.as_hamster(self.store) if found else None
        return found_fact

    # ***

    def antecedent(self, fact=None, ref_time=None):
        """
        Return the Fact immediately preceding the indicated Fact.

        Args:
            fact (nark.Fact):
                The Fact to reference, with its ``start`` set.

            ref_time (datetime.datetime):
                In lieu of fact, pass the datetime to reference.

        Returns:
            nark.Fact: The antecedent Fact, or None if none found.

        Raises:
            ValueError: If neither ``start`` nor ``end`` is set on fact.
        """
        query = self.store.session.query(AlchemyFact)

        if fact is not None:
            if fact.end and isinstance(fact.end, datetime):
                ref_time = fact.end
            elif fact.start and isinstance(fact.start, datetime):
                ref_time = fact.start
        if not isinstance(ref_time, datetime):
            raise ValueError(_('No reference time for antecedent(fact).'))

        ref_time = self._get_sql_datetime(ref_time)

        before_ongoing_fact_start = and_(
            AlchemyFact.end == None,  # noqa: E711
            # Except rather than <=, use less than, otherwise
            # penultimate_fact.antecedent might find the ultimate
            # fact, if that final fact is ongoing.
            #   E.g., considering
            #     fact  1: time-a to time-b
            #     ...
            #     fact -2: time-x to time-y
            #     fact -1: time-y to <now>
            #   antecedent of fact -2 should check time-y < time-y and
            #   not <= otherwise antecedent of fact -2 would be fact -1.
            #   (The subsequent function will see it, though, as it
            #   looks for AlchemyFact.start >= ref_time.)
            func.datetime(AlchemyFact.start) < ref_time,
        )

        if fact is None or fact.pk is None:
            before_closed_fact_end = and_(
                AlchemyFact.end != None,  # noqa: E711
                # Special case for ongoing fact (check its start).
                # Be most inclusive and compare against facts' ends.
                func.datetime(AlchemyFact.end) <= ref_time,
            )
        else:
            before_closed_fact_end = and_(
                AlchemyFact.end != None,  # noqa: E711
                or_(
                    func.datetime(AlchemyFact.end) < ref_time,
                    and_(
                        func.datetime(AlchemyFact.end) == ref_time,
                        AlchemyFact.pk != fact.pk,
                    ),
                ),
            )

        condition = or_(
            before_ongoing_fact_start,
            before_closed_fact_end,
        )

        # Excluded 'deleted' Facts.
        condition = and_(condition, AlchemyFact.deleted == False)  # noqa: E712
        query = query.filter(condition)
        # Exclude fact.pk from results.
        query = self.query_exclude_fact(query, fact)
        # Order by start time (end time, fact ID), descending.
        query = self.query_order_by_start(query, desc)

        query = query.limit(1)

        self.store.logger.debug(_(
            'fact: {} / ref_time: {} / query: {}'
            .format(fact, ref_time, str(query))
        ))

        found = query.one_or_none()
        found_fact = found.as_hamster(self.store) if found else None
        return found_fact

    # ***

    def subsequent(self, fact=None, ref_time=None):
        """
        Return the Fact immediately following the indicated Fact.

        Args:
            fact (nark.Fact):
                The Fact to reference, with its ``end`` set.

            ref_time (datetime.datetime):
                In lieu of fact, pass the datetime to reference.

        Returns:
            nark.Fact: The subsequent Fact, or None if none found.

        Raises:
            ValueError: If neither ``start`` nor ``end`` is set on fact.
        """
        query = self.store.session.query(AlchemyFact)

        if fact is not None:
            if fact.start and isinstance(fact.start, datetime):
                ref_time = fact.start
            elif fact.end and isinstance(fact.end, datetime):  # pragma: no cover
                # (lb): This would be unexpected, if not impossible:
                #       a Fact with no start, but it has an end.
                self.store.logger.warning('Unexpected path!')
                ref_time = fact.end
        if ref_time is None:
            raise ValueError(_('No reference time for subsequent(fact).'))

        ref_time = self._get_sql_datetime(ref_time)

        if fact is None or fact.pk is None:
            condition = and_(func.datetime(AlchemyFact.start) >= ref_time)
        else:
            condition = or_(
                func.datetime(AlchemyFact.start) > ref_time,
                and_(
                    func.datetime(AlchemyFact.start) == ref_time,
                    AlchemyFact.pk != fact.pk,
                ),
            )

        # Excluded 'deleted' Facts.
        condition = and_(condition, AlchemyFact.deleted == False)  # noqa: E712
        query = query.filter(condition)
        # Exclude fact.pk from results.
        query = self.query_exclude_fact(query, fact)
        # Order by start time (end time, fact ID), ascending.
        query = self.query_order_by_start(query, asc)

        query = query.limit(1)

        self.store.logger.debug(_(
            'fact: {} / ref_time: {} / query: {}'
            .format(fact, ref_time, str(query))
        ))

        found = query.one_or_none()
        found_fact = found.as_hamster(self.store) if found else None
        return found_fact

    # ***

    def strictly_during(self, since, until, result_limit=1000):
        """
        Return the fact(s) strictly contained within a since and until time.

        Args:
            since (datetime.datetime):
                Start datetime of facts to find.

            until (datetime.datetime):
                End datetime of facts to find.

            result_limit (int):
                Maximum number of facts to find, else log warning message.

        Returns:
            list: List of ``nark.Facts`` instances.
        """
        query = self.store.session.query(AlchemyFact)

        condition = and_(
            func.datetime(AlchemyFact.start) >= self._get_sql_datetime(since),
            or_(
                and_(
                    AlchemyFact.end != None,  # noqa: E711
                    func.datetime(AlchemyFact.end) <= self._get_sql_datetime(until),
                ),
                and_(
                    AlchemyFact.end == None,  # noqa: E711
                    func.datetime(AlchemyFact.start) <= self._get_sql_datetime(until),
                ),
            ),
        )

        condition = and_(condition, AlchemyFact.deleted == False)  # noqa: E712

        query = query.filter(condition)

        query = self.query_order_by_start(query, asc)

        self.store.logger.debug(_(
            'since: {} / until: {} / query: {}'
            .format(since, until, str(query))
        ))

        # LATER: (lb): We'll let the client ask for as many records as they
        # want. But we might want to offer ways to deal more gracefully with
        # it, like via pagination; or a fetch_one callback, so that only item
        # gets loaded in memory at a time, rather than everything. For now, we
        # can at least warn, I suppose.
        during_count = query.count()
        if during_count > result_limit:
            # (lb): hamster-lib would `raise OverflowError`,
            # but that seems drastic.
            message = (_(
                'This is your alert that lots of Facts were found between '
                'the two dates specified: found {}.'
                .factor(during_count)
            ))
            self.store.logger.warning(message)

        facts = query.all()
        found_facts = [fact.as_hamster(self.store) for fact in facts]
        return found_facts

    # ***

    def surrounding(self, fact_time, inclusive=False):
        """
        Return the fact(s) at the given moment in time.
        Note that this excludes a fact that starts or ends at this time.
        (See antecedent and subsequent for finding those facts.)

        Args:
            fact_time (datetime.datetime):
                Time of fact(s) to match.

        Returns:
            list: List of ``nark.Facts`` instances.

        Raises:
            ValueError: If more than one Fact found at given time.
        """
        query = self.store.session.query(AlchemyFact)

        cmp_time = self._get_sql_datetime(fact_time)

        if not inclusive:
            condition = and_(
                func.datetime(AlchemyFact.start) < cmp_time,
                # Find surrounding complete facts, or the ongoing fact.
                or_(
                    AlchemyFact.end == None,  # noqa: E711
                    func.datetime(AlchemyFact.end) > cmp_time,
                ),
            )
        else:
            condition = and_(
                func.datetime(AlchemyFact.start) <= cmp_time,
                # Find surrounding complete facts, or the ongoing fact.
                or_(
                    AlchemyFact.end == None,  # noqa: E711
                    func.datetime(AlchemyFact.end) >= cmp_time,
                ),
            )

        condition = and_(condition, AlchemyFact.deleted == False)  # noqa: E712

        query = query.filter(condition)

        query = self.query_order_by_start(query, asc)

        self.store.logger.debug(_(
            'fact_time: {} / query: {}'.format(
                fact_time, str(query)
            )
        ))

        if not inclusive:
            n_facts = query.count()
            if n_facts > 1:
                message = 'Broken time frame found at "{}": {} facts found'.format(
                    fact_time, n_facts
                )
                raise ValueError(message)

        facts = query.all()
        found_facts = [fact.as_hamster(self.store) for fact in facts]
        return found_facts

    # ***

    def endless(self):
        """
        Return any facts without a fact.start or fact.end.

        Args:
            <none>

        Returns:
            list: List of ``nark.Facts`` instances.
        """
        query = self.store.session.query(AlchemyFact)

        # NOTE: (lb): Use ==/!=, not `is`/`not`, b/c SQLAlchemy
        #       overrides ==/!=, not `is`/`not`.
        condition = or_(AlchemyFact.start == None, AlchemyFact.end == None)  # noqa: E711
        condition = and_(condition, AlchemyFact.deleted == False)  # noqa: E712

        query = query.filter(condition)

        self.store.logger.debug(_('query: {}'.format(str(query))))

        facts = query.all()
        found_facts = [fact.as_hamster(self.store) for fact in facts]
        return found_facts


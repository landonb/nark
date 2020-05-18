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

from sqlalchemy import asc, case, desc, func
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
            result = self.store.session.query(AlchemyFact).get(pk)
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
    }

    # ***

    def _get_all(
        self,
        endless=False,
        # FIXME/2020-05-09: (lb): I don't see partial ever being True.
        partial=False,
        include_usage=False,
        count_results=False,
        since=None,
        until=None,
        # FIXME/2018-06-09: (lb): Implement deleted/hidden.
        # FIXME/2020-05-16: (lb): Remove deleted/hidden....
        deleted=False,
        search_term='',
        activity=False,
        category=False,
        group_activity=False,
        group_category=False,
        group_tags=False,
        sort_col='',
        sort_order='',
        raw=False,
        exclude_ongoing=None,
        # (lb): IMPOSSIBLE_BRANCH: We should always be able to preload tags
        # (eager loading), which is a lot quicker than lazy-loading tags,
        # especially when exporting all Facts. I.e., when eager loading,
        # there's only one SELECT call; but if lazy loading, there'd be one
        # SELECT to get all the Facts, and then one SELECT to get the tags
        # for each Fact; inefficient!). In any case, if there are problems
        # with pre-loading, you can flip this switch to sample the other
        # behavior, which is SQLAlchemy's "default", which is to lazy-load.
        lazy_tags=False,
        # kwargs: limit, offset
        **kwargs
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

        is_grouped = group_activity or group_category or group_tags

        i_duration = FactManager.RESULT_GRP_INDEX['duration']
        i_group_count = FactManager.RESULT_GRP_INDEX['group_count']
        i_first_start = FactManager.RESULT_GRP_INDEX['first_start']
        i_final_end = FactManager.RESULT_GRP_INDEX['final_end']
        i_activities = FactManager.RESULT_GRP_INDEX['activities']
        i_actegories = FactManager.RESULT_GRP_INDEX['actegories']

        def _get_all_facts():
            message = _(
                'since: {} / until: {} / srch_term: {} / srt_col: {} / srt_ordr: {}'
                .format(since, until, search_term, sort_col, sort_order)
            )
            self.store.logger.debug(message)

            must_support_db_engine_funcs()

            query = self.store.session.query(AlchemyFact)

            query, span_cols = _get_all_prepare_span_cols(query)

            query, grouping_cols = _get_all_prepare_grouping_cols(query)

            query, tags_col = _get_all_prepare_tags_col(query)

            query = _get_all_prepare_joins(query)

            query = self.get_all_filter_partial(
                query, since=since, until=until, endless=endless, partial=partial,
            )

            query = _get_all_filter_by_activity(query)

            query = _get_all_filter_by_category(query)

            query = _get_all_filter_by_search_term(query)

            query = query_apply_true_or_not(query, AlchemyFact.deleted, deleted)

            query = _get_all_filter_by_ongoing(query)

            query = _get_all_group_by(query)

            query = _get_all_order_by(query, span_cols)

            query = query_apply_limit_offset(query, **kwargs)

            query = _get_all_with_entities(query, span_cols, grouping_cols, tags_col)

            self.store.logger.debug(_('query: {}'.format(str(query))))

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
            # MAGIC_NUMBER: Check any record (0) to see if any aggregate columns
            # exist or not -- if length is 1, it's just the Fact, no aggregates.
            if not records or len(records[0]) == 1:
                if not raw:
                    records = [fact.as_hamster(self.store) for fact in records]
                return records, None

            return _process_records(records)

        def _process_records(records):
            results = []

            # MAGIC_ARRAY: Create aggregate values of all results.
            # These are the indices of this results aggregate:
            #   0: Durations summation.
            #   1: Group count count.
            #   2: First first_start.
            #   3: Final final_end.
            #   Skip: Activities, Actegories.
            # - See: FactManager.RESULT_GRP_INDEX.
            gross_totals = [0, 0, None, None]

            # PROFILING: Here's a loop over all the results!
            # If the user didn't limit or restrict their query,
            # this could be all the Facts!
            for fact, *cols in records:
                fact_or_tuple = _process_record(fact, cols, gross_totals)
                results.append(fact_or_tuple)

            return results, gross_totals

        # The results list is one of:
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
        #       _get_all_prepare_grouping_cols.
        #   - The order of aggregates is also reflected by RESULT_GRP_INDEX.
        # - The intermediate results might also end with a coalesced Tags value
        #   (see _get_all_prepare_tags_col), but the tags_col is pulled before
        #   the results are returned.

        def _process_record(fact, cols, gross_totals):
            new_tags = _process_record_tags(cols)
            new_fact = _process_record_prepare_fact(fact, new_tags)
            _process_record_update_gross(new_fact, cols, gross_totals)
            _process_record_reduce_aggregates(cols)
            return _process_record_new_fact_or_tuple(new_fact, cols)

        # +++

        def _process_record_tags(cols):
            # If tags were fetched, they'll be coalesced in the final column.
            new_tags = None
            if not lazy_tags:
                tags = cols.pop()
                new_tags = tags.split(magic_tag_sep) if tags else []
            return new_tags

        # +++

        def _process_record_prepare_fact(fact, new_tags):
            # Unless the caller wants raw results, create a Fact.
            if not raw:
                new_fact = fact.as_hamster(self.store, new_tags)
            else:
                # Even if user wants raw results, still attach the tags.
                if new_tags:
                    fact.tags = new_tags
                new_fact = fact
            return new_fact

        # +++

        def _process_record_update_gross(new_fact, cols, gross_totals):
            if not cols:
                _process_record_update_gross_single_fact(new_fact, gross_totals)
            else:
                _process_record_update_gross_grouped_facts(cols, gross_totals)

        def _process_record_update_gross_single_fact(new_fact, gross_totals):
            # Because julianday, expects days. MAGIC_NUMBER: 86400 secs/day.
            duration = new_fact.delta().total_seconds() / 86400.0
            group_count = 1
            first_start = new_fact.start
            final_end = new_fact.end
            _process_record_update_gross_values(
                gross_totals, duration, group_count, first_start, final_end,
            )

        def _process_record_update_gross_grouped_facts(cols, gross_totals):
            duration = cols[i_duration]
            group_count = cols[i_group_count]
            first_start = cols[i_first_start]
            final_end = cols[i_final_end]
            _process_record_update_gross_values(
                gross_totals, duration, group_count, first_start, final_end,
            )

        def _process_record_update_gross_values(
            gross_totals, duration, group_count, first_start, final_end,
        ):
            gross_totals[i_duration] += duration

            gross_totals[i_group_count] += group_count

            if gross_totals[i_first_start] is None:
                gross_totals[i_first_start] = first_start
            else:
                gross_totals[i_first_start] = min(
                    gross_totals[i_first_start], first_start,
                )

            if gross_totals[i_final_end] is None:
                gross_totals[i_final_end] = final_end
            else:
                gross_totals[i_final_end] = max(
                    gross_totals[i_final_end], final_end,
                )

        # +++

        def _process_record_reduce_aggregates(cols):
            if not cols:
                return

            _process_record_reduce_aggregate_activities(cols)
            _process_record_reduce_aggregate_actegories(cols)

        def _process_record_reduce_aggregate_activities(cols):
            _process_record_reduce_aggregate_value(cols, i_activities)

        def _process_record_reduce_aggregate_actegories(cols):
            _process_record_reduce_aggregate_value(cols, i_actegories)

        def _process_record_reduce_aggregate_value(cols, index):
            encoded_value = cols[index]
            if encoded_value in (0, None):
                return

            concated_values = encoded_value.split(magic_tag_sep)
            unique_values = set(concated_values)
            cols[index] = unique_values

        # +++

        def _process_record_new_fact_or_tuple(new_fact, cols):
            # Make a tuple for group-by results, if any.
            if cols:
                return (new_fact, *cols)
            else:
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
            if not include_usage and not is_grouped:
                return query, None

            span_cols = []

            group_span_col = _get_all_prepare_span_cols_group_span(query)
            span_cols.append(group_span_col)

            group_count_col = _get_all_prepare_span_cols_group_count(query)
            span_cols.append(group_count_col)

            first_start_col = _get_all_prepare_span_cols_first_start(query)
            span_cols.append(first_start_col)

            final_end_col = _get_all_prepare_span_cols_final_end(query)
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
            return group_span_col

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
                AlchemyFact.pk
            ).label('group_count')
            query = query.add_columns(group_count_col)
            return group_count_col

        def _get_all_prepare_span_cols_first_start(query):
            first_start_col = func.min(
                AlchemyFact.start
            ).label('first_start')
            query = query.add_columns(first_start_col)
            return first_start_col

        def _get_all_prepare_span_cols_final_end(query):
            final_end_col = func.max(
                AlchemyFact.start
            ).label('final_end')
            query = query.add_columns(final_end_col)
            return final_end_col

        # ***

        # Note that grouping by Activity.pk inherently also groups by the
        # Category, because of the many-to-one relationship.
        # - The same is also true if grouping by Activity and Category,
        #   which is essentially no different than grouping by Activity.
        # - An alternative would be to group by Activity name, thereby
        #   combining Facts from same-named Activities in different
        #   Categories. But this is not currently supported -- and there
        #   are no plans to support such a feature (it does not seem like
        #   useful information that the user would care about. Though,
        #   as an example, if a user had Email@Personal and Email@Work,
        #   grouping by Activity name would show overall time spent on
        #   Email -- but you could instead use an #Email tag to generate
        #   a report with this information, which currently *is* supported).
        # - Also note that grouping by Category (but not Activity) will
        #   collapse one or more Activities, as will grouping by Tags.
        # - Depending on what's grouped -- Activity, Category, and/or Tags --
        #   we'll make a coalesced Activities or Act@gories column to combine
        #   all Activity names that are grouped.

        def _get_all_prepare_grouping_cols(query):
            grouping_cols = None
            if not include_usage and not is_grouped:
                return query, grouping_cols

            # Use placeholder values -- may as well be zero -- for columns we do
            # not need for this query, so that the return tuple is always the same
            # size and always has the same layout as reflected by RESULT_GRP_INDEX.
            # Because the concatenated names columns are strings, the caller can
            # check if the value is not a string, but an integer (0) instead, to
            # help decide which columns to use in the report output.
            activities_col = '0'
            actegories_col = '0'

            if group_activity:
                # The Activity@Category for each result is unique/not an aggregate.
                pass
            elif group_category:
                # Just one Category per result, but one or Activities were flattened.
                activities_col = _get_all_prepare_grouping_cols_activities(query)
            elif group_tags:
                # When grouping by tags, both Activities and Categories are grouped.
                actegories_col = _get_all_prepare_grouping_cols_actegories(query)

            grouping_cols = [activities_col, actegories_col]

            return query, grouping_cols

        def _get_all_prepare_grouping_cols_activities(query):
            activities_col = func.group_concat(
                AlchemyActivity.name, magic_tag_sep,
            ).label("facts_activities")
            query = query.add_columns(activities_col)
            return activities_col

        def _get_all_prepare_grouping_cols_actegories(query):
            # SQLite supports column || concatenation, which is + in SQLAlchemy.
            # MAYBE/2020-05-18: Is there a config value that specs the '@' sep?
            # - I.e., replace the hardcoded '@' with a config value.
            actegory_col = AlchemyActivity.name + '@' + AlchemyCategory.name
            # SKIP/Not necessary:
            #   actegory_col.label("actegory")
            #   query = query.add_columns(actegory_col)
            #   grouping_cols.append(actegory_col)
            actegories_col = func.group_concat(
                actegory_col, magic_tag_sep,
            ).label("facts_actegories")
            query = query.add_columns(actegories_col)
            return actegories_col

        # ***

        def _get_all_prepare_joins(query):
            join_category = (
                group_category
                or group_tags  # b/c _get_all_prepare_grouping_cols_actegories
                or (category is not False)
                or search_term
            )
            if (
                include_usage
                or group_activity
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

        def _get_all_filter_by_activity(query):
            if activity is False:
                return query

            if activity:
                if activity.pk:
                    query = query.filter(AlchemyActivity.pk == activity.pk)
                else:
                    query = query.filter(
                        func.lower(AlchemyActivity.name) == func.lower(activity.name)
                    )
            else:
                query = query.filter(AlchemyFact.activity == None)  # noqa: E711
            return query

        def _get_all_filter_by_category(query):
            if category is False:
                return query
            if category:
                if category.pk:
                    query = query.filter(AlchemyCategory.pk == category.pk)
                else:
                    query = query.filter(
                        func.lower(AlchemyCategory.name) == func.lower(category.name)
                    )
            else:
                query = query.filter(AlchemyFact.category == None)  # noqa: E711
            return query

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
            if group_activity:
                # NOTE:The wrong group-by returns 1 record:
                #        query = query.group_by(AlchemyFact.activity)
                #      generates:
                #         GROUP BY activities.id = facts.activity_id
                #      But we want more simply:
                #         GROUP BY activities.id
                query = query.group_by(AlchemyActivity.pk)
            if group_category:
                query = query.group_by(AlchemyCategory.pk)
            if group_tags:
                query = query.group_by(AlchemyTag.pk)
            return query

        # ***

        # FIXME/2018-06-09: (lb): DRY: Combine each manager's _get_all_order_by.
        def _get_all_order_by(query, span_cols=None):
            direction = desc if sort_order == 'desc' else asc
            if sort_col == 'start':
                direction = desc if not sort_order else direction
                query = self._get_all_order_by_times(query, direction)
            elif sort_col == 'time':
                assert include_usage and span_cols is not None
                direction = desc if not sort_order else direction
                query = query.order_by(direction(span_cols[i_duration]))
            elif sort_col == 'activity':
                query = query.order_by(direction(AlchemyActivity.name))
                query = query.order_by(direction(AlchemyCategory.name))
            elif sort_col == 'category':
                query = query.order_by(direction(AlchemyCategory.name))
                query = query.order_by(direction(AlchemyActivity.name))
            else:
                # Meh. Rather than make a custom --order for each command,
                # just using the same big list. So 'activity', 'category',
                # etc., are acceptable here, if not simply ignored.
                assert sort_col in ('', 'name', 'tag', 'fact')
                direction = desc if not sort_order else direction
                query = self._get_all_order_by_times(query, direction)
            return query

        # ***

        def _get_all_with_entities(query, span_cols, grouping_cols, tags_col):
            # Even if grouping, we still want to fetch all columns. For one,
            # _process_results expects a Fact object as leading item in each
            # result tuple, and also because as_hamster expects certain fields
            # (and in a specific order). We'd also have to at least specify
            # AlchemyFact.pk so that SQLAlchemy uses `FROM facts`, and not,
            # e.g., `FROM category`. So use all Fact cols to start the select.
            columns = [AlchemyFact]

            # The order of the aggregate columns added here is reflected
            # by RESULT_GRP_INDEX.
            if span_cols is not None:
                columns.extend(span_cols)
            if grouping_cols is not None:
                columns.extend(grouping_cols)

            # Ensure tags_col is last, because _process_record_tags expects (pops) it.
            if tags_col is not None:
                assert not lazy_tags
                columns.append(tags_col)

            query = query.with_entities(*columns)

            return query

        # ***

        return _get_all_facts()

    # ***

    def _get_all_order_by_times(self, query, direction, fact=None):
        if fact and not fact.unstored:
            query = query.filter(AlchemyFact.pk != fact.pk)

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

        condition = and_(condition, AlchemyFact.deleted == False)  # noqa: E712

        query = query.filter(condition)

        query = self._get_all_order_by_times(query, asc, fact=fact)

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

        condition = and_(condition, AlchemyFact.deleted == False)  # noqa: E712

        query = query.filter(condition)

        query = self._get_all_order_by_times(query, desc, fact=fact)

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

        condition = and_(condition, AlchemyFact.deleted == False)  # noqa: E712

        query = query.filter(condition)

        # Exclude fact.pk from results.
        query = self._get_all_order_by_times(query, desc, fact=fact)

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
            elif fact.end and isinstance(fact.end, datetime):
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

        condition = and_(condition, AlchemyFact.deleted == False)  # noqa: E712

        query = query.filter(condition)

        # Exclude fact.pk from results.
        query = self._get_all_order_by_times(query, asc, fact=fact)

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

        query = self._get_all_order_by_times(query, asc)

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

        query = self._get_all_order_by_times(query, asc)

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


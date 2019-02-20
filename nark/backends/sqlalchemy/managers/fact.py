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

from builtins import str
from datetime import datetime

from future.utils import python_2_unicode_compatible
from sqlalchemy import asc, desc, func
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


@python_2_unicode_compatible
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
            # The fact is ongoing, so also match the ongoing Fact in the store.
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

            ValueError: If the timewindow is already occupied.
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
            ValueError: If the timewindow is already occupied.
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
                allow_momentaneous = self.store.config['allow_momentaneous']
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

    def _get_all(
        self,
        endless=False,
        partial=False,
        include_usage=False,
        count_results=False,
        since=None,
        until=None,
        # FIXME/2018-06-09: (lb): Implement deleted/hidden.
        deleted=False,
        search_term='',
        activity=False,
        category=False,
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
            search_term (text_type):
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

        def _get_all_facts():
            message = _(
                'since: {} / until: {} / srch_term: {} / srt_col: {} / srt_ordr: {}'
                .format(since, until, search_term, sort_col, sort_order)
            )
            self.store.logger.debug(message)

            query = self.store.session.query(AlchemyFact)

            query, span_col = _get_all_prepare_span_col(query)

            query, tags_col = _get_all_prepare_tags_col(query)

            query = _get_all_prepare_joins(query)

            query = _get_all_filter_partial(query)

            query = _get_all_filter_by_activity(query)

            query = _get_all_filter_by_category(query)

            query = _get_all_filter_by_search_term(query)

            query = query_apply_true_or_not(query, AlchemyFact.deleted, deleted)

            query = _get_all_filter_by_ongoing(query)

            query = _get_all_order_by(query, span_col, tags_col)

            query = query_apply_limit_offset(query, **kwargs)

            query = _get_all_with_entities(query, span_col, tags_col)

            self.store.logger.debug(_('query: {}'.format(str(query))))

            if count_results:
                results = query.count()
            else:
                # Profiling: 2018-07-15: (lb): ~ 0.120 s. to fetch latest of 20K Facts.
                records = query.all()
                results = _process_results(records, span_col, tags_col)

            return results

        def _process_results(records, span_col, tags_col):
            if span_col is None and tags_col is None:
                if raw:
                    return records
                else:
                    return [fact.as_hamster(self.store) for fact in records]

            results = []
            for fact, *cols in records:
                new_tags = None
                if not lazy_tags:
                    tags = cols.pop()
                    new_tags = tags.split(magic_tag_sep) if tags else []

                if not raw:
                    new_fact = fact.as_hamster(self.store, new_tags)
                else:
                    if new_tags:
                        fact.tags = new_tags
                    new_fact = fact

                if len(cols):
                    results.append((new_fact, *cols))
                else:
                    results.append(new_fact)
            return results

        # ***

        def _get_all_prepare_tags_col(query):
            if lazy_tags:
                return query, None
            # (lb): Always include tags. We could let SQLAlchemy lazy load,
            # but this can be slow. E.g., on 15K Facts, calling fact.tags on
            # each -- triggering lazy load -- takes 7 seconds on my machine.
            # As opposed to 0 seconds (rounded down) when preloading tags.
            tags_col = func.group_concat(
                AlchemyTag.name, magic_tag_sep,
            ).label("facts_tags")
            query = query.add_columns(tags_col)
            query = query.outerjoin(fact_tags)
            query = query.outerjoin(AlchemyTag)
            query = query.group_by(AlchemyFact.pk)
            # (lb): 2019-01-22: Old comment re: joinedload. Leaving here as
            # documentation in case I try using joinedload again in future.
            #   # FIXME/2018-06-25: (lb): Not quite sure this'll work...
            #   # http://docs.sqlalchemy.org/en/latest/orm/loading_relationships.html
            #   #   # joined-eager-loading
            #   from sqlalchemy.orm import joinedload
            #   # 2019-01-22: Either did not need, or did not work, !remember which!
            #   query = query.options(joinedload(AlchemyFact.tags))
            return query, tags_col

        def _get_all_prepare_span_col(query):
            if not include_usage:
                return query, None

            span_col = (
                func.julianday(AlchemyFact.end) - func.julianday(AlchemyFact.start)
            ).label('span')
            query = self.store.session.query(AlchemyFact, span_col)
            return query, span_col

        def _get_all_prepare_joins(query):
            if (
                include_usage
                or (activity is not False)
                or (category is not False)
                or search_term
            ):
                query = query.outerjoin(AlchemyFact.activity)  # Same as: AlchemyActivity
            if (category is not False) or search_term:
                query = query.outerjoin(AlchemyCategory)
            return query

        def _get_all_filter_partial(query):
            fmt_since = self._get_sql_datetime(since) if since else None
            fmt_until = self._get_sql_datetime(until) if until else None
            if partial:
                query = _get_partial_overlaps(query, fmt_since, fmt_until)
            else:
                query = _get_complete_overlaps(query, fmt_since, fmt_until, endless)
            return query

        def _get_partial_overlaps(query, since, until):
            """Return all facts where either start or end falls within the timeframe."""
            if since and not until:
                # (lb): Checking AlchemyFact.end >= since is sorta redundant,
                # because AlchemyFact.start >= since should guarantee that.
                query = query.filter(
                    or_(
                        func.datetime(AlchemyFact.start) >= since,
                        func.datetime(AlchemyFact.end) >= since,
                    ),
                )
            elif not since and until:
                # (lb): Checking AlchemyFact.start <= until is sorta redundant,
                # because AlchemyFact.end <= until should guarantee that.
                query = query.filter(
                    or_(
                        func.datetime(AlchemyFact.start) <= until,
                        func.datetime(AlchemyFact.end) <= until,
                    ),
                )
            elif since and until:
                query = query.filter(or_(
                    and_(
                        func.datetime(AlchemyFact.start) >= since,
                        func.datetime(AlchemyFact.start) <= until,
                    ),
                    and_(
                        func.datetime(AlchemyFact.end) >= since,
                        func.datetime(AlchemyFact.end) <= until,
                    ),
                ))
            else:
                pass
            return query

        def _get_complete_overlaps(query, since, until, endless=False):
            """Return all facts with start and end within the timeframe."""
            if since:
                query = query.filter(func.datetime(AlchemyFact.start) >= since)
            if until:
                query = query.filter(func.datetime(AlchemyFact.end) <= until)
            elif endless:
                query = query.filter(AlchemyFact.end == None)  # noqa: E711
            return query

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

        def _get_all_filter_by_ongoing(query):
            if not exclude_ongoing:
                return query
            if exclude_ongoing:
                query = query.filter(AlchemyFact.end != None)  # noqa: E711
            return query

        # FIXME/2018-06-09: (lb): DRY: Combine each manager's _get_all_order_by.
        def _get_all_order_by(query, span_col=None, tags_col=None):
            direction = desc if sort_order == 'desc' else asc
            if sort_col == 'start':
                direction = desc if not sort_order else direction
                query = self._get_all_order_by_times(query, direction)
            elif sort_col == 'time':
                assert include_usage and span_col is not None
                direction = desc if not sort_order else direction
                query = query.order_by(direction(span_col))
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

        def _get_all_with_entities(query, span_col, tags_col):
            columns = []

            if span_col is not None:
                # Throw in the count column, which act/cat/tag fetch, so we can
                # use the same utility functions (that except a count column).
                static_count = '1'
                columns.append(static_count)
                columns.append(span_col)

            if tags_col is not None:
                assert not lazy_tags
                columns.append(tags_col)

            query = query.with_entities(AlchemyFact, *columns)

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

    def _get_sql_datetime(self, datetm):
        # Be explicit with the format used by the SQL engine, otherwise,
        #   e.g., and_(AlchemyFact.start > start) might match where
        #   AlchemyFact.start == start. In the case of SQLite, the stored
        #   date will be translated with the seconds, even if 0, e.g.,
        #   "2018-06-29 16:32:00", but the datetime we use for the compare
        #   gets translated without, e.g., "2018-06-29 16:32". And we
        #   all know that "2018-06-29 16:32:00" > "2018-06-29 16:32".
        # See also: func.datetime(AlchemyFact.start/end).
        cmp_fmt = '%Y-%m-%d %H:%M:%S'
        text = datetm.strftime(cmp_fmt)
        return text

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
                        AlchemyFact.pk < fact.pk,
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
                    AlchemyFact.pk > fact.pk,
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


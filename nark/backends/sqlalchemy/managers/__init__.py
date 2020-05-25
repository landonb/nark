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

"""``nark`` storage object managers."""

from gettext import gettext as _

from sqlalchemy import asc, desc, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql.expression import and_, or_

from ..objects import AlchemyActivity, AlchemyCategory, AlchemyFact, AlchemyTag

__all__ = (
    'BaseAlchemyManager',
    'query_apply_limit_offset',
    'query_apply_true_or_not',
    'query_sort_order_at_index',
)


def query_apply_limit_offset(query, limit=None, offset=None):
    """
    Applies 'limit' and 'offset' to the database fetch query

    On applies 'limit' if specified; and only applies 'offset' if specified.

    Args:
        query (???): Query (e.g., return from self.store.session.query(...))

        kwargs (keyword arguments):
            limit (int|str, optional): Limit to apply to the query.

            offset (int|str, optional): Offset to apply to the query.

    Returns:
        list: The query passed in, possibly updated with limit and/or offset.
    """
    if limit and limit > 0:
        query = query.limit(limit)
    if offset and offset > 0:
        query = query.offset(offset)
    return query


def query_apply_true_or_not(query, column, condition):
    if condition is not None:
        return query.filter(column == condition)
    return query


def query_sort_order_at_index(sort_orders, idx):
    try:
        direction = desc if sort_orders[idx] == 'desc' else asc
    except IndexError:
        direction = asc
    return direction


# ***

class BaseAlchemyManager(object):
    """Base class for sqlalchemy managers."""

    # ***

    def add_and_commit(self, alchemy_item, raw=False, skip_commit=False):
        """
        Adds the item to the data store, and perhaps calls commit.

        Generally, unless importing Facts, the session is committed
        after an item is added or updated. However, when adding or
        updating a Fact, we might also create other items (activity,
        category, tags), so we delay committing until everything is
        added/updated.
        """
        def _add_and_commit():
            session_add()
            session_commit_maybe()
            result = prepare_item()
            self.store.logger.debug(_("Added item: {!r}".format(result)))
            return result

        def session_add():
            self.store.session.add(alchemy_item)

        def session_commit_maybe():
            if skip_commit:
                return
            try:
                self.store.session.commit()
            except IntegrityError as err:
                message = _(
                    "An error occured! Are you sure that the {0}'s name "
                    "or ID is not already present? Error: '{1}'.".format(
                        self.__class__.__name__, err,
                    )
                )
                self.store.logger.error(message)
                raise ValueError(message)

        def prepare_item():
            result = alchemy_item
            if not raw:
                result = alchemy_item.as_hamster(self.store)
            return result

        return _add_and_commit()

    # ***

    # ***
    # *** _get_all() et al
    # ***

    def _get_all(self, query_terms):
        """
        Retrieve all matching activities stored in the backend.

        Args:
            query_terms (nark.managers.query_terms.QueryTerms, required):
                The requested query settings used to find Activities,
                and also the requested results settings. See the QueryTerms
                class for details.

        Returns:
            list: List of ``nark.Activity`` instances matching constrains.
                The list is ordered by ``Activity.name``.
        """
        qt = query_terms

        # If user is requesting sorting according to time, need Fact table.
        requires_fact_table = (
            qt.include_usage
            or set(qt.sort_cols).intersection(('start', 'usage', 'time'))
            or qt.since or qt.until or qt.endless
        )

        # Bounce to the simple get() method if a PK specified.
        if qt.key:
            activity = self.get(pk=qt.key, deleted=qt.deleted, raw=qt.raw)
            if qt.include_usage:
                activity = (activity,)
            return [activity]

        def _gather_items():
            self.store.logger.debug(qt)

            query, agg_cols = _get_all_start_query()

            query = self.query_filter_by_fact_times(
                query, qt.since, qt.until, qt.endless, qt.partial,
            )

            query = self._get_all_filter_by_activities(
                query, qt.match_activities + [qt.activity],
            )

            query = self._get_all_filter_by_categories(
                query, qt.match_categories + [qt.category],
            )

            query = _get_all_filter_by_search_term(query)

            query = _get_all_group_by(query, agg_cols)

            query = self._get_all_order_by(
                query, qt.sort_cols, qt.sort_orders, *agg_cols,
            )

            query = query_apply_limit_offset(query, qt.limit, qt.offset)

            query = _get_all_with_entities(query, agg_cols)

            self._log_sql_query(query)

            if qt.count_results:
                results = query.count()
            else:
                results = query.all()
                results = _process_results(results)

            return results

        # ***

        def _get_all_start_query():
            agg_cols = []
            if not requires_fact_table:
                query = self.store.session.query(AlchemyActivity)
            else:
                if requires_fact_table:
                    if qt.include_usage or 'usage' in qt.sort_cols:
                        count_col = func.count(AlchemyActivity.pk).label('uses')
                        agg_cols.append(count_col)
                    if qt.include_usage or 'time' in qt.sort_cols:
                        time_col = func.sum(
                            func.julianday(AlchemyFact.end)
                            - func.julianday(AlchemyFact.start)
                        ).label('span')
                        agg_cols.append(time_col)
                query = self.store.session.query(AlchemyFact, *agg_cols)
                query = query.join(AlchemyFact.activity)

            # Note that SQLAlchemy automatically lazy-loads any attribute
            # that's another object but that we did not join. E.g., if this
            # is query for Activity, and we did not join Category, then when
            # the code references activity.category on one of the returned
            # objects, the value will then be retrieved from the data store.
            # So we do not need to join values we do not need until after the
            # query. Except unless we want to sort by category.name, then we
            # need to join the table, so we can reference category.name in the
            # query.
            if 'category' in qt.sort_cols:
                query = query.join(AlchemyCategory)

            return query, agg_cols

        # ***

        def _get_all_filter_by_search_term(query):
            if not qt.search_term:
                return query

            condits = None
            for term in qt.search_term:
                condit = AlchemyActivity.name.ilike('%{}%'.format(term))
                if condits is None:
                    condits = condit
                else:
                    condits = or_(condits, condit)

            query = query.filter(condits)
            return query

        # ***

        def _get_all_group_by(query, agg_cols):
            if not agg_cols:
                return query
            query = query.group_by(AlchemyActivity.pk)
            return query

        # ***

        def _get_all_with_entities(query, agg_cols):
            if not agg_cols:
                return query
            # (lb): Get tricky with it. The query now SELECTs all Fact columns,
            #  and it JOINs and GROUPs BY activities to produce the counts. But
            #  the Fact is meaningless after the group-by; we want the Activity
            #  instead. So use with_entities trickery to tell SQLAlchemy which
            #  columns we really want -- it'll transform the query so that the
            #  SELECT fetches all the Activity columns; but the JOIN and GROUP BY
            #  remain the same! (I'm not quite sure how it works, but it does.)
            # And as an aside, because of the 1-to-many relationship, the
            #  Activity table does not reference Fact, so, e.g., this wouldn't
            #  work, or at least I assume not, but maybe SQLAlchemy would figure
            #  it out: self.store.session.query(AlchemyActivity).join(AlchemyFact).
            query = query.with_entities(AlchemyActivity, *agg_cols)
            return query

        # ***

        def _process_results(records):
            return self._get_all_process_results_simple(
                records,
                raw=qt.raw,
                include_usage=requires_fact_table,
                requested_usage=qt.include_usage,
            )

        # ***

        return _gather_items()

    # ***

    def query_filter_by_fact_times(
        self, query, since=None, until=None, endless=False, partial=False,
    ):
        def _query_filter_by_fact_times(query, since, until, endless, partial):
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

        return _query_filter_by_fact_times(query, since, until, endless, partial)

    # ***

    def _get_all_filter_by_activities(self, query, activities=[]):
        filters = []
        for activity in activities:
            item_filter = self._get_all_filter_by_activity(activity)
            if item_filter is not None:
                filters.append(item_filter)
        if filters:
            query = query.filter(or_(*filters))
        return query

    def _get_all_filter_by_activity(self, activity):
        if activity is False:
            return None

        item_filter = None
        if activity is not None:
            activity_name = self._get_all_filter_by_activity_name(activity)
            if activity_name is None:
                item_filter = AlchemyActivity.pk == activity.pk
            else:
                # NOTE: Strict name matching, case and exactness.
                #       Not, say, func.lower(name) == func.lower(...),
                #       or using sqlalchemy ilike().
                item_filter = AlchemyActivity.name == activity_name
        else:  # activity is None.
            item_filter = AlchemyFact.activity == None  # noqa: E711
        return item_filter

    def _get_all_filter_by_activity_name(self, activity):
        activity_name = None
        try:
            if not activity.pk:
                activity_name = activity.name
        except AttributeError:
            activity_name = activity
        return activity_name

    # ***

    def _get_all_filter_by_categories(self, query, categories=[]):
        filters = []
        for category in categories:
            item_filter = self._get_all_filter_by_category(category)
            if item_filter is not None:
                filters.append(item_filter)
        if filters:
            query = query.filter(or_(*filters))
        return query

    def _get_all_filter_by_category(self, category):
        if category is False:
            return None

        item_filter = None
        if category is not None:
            category_name = self._get_all_filter_by_category_name(category)
            if category_name is None:
                item_filter = AlchemyCategory.pk == category.pk
            else:
                # NOTE: Strict name matching, case and exactness.
                item_filter = AlchemyCategory.name == category_name
        else:
            item_filter = AlchemyFact.category == None  # noqa: E711
        return item_filter

    def _get_all_filter_by_category_name(self, category):
        category_name = None
        try:
            if not category.pk:
                category_name = category.name
        except AttributeError:
            category_name = category
        return category_name

    # ***

    def _get_all_order_by(self, query, sort_cols, sort_orders, *agg_cols):
        for idx, sort_col in enumerate(sort_cols):
            direction = query_sort_order_at_index(sort_orders, idx)
            query = self._get_all_order_by_col(query, sort_col, direction, *agg_cols)
        return query

    def _get_all_order_by_col(
        self, query, sort_col, direction, count_col=None, time_col=None,
    ):
        raise NotImplemented

    def _get_all_order_by_col_common(
        self, query, sort_col, direction, default, count_col=None, time_col=None,
    ):
        # Each get_all() method maintains an include_usage that indicates
        # if AlchemyFact is joined, but we can glean same if the agg_cols,
        # count_col and time_col, are not None; that'll mean Fact avail, too.
        target = None
        check_aggs = False
        if sort_col == 'start':
            target = AlchemyFact.start
            check_aggs = True
        elif sort_col == 'usage':
            target = count_col
            check_aggs = True
        elif sort_col == 'time':
            target = time_col
            check_aggs = True
        elif (
            sort_col == 'activity'
            or (default == 'activity' and (sort_col == 'name' or not sort_col))
        ):
            target = AlchemyActivity.name
        elif (
            sort_col == 'category'
            or (default == 'category' and (sort_col == 'name' or not sort_col))
        ):
            target = AlchemyCategory.name
        elif (
            sort_col == 'tag'
            or (default == 'tag' and (sort_col == 'name' or not sort_col))
        ):
            target = AlchemyTag.name

        if (
            target is not None
            and check_aggs
            and count_col is None
            and time_col is None
        ):
            self.store.logger.warn("Invalid sort_col: {}".format(sort_col))
        elif target is None:
            self.store.logger.warn("Unknown sort_col: {}".format(sort_col))
        else:
            query = query.order_by(direction(target))
        return query

    # ***

    def _get_all_process_results_simple(
        self,
        records,
        raw,
        include_usage,
        requested_usage,
    ):
        def _process_results(records):
            if not records or not include_usage:
                return _process_records_items_only(records)
            return _process_records_items_and_aggs(records)

        def _process_records_items_only(records):
            if not raw:
                return [item.as_hamster(self.store) for item in records]
            return records

        def _process_records_items_and_aggs(records):
            if not raw:
                return _process_records_items_and_aggs_hydrate(records)
            return records

        def _process_records_items_and_aggs_hydrate(records):
            if requested_usage:
                return [(item.as_hamster(self.store), *cols) for item, *cols in records]
            return [item.as_hamster(self.store) for item, *cols in records]

        return _process_results(records)

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

    def _log_sql_query(self, query):
        if self.store.config['dev.catch_errors']:
            # 2020-05-21: I don't generally like more noise in my tmux dev environment
            # logger pane, but I do like seeing the query, especially with all the
            # recent get_all() tweaks (improved grouping, sorting, and aggregates).
            logf = self.store.logger.warn
        else:
            logf = self.store.logger.debug
        logf('Query: {}'.format(str(query)))

    # ***

# ***


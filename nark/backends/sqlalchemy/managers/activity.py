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

from sqlalchemy import asc, desc, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql.expression import or_

from . import BaseAlchemyManager, query_apply_limit_offset, query_apply_true_or_not
from ....managers.activity import BaseActivityManager
from ..objects import AlchemyActivity, AlchemyCategory, AlchemyFact


class ActivityManager(BaseAlchemyManager, BaseActivityManager):
    def get_or_create(self, activity, raw=False, skip_commit=False):
        """
        Custom version of the default method in order to provide access to
        Alchemy instances.

        Args:
            activity (nark.Activity): Activity we want.
            raw (bool): Whether to return the AlchemyActivity instead.

        Returns:
            nark.Activity: Activity.
        """

        message = _("Received {!r}, raw={}.").format(activity, raw)
        self.store.logger.debug(message)

        try:
            result = self.get_by_composite(activity.name, activity.category, raw=raw)
        except KeyError:
            result = self._add(activity, raw=raw, skip_commit=skip_commit)
        self.store.logger.debug(_("Returning {!r}.").format(result))
        return result

    def _add(self, activity, raw=False, skip_commit=False):
        """
        Add a new ``Activity`` instance to the databasse.

        Args:
            activity (nark.Activity): nark activity

        Returns:
            nark.Activity: nark activity representation of stored instance.

        Raises:
            ValueError: If the passed activity has a PK.
            ValueError: If the category/activity.name combination to be added is
                already present in the db.
        """
        self.adding_item_must_not_have_pk(activity)

        try:
            self.get_by_composite(activity.name, activity.category)
            # FIXME/2018-06-08: (lb): DRY: See "Our database already" elsewhere.
            message = _("Our database already contains the passed name/category.name"
                        "combination.")
            self.store.logger.error(message)
            raise ValueError(message)
        except KeyError:
            pass

        alchemy_activity = AlchemyActivity(
            pk=None,
            name=activity.name,
            category=None,
            deleted=bool(activity.deleted),
            # FIXME/2020-05-19: Remove hidden...
            hidden=bool(activity.hidden),
        )
        if activity.category:
            try:
                category = self.store.categories.get_by_name(
                    activity.category.name, raw=True)
            except KeyError:
                category = AlchemyCategory(
                    pk=None,
                    name=activity.category.name,
                    deleted=bool(activity.category.deleted),
                    hidden=bool(activity.category.hidden),
                )
        else:
            category = None
        alchemy_activity.category = category

        result = self.add_and_commit(
            alchemy_activity, raw=raw, skip_commit=skip_commit,
        )

        return result

    def _update(self, activity):
        """
        Update a given Activity.

        Args:
            activity (nark.Activity): Activity to be updated.

        Returns:
            nark.Activity: Updated activity.

        Raises:
            ValueError: If the new name/category.name combination is already taken.
            ValueError: If the the passed activity does not have a PK assigned.
            KeyError: If the the passed activity.pk can not be found.
        """

        message = _("Received {!r}.".format(activity))
        self.store.logger.debug(message)

        if not activity.pk:
            message = _(
                "The activity passed ('{!r}') does not seem to havea PK. We don't know"
                "which entry to modify.".format(activity))
            self.store.logger.error(message)
            raise ValueError(message)

        try:
            self.get_by_composite(activity.name, activity.category)
            # FIXME/2018-06-08: (lb): DRY: See "Our database already" elsewhere.
            message = _("Our database already contains the passed name/category.name"
                        "combination.")
            self.store.logger.error(message)
            raise ValueError(message)
        except KeyError:
            pass

        alchemy_activity = self.store.session.query(AlchemyActivity).get(activity.pk)
        if not alchemy_activity:
            message = _("No activity with this pk can be found.")
            self.store.logger.error(message)
            raise KeyError(message)
        alchemy_activity.name = activity.name
        alchemy_activity.category = self.store.categories.get_or_create(
            activity.category, raw=True,
        )
        alchemy_activity.deleted = bool(activity.deleted)
        try:
            self.store.session.commit()
        except IntegrityError as err:
            message = _(
                'There seems to already be an activity like this for the given category.'
                " Cannot change this activity's values. Original exception: {}"
            ).format(str(err))
            self.store.logger.error(message)
            raise ValueError(message)
        result = alchemy_activity.as_hamster(self.store)
        self.store.logger.debug(_("Returning: {!r}.").format(result))
        return result

    def remove(self, activity):
        """
        Remove an activity from our internal backend.

        Args:
            activity (nark.Activity): The activity to be removed.

        Returns:
            bool: True

        Raises:
            KeyError: If the given ``Activity`` can not be found in the database.
        """

        message = _("Received {!r}.").format(activity)
        self.store.logger.debug(message)

        if not activity.pk:
            message = _(
                "The activity you passed does not have a PK. Please provide one."
            )
            self.store.logger.error(message)
            raise ValueError(message)

        alchemy_activity = self.store.session.query(AlchemyActivity).get(activity.pk)
        if not alchemy_activity:
            message = _("The activity you try to remove does not seem to exist.")
            self.store.logger.error(message)
            raise KeyError(message)
        if alchemy_activity.facts:
            alchemy_activity.deleted = True
            self.store.activities._update(alchemy_activity)
        else:
            self.store.session.delete(alchemy_activity)
        self.store.session.commit()
        self.store.logger.debug(_("Deleted {!r}.").format(activity))
        return True

    def get(self, pk, deleted=None, raw=False):
        """
        Query for an Activity with given key.

        Args:
            pk: PK to look up.
            raw (bool): Return the AlchemyActivity instead.

        Returns:
            nark.Activity: Activity with given PK.

        Raises:
            KeyError: If no such pk was found.
        """

        message = _("Received PK: '{}', raw={}.").format(pk, raw)
        self.store.logger.debug(message)

        if deleted is None:
            result = self.store.session.query(AlchemyActivity).get(pk)
        else:
            query = self.store.session.query(AlchemyActivity)
            query = query.filter(AlchemyActivity.pk == pk)
            query = query_apply_true_or_not(query, AlchemyActivity.deleted, deleted)
            results = query.all()
            assert(len(results) <= 1)
            result = results[0] if results else None

        if not result:
            message = _("No Activity with 'pk: {}' was found!").format(pk)
            self.store.logger.error(message)
            raise KeyError(message)
        if not raw:
            result = result.as_hamster(self.store)
        self.store.logger.debug(_("Returning: {!r}.").format(result))
        return result

    def get_by_composite(self, name, category, raw=False):
        """
        Retrieve an activity by its name and category.

        Args:
            name (str): The activities name.
            category (nark.Category or None): The activities category.
                May be None.
            raw (bool): Return the AlchemyActivity instead.

        Returns:
            nark.Activity: The activity if it exists in this combination.

        Raises:
            KeyError: if composite key can not be found in the db.

        Note:
            As far as we understand the legacy code in ``__change_category``
            and ``__get_activity_by`` the combination of activity.name and
            activity.category is unique. This is reflected in the uniqueness
            constraint of the underlying table.
        """

        message = _(
            "Received name: '{}' and {!r} with 'raw'={}."
        ).format(name, category, raw)

        self.store.logger.debug(message)

        if category:
            category = category.name
            try:
                alchemy_category = self.store.categories.get_by_name(category, raw=True)
            except KeyError:
                message = _(
                    'The category passed ({}) does not exist in the backend. '
                    'Consequently no related activity can be returned.'
                ).format(category)
                # (lb): This was error, but shouldn't be; callers catch if they care.
                self.store.logger.debug(message)
                raise KeyError(message)
        else:
            alchemy_category = None

        # EXPLAIN: (lb): Is name ever not a string here?
        name = str(name)
        try:
            query = self.store.session.query(AlchemyActivity)
            query = query.filter_by(name=name).filter_by(category=alchemy_category)
            result = query.one()
        except NoResultFound:
            message = _(
                "No activity named '{name}' of category '{category}' was found"
            ).format(name=name, category=category)
            self.store.logger.debug(message)
            raise KeyError(message)
        if not raw:
            result = result.as_hamster(self.store)
        self.store.logger.debug(_("Returning: {!r}.").format(result))
        return result

    # ***

    def get_all(self, *args, include_usage=False, sort_cols=('name',), **kwargs):
        """
        Return all matching activities.

        Args:
            category (nark.Category, optional): Limit activities to this category.
                Defaults to ``False``. If ``category=None`` only activities without a
                category will be considered.
            search_term (str, optional): Limit activities to those matching this string
                a substring in their name. Defaults to ``empty string``.

        Returns:
            list: List of ``nark.Activity`` instances matching constrains.
                This list is ordered by ``Activity.name``.

        Note:
            * This method combines legacy ``storage.db.__get_activities`` and
                ``storage.db.____get_category_activities``.
            * Can search terms be prefixed with 'not'?
            * Original implementation in ``nark.storage.db.__get_activities`` returns
                activity names converted to lowercase!
            * Does exclude activities with ``deleted=True``.
        """
        kwargs['include_usage'] = include_usage
        kwargs['sort_cols'] = sort_cols
        return super(ActivityManager, self).get_all(*args, **kwargs)

    def get_all_by_usage(self, *args, sort_cols=('usage',), **kwargs):
        assert(not args)
        kwargs['include_usage'] = True
        kwargs['sort_cols'] = sort_cols
        return super(ActivityManager, self).get_all(*args, **kwargs)

    def _get_all(
        self,
        # - If specified, look for an Activity with this PK.
        key=None,
        # - If True, include count of Facts that use this Activity, as
        #   well as the cumulative duration (end - start) of those Facts.
        include_usage=True,
        # - If True, return only a count of query matches (an integer).
        #   Otherwise, the method returns a list of result rows.
        count_results=False,
        # - Use since and/or until to find Activities used by Facts from a
        #   specific time range.
        since=None,
        until=None,
        # - Use endless and partial to further influence the time range query.
        endless=False,
        partial=False,
        # FIXME/2020-05-19: (lb): What's the status of the 'deleted' feature?
        # - There's code wired to 'delete' an Activity, but what does that mean?
        # - Really, the user should be able to 'orphan' an Activity (by removing
        #   it from all Facts), but if an Activity is still being used by Facts,
        #   what would delete do? Would we want to remove the Activity from all
        #   the Facts it's applied to?
        #   - I think an 'orphaned' option makes sense here. And maybe a feature
        #     to "rename" an Activity, or really to assign a different Activity
        #     to some collection of Facts. Then maybe 'delete' is okay, i.e.,
        #     once a Activity is orphaned, then it can be deleted.
        #   - In the meantime, the user can hide Activities from the CLI front
        #     end using the ignore feature, which omits matching Activities
        #     from the auto-complete and suggestion widgets.
        # In any case, this 'deleted' option is still wired in the CLI, so
        # maintaining support here. For now.
        deleted=False,
        # - Specify one or_ more search terms to match against the Activity name.
        #   - Note that if more than one term is supplied, they're ORed together,
        #     so an Activity only has to match one term.
        #   - Note also that the search is loose: It ignores case and will match
        #     in the middle of the Activity name.
        search_term=None,
        # - Specify an Activity object to restrict to that specific Activity.
        #   Note that the CLI does not expose this option.
        activity=False,
        # - Specify a name or Category object to restrict to that specific Category.
        #   - Note that this match is strict -- case and exactness count.
        category=False,
        # - MEH: (lb): For parity, could add a 'tags' option to restrict the
        #   search to Activities used on Facts with specific 'tags', but how
        #   complicated and useless does that sound.
        # - (lb): I added grouping support to FactManager.get_all via the options:
        #     group_activity
        #     group_category
        #     group_tags
        #   We could add them to this query, but it'd make it much more complex,
        #   and you'd get essentially the same results as using Fact.get_all (save
        #   for any Activities that are not applied to any Facts, but we can live
        #   with that gap in support). (tl;dr, use `dob list fact` or `dob usage fact`
        #   to group query results, and use the --column option if you want to tweak
        #   the output report columns, e.g., to match this method's output.)
        # - The user can specify one or more columns on which to sort,
        #   and an 'asc' or 'desc' modifier for each column under sort.
        sort_cols='',
        sort_orders='',
        # - The user can request a subset of results.
        limit=None,
        offset=None,
        # - The user can request raw SQLAlchemy results (where each result
        #   has a leaving AlchemyActivity object, and then the 'uses' and
        #   'span' columns; and the result object has object attributes,
        #   e.g., result.uses, result.span); or the user can expect tuple
        #   results (with a proper Activity object as the first item in
        #   the tuple, and the extra columns following). Note that when
        #   raw=False, it is up to the caller to know how tuple layout.
        raw=False,
    ):
        """
        FIXME: Update this docstring.

        Retrieve all matching activities stored in the backend.

        Args:
            include_usage (int, optional): If true, include count of Facts that reference
                each Activity.
            search_term (list of str, optional): Limit activities to those matching a
                substring in their name. Defaults to None/disabled.
            activity (nark.Activity, optional): Limit activities to this activity.
                Defaults to ``False``. If ``activity=None`` only activities with a
                matching name will be considered.
            category (nark.Category or str, optional): Limit activities to this
                category. Defaults to ``False``. If ``category=None`` only activities
                without a category will be considered.
            sort_cols (list of str, optional): Which column(s) to sort by. Defaults to
                'activity'. Choices: 'activity, 'category', 'start', 'usage'.
                Note that 'start' and 'usage' only apply if include_usage.
            sort_orders (list of str, optional): Each element one of:
                'asc': Whether to search the results in ascending order.
                'desc': Whether to search the results in descending order.
            limit (int, optional): Query "limit".
            offset (int, optional): Query "offset".

        Returns:
            list: List of ``nark.Activity`` instances matching constrains.
                The list is ordered by ``Activity.name``.
        """
        # If user is requesting sorting according to time, need Fact table.
        requested_usage = include_usage
        include_usage = (
            include_usage
            or set(sort_cols).intersection(('start', 'usage', 'time'))
        )

        # Bounce to the simple get() method if a PK specified.
        if key:
            activity = self.get(pk=key, deleted=deleted, raw=raw)
            if requested_usage:
                activity = (activity,)
            return [activity]

        def _get_all_activities():
            message = (
                _('usage: {} / term: {} / cat.: {} / act.: {} / col: {} / order: {}')
                .format(
                    include_usage,
                    search_term,
                    category,
                    activity,
                    sort_cols,
                    sort_orders,
                )
            )
            self.store.logger.debug(message)

            query, agg_cols = _get_all_start_query()

            query = self.get_all_filter_partial(
                query, since=since, until=until, endless=endless, partial=partial,
            )

            query = _get_all_filter_by_category(query)

            query = _get_all_filter_by_activity(query)

            query = _get_all_filter_by_search_term(query)

            query = _get_all_order_by(query, *agg_cols)

            query = _get_all_group_by(query, agg_cols)

            query = query_apply_limit_offset(query, limit=limit, offset=offset)

            query = _get_all_with_entities(query, agg_cols)

            self.store.logger.debug(_('Query') + ': {}'.format(str(query)))

            if count_results:
                results = query.count()
            else:
                results = query.all()
                results = _process_results(results)

            return results

        # ***

        def _get_all_start_query():
            agg_cols = []
            if not (include_usage or since or until or endless):
                query = self.store.session.query(AlchemyActivity)
            else:
                if include_usage:
                    count_col = func.count(AlchemyActivity.pk).label('uses')
                    agg_cols.append(count_col)
                    time_col = func.sum(
                        func.julianday(AlchemyFact.end)
                        - func.julianday(AlchemyFact.start)
                    ).label('span')
                    agg_cols.append(time_col)
                    query = self.store.session.query(AlchemyFact, count_col, time_col)
                query = query.join(AlchemyFact.activity)
                # NOTE: (lb): SQLAlchemy will lazy load category if/when caller
                #       references it. (I tried using query.options(joinedload(...))
                #       but that route was a mess; and I don't know SQLAlchemy well.)

            # SQLAlchemy automatically lazy-loads activity.category if we
            # reference it after executing the query, so we don't need to
            # join, except that we want to sort by category.name, so we do.
            query = query.join(AlchemyCategory)

            return query, agg_cols

        # ***

        def _get_all_filter_by_category(query):
            if category is False:
                return query
            # FIXME/2018-05-15 22:30: (lb): MRU activities by category: GLOB:
            #   do fuzzy search on name rather than PK, if special query,
            #     e.g., ``if '*' in category.name: ...``
            if category:
                category_name = None
                if isinstance(category, str):
                    category_name = category
                elif not category.pk:
                    category_name = category.name

                if not category_name:
                    query = query.filter(AlchemyCategory.pk == category.pk)
                else:
                    query = query.filter(
                        func.lower(AlchemyCategory.name) == func.lower(category_name)
                    )
            else:
                query = query.filter(AlchemyActivity.category == None)  # noqa: E711
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
            else:  # activity is None.
                query = query.filter(AlchemyFact.activity == None)  # noqa: E711
            return query

        def _get_all_filter_by_search_term(query):
            if not search_term:
                return query

            condits = None
            for term in search_term:
                condit = AlchemyActivity.name.ilike('%{}%'.format(term))
                if condits is None:
                    condits = condit
                else:
                    condits = or_(condits, condit)

            query = query.filter(condits)
            return query

        # ***

        def _get_all_order_by(query, count_col=None, time_col=None):
            for idx, sort_col in enumerate(sort_cols):
                direction = desc if sort_orders[idx] == 'desc' else asc
                query = _get_all_order_by_col(
                    query, sort_col, direction, count_col, time_col,
                )
            return query

        def _get_all_order_by_col(query, sort_col, direction, count_col, time_col):
            if sort_col == 'start':
                query = query.order_by(direction(AlchemyFact.start))
            elif sort_col == 'usage':
                query = query.order_by(direction(count_col))
            elif sort_col == 'time':
                query = query.order_by(direction(time_col))
            elif sort_col == 'activity' or sort_col == 'name' or not sort_col:
                query = query.order_by(direction(AlchemyActivity.name))
                # MAYBE/2020-05-19: Now that sort_cols is multiple=True, omit this?:
                query = query.order_by(direction(AlchemyCategory.name))
            elif sort_col == 'category':
                query = query.order_by(direction(AlchemyCategory.name))
                # MAYBE/2020-05-19: Now that sort_cols is multiple=True, omit this?:
                query = query.order_by(direction(AlchemyActivity.name))
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

        # ***

        return _get_all_activities()


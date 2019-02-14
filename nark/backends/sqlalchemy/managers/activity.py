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

from future.utils import python_2_unicode_compatible
from six import text_type
from sqlalchemy import asc, desc, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound

from . import BaseAlchemyManager, query_apply_limit_offset, query_apply_true_or_not
from ....managers.activity import BaseActivityManager
from ..objects import AlchemyActivity, AlchemyCategory, AlchemyFact


@python_2_unicode_compatible
class ActivityManager(BaseAlchemyManager, BaseActivityManager):
    def get_or_create(self, activity, raw=False, skip_commit=False):
        """
        Custom version of the default method in order to provide access to
        Alchemy instances.

        Args:
            activity (nark.Activity): Activity we want.
            raw (bool): Wether to return the AlchemyActivity instead.

        Returns:
            nark.Activity: Activity.
        """

        message = _("Received {!r}, raw={}.".format(activity, raw))
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
        except IntegrityError as e:
            message = _(
                'There seems to already be an activity like this for the given category.'
                " Cannot change this activity's values. Original exception: {}".format(e)
            )
            self.store.logger.error(message)
            raise ValueError(message)
        result = alchemy_activity.as_hamster(self.store)
        self.store.logger.debug(_("Returning: {!r}.".format(result)))
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

        message = _("Received {!r}.".format(activity))
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
        self.store.logger.debug(_("Deleted {!r}.".format(activity)))
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

        message = _("Received PK: '{}', raw={}.".format(pk, raw))
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
            message = _("No Activity with 'pk: {}' was found!".format(pk))
            self.store.logger.error(message)
            raise KeyError(message)
        if not raw:
            result = result.as_hamster(self.store)
        self.store.logger.debug(_("Returning: {!r}.".format(result)))
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
            "Received name: '{}' and {!r} with 'raw'={}.".format(name, category, raw)
        )
        self.store.logger.debug(message)

        if category:
            # EXPLAIN: (lb): Do we really need to cast?
            category = text_type(category.name)
            try:
                alchemy_category = self.store.categories.get_by_name(category, raw=True)
            except KeyError:
                message = _(
                    'The category passed ({}) does not exist in the backend. '
                    'Consequently no related activity can be returned.'
                    .format(category)
                )
                # (lb): This was error, but shouldn't be; callers catch if they care.
                self.store.logger.debug(message)
                raise KeyError(message)
        else:
            alchemy_category = None

        # EXPLAIN: (lb): Do we really need to cast? Why not to text_type?
        #   (I realize text_type is str in Py3. I'm curious if this fails
        #   in Py2 (dropping Py2 support anyway?). And I'm curious if name
        #   is ever not a string.
        name = str(name)
        try:
            query = self.store.session.query(AlchemyActivity)
            query = query.filter_by(name=name).filter_by(category=alchemy_category)
            result = query.one()
        except NoResultFound:
            message = _(
                "No activity named '{name}' of category '{category}' was found"
                .format(name=name, category=category)
            )
            self.store.logger.debug(message)
            raise KeyError(message)
        if not raw:
            result = result.as_hamster(self.store)
        self.store.logger.debug(_("Returning: {!r}.".format(result)))
        return result

    def get_all(self, *args, include_usage=False, sort_col='name', **kwargs):
        """Get all activities."""
        kwargs['include_usage'] = include_usage
        kwargs['sort_col'] = sort_col
        return self._get_all(*args, **kwargs)

    def get_all_by_usage(self, *args, sort_col='usage', **kwargs):
        assert(not args)
        kwargs['include_usage'] = True
        kwargs['sort_col'] = sort_col
        return self._get_all(*args, **kwargs)

    def _get_all(
        self,
        include_usage=True,
        count_results=False,
        # FIXME/2018-06-20: (lb): Implement since/until.
        since=None,
        until=None,
        # FIXME/2018-06-09: (lb): Implement deleted/hidden.
        deleted=False,
        hidden=False,
        # FIXME/2018-06-20: (lb): Do what with key now?
        key=None,
        search_term='',
        category=False,
        activity=False,
        sort_col='',
        sort_order='',
        # kwargs: limit, offset
        **kwargs
    ):
        """
        FIXME: Update this docstring.

        Retrieve all matching activities stored in the backend.

        Args:
            include_usage (int, optional): If true, include count of Facts that reference
                each Activity.
            search_term (str, optional): Limit activities to those matching a substring
                in their name. Defaults to ``empty string``.
            category (nark.Category or str, optional): Limit activities to this
                category. Defaults to ``False``. If ``category=None`` only activities
                without a category will be considered.
            activity (nark.Activity, optional): Limit activities to this activity.
                Defaults to ``False``. If ``activity=None`` only activities with a
                matching name will be considered.
            sort_col (str, optional): Which columns to sort by. Defaults to 'activity'.
                Choices: 'activity, 'category', 'start', 'usage'.
                Note that 'start' and 'usage' only apply if include_usage.
            sort_order (str, optional): One of:
                'asc': Whether to search the results in ascending order.
                'desc': Whether to search the results in descending order.
            limit (int, optional): Query "limit".
            offset (int, optional): Query "offset".

        Returns:
            list: List of ``nark.Activity`` instances matching constrains.
                The list is ordered by ``Activity.name``.
        """

        def _get_all_activities():
            message = (
                _('usage: {} / term: {} / cat.: {} / act.: {} / col: {} / order: {}')
                .format(
                    include_usage, search_term, category, activity, sort_col, sort_order,
                )
            )
            self.store.logger.debug(message)

            query, agg_cols = _get_all_start_query()

            query = _get_all_filter_by_category(query)

            query = _get_all_filter_by_activity(query)

            query = _get_all_filter_by_search_term(query)

            query = _get_all_order_by(query, *agg_cols)

            query = _get_all_group_by(query, agg_cols)

            query = query_apply_limit_offset(query, **kwargs)

            query = _get_all_with_entities(query, agg_cols)

            self.store.logger.debug(_('Query') + ': {}'.format(str(query)))

            results = query.all() if not count_results else query.count()

            return results

        def _get_all_start_query():
            agg_cols = []
            if not include_usage:
                query = self.store.session.query(AlchemyActivity)
            else:
                count_col = func.count(AlchemyActivity.pk).label('uses')
                agg_cols.append(count_col)

                time_col = func.sum(
                    func.julianday(AlchemyFact.end) - func.julianday(AlchemyFact.start)
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

        def _get_all_filter_by_category(query):
            if category is False:
                return query
            # FIXME/2018-05-15 22:30: (lb): MRU activities by category: GLOB:
            #   do fuzzy search on name rather than PK, if special query,
            #     e.g., ``if '*' in category.name: ...``
            if category:
                category_name = None
                if isinstance(category, text_type):
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
            else:
                query = query.filter(AlchemyFact.activity == None)  # noqa: E711
            return query

        def _get_all_filter_by_search_term(query):
            if not search_term:
                return query
            query = query.filter(
                AlchemyActivity.name.ilike('%{}%'.format(search_term))
            )
            return query

        def _get_all_order_by(query, count_col=None, time_col=None):
            direction = desc if sort_order == 'desc' else asc
            if sort_col == 'start':
                assert include_usage
                direction = desc if not sort_order else direction
                query = query.order_by(direction(AlchemyFact.start))
            elif sort_col == 'usage':
                assert include_usage and count_col is not None
                direction = desc if not sort_order else direction
                query = query.order_by(direction(count_col), direction(time_col))
            elif sort_col == 'time':
                assert include_usage and time_col is not None
                direction = desc if not sort_order else direction
                query = query.order_by(direction(time_col), direction(count_col))
            elif sort_col == 'activity':
                query = query.order_by(direction(AlchemyActivity.name))
                query = query.order_by(direction(AlchemyCategory.name))
            elif sort_col == 'category':
                query = query.order_by(direction(AlchemyCategory.name))
                query = query.order_by(direction(AlchemyActivity.name))
            else:
                assert sort_col in ('', 'name', 'tag', 'fact')
                query = query.order_by(direction(AlchemyActivity.name))
                query = query.order_by(direction(AlchemyCategory.name))
            return query

        def _get_all_group_by(query, agg_cols):
            if not agg_cols:
                return query
            query = query.group_by(AlchemyActivity.pk)
            return query

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

        return _get_all_activities()


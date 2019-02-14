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

from future.utils import python_2_unicode_compatible
from six import text_type
from sqlalchemy import asc, desc, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound

from . import BaseAlchemyManager, query_apply_limit_offset, query_apply_true_or_not
from ....managers.category import BaseCategoryManager
from ..objects import AlchemyActivity, AlchemyCategory, AlchemyFact


@python_2_unicode_compatible
class CategoryManager(BaseAlchemyManager, BaseCategoryManager):
    def get_or_create(self, category, raw=False, skip_commit=False):
        """
        Custom version of the default method in order to provide access
        to alchemy instances.

        Args:
            category (nark.Category): Category we want.
            raw (bool): Wether to return the AlchemyCategory instead.

        Returns:
            nark.Category or None: Category.
        """

        message = _("Received {!r} and raw={}.".format(category, raw))
        self.store.logger.debug(message)

        try:
            category = self.get_by_name(category.name, raw=raw)
        except KeyError:
            category = self._add(category, raw=raw, skip_commit=skip_commit)
        return category

    def _add(self, category, raw=False, skip_commit=False):
        """
        Add a new category to the database.

        This method should not be used by any client code. Call ``save`` to
        make the decission wether to modify an existing entry or to add a new
        one is done correctly.

        Args:
            category (nark.Category): nark Category instance.
            raw (bool): Wether to return the AlchemyCategory instead.

        Returns:
            nark.Category: Saved instance, as_hamster()

        Raises:
            ValueError: If the name to be added is already present in the db.
            ValueError: If category passed already got an PK. Indicating that
                update would be more apropiate.
        """
        self.adding_item_must_not_have_pk(category)

        alchemy_category = AlchemyCategory(
            pk=None,
            name=category.name,
            deleted=bool(category.deleted),
            hidden=bool(category.hidden),
        )

        result = self.add_and_commit(
            alchemy_category, raw=raw, skip_commit=skip_commit,
        )

        return result

    def _update(self, category):
        """
        Update a given Category.

        Args:
            category (nark.Category): Category to be updated.

        Returns:
            nark.Category: Updated category.

        Raises:
            ValueError: If the new name is already taken.
            ValueError: If category passed does not have a PK.
            KeyError: If no category with passed PK was found.
        """

        message = _("Received {!r}.".format(category))
        self.store.logger.debug(message)

        if not category.pk:
            message = _(
                "The category passed ('{!r}') does not seem to havea PK. We don't know"
                "which entry to modify.".format(category)
            )
            self.store.logger.error(message)
            raise ValueError(message)
        alchemy_category = self.store.session.query(AlchemyCategory).get(category.pk)
        if not alchemy_category:
            message = _("No category with PK: {} was found!".format(category.pk))
            self.store.logger.error(message)
            raise KeyError(message)
        alchemy_category.name = category.name

        try:
            self.store.session.commit()
        except IntegrityError as e:
            message = _(
                "An error occured! Is category.name already present in the database?"
                " / Error: '{}'.".format(e)
            )
            self.store.logger.error(message)
            raise ValueError(message)

        return alchemy_category.as_hamster(self.store)

    def remove(self, category):
        """
        Delete a given category.

        Args:
            category (nark.Category): Category to be removed.

        Returns:
            None: If everything went alright.

        Raises:
            KeyError: If the ``Category`` can not be found by the backend.
            ValueError: If category passed does not have an pk.
        """

        message = _("Received {!r}.".format(category))
        self.store.logger.debug(message)

        if not category.pk:
            message = _("PK-less Category. Are you trying to remove a new Category?")
            self.store.logger.error(message)
            raise ValueError(message)
        alchemy_category = self.store.session.query(AlchemyCategory).get(category.pk)
        if not alchemy_category:
            message = _("``Category`` can not be found by the backend.")
            self.store.logger.error(message)
            raise KeyError(message)
        self.store.session.delete(alchemy_category)
        self.store.session.commit()
        message = _("{!r} successfully deleted.".format(category))
        self.store.logger.debug(message)

    def get(self, pk, deleted=None):
        """
        Return a category based on their pk.

        Args:
            pk (int): PK of the category to be retrieved.

        Returns:
            nark.Category: Category matching given PK.

        Raises:
            KeyError: If no such PK was found.

        Note:
            We need this for now, as the service just provides pks, not names.
        """

        message = _("Received PK: '{}'.".format(pk))
        self.store.logger.debug(message)

        if deleted is None:
            result = self.store.session.query(AlchemyCategory).get(pk)
        else:
            query = self.store.session.query(AlchemyCategory)
            query = query.filter(AlchemyCategory.pk == pk)
            query = query_apply_true_or_not(query, AlchemyCategory.deleted, deleted)
            results = query.all()
            assert(len(results) <= 1)
            result = results[0] if results else None

        if not result:
            message = _("No category with 'pk: {}' was found!".format(pk))
            self.store.logger.error(message)
            raise KeyError(message)
        message = _("Returning {!r}.".format(result))
        self.store.logger.debug(message)
        return result.as_hamster(self.store)

    def get_by_name(self, name, raw=False):
        """
        Return a category based on its name.

        Args:
            name (str): Unique name of the category.
            raw (bool): Whether to return the AlchemyCategory instead.

        Returns:
            nark.Category: Category of given name.

        Raises:
            KeyError: If no category matching the name was found.

        """

        message = _("Received name: '{}', raw={}.".format(name, raw))
        self.store.logger.debug(message)

        name = text_type(name)
        try:
            result = self.store.session.query(AlchemyCategory).filter_by(name=name).one()
        except NoResultFound:
            message = _("No category named '{}' was found".format(name))
            self.store.logger.debug(message)
            raise KeyError(message)

        if not raw:
            result = result.as_hamster(self.store)
            self.store.logger.debug(_("Returning: {!r}.").format(result))
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

    # DRY: This fcn. very much similar between activity/category/tag.
    def _get_all(
        self,
        include_usage=True,
        count_results=False,
        # FIXME/2018-06-20: (lb): Implement since/until.
        since=None,
        until=None,
        # FIXME/2018-06-09: (lb): Implement deleted/hidden. [i.e., in UI]
        deleted=False,
        hidden=False,
        # FIXME/2018-06-20: (lb): Do what with key now?
        key=None,
        search_term='',
        activity=False,
        sort_col='',
        sort_order='',
        # kwargs: limit, offset
        **kwargs
    ):
        """
        Get all Categories, possibly filtered by related Activity, and possible sorted.

        Returns:
            list: List of all Categories present in the database, ordered
            by lower(name) or however caller asked that they be ordered.
        """

        def _get_all_categories():
            message = _('usage: {} / term: {} / act.: {} / col: {} / order: {}'.format(
                include_usage, search_term, activity, sort_col, sort_order,
            ))
            self.store.logger.debug(message)

            query, agg_cols = _get_all_start_query()

            query = _get_all_filter_by_activity(query)

            query = _get_all_filter_by_search_term(query)

            # FIXME/LATER/2018-05-29: (lb): Filter by tags used around this time.
            #   E.g., if it's 4 PM, only suggest tags used on same day at same time...
            #   something like that. I.e., tags you use during weekday at work should
            #   be suggested. For now, filter by category can give similar effect,
            #   depending on how one uses categories.

            query = _get_all_order_by(query, *agg_cols)

            query = _get_all_group_by(query, agg_cols)

            query = query_apply_limit_offset(query, **kwargs)

            query = _get_all_with_entities(query, agg_cols)

            self.store.logger.debug(_('Query') + ': {}'.format(str(query)))

            results = query.all() if not count_results else query.count()

            return results

        def _get_all_start_query():
            agg_cols = []
            if (
                not include_usage
                and not activity
                and sort_col not in ['start', 'activity', ]
            ):
                query = self.store.session.query(AlchemyCategory)
            else:
                count_col = func.count(AlchemyCategory.pk).label('uses')
                agg_cols.append(count_col)

                time_col = func.sum(
                    func.julianday(AlchemyFact.end) - func.julianday(AlchemyFact.start)
                ).label('span')
                agg_cols.append(time_col)

                query = self.store.session.query(AlchemyFact, count_col, time_col)
                query = query.join(AlchemyFact.activity)
                query = query.join(AlchemyCategory)

            return query, agg_cols

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
                AlchemyCategory.name.ilike('%{}%'.format(search_term))
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
                if count_col is not None:
                    query = query.order_by(direction(AlchemyActivity.name))
            else:
                # FIXME/2018-05-29: (lb): Are all these sort_col's for real?
                # Seems like they wouldn't sort like user would be expecting.
                assert sort_col in ('', 'name', 'tag', 'fact')
                query = query.order_by(direction(AlchemyCategory.name))
                if count_col is not None:
                    query = query.order_by(direction(AlchemyActivity.name))
            return query

        def _get_all_group_by(query, agg_cols):
            if not agg_cols:
                return query
            query = query.group_by(AlchemyCategory.pk)
            return query

        def _get_all_with_entities(query, agg_cols):
            if not agg_cols:
                return query
            query = query.with_entities(AlchemyCategory, *agg_cols)
            return query

        # ***

        return _get_all_categories()


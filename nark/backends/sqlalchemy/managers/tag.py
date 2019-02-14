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
from ....managers.tag import BaseTagManager
from ..objects import (
    AlchemyActivity,
    AlchemyCategory,
    AlchemyFact,
    AlchemyTag,
    fact_tags
)


@python_2_unicode_compatible
class TagManager(BaseAlchemyManager, BaseTagManager):
    def get_or_create(self, tag, raw=False, skip_commit=False):
        """
        Custom version of the default method in order to provide access to
        alchemy instances.

        Args:
            tag (nark.Tag): Tag we want.
            raw (bool): Wether to return the AlchemyTag instead.

        Returns:
            nark.Tag or None: Tag.
        """

        message = _("Received {!r} and raw={}.".format(tag, raw))
        self.store.logger.debug(message)

        try:
            tag = self.get_by_name(tag.name, raw=raw)
        except KeyError:
            tag = self._add(tag, raw=raw, skip_commit=skip_commit)
        return tag

    def _add(self, tag, raw=False, skip_commit=False):
        """
        Add a new tag to the database.

        This method should not be used by any client code. Call ``save`` to make
        the decission wether to modify an existing entry or to add a new one is
        done correctly..

        Args:
            tag (nark.Tag): nark Tag instance.
            raw (bool): Wether to return the AlchemyTag instead.

        Returns:
            nark.Tag: Saved instance, as_hamster()

        Raises:
            ValueError: If the name to be added is already present in the db.
            ValueError: If tag passed already got an PK. Indicating that update
                would be more apropiate.
        """
        self.adding_item_must_not_have_pk(tag)

        alchemy_tag = AlchemyTag(
            pk=None,
            name=tag.name,
            deleted=bool(tag.deleted),
            hidden=bool(tag.hidden),
        )

        result = self.add_and_commit(
            alchemy_tag, raw=raw, skip_commit=skip_commit,
        )

        return result

    def _update(self, tag):
        """
        Update a given Tag.

        Args:
            tag (nark.Tag): Tag to be updated.

        Returns:
            nark.Tag: Updated tag.

        Raises:
            ValueError: If the new name is already taken.
            ValueError: If tag passed does not have a PK.
            KeyError: If no tag with passed PK was found.
        """

        message = _("Received {!r}.".format(tag))
        self.store.logger.debug(message)

        if not tag.pk:
            message = _(
                "The tag passed ('{!r}') does not seem to havea PK. "
                "We don't know which entry to modify.".format(tag)
            )
            self.store.logger.error(message)
            raise ValueError(message)
        alchemy_tag = self.store.session.query(AlchemyTag).get(tag.pk)
        if not alchemy_tag:
            message = _("No tag with PK: {} was found!".format(tag.pk))
            self.store.logger.error(message)
            raise KeyError(message)
        alchemy_tag.name = tag.name

        try:
            self.store.session.commit()
        except IntegrityError as e:
            message = _(
                "An error occured! Are you sure that tag.name is not "
                "already present in the database? Error: '{}'.".format(e)
            )
            self.store.logger.error(message)
            raise ValueError(message)

        return alchemy_tag.as_hamster(self.store)

    def remove(self, tag):
        """
        Delete a given tag.

        Args:
            tag (nark.Tag): Tag to be removed.

        Returns:
            None: If everything went alright.

        Raises:
            KeyError: If the ``Tag`` can not be found by the backend.
            ValueError: If tag passed does not have an pk.
        """

        message = _("Received {!r}.".format(tag))
        self.store.logger.debug(message)

        if not tag.pk:
            message = _("PK-less Tag. Are you trying to remove a new Tag?")
            self.store.logger.error(message)
            raise ValueError(message)
        alchemy_tag = self.store.session.query(AlchemyTag).get(tag.pk)
        if not alchemy_tag:
            message = _("``Tag`` can not be found by the backend.")
            self.store.logger.error(message)
            raise KeyError(message)
        self.store.session.delete(alchemy_tag)
        self.store.session.commit()
        message = _("{!r} successfully deleted.".format(tag))
        self.store.logger.debug(message)

    def get(self, pk, deleted=None):
        """
        Return a tag based on their pk.

        Args:
            pk (int): PK of the tag to be retrieved.

        Returns:
            nark.Tag: Tag matching given PK.

        Raises:
            KeyError: If no such PK was found.

        Note:
            We need this for now, as the service just provides pks, not names.
        """

        message = _("Received PK: '{}'.".format(pk))
        self.store.logger.debug(message)

        if deleted is None:
            result = self.store.session.query(AlchemyTag).get(pk)
        else:
            query = self.store.session.query(AlchemyTag)
            query = query.filter(AlchemyTag.pk == pk)
            query = query_apply_true_or_not(query, AlchemyTag.deleted, deleted)
            results = query.all()
            assert(len(results) <= 1)
            result = results[0] if results else None

        if not result:
            message = _("No tag with 'pk: {}' was found!".format(pk))
            self.store.logger.error(message)
            raise KeyError(message)
        message = _("Returning {!r}.".format(result))
        self.store.logger.debug(message)
        return result.as_hamster(self.store)

    def get_by_name(self, name, raw=False):
        """
        Return a tag based on its name.

        Args:
            name (str): Unique name of the tag.
            raw (bool): Wether to return the AlchemyTag instead.

        Returns:
            nark.Tag: Tag of given name.

        Raises:
            KeyError: If no tag matching the name was found.

        """

        message = _("Received name: '{}', raw={}.".format(name, raw))
        self.store.logger.debug(message)

        name = text_type(name)
        try:
            result = self.store.session.query(AlchemyTag).filter_by(name=name).one()
        except NoResultFound:
            message = _("No tag named '{}' was found".format(name))
            self.store.logger.debug(message)
            raise KeyError(message)

        if not raw:
            result = result.as_hamster(self.store)
            self.store.logger.debug(_("Returning: {!r}.").format(result))
        return result

    def get_all(self, *args, include_usage=False, sort_col='name', **kwargs):
        """Get all tags."""
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
        activity=False,
        category=False,
        sort_col='',
        sort_order='',
        # kwargs: limit, offset
        **kwargs
    ):
        """
        Get all tags, with filtering and sorting options.

        Returns:
            list: List of all Tags present in the database,
                  ordered by lower(name), or most recently
                  used; possibly filtered by a search term.
        """

        def _get_all_tags():
            message = _('usage: {} / term: {} / col: {} / order: {}'.format(
                include_usage, search_term, sort_col, sort_order,
            ))
            self.store.logger.debug(message)

            query, agg_cols = _get_all_start_query()

            query = _get_all_filter_by_activity(query)

            query = _get_all_filter_by_category(query)

            query = _get_all_filter_by_search_term(query)

            # FIXME/MIGRATIONS: (lb): Add column: Fact.deleted.
            #  condition = and_(condition, not AlchemyFact.deleted)
            #  query = query.filter(condition)

            query = _get_all_group_by(query, agg_cols)

            query = _get_all_order_by(query, *agg_cols)

            query = query_apply_limit_offset(query, **kwargs)

            query = _get_all_with_entities(query, agg_cols)

            self.store.logger.debug(_('query: {}'.format(str(query))))

            results = query.all() if not count_results else query.count()

            return results

        def _get_all_start_query():
            agg_cols = []
            if not include_usage:
                query = self.store.session.query(AlchemyTag)
            else:
                count_col = func.count(AlchemyTag.pk).label('uses')
                agg_cols.append(count_col)

                time_col = func.sum(
                    func.julianday(AlchemyFact.end) - func.julianday(AlchemyFact.start)
                ).label('span')
                agg_cols.append(time_col)

                query = self.store.session.query(AlchemyTag, count_col, time_col)
                query = query.join(fact_tags)
                query = query.join(AlchemyFact)

            return query, agg_cols

        def _get_all_filter_by_activity(query):
            if activity is False:
                return query
            query = query.join(AlchemyActivity)
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
            query = query.join(AlchemyActivity).join(AlchemyCategory)
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
            if not search_term:
                return query
            query = query.filter(
                AlchemyTag.name.ilike('%{}%'.format(search_term))
            )
            return query

        def _get_all_group_by(query, agg_cols):
            if not agg_cols:
                return query
            query = query.group_by(AlchemyTag.pk)
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
                # Meh. Rather than make a custom --order for each command,
                # just using the same big list. So 'activity', 'category',
                # etc., are acceptable here, if not simply ignored.
                assert sort_col in ('', 'name', 'tag', 'fact')
                query = query.order_by(direction(AlchemyTag.name))
            return query

        def _get_all_with_entities(query, agg_cols):
            if not agg_cols:
                return query
            query = query.with_entities(AlchemyTag, *agg_cols)
            return query

        # ***

        return _get_all_tags()


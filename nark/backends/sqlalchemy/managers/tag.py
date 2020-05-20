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
from ....managers.tag import BaseTagManager
from ..objects import (
    AlchemyActivity,
    AlchemyCategory,
    AlchemyFact,
    AlchemyTag,
    fact_tags
)


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

        message = _("Received {!r} and raw={}.").format(tag, raw)
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
                would be more appropriate.
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

        message = _("Received {!r}.").format(tag)
        self.store.logger.debug(message)

        if not tag.pk:
            message = _(
                "The tag passed ('{!r}') does not seem to havea PK. "
                "We don't know which entry to modify."
            ).format(tag)

            self.store.logger.error(message)
            raise ValueError(message)
        alchemy_tag = self.store.session.query(AlchemyTag).get(tag.pk)
        if not alchemy_tag:
            message = _("No tag with PK: {} was found!").format(tag.pk)
            self.store.logger.error(message)
            raise KeyError(message)
        alchemy_tag.name = tag.name

        try:
            self.store.session.commit()
        except IntegrityError as err:
            message = _(
                "An error occured! Are you sure that tag.name is not "
                "already present in the database? Error: '{}'."
            ).format(str(err))
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

        message = _("Received {!r}.").format(tag)
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
        message = _("{!r} successfully deleted.").format(tag)
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

        message = _("Received PK: '{}'.").format(pk)
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
            message = _("No tag with 'pk: {}' was found!").format(pk)
            self.store.logger.error(message)
            raise KeyError(message)
        message = _("Returning {!r}.").format(result)
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

        message = _("Received name: '{}', raw={}.").format(name, raw)
        self.store.logger.debug(message)

        try:
            result = self.store.session.query(AlchemyTag).filter_by(name=name).one()
        except NoResultFound:
            message = _("No tag named '{}' was found").format(name)
            self.store.logger.debug(message)
            raise KeyError(message)

        if not raw:
            result = result.as_hamster(self.store)
            self.store.logger.debug(_("Returning: {!r}.").format(result))
        return result

    def get_all(self, *args, include_usage=False, sort_cols=('name',), **kwargs):
        """
        Get all tags, with filtering and sorting options.

        Returns:
            list: List of all Tags present in the database,
                  ordered by lower(name), or most recently
                  used; possibly filtered by a search term.
        """
        kwargs['include_usage'] = include_usage
        kwargs['sort_cols'] = sort_cols
        return super(TagManager, self).get_all(*args, **kwargs)

    def get_all_by_usage(self, *args, sort_cols=('usage',), **kwargs):
        assert(not args)
        kwargs['include_usage'] = True
        kwargs['sort_cols'] = sort_cols
        return super(TagManager, self).get_all(*args, **kwargs)

    # DRY: This fcn. very much similar between activity/category/tag.
    # - See FactManager.get_all and ActivityManager.get_all for more
    #   comments about this method.
    def _get_all(
        self,
        # FIXME/2018-06-20: (lb): Do what with key now?
        key=None,
        include_usage=True,
        count_results=False,
        since=None,
        until=None,
        endless=False,
        # FIXME/2020-05-09: (lb): I don't see partial ever being True.
        partial=False,
        deleted=False,
        search_term=None,
        activity=False,
        category=False,
        sort_cols='',
        sort_orders='',
        limit=None,
        offset=None,
        raw=False,
    ):
        """
        Get all tags, with filtering and sorting options.

        Returns:
            list: List of all Tags present in the database,
                  ordered by lower(name), or most recently
                  used; possibly filtered by a search term.
        """
        # If user is requesting sorting according to time, need Fact table.
        requested_usage = include_usage
        include_usage = (
            include_usage
            or set(sort_cols).intersection(('start', 'usage', 'time'))
        )

        def _get_all_tags():
            message = _('usage: {} / term: {} / col: {} / order: {}').format(
                include_usage, search_term, sort_cols, sort_orders,
            )
            self.store.logger.debug(message)

            query, agg_cols = _get_all_start_query()

            query = self.get_all_filter_partial(
                query, since=since, until=until, endless=endless, partial=partial,
            )

            query = _get_all_filter_by_activity(query)

            query = _get_all_filter_by_category(query)

            query = _get_all_filter_by_search_term(query)

            # FIXME/MIGRATIONS: (lb): Add column: Fact.deleted.
            #  condition = and_(condition, not AlchemyFact.deleted)
            #  query = query.filter(condition)

            query = _get_all_group_by(query, agg_cols)

            query = _get_all_order_by(query, *agg_cols)

            query = query_apply_limit_offset(query, limit=limit, offset=offset)

            query = _get_all_with_entities(query, agg_cols)

            self.store.logger.debug(_('query: {}').format(str(query)))

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
                query = self.store.session.query(AlchemyTag)
            else:
                if include_usage:
                    count_col = func.count(AlchemyTag.pk).label('uses')
                    agg_cols.append(count_col)
                    time_col = func.sum(
                        func.julianday(AlchemyFact.end)
                        - func.julianday(AlchemyFact.start)
                    ).label('span')
                    agg_cols.append(time_col)
                    query = self.store.session.query(AlchemyTag, count_col, time_col)
                query = query.join(
                    fact_tags, AlchemyTag.pk == fact_tags.columns.tag_id,
                )
                query = query.join(AlchemyFact)

            return query, agg_cols

        # ***

        def _get_all_filter_by_activity(query):
            if activity is False:
                return query

            query = query.join(AlchemyActivity)

            query = self._get_all_filter_by_activity(query, activity)

            return query

        def _get_all_filter_by_category(query):
            if category is False:
                return query
            query = query.join(AlchemyActivity).join(AlchemyCategory)

            query = self._get_all_filter_by_category(query, category)

            return query

        def _get_all_filter_by_search_term(query):
            if not search_term:
                return query

            condits = None
            for term in search_term:
                condit = AlchemyTag.name.ilike('%{}%'.format(term))
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
            query = query.group_by(AlchemyTag.pk)
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
            elif sort_col == 'activity':
                query = query.order_by(direction(AlchemyActivity.name))
                # MAYBE/2020-05-19: Now that sort_cols is multiple=True, omit this?:
                query = query.order_by(direction(AlchemyCategory.name))
            elif sort_col == 'category':
                query = query.order_by(direction(AlchemyCategory.name))
                # MAYBE/2020-05-19: Now that sort_cols is multiple=True, omit this?:
                query = query.order_by(direction(AlchemyActivity.name))
            elif sort_col == 'tag' or sort_col == 'name' or not sort_col:
                query = query.order_by(direction(AlchemyTag.name))
            else:
                self.store.logger.warn("Unknown sort_col: {}".format(sort_col))
            return query

        # ***

        def _get_all_with_entities(query, agg_cols):
            if not agg_cols:
                return query
            query = query.with_entities(AlchemyTag, *agg_cols)
            return query

        # ***

        def _process_results(records):
            return self._get_all_process_results_simple(
                records, raw, include_usage, requested_usage,
            )

        # ***

        return _get_all_tags()


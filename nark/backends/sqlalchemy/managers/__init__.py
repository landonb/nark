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

"""``nark`` storage object managers."""

from __future__ import absolute_import, unicode_literals

from future.utils import python_2_unicode_compatible
from sqlalchemy.exc import IntegrityError

__all__ = (
    'BaseAlchemyManager',
    'query_apply_limit_offset',
    'query_apply_true_or_not',
)


def query_apply_limit_offset(query, **kwargs):
    """
    Applies 'limit' and 'offset' to the database fetch query

    On applies 'limit' if specified; and only applies 'offset' if specified.

    Args:
        query (???): Query (e.g., return from self.store.session.query(...))

        kwargs (keyword arguments):
            limit (int|str, optional): Limit to apply to the query.

            offset (int|str, optional): Offset to apply to the query.

    Returns:
        list: The query passed in, modified with limit and/or offset, maybe.
    """
    try:
        if kwargs['limit']:
            query = query.limit(kwargs['limit'])
    except KeyError:
        pass
    try:
        if kwargs['offset']:
            query = query.offset(kwargs['offset'])
    except KeyError:
        pass
    return query


def query_apply_true_or_not(query, column, condition, **kwargs):
    if condition is not None:
        return query.filter(column == condition)
    return query


@python_2_unicode_compatible
class BaseAlchemyManager(object):
    """Base class for sqlalchemy managers."""

    # ***

    def add_and_commit(self, alchemy_item, raw=False, skip_commit=False):
        """
        Adds the item to the datastore, and perhaps calls commit.

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


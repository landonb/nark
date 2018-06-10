# -*- coding: utf-8 -*-

# This file is part of 'hamster-lib'.
#
# 'hamster-lib' is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# 'hamster-lib' is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with 'hamster-lib'.  If not, see <http://www.gnu.org/licenses/>.

"""Hamster LIB storage object managers."""

from __future__ import absolute_import, unicode_literals


__all__ = ['query_apply_limit_offset', 'query_apply_true_or_not']


# ***
# *** Helper functions.
# ***


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


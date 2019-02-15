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

"""
Base classes for implementing storage backends.

Note:
    * This is propably going to be replaced by a ``ABC``-bases solution.
    * Basic sanity checks could be done here then. This would mean we just need
      to test them once and our actual backends focus on the CRUD implementation.
"""

from __future__ import absolute_import, unicode_literals

from future.utils import python_2_unicode_compatible

from ..items.item_base import BaseItem

__all__ = ('BaseManager', )


@python_2_unicode_compatible
class BaseManager(object):
    """Base class for all object managers."""

    def __init__(self, store):
        self.store = store

    # ***

    def adding_item_must_not_have_pk(self, hamster_item):
        message = _("Adding item: {!r}.".format(hamster_item))
        self.store.logger.debug(message)
        if not hamster_item.pk:
            return
        message = _(
            "The {} item ({!r}) cannot be added because it already has a PK."
            " Perhaps call the ``_update`` method instead".format(
                self.__class__.__name__, hamster_item,
            )
        )
        self.store.logger.error(message)
        raise ValueError(message)

    # ***

    def save(self, item, cls=BaseItem, named=False, **kwargs):
        """
        Save a Nark object instance to user's selected backend.

        Will either ``_add`` or ``_update`` based on item PK.

        Args:
            tag (nark.BaseItem, i.e., Activity/Category/Fact/Tag):
                Nark instance to be saved.

        Returns:
            nark.BaseItem: Saved Nark instance.

        Raises:
            TypeError: If the ``item`` parameter is not a valid ``BaseItem`` instance.
        """

        if not isinstance(item, cls):
            message = _("You need to pass a {} object").format(cls.__name__)
            self.store.logger.debug(message)
            raise TypeError(message)

        # (lb): Not sure this is quite what we want, but Activity has been doing this,
        # and I just made this base class, so now all items will be doing this.
        if named and not item.name:
            raise ValueError(_("You must specify an item name."))

        self.store.logger.debug(_("'{}' has been received.".format(item)))

        # NOTE: Not assuming that PK is an int, i.e., not testing '> 0'.
        if item.pk or item.pk == 0:
            result = self._update(item, **kwargs)
        else:
            # PK is empty string, empty list, None, etc., but not 0.
            result = self._add(item, **kwargs)
        return result


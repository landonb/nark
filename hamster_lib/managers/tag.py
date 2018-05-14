# -*- encoding: utf-8 -*-

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

from __future__ import absolute_import, unicode_literals

from future.utils import python_2_unicode_compatible

from . import BaseManager
from ..items.tag import Tag


@python_2_unicode_compatible
class BaseTagManager(BaseManager):
    """Base class defining the minimal API for a TagManager implementation."""

    def save(self, tag):
        """
        Save a Tag to our selected backend.
        Internal code decides whether we need to add or update.

        Args:
            tag (hamster_lib.Tag): Tag instance to be saved.

        Returns:
            hamster_lib.Tag: Saved Tag

        Raises:
            TypeError: If the ``tag`` parameter is not a valid ``Tag`` instance.
        """

        if not isinstance(tag, Tag):
            message = _("You need to pass a hamster tag")
            self.store.logger.debug(message)
            raise TypeError(message)

        self.store.logger.debug(_("'{}' has been received.".format(tag)))

        # We don't check for just ``tag.pk`` because we don't want to make
        # assumptions about the PK being an int or being >0.
        if tag.pk or tag.pk == 0:
            result = self._update(tag)
        else:
            result = self._add(tag)
        return result

    def get_or_create(self, tag):
        """
        Check if we already got a tag with that name, if not create one.

        This is a convenience method as it seems sensible to rather implement
        this once in our controller than having every client implementation
        deal with it anew.

        It is worth noting that the lookup completely ignores any PK contained in the
        passed tag. This makes this suitable to just create the desired Tag
        and pass it along. One way or the other one will end up with a persisted
        db-backed version.

        Args:
            tag (hamster_lib.Tag or None): The categories.

        Returns:
            hamster_lib.Tag or None: The retrieved or created tag. Either way,
                the returned Tag will contain all data from the backend, including
                its primary key.
        """

        self.store.logger.debug(_("'{}' has been received.'.".format(tag)))
        if tag:
            try:
                tag = self.get_by_name(tag)
            except KeyError:
                tag = Tag(tag)
                tag = self._add(tag)
        else:
            # We want to allow passing ``tag=None``, so we normalize here.
            tag = None
        return tag

    def _add(self, tag):
        """
        Add a ``Tag`` to our backend.

        Args:
            tag (hamster_lib.Tag): ``Tag`` to be added.

        Returns:
            hamster_lib.Tag: Newly created ``Tag`` instance.

        Raises:
            ValueError: When the tag name was already present! It is supposed to be
            unique.
            ValueError: If tag passed already got an PK. Indicating that update would
                be more appropriate.
        """
        raise NotImplementedError

    def _update(self, tag):
        """
        Update a ``Tags`` values in our backend.

        Args:
            tag (hamster_lib.Tag): Tag to be updated.

        Returns:
            hamster_lib.Tag: The updated Tag.

        Raises:
            KeyError: If the ``Tag`` can not be found by the backend.
            ValueError: If the ``Tag().name`` is already being used by
                another ``Tag`` instance.
            ValueError: If tag passed does not have a PK.
        """
        raise NotImplementedError

    def remove(self, tag):
        """
        Remove a tag.

        Any ``Fact`` referencing the passed tag will have this tag removed.

        Args:
            tag (hamster_lib.Tag): Tag to be updated.

        Returns:
            None: If everything went ok.

        Raises:
            KeyError: If the ``Tag`` can not be found by the backend.
            TypeError: If tag passed is not an hamster_lib.Tag instance.
            ValueError: If tag passed does not have an pk.
        """
        raise NotImplementedError

    def get(self, pk):
        """
        Get an ``Tag`` by its primary key.

        Args:
            pk (int): Primary key of the ``Tag`` to be fetched.

        Returns:
            hamster_lib.Tag: ``Tag`` with given primary key.

        Raises:
            KeyError: If no ``Tag`` with this primary key can be found by the backend.
        """

        raise NotImplementedError

    def get_by_name(self, name):
        """
        Look up a tag by its name.

        Args:
            name (str): Unique name of the ``Tag`` to we want to fetch.

        Returns:
            hamster_lib.Tag: ``Tag`` with given name.

        Raises:
            KeyError: If no ``Tag`` with this name was found by the backend.
        """
        raise NotImplementedError

    def get_all(
        self,
        search_term='',
        sort_by_name=False,
        sort_by_use=False,
        **kwargs
    ):
        """
        Get all tags, with filtering and sorting options.

        Returns:
            list: List of all Tags present in the database,
                  ordered by lower(name), or most recently
                  used; possibly filtered by a search term.
        """
        raise NotImplementedError


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
from ..items.activity import Activity


@python_2_unicode_compatible
class BaseActivityManager(BaseManager):
    """Base class defining the minimal API for a ActivityManager implementation."""
    def save(self, activity):
        """
        Save a ``Activity`` to the backend.

        This public method decides if it calls either ``_add`` or ``_update``.

        Args:
            activity (hamster_lib.Activity): ``Activity`` to be saved.

        Returns:
            hamster_lib.Activity: The saved ``Activity``.
        """

        self.store.logger.debug(_("'{}' has been received.".format(activity)))
        if activity.pk or activity.pk == 0:
            result = self._update(activity)
        else:
            result = self._add(activity)
        return result

    def get_or_create(self, activity):
        """
        Convenience method to either get an activity matching the specs or create a new one.

        Args:
            activity (hamster_lib.Activity): The activity we want.

        Returns:
            hamster_lib.Activity: The retrieved or created activity
        """
        self.store.logger.debug(_("'{}' has been received.".format(activity)))
        try:
            activity = self.get_by_composite(activity.name, activity.category)
        except KeyError:
            activity = self.save(Activity(activity.name, category=activity.category,
                deleted=activity.deleted))
        return activity

    def _add(self, activity):
        """
        Add a new ``Activity`` instance to the database.

        Args:
            activity (hamster_lib.Activity): The ``Activity`` to be added.

        Returns:
            hamster_lib.Activity: The newly created ``Activity``.

        Raises:
            ValueError: If the passed activity has a PK.
            ValueError: If the category/activity.name combination to be added is
                already present in the db.

        Note:
            According to ``storage.db.Storage.__add_activity``: when adding a new activity
            with a new category, this category does not get created but instead this
            activity.category=None. This makes sense as categories passed are just ids, we
            however can pass full category objects. At the same time, this approach allows
            to add arbitrary category.id as activity.category without checking their existence.
            this may lead to db anomalies.
        """
        raise NotImplementedError

    def _update(self, activity):
        """
        Update values for a given activity.

        Which activity to refer to is determined by the passed PK new values
        are taken from passed activity as well.

        Args:
            activity (hamster_lib.Activity): Activity to be updated.

        Returns:
            hamster_lib.Activity: Updated activity.
        Raises:
            ValueError: If the new name/category.name combination is already taken.
            ValueError: If the the passed activity does not have a PK assigned.
            KeyError: If the the passed activity.pk can not be found.

        Note:
            Seems to modify ``index``.
        """

        raise NotImplementedError

    def remove(self, activity):
        """
        Remove an ``Activity`` from the database.import

        If the activity to be removed is associated with any ``Fact``-instances,
        we set ``activity.deleted=True`` instead of deleting it properly.
        If it is not, we delete it from the backend.

        Args:
            activity (hamster_lib.Activity): The activity to be removed.

        Returns:
            bool: True

        Raises:
            KeyError: If the given ``Activity`` can not be found in the database.

        Note:
            Should removing the last activity of a category also trigger category
            removal?
        """

        raise NotImplementedError

    def get(self, pk):
        """
        Return an activity based on its primary key.

        Args:
            pk (int): Primary key of the activity

        Returns:
            hamster_lib.Activity: Activity matching primary key.

        Raises:
            KeyError: If the primary key can not be found in the database.
        """
        raise NotImplementedError

    def get_by_composite(self, name, category):
        """
        Lookup for unique 'name/category.name'-composite key.

        This method utilizes that to return the corresponding entry or None.

        Args:
            name (str): Name of the ``Activities`` in question.
            category (hamster_lib.Category or None): ``Category`` of the activities. May be None.

        Returns:
            hamster_lib.Activity: The corresponding activity

        Raises:
            KeyError: If the composite key can not be found.
        """
        # [FIXME]
        # Handle resurrection. See legacy
        # ``hamster.sorage.db.__get_activity_by_name``

        raise NotImplementedError

    def get_all(self, category=False, search_term='', sort_by_column='', **kwargs):
        """
        Return all matching activities.

        Args:
            category (hamster_lib.Category, optional): Limit activities to this category.
                Defaults to ``False``. If ``category=None`` only activities without a
                category will be considered.
            search_term (str, optional): Limit activities to those matching this string
                a substring in their name. Defaults to ``empty string``.

        Returns:
            list: List of ``hamster_lib.Activity`` instances matching constrains. This list
                is ordered by ``Activity.name``.

        Note:
            * This method combines legacy ``storage.db.__get_activities`` and
                ``storage.db.____get_category_activities``.
            * Can search terms be prefixed with 'not'?
            * Original implementation in ``hamster.storage.db.__get_activities`` returns
                activity names converted to lowercase!
            * Does exclude activities with ``deleted=True``.
        """
        # [FIXME]
        # ``__get_category_activity`` order by lower(activity.name),
        # ``__get_activities```orders by most recent start date *and*
        # lower(activity.name).
        raise NotImplementedError

    def get_all_by_usage(self, category=False, search_term='', sort_by_column='', **kwargs):
        """
        Similar to get_all(), but include count of Facts that reference each Activity.
        """
        raise NotImplementedError


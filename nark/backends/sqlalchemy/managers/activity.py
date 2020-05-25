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

from sqlalchemy import func
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

    # ***

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

    # ***

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

    # ***

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

    # ***

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

    # ***

    # NOTE: Unlike Category and Tag, there is no Activity.get_by_name.

    # ***

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
            # Note that if alchemy_category is None -- because caller passed None --
            # then this only finds an Activity if it has no Category.
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

    # ***

    def _get_all_order_by_col(
        self, query, sort_col, direction, count_col=None, time_col=None,
    ):
        return self._get_all_order_by_col_common(
            query,
            sort_col,
            direction,
            default='activity',
            count_col=count_col,
            time_col=time_col,
        )

    # ***


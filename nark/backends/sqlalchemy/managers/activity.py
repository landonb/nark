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

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound

from ....managers.activity import BaseActivityManager
from ..objects import AlchemyActivity, AlchemyCategory, AlchemyFact
from . import query_apply_true_or_not
from .manager_base import BaseAlchemyManager

__all__ = (
    'ActivityManager',
)


class ActivityManager(BaseAlchemyManager, BaseActivityManager):
    """
    """
    def __init__(self, *args, **kwargs):
        super(ActivityManager, self).__init__(*args, **kwargs)

    # ***

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

        self.store.logger.debug("Received: {!r} / raw: {}".format(activity, raw))

        try:
            result = self.get_by_composite(activity.name, activity.category, raw=raw)
        except KeyError:
            result = self._add(activity, raw=raw, skip_commit=skip_commit)
        self.store.logger.debug("Returning: {!r}".format(result))
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
            message = _(
                "The database already contains that name/category.name combination."
            )
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

        self.store.logger.debug("Received: {!r}".format(activity))

        if not activity.pk:
            message = _(
                "The Activity passed ('{!r}') does not have a PK."
                " We do not know which entry to modify."
            ).format(activity)
            self.store.logger.error(message)
            raise ValueError(message)

        try:
            self.get_by_composite(activity.name, activity.category)
            # FIXME/2018-06-08: (lb): DRY: See "Our database already" elsewhere.
            message = _(
                "The database already contains that Activity and Category combination."
            )
            self.store.logger.error(message)
            raise ValueError(message)
        except KeyError:
            pass

        alchemy_activity = self.store.session.query(AlchemyActivity).get(activity.pk)
        if not alchemy_activity:
            message = _("No Activity with PK ‘{}’ was found.").format(activity.pk)
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
        self.store.logger.debug("Returning: {!r}".format(result))
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

        self.store.logger.debug("Received: {!r}".format(activity))

        if not activity.pk:
            message = _(
                "Activity ‘{!r}’ has no PK. Are you trying to remove a new Activity?"
            ).format(activity)
            self.store.logger.error(message)
            raise ValueError(message)

        alchemy_activity = self.store.session.query(AlchemyActivity).get(activity.pk)
        if not alchemy_activity:
            message = _("No Activity with PK ‘{}’ was found.").format(activity.pk)
            self.store.logger.error(message)
            raise KeyError(message)

        if alchemy_activity.facts:
            alchemy_activity.deleted = True
            self.store.activities._update(alchemy_activity)
        else:
            self.store.session.delete(alchemy_activity)
        self.store.session.commit()
        self.store.logger.debug("Deleted: {!r}".format(activity))

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

        self.store.logger.debug("Received PK: ‘{}’ / raw: {}.".format(pk, raw))

        if deleted is None:
            result = self.store.session.query(AlchemyActivity).get(pk)
        else:
            query = self.store.session.query(AlchemyActivity)
            query = query.filter(AlchemyActivity.pk == pk)
            query = query_apply_true_or_not(query, AlchemyActivity.deleted, deleted)
            results = query.all()
            assert len(results) <= 1
            result = results[0] if results else None

        if not result:
            message = _("No Activity with PK ‘{}’ was found.").format(pk)
            self.store.logger.error(message)
            raise KeyError(message)
        if not raw:
            result = result.as_hamster(self.store)
        self.store.logger.debug("Returning: {!r}.".format(result))
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

        self.store.logger.debug(
            "Received: {!r} / name: ‘{}’ / raw: {}".format(category, name, raw)
        )

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
                "No activity named ‘{name}’ of category ‘{category}’ was found."
            ).format(name=name, category=category)
            self.store.logger.debug(message)
            raise KeyError(message)
        if not raw:
            result = result.as_hamster(self.store)
        self.store.logger.debug("Returning: {!r}.".format(result))
        return result

    # ***
    # *** gather() call-outs (used by get_all/get_all_by_usage).
    # ***

    @property
    def _gather_query_alchemy_cls(self):
        return AlchemyActivity

    @property
    def _gather_query_order_by_name_col(self):
        return 'activity'

    def _gather_query_start_timeless(self, qt, alchemy_cls):
        # Query on AlchemyActivity.
        query = super(
            ActivityManager, self
        )._gather_query_start_timeless(qt, alchemy_cls)

        query = self._gather_query_join_category(qt, query)
        return query

    def _gather_query_start_aggregate(self, qt, agg_cols):
        query = self.store.session.query(AlchemyFact, *agg_cols)
        query = query.outerjoin(AlchemyFact.activity)
        query = self._gather_query_join_category(qt, query)
        return query

    def _gather_query_join_category(self, qt, query):
        # Note that SQLAlchemy automatically lazy-loads any attribute
        # that's another object but that we did not join. E.g., in a
        # query for Activity, if we did not join Category, then if/when
        # the code references activity.category on one of the returned
        # objects, the value will then be retrieved from the data store.
        # So we do not need to join values we do not need until after the
        # query. Except unless we want to sort by category.name, then we
        # need to join the table, so we can reference category.name in the
        # query. Same for matching category name.
        match_categories = qt.categories
        requires_category_table = (
            qt.sort_cols_has_any('category')
            or match_categories
        )
        if requires_category_table:
            query = query.outerjoin(AlchemyCategory)

        return query

    # ***


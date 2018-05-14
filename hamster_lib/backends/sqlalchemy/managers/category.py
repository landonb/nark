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

from __future__ import unicode_literals

from future.utils import python_2_unicode_compatible
from six import text_type
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound

from . import query_apply_limit_offset
from ..objects import AlchemyCategory
from ....managers.category import BaseCategoryManager


@python_2_unicode_compatible
class CategoryManager(BaseCategoryManager):
    def get_or_create(self, category, raw=False):
        """
        Custom version of the default method in order to provide access to alchemy instances.

        Args:
            category (hamster_lib.Category): Category we want.
            raw (bool): Wether to return the AlchemyCategory instead.

        Returns:
            hamster_lib.Category or None: Category.
        """

        message = _("Received {!r} and raw={}.".format(category, raw))
        self.store.logger.debug(message)

        try:
            category = self.get_by_name(category.name, raw=raw)
        except KeyError:
            category = self._add(category, raw=raw)
        return category

    def _add(self, category, raw=False):
        """
        Add a new category to the database.

        This method should not be used by any client code. Call ``save`` to make
        the decission wether to modify an existing entry or to add a new one is
        done correctly..

        Args:
            category (hamster_lib.Category): Hamster Category instance.
            raw (bool): Wether to return the AlchemyCategory instead.

        Returns:
            hamster_lib.Category: Saved instance, as_hamster()

        Raises:
            ValueError: If the name to be added is already present in the db.
            ValueError: If category passed already got an PK. Indicating that update would
                be more apropiate.
        """

        message = _("Received {!r} and raw={}.".format(category, raw))
        self.store.logger.debug(message)

        if category.pk:
            message = _(
                "The category ('{!r}') you are trying to add already has an PK."
                " Are you sure you do not want to ``_update`` instead?".format(category)
            )
            self.store.logger.error(message)
            raise ValueError(message)
        alchemy_category = AlchemyCategory(pk=None, name=category.name)
        self.store.session.add(alchemy_category)
        try:
            self.store.session.commit()
        except IntegrityError as e:
            message = _(
                "An error occured! Are you sure the category.name is not already present in our"
                " database? Here is the full original exception: '{}'.".format(e)
            )
            self.store.logger.error(message)
            raise ValueError(message)
        self.store.logger.debug(_("'{!r}' added.".format(alchemy_category)))

        if not raw:
            alchemy_category = alchemy_category.as_hamster(self.store)
        return alchemy_category

    def _update(self, category):
        """
        Update a given Category.

        Args:
            category (hamster_lib.Category): Category to be updated.

        Returns:
            hamster_lib.Category: Updated category.

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
                "An error occured! Are you sure the category.name is not already present in our"
                " database? Here is the full original exception: '{}'.".format(e)
            )
            self.store.logger.error(message)
            raise ValueError(message)

        return alchemy_category.as_hamster(self.store)

    def remove(self, category):
        """
        Delete a given category.

        Args:
            category (hamster_lib.Category): Category to be removed.

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
        message = _("{!r} successfully deleted.".format(category))
        self.store.logger.debug(message)
        self.store.session.commit()

    def get(self, pk):
        """
        Return a category based on their pk.

        Args:
            pk (int): PK of the category to be retrieved.

        Returns:
            hamster_lib.Category: Category matching given PK.

        Raises:
            KeyError: If no such PK was found.

        Note:
            We need this for now, as the service just provides pks, not names.
        """

        message = _("Received PK: '{}'.".format(pk))
        self.store.logger.debug(message)

        result = self.store.session.query(AlchemyCategory).get(pk)
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
            raw (bool): Wether to return the AlchemyCategory instead.

        Returns:
            hamster_lib.Category: Category of given name.

        Raises:
            KeyError: If no category matching the name was found.

        """

        message = _("Received name: '{}', raw={}.".format(name, raw))
        self.store.logger.debug(message)

        name = text_type(name)
        try:
            result = self.store.session.query(AlchemyCategory).filter_by(name=name).one()
        except NoResultFound:
            message = _("No category with 'name: {}' was found!".format(name))
            self.store.logger.error(message)
            raise KeyError(message)

        if not raw:
            result = result.as_hamster(self.store)
            self.store.logger.debug(_("Returning: {!r}.").format(result))
        return result

    def get_all(self, **kwargs):
        """
        Get all categories.

        Returns:
            list: List of all Categories present in the database, ordered by lower(name).
        """

        # We avoid the costs of always computing the length of the returned list
        # or even spamming the logs with the enrire list. Instead we just state
        # that we return something.
        self.store.logger.debug(_("Returning list of all categories."))
        query = self.store.session.query(AlchemyCategory)
        query = query.order_by(AlchemyCategory.name)
        query = query_apply_limit_offset(query, **kwargs)
        categories = query.all()
        return categories


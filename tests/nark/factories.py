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

"""Factories providing randomized object instances."""

import datetime

import factory
import fauxfactory
from nark.items.activity import Activity
from nark.items.category import Category
from nark.items.fact import Fact
from nark.items.tag import Tag


class CategoryFactory(factory.Factory):
    """Factory providing randomized ``nark.Category`` instances."""

    pk = None
    # Although we do not need to reference to the object beeing created and
    # ``LazyFunction`` seems sufficient it is not as we could not pass on the
    # string encoding. ``LazyAttribute`` allows us to specify a lambda that
    # circumvents this problem.
    name = factory.LazyAttribute(lambda x: fauxfactory.gen_string('utf8'))

    class Meta:
        model = Category


class ActivityFactory(factory.Factory):
    """Factory providing randomized ``nark.Activity`` instances."""

    pk = None
    name = factory.Faker('word')
    category = factory.SubFactory(CategoryFactory)
    deleted = False

    class Meta:
        model = Activity


class TagFactory(factory.Factory):
    """Factory providing randomized ``nark.Category`` instances."""

    pk = None
    name = factory.Faker('word')

    class Meta:
        model = Tag


class FactFactory(factory.Factory):
    """
    Factory providing randomized ``nark.Fact`` instances.

    Instances have a duration of 3 hours.
    """

    pk = None
    activity = factory.SubFactory(ActivityFactory)
    start = factory.Faker('date_time')
    end = factory.LazyAttribute(lambda o: o.start + datetime.timedelta(hours=3))
    description = factory.Faker('paragraph')

    class Meta:
        model = Fact

    @factory.post_generation
    def tags(self, create, extracted, **kwargs):
        """Add new random tags after instance creation."""
        self.tags = set([TagFactory() for i in range(1)])


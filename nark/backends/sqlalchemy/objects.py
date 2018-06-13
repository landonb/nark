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
This module provides the database layout.

We inherit from our hamster objects in order to use the custom
methods, making instance comparisons so much easier.

The reason we are not mapping our native hamster objects directly is
that this seems to break the flexible plugable backend architecture
as SQLAlchemy establishes the mapping right away. This may be
avoidable and should be investigates later on.

If those classes are instantiated manually any nested related
instance needs to be added manually.

Note:

    Our dedicated SQLAlchemy objects do not perform any general data
    validation as not to duplicate code. This is expected to be
    handled by the generic ``hamster_lib`` objects.

    If need for backend specific validation should arise, it could of
    cause be added here.
"""

from __future__ import absolute_import, unicode_literals
from future.utils import python_2_unicode_compatible

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    MetaData,
    Table,
    Unicode,
    UnicodeText,
    UniqueConstraint,
)
from sqlalchemy.orm import mapper, relationship

from ...items.activity import Activity
from ...items.category import Category
from ...items.fact import Fact
from ...items.tag import Tag


DEFAULT_STRING_LENGTH = 254


@python_2_unicode_compatible
class AlchemyCategory(Category):
    def __init__(self, pk, name, deleted, hidden):
        """
        Initiate a new SQLAlchemy category instance.

        Raises:
            TypeError: If ``category`` is not a ``Category`` instance.
        """

        self.pk = pk
        self.name = name
        self.deleted = deleted
        self.hidden = hidden

    def as_hamster(self, store):
        """Return store object as a real ``hamster_lib.Category`` instance."""
        return Category(
            pk=self.pk,
            name=self.name,
            deleted=self.deleted,
            hidden=self.hidden,
        )


@python_2_unicode_compatible
class AlchemyActivity(Activity):
    def __init__(self, pk, name, category, deleted, hidden):
        """
        Initiate a new instance.

        Args:
            activity (hamster_lib.Activity): An activity that is to be
                represented as a backend instance.

        Raises:
            TypeError: If ``activity`` is not an ``Activity`` instance.
        """

        self.pk = pk
        self.name = name
        self.category = category
        self.deleted = deleted
        self.hidden = hidden

    def as_hamster(self, store):
        """Return new ``hamster_lib.Activity`` representation of SQLAlchemy instance."""
        if self.category:
            category = self.category.as_hamster(store)
        else:
            category = None
        activity_name = self.name
        # Play nice with "corrupt" databases (lacking integrity):
        #   Allow nameless items, rather than raising ValueError.
        # User can easily discover problem through CLI, and they can fix it.
        # Try this to find nameless activities and their IDs:
        #   hamster list activities ''
        # Then, e.g.,
        #   hamster edit activity #24 newname@newcategory
        if not activity_name:
            if self.deleted:
                activity_name = '<unnamed>'
                store.logger.warn(_('Activity in database has no name: {}').format(self))
            # else, let Activity() raise ValueError; at least for now.
            # MAYBE: else, if this is an issue, add a migration option to
            #              fix nameless activities. Or something.
        return Activity(
            pk=self.pk,
            name=activity_name,
            category=category,
            deleted=self.deleted,
            hidden=self.hidden,
        )


@python_2_unicode_compatible
class AlchemyTag(Tag):
    def __init__(self, pk, name, deleted, hidden):
        """
        Initiate a new SQLAlchemy tag instance.

        Raises:
            TypeError: If ``category`` is not a ``Category`` instance.
        """

        self.pk = pk
        self.name = name
        self.deleted = deleted
        self.hidden = hidden

    def as_hamster(self, store):
        """Provide an convenient way to return it as a ``hamster_lib.Tag`` instance."""
        return Tag(
            pk=self.pk,
            name=self.name,
            deleted=self.deleted,
            hidden=self.hidden,
        )


@python_2_unicode_compatible
class AlchemyFact(Fact):
    def __init__(self, pk, activity, start, end, description, deleted, split_from):
        """
        Initiate a new instance.

        Args:
            fact (hamster_lib.Fact): A fact that is to be represented
                as a backend instance.

        Raises:
            TypeError: If ``fact`` is not an ``Fact`` instance.
        """
        # FIXME/2018-05-15: (lb): DRY: Any reason this doesn't called super()?
        self.pk = pk
        self.deleted = deleted
        self.split_from = split_from
        self.activity = activity
        self.start = start
        self.end = end
        self.description = description
        # Tags can only be assigned after the fact has been created.
        self.tags = list()

    def as_hamster(self, store):
        """Provide an convenient way to return it as a ``hamster_lib.Fact`` instance."""
        return Fact(
            pk=self.pk,
            deleted=self.deleted,
            split_from=self.split_from,
            activity=self.activity.as_hamster(store),
            start=self.start,
            end=self.end,
            description=self.description,
            tags=set([tag.as_hamster(store) for tag in self.tags]),
        )


metadata = MetaData()

categories = Table(
    'categories', metadata,
    Column('id', Integer, primary_key=True),

    # FIXME/2018-05-20: (lb): Why the hard limit? And why isn't it documented?
    Column('name', Unicode(DEFAULT_STRING_LENGTH), unique=True),

    Column('deleted', Boolean),
    Column('hidden', Boolean),
)

# (lb): This code uses SQLAlchemy Classical Mappings, and not Declarative Mappings.
#   http://docs.sqlalchemy.org/en/latest/orm/mapping_styles.html

mapper(AlchemyCategory, categories, properties={
    'pk': categories.c.id,
})

activities = Table(
    'activities', metadata,
    Column('id', Integer, primary_key=True),

    # FIXME/2018-05-20: (lb): Why the hard limit? And why isn't it documented?
    # And why isn't this DEFAULT_STRING_LENGTH instead of 500?
    Column('name', Unicode(500)),

    Column('deleted', Boolean),
    Column('hidden', Boolean),
    Column('category_id', Integer, ForeignKey(categories.c.id)),
    UniqueConstraint('name', 'category_id'),
)

mapper(AlchemyActivity, activities, properties={
    'pk': activities.c.id,
    'category': relationship(AlchemyCategory, backref='activities'),
})

tags = Table(
    'tags', metadata,
    Column('id', Integer, primary_key=True),

    # FIXME/2018-05-20: (lb): Why the hard limit? And why isn't it documented?
    Column('name', Unicode(DEFAULT_STRING_LENGTH), unique=True),

    Column('deleted', Boolean),
    Column('hidden', Boolean),
)

mapper(AlchemyTag, tags, properties={
    'pk': tags.c.id,
})

facts = Table(
    'facts', metadata,
    Column('id', Integer, primary_key=True),
    Column('deleted', Boolean),
    Column('split_from_id', Integer, ForeignKey('facts.id'), nullable=True),
    # SKIP: Column('hidden', Boolean),
    # NOTE/2018-04-22: Old Timey Hamster uses SQLite 'timestamp' data type.
    # In ProjectHamster Hamster, the data type shows as DATETIME. The type
    # is more of a suggestion in SQLite, which stores both types as strings,
    # and the strings are your typical Hamster time, "YYYY-MM-DD HH:MM:SS".
    Column('start_time', DateTime),
    Column('end_time', DateTime),
    Column('activity_id', Integer, ForeignKey(activities.c.id)),

    # FIXME/2018-05-20: (lb): Why the hard limit? And why isn't it documented?
    # ALSO: seriously, only 500 chars for "description"??
    #    Column('description', Unicode(500)),
    # [In SQLite the size is meaningless (you can store anything, any size)
    #  but it probably matters in other databases]...
    # FIXME/2018-06-09: (lb): Remove this comment after verifying against
    #   another store, e.g., Postgres.
    Column('description', UnicodeText()),
)

mapper(AlchemyFact, facts, properties={
    'pk': facts.c.id,
    'activity': relationship(AlchemyActivity, backref='facts'),
    'tags': relationship(AlchemyTag, backref='facts', secondary=lambda: fact_tags),

    # 2018-04-22: (lb): I'm not sure if there's a migration script or not,
    # but I could not find one, and for some reason ProjectHamster renamed
    # the facts' start and end columns to start_time and end_time, respectively.
    # FIXME: (lb): Remove this comment (and newlines) after verifying it's eh-okay.
    'start': facts.c.start_time,
    'end': facts.c.end_time,

    'split_from': relationship(
        lambda: AlchemyFact, remote_side=facts.c.id, backref='sub_facts',
    )
})

# 2018-04-22: (lb): ProjectHamster renamed fact_tags to facttags. But
# that term isn't used in the code other than in this Table mapping
# (which no other code uses; though maybe SQLAlchemy uses it internally?).
fact_tags = Table(
    'fact_tags', metadata,
    Column('fact_id', Integer, ForeignKey(facts.c.id)),
    Column('tag_id', Integer, ForeignKey(tags.c.id)),
)


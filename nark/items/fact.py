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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with 'nark'. If not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import, unicode_literals
from future.utils import python_2_unicode_compatible

from collections import namedtuple
from datetime import datetime
from operator import attrgetter
from six import text_type

from .activity import Activity
from .category import Category
from .item_base import BaseItem
from .tag import Tag
from ..helpers import fact_time
from ..helpers import format_fact
from ..helpers import format_time
from ..helpers.facts_diff import FactsDiff
from ..helpers.parsing import parse_factoid


FactTuple = namedtuple(
    'FactTuple',
    (
        'pk',
        'activity',
        'start',
        'end',
        'description',
        'tags',
        'deleted',
        'split_from',
    ),
)


@python_2_unicode_compatible
class Fact(BaseItem):
    """Storage agnostic class for facts."""
    def __init__(
        self,
        activity,
        start,
        end=None,
        pk=None,
        description=None,
        tags=None,
        deleted=False,
        split_from=None,
        ephemeral=None,
    ):
        """
        Initiate our new instance.

        Args:
            activity (nark.Activity): Activity associated with this fact.

            start (datetime.datetime): Start datetime of this fact.

            end (datetime.datetime, optional): End datetime of this fact.
                Defaults to ``None``.

            pk (optional): Primary key used by the backend to identify this instance.
                Defaults to ``None``.

            description (str, optional): Additional information relevant to this
                singular fact. Defaults to ``None``.

            tags (Iterable, optional): Iterable of ``strings`` identifying *tags*.
                Defaults to ``None``.

            deleted (bool, optional): True if fact was deleted/edited/split.

            split_from (nark.Fact.id, optional): ID of deleted fact this
                fact succeeds.
        """
        super(Fact, self).__init__(pk, name=None)
        assert activity is None or isinstance(activity, Activity)
        self.activity = activity
        self.start = start
        self.end = end
        self.description = description

        self.tags_replace(tags)

        # (lb): Legacy Hamster did not really have an edit-fact feature.
        # Rather, when the user "edited" a Fact, Hamster would delete
        # the existing row and make a new one. This is very unwikilike!
        # To preserve history, let's instead mark edited Facts deleted.
        # FIXME/2018-05-23 10:56: (lb): Add column to record new Facts ID?
        self.deleted = bool(deleted)
        self.split_from = split_from

        # For state changes.
        # LATER/2018-05-23: (lb): Either make use of this, or remove.
        #   I'm not sure I need, other than for debugging/developing
        #   currently. And even then, edited facts are currently passed
        #   around in a conflicts collection with their original fact,
        #   so it's easy to tell what changed.
        self.dirty_reasons = set()

        # (lb): I feel a little dirty about this, but it lets us easily
        # ride some meta data along the fact during the import command.
        self.ephemeral = ephemeral

    def __eq__(self, other):
        if other is not None and not isinstance(other, FactTuple):
            other = other.as_tuple()

        return self.as_tuple() == other

    def __hash__(self):
        """Naive hashing method."""
        return hash(self.as_tuple())

    def __str__(self):
        return format_fact.friendly_str(text_type)

    def __repr__(self):
        return format_fact.friendly_str(repr)

    def as_tuple(self, include_pk=True):
        """
        Provide a tuple representation of this facts relevant attributes.

        Args:
            include_pk (bool): Whether to include the instances pk or not. Note that if
            ``False`` ``tuple.pk = False``!

        Returns:
            nark.FactTuple: Representing this categories values.
        """
        pk = self.pk
        if not include_pk:
            pk = False

        activity_tup = self.activity and self.activity.as_tuple(include_pk=include_pk)

        sorted_tags = self.tags_sorted
        ordered_tags = [tag.as_tuple(include_pk=include_pk) for tag in sorted_tags]

        return FactTuple(
            pk=pk,
            activity=activity_tup,
            start=self.start,
            end=self.end,
            description=self.description,
            tags=frozenset(ordered_tags),
            deleted=bool(self.deleted),
            split_from=self.split_from,
            # SKIP: self.ephemeral
        )

    def copy(self, include_pk=True):
        """
        """
        new_fact = self.__class__(
            activity=self.activity,
            start=self.start,
            end=self.end,
            description=self.description,
            # self.tags might be an sqlalchemy.orm.collections.InstrumentedList
            # and calling list() on it will create a new list of what could be
            # nark.backends.sqlalchemy.objects.AlchemyTag.
            tags=list(self.tags),
            deleted=bool(self.deleted),
            split_from=self.split_from,
            # If this is an AlchemyFact object, it won't have non-table
            # attrs, like dirty_reasons or ephemeral.
        )
        new_fact.dirty_reasons = set(list(self.dirty_reasons))
        if include_pk:
            new_fact.pk = self.pk
        return new_fact

    def equal_fields(self, other):
        """
        Compare this instances fields with another fact. This excludes comparing the PK.

        Args:
            other (Fact): Fact to compare this instance with.

        Returns:
            bool: ``True`` if all fields but ``pk`` are equal, ``False`` if not.

        Note:
            This is particularly useful if you want to compare a new ``Fact`` instance
            with a freshly created backend instance. As the latter will probably have a
            primary key assigned now and so ``__eq__`` would fail.
        """
        return self.as_tuple(include_pk=False) == other.as_tuple(include_pk=False)

    def squash(self, other, squash_sep=''):
        # (lb): Not super happy about this whole squash business,
        #   as you can probably suss form all these asserts....
        assert other.pk is None or other.pk < 0
        assert not self.deleted
        assert not other.deleted
        assert not other.split_from
        assert self.start
        assert not self.end
        assert not (other.start and other.end)

        self.end = other.start or other.end
        assert self.end

        if other.activity_name or other.category_name:
            self.activity = other.activity

        self.tags_replace(self.tags + other.tags)

        self.description_squash(other, squash_sep)

        other.deleted = True
        # For completeness, and to make verification easier.
        other.start = self.start
        other.end = self.end

    # ***

    LOCALIZE = False

    @classmethod
    def localize(cls, localize=None):
        if localize is not None:
            cls.LOCALIZE = localize
        return cls.LOCALIZE

    # ***

    @property
    def start(self):
        return self._start

    @start.setter
    def start(self, start):
        """
        Make sure that we receive a ``datetime.datetime`` instance,
          or relative time string.

        Args:
            start (datetime.datetime, text_type): Start datetime of this ``Fact``.

        Raises:
            TypeError: If we receive something other than a ``datetime.datetime``
                (sub-)class or ``None``.
        """
        # MOTE: (lb): The AlchemyFact class derives from this class, but it
        # has columns of the same names as theses @property definitions, e.g.,
        # `start`. So when you set, e.g, `self.start = X` from the AlchemyFact
        # class, it does not call this base class' @setter for start. So don't
        # use self._start except in self.start()/=.
        self._start = fact_time.must_be_datetime_or_relative(start)

    @property
    def start_fmt_utc(self):
        """FIXME: Document"""
        if not self.start:
            return ''
        # Format like: '%Y-%m-%d %H:%M:%S%z'
        return format_time.isoformat_tzinfo(self.start, sep=' ', timespec='seconds')

    @property
    def start_fmt_local(self):
        """FIXME: Document"""
        if not self.start:
            return ''
        # Format like: '%Y-%m-%d %H:%M:%S'
        return format_time.isoformat_tzless(self.start, sep=' ', timespec='seconds')

    # ***

    @property
    def end(self):
        return self._end

    @end.setter
    def end(self, end):
        """
        Make sure that we receive a ``datetime.datetime`` instance.

        Args:
            end (datetime.datetime): End datetime of this ``Fact``.

        Raises:
            TypeError: If we receive something other than a ``datetime.datetime``
                (sub-)class or ``None``.
        """
        self._end = fact_time.must_be_datetime_or_relative(end)

    @property
    def end_fmt_utc(self):
        """FIXME: Document"""
        if not self.end:
            return ''
        return format_time.isoformat_tzinfo(self.end, sep=' ', timespec='seconds')

    @property
    def end_fmt_local(self):
        """FIXME: Document"""
        if not self.end:
            return ''
        return format_time.isoformat_tzless(self.end, sep=' ', timespec='seconds')

    @property
    def end_fmt_local_nowwed(self):
        """FIXME: Document"""
        if not self.end:
            return '{} <now>'.format(self.end_fmt_local_or_now)
        return self.end_fmt_local

    @property
    def end_fmt_local_or_now(self):
        if not self.end:
            return '{}'.format(format_time.isoformat_tzless(
                self.time_now, sep=' ', timespec='seconds',
            ))
        return self.end_fmt_local

    # ***

    @property
    def momentaneous(self):
        if self.times_ok and self.start == self.end:
            return True
        return False

    @property
    def time_now(self):
        return datetime.now() if self.localize else datetime.utcnow()

    @property
    def times(self):
        return (self.start, self.end)

    @property
    def times_ok(self):
        if isinstance(self.start, datetime) and isinstance(self.end, datetime):
            return True
        return False

    # ***

    def delta(self):
        """
        Provide the offset of start to end for this fact.

        Returns:
            datetime.timedelta or None: Difference between start- and end datetime.
                If we only got a start datetime, return ``None``.
        """
        end_time = self.end
        if not end_time:
            end_time = self.time_now

        return end_time - self.start

    def format_delta(self, formatting='%M'):
        """
        Return a string representation of ``Fact().delta``.

        Args:
            formatting (str): Specifies the output format.

              Valid choices are:
                * ``'%M'``: As minutes, rounded down.
                * ``'%H:%M'``: As 'hours:minutes'. rounded down.
                * ````: As human friendly time.

        Returns:
            str: Formatted string representing this fact's *duration*.
        """
        return format_time.format_delta(self.delta())

    # ***

    @property
    def midpoint(self):
        if not self.times_ok:
            return None
        midpoint = self.end - ((self.end - self.start) / 2)
        return midpoint

    @property
    def time_of_day_midpoint(self):
        if not self.midpoint:
            return ''
        clock_sep = ' ◐ '
        hamned = '{0}'.format(
            self.midpoint.strftime("%a %d %b %Y{0}%I:%M %p").format(clock_sep),
            # FIXME: (lb): Add Colloquial TOD suffix, e.g., "morning".
        )
        return hamned

    def time_of_day_humanize(self, show_now=False):
        if not self.times_ok and not show_now:
            return ''
        clock_sep = ' ◐ '
        wkd_day_mon_year = self.start.strftime("%a %d %b %Y")
        text = self.start.strftime("{0}{1}%I:%M %p").format(
            wkd_day_mon_year, clock_sep,
        )
        if self.end == self.start:
            return text
        text += _(" — ")
        end_time = self.end if self.end is not None else self.time_now
        text += end_time.strftime("%I:%M %p")
        end_wkd_day_mon_year = end_time.strftime("%a %d %b %Y")
        if end_wkd_day_mon_year == wkd_day_mon_year:
            return text
        text += " "
        text += end_wkd_day_mon_year
        return text

    # ***

    @property
    def activity_name(self):
        """..."""
        try:
            return self.activity.name
        except AttributeError:
            return ''

    @property
    def category(self):
        """Just a convenience shim to underlying category object."""
        return self.activity.category

    @property
    def category_name(self):
        """..."""
        try:
            return self.activity.category.name
        except AttributeError:
            return ''

    @property
    def description(self):
        return self._description

    @description.setter
    def description(self, description):
        """"
        Normalize all descriptions that evaluate to ``False``.
        Store everything else as string.
        """
        if description:
            description = text_type(description)
        else:
            description = None
        self._description = description

    def description_squash(self, other, description_sep):
        if not other.description:
            return
        # (lb): Build local desc. copy, because setter stores None, never ''.
        new_description = self.description or ''
        new_description += description_sep if new_description else ''
        new_description += other.description
        self.description = new_description
        other.description = None

    def tags_replace(self, tags):
        new_tags = set()
        for tagn in set(tags) if tags else set():
            tag = tagn if isinstance(tagn, Tag) else Tag(name=tagn)
            new_tags.add(tag)
        # (lb): Do this in one swoop, and be sure to assign a list; when wrapped
        # by SQLAlchemy, if tried to set to, e.g., set(), complains:
        #   TypeError: Incompatible collection type: set is not list-like
        # (That error is from orm.attribute.CollectionAttributeImpl.set.)
        self.tags = list(new_tags)

    @property
    def tags_sorted(self):
        return sorted(list(self.tags), key=attrgetter('name'))

    # ***

    def tagnames(self, *args, **kwargs):
        return format_fact.tags_inline(*args, **kwargs)

    def tags_inline(self, underlined=True, **kwargs):
        return format_fact.tags_inline(underlined=underlined, **kwargs)

    def tags_tuples(self, underlined=True, **kwargs):
        return format_fact.tags_tuples(underlined=underlined, **kwargs)

    # ***

    def friendly_str(self, *args, **kwargs):
        return format_fact.friendly_str(self, *args, **kwargs)

    # ***

    def get_serialized_string(self, shellify=False):
        """
        Return a canonical, "stringified" version of the Fact.

        - Akin to: encoding/flattening/marshalling/packing/pickling.

        This function is mostly meant for machines, not for people.

        - Generally, use ``__str__`` if you want a human-readable string.

          I.e., one whose datetimes are localized relative to the Fact.
          This serializing function defaults to using UTC.

        - Use this function to encode a Fact in a canonical way, which can
          be consumed again later, i.e., using ``Fact.create_from_factoid``.

        - A complete serialized fact might look like this:

              2016-02-01 17:30 to 2016-02-01 18:10 making plans@world domination
              #tag 1 #tag 2, description

          - Note that nark is very unassuming with whitespace. It can be
            used in the Activity and Category names, as well as in tags.

        Attention:

            ``Fact.tags`` is a set and hence unordered. In order to provide
            a deterministic canonical return string, we sort tags by name.
            This is purely cosmetic and does not imply any actual ordering
            of those facts on the instance level.

        Returns:
            text_type: Canonical string encoding all available fact info.
        """
        return format_fact.friendly_str(shellify=shellify)

    @property
    def short(self):
        """
        A brief Fact one-liner.

        (lb): Not actually called by any code, but useful for debugging!
        """
        return format_fact.friendly_str(include_id=True, cut_width=39)

    @property
    def html_notif(self):
        """
        A briefer Fact one-liner using HTML. Useful for, e.g., notifier toast.
        """
        return format_fact.html_notif(self)

    # ***

    def friendly_diff(self, other, formatted=False, **kwargs):
        facts_diff = FactsDiff(self, other, formatted=formatted)
        return facts_diff.friendly_diff(**kwargs)

    # ***

    @classmethod
    def create_from_factoid(
        cls,
        factoid,
        time_hint='',
        separators=None,
        lenient=False,
    ):
        """
        Construct a new ``nark.Fact`` from a string of fact details,
            or factoid.

        NOTE: This naïvely creates a new Fact and does not check against
        other Facts for integrity. It's up to the caller to see if the new
        Fact conflicts with existing Facts presently in the system.

        Args:
            factoid (str): Raw fact to be parsed.

            time_hint (text_type, optional): One of:
                'verify_none': Do not expect to find any time encoded in factoid.
                'verify_both': Expect to find both start and end times.
                'verify_start': Expect to find just one time, which is the start.
                'verify_end': Expect to find just one time, which is the end.
                'verify_then': Time specifies new start; and back-fill interval gap.
                'verify_after': No time spec. Start new Fact at time of previous end.

            lenient (bool, optional): If False, parser raises errors on misssing
                mandatory components (such as time or activity). (Category,
                tags, and description are optional.)

        Returns:
            nark.Fact: New ``Fact`` object constructed from factoid.

        Raises:
            ValueError: If we fail to extract at least ``start`` or ``activity.name``.
            ValueError: If ``end <= start``.
            ParserException: On parser error, one of the many ParserException
                derived classes will be raised.
        """
        parsed_fact, err = parse_factoid(
            factoid,
            time_hint=time_hint,
            separators=separators,
            lenient=lenient,
        )

        # COUPLING: Note that this object is used by dob, and not by nark;
        #   nark is being nice and helping out the the CLI by setting this.
        # MAYBE: Move ephemeral back to CLI (and, e.g., use wrapper class around Fact).
        ephemeral = {
            'line_num': 1,
            'line_raw': ' '.join(factoid),
        }

        new_fact = cls.create_from_parsed_fact(
            parsed_fact, lenient=lenient, ephemeral=ephemeral,
        )

        return new_fact, err

    @classmethod
    def create_from_parsed_fact(
        cls,
        parsed_fact,
        lenient=False,
        **kwargs
    ):
        start = parsed_fact['start']
        end = parsed_fact['end']
        # Verify that start > end, if neither are None or not a datetime.
        start, end = fact_time.must_not_start_after_end((start, end))

        activity = ''
        activity_name = parsed_fact['activity']
        if activity_name:
            activity = Activity(activity_name)
        elif lenient:
            activity = Activity(name='')
        else:
            raise ValueError(_('Unable to extract activity name'))

        category_name = parsed_fact['category']
        if category_name:
            activity.category = Category(category_name)

        description = parsed_fact['description']

        tags = parsed_fact['tags']

        return cls(
            activity,
            start,
            end=end,
            description=description,
            tags=tags,
            **kwargs
        )


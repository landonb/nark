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

from collections import namedtuple
from datetime import datetime
from operator import attrgetter

from future.utils import python_2_unicode_compatible
from six import text_type

from ..helpers import fact_time, format_fact, format_time
from ..helpers.parsing import parse_factoid
from .activity import Activity
from .category import Category
from .item_base import BaseItem
from .tag import Tag

try:
    from math import inf
except ImportError:
    # < Python 3.5.
    inf = float('inf')


__all__ = (
    'SinceTimeBegan',
    'UntilTimeStops',
    'FactTuple',
    'Fact',
)


SinceTimeBegan = datetime(1, 1, 1)


UntilTimeStops = datetime(9999, 12, 31, 23, 59, 59)


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

    def __eq__(self, other):
        if other is not None and not isinstance(other, FactTuple):
            other = other.as_tuple()

        return self.as_tuple() == other

    def equal_sans_end(self, other):
        if other is not None and not isinstance(other, FactTuple):
            other = other.as_tuple(sans_end=True)

        return self.as_tuple(sans_end=True) == other

    def __hash__(self):
        """Naive hashing method."""
        return hash(self.as_tuple())

    def __gt__(self, other):
        return self.sorty_tuple > other.sorty_tuple

    def __lt__(self, other):
        return self.sorty_tuple < other.sorty_tuple

    @property
    def sorty_times(self):
        fact_end = self.end if self.end is not None else UntilTimeStops
        return (self.start, fact_end)

    @property
    def sorty_tuple(self):
        fact_end = self.end if self.end is not None else UntilTimeStops
        fact_pk = self.pk if self.pk is not None else -inf
        return (self.start, fact_end, fact_pk)

    def __str__(self):
        # MAYBE: (lb): __str__ used to pass fmttr=text_type to friendly_str,
        #   and __repr__ used to pass fmttr=repr; and then friendly_str would
        #   wrap all strings that it assembled with that formatter, e.g.,
        #     fmttr(self.activity.name)
        #   but I did not understand why (what's the difference between
        #   text_type and repr? text_type is a no-op in py3, and converts
        #   py2 string to unicode, right?). In any case, I don't think we
        #   need to cast to text_type/repr anymore (especially if we drop
        #   Python 2 support).
        return format_fact.friendly_str(self)

    def __repr__(self):
        parts = []
        for key in sorted(self.__dict__.keys()):
            if key == 'name':
                assert self.name is None
                continue  # Part of BaseItem, and not used by Fact.
            elif key == 'tags':
                val = repr(self.tags_sorted)
            else:
                # Not that nark knows anything about this, but dob's derived
                # class, PlaceableFact, has a next_fact and prev_fact pointer.
                # To avoid a deadly RecursionError by following pointers of a
                # doubly-linked list, check that the attribute value is not
                # another Fact. (For the sake of coupling, PlaceableFact could
                # just supply its own __repr__() function, but this function
                # is already doing a lot, so might as well toss in the kitchen
                # sink.)
                raw = getattr(self, key)
                if isinstance(raw, self.__class__):
                    val = id(raw)
                else:
                    val = repr(raw)
            parts.append(
                "{key}={val}".format(key=key, val=val)
            )
        repred = "Fact({})".format(', '.join(parts))
        return repred

    def as_tuple(self, include_pk=True, sans_end=False):
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

        end_time = -1 if sans_end else self.end

        return FactTuple(
            pk=pk,
            activity=activity_tup,
            start=self.start,
            end=end_time,
            description=self.description,
            tags=frozenset(ordered_tags),
            deleted=bool(self.deleted),
            split_from=self.split_from,
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
        )
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

    def format_delta(self, style='%M'):
        """
        Return a string representation of ``Fact().delta``.

        Args:
            formatting (str): Specifies the output format.

              Valid choices are:
                * ``'%M'``: As minutes, rounded down.
                * ``'%H:%M'``: As 'hours:minutes'. rounded down.
                * ``'HHhMMm'``: As '{hours} hour(s) {minutes} minute(s)'.
                * ``''``: As human friendly time.

        Returns:
            str: Formatted string representing this fact's *duration*.
        """
        return format_time.format_delta(self.delta(), style=style)

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
        return format_fact.tags_inline(self, *args, **kwargs)

    def tags_inline(self, colorful=False, underlined=False, **kwargs):
        return format_fact.tags_inline(
            self, colorful=colorful, underlined=underlined, **kwargs
        )

    def tags_tuples(self, colorful=False, underlined=False, **kwargs):
        return format_fact.tags_tuples(
            self, colorful=colorful, underlined=underlined, **kwargs
        )

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
        return format_fact.friendly_str(self, shellify=shellify)

    @property
    def short(self):
        """
        A brief Fact one-liner.

        (lb): Not actually called by any code, but useful for debugging!
        """
        return format_fact.friendly_str(self, include_id=True, cut_width=39)

    @property
    def html_notif(self):
        """
        A briefer Fact one-liner using HTML. Useful for, e.g., notifier toast.
        """
        return format_fact.html_notif(self)

    # ***

    @classmethod
    def create_from_factoid(
        cls,
        factoid,
        time_hint='verify_none',
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

        new_fact = cls.create_from_parsed_fact(
            parsed_fact, lenient=lenient,
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


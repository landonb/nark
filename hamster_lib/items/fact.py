# -*- coding: utf-8 -*-

# This file is part of 'hamster-lib'.
#
# 'hamster-lib' is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# 'hamster-lib' is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with 'hamster-lib'. If not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import, unicode_literals
from future.utils import python_2_unicode_compatible

from collections import namedtuple
from datetime import datetime
from operator import attrgetter
from pyoiler_timedelta import timedelta_wrap
from six import text_type

from .activity import Activity
from .category import Category
from .tag import Tag
from ..helpers import time as time_helpers
from ..helpers.colored import fg, attr, colorize, set_coloring
from ..helpers.objects import resolve_attr_or_method
from ..helpers.parsing import parse_factoid
from ..helpers.strings import format_value_truncate


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
class Fact(object):
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
            activity (hamster_lib.Activity): Activity associated with this fact.

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

            split_from (hamster_lib.Fact.id, optional): ID of deleted fact this
                fact succeeds.
        """
        self.pk = pk
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

    def __eq__(self, other):
        if not isinstance(other, FactTuple):
            other = other.as_tuple()

        return self.as_tuple() == other

    def __hash__(self):
        """Naive hashing method."""
        return hash(self.as_tuple())

    def __str__(self):
        return self.friendly_str(text_type)

    def __repr__(self):
        return self.friendly_str(repr)

    def as_tuple(self, include_pk=True):
        """
        Provide a tuple representation of this facts relevant attributes.

        Args:
            include_pk (bool): Whether to include the instances pk or not. Note that if
            ``False`` ``tuple.pk = False``!

        Returns:
            hamster_lib.FactTuple: Representing this categories values.
        """
        pk = self.pk
        if not include_pk:
            pk = False

        ordered_tags = [
            tag.as_tuple(include_pk=include_pk) for tag in self.tags_sorted
        ]

        return FactTuple(
            pk=pk,
            activity=self.activity.as_tuple(include_pk=include_pk),
            start=self.start,
            end=self.end,
            description=self.description,
            tags=frozenset(ordered_tags),
            deleted=self.deleted,
            split_from=self.split_from,
        )

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

    @property
    def start(self):
        return self._start

    @start.setter
    def start(self, start):
        """
        Make sure that we receive a ``datetime.datetime`` instance.

        Args:
            start (datetime.datetime): Start datetime of this ``Fact``.

        Raises:
            TypeError: If we receive something other than a ``datetime.datetime``
                (sub-)class or ``None``.
        """
        # MOTE: (lb): The AlchemyFact class derives from this class, but it
        # has columns of the same names as theses @property definitions, e.g.,
        # `start`. So when you set, e.g, `self.start = X` from the AlchemyFact
        # class, it does not call this base class' @setter for start. So don't
        # use self._start except in self.start()/=.
        self._start = time_helpers.must_be_datetime_or_relative(start)

    @property
    def start_fmt_utc(self, sep=' ', timespec='seconds'):
        """FIXME: Document"""
        if not self.start:
            return ''
        # Format like: '%Y-%m-%d %H:%M:%S%z'
        return time_helpers.isoformat_tzinfo(self.start, sep=sep, timespec=timespec)

    @property
    def start_fmt_local(self, sep=' ', timespec='seconds'):
        """FIXME: Document"""
        if not self.start:
            return ''
        # Format like: '%Y-%m-%d %H:%M:%S'
        return time_helpers.isoformat_tzless(self.start, sep=sep, timespec=timespec)

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
        self._end = time_helpers.must_be_datetime_or_relative(end)

    @property
    def end_fmt_utc(self, sep=' ', timespec='seconds'):
        """FIXME: Document"""
        if not self.end:
            return ''
        return time_helpers.isoformat_tzinfo(self.end, sep=sep, timespec=timespec)

    @property
    def end_fmt_local(self, sep=' ', timespec='seconds'):
        """FIXME: Document"""
        if not self.end:
            return ''
        return time_helpers.isoformat_tzless(self.end, sep=sep, timespec=timespec)

    def delta(self, localize=False):
        """
        Provide the offset of start to end for this fact.

        Returns:
            datetime.timedelta or None: Difference between start- and end datetime.
                If we only got a start datetime, return ``None``.
        """
        result = None
        end_time = self.end
        if not end_time:
            end_time = datetime.now() if localize else datetime.utcnow()
        result = end_time - self.start
        return result

    def get_string_delta(self, format='%M', localize=False):
        """
        Return a string representation of ``Fact().delta``.

        Args:
            format (str): Specifies the output format. Valid choices are:
                * ``'%M'``: As minutes, rounded down.
                * ``'%H:%M'``: As 'hours:minutes'. rounded down.

        Returns:
            str: String representing this facts *duration* in the given format.capitalize

        Raises:
            ValueError: If a unrecognized format specifier is received.
        """
        seconds = int(self.delta(localize).total_seconds())
        # MAYBE/2018-05-05: (lb): scientificsteve rounds instead of floors.
        # I'm not sure this is correct. The user only commented in the commit,
        #   "Round the minutes instead of flooring." But they did not bother to
        #   edit the docstring above, which explicitly says that time is rounded
        #   down!
        # So I'm making a note of this -- because I incorporated the tags feature
        #   from scientificsteve's PR -- but I did not incorporate the rounding
        #   change. For one, I am not sure what uses this function, so I don't
        #   feel confident changing it.
        # See:
        #   SHA 369050067485636475cd38d2cc8f38aaf58a3932
        if format == '%M':
            result = text_type(int(seconds / 60))
            # From scientificsteve's PR:
            #  result = text_type(int(round(seconds / 60.)))
        elif format == '%H:%M':
            result = (
                '{hours:02d}:{minutes:02d}'.format(
                    hours=int(seconds / 3600),
                    minutes=int((seconds % 3600) / 60),
                )
            )
        else:
            (
                tm_fmttd, tm_scale, tm_units,
            ) = timedelta_wrap(seconds=seconds).time_format_scaled()
            result = tm_fmttd

        return result

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
        self.tags = set()
        for tagn in set(tags) if tags else set():
            tag = tagn if isinstance(tagn, Tag) else Tag(name=tagn)
            self.tags.add(tag)

    @property
    def tags_sorted(self):
        return sorted(list(self.tags), key=attrgetter('name'))

    @property
    def tagfield(self):
        return self.tagnames()

    # (lb): People associate tags with pound signs -- like, #hashtag!
    # But Bash, and other shells, use octothorpes to start comments.
    # The user can tell Bash to interpret a pound sign as input by
    # "#quoting" it, or by \#delimiting it. Hamster also lets the user
    # use an '@' at symbol instead (not to be confused with typical
    # social media usage of '@' to refer to other users or people).
    # By default, this function assumes the tags do not need special
    # delimiting; that the pound sign is fine.
    def tagnames(
        self,
        hashtag_token='#',
        quote_tokens=False,
        underlined=False,
    ):
        def format_tagname(tag):
            tagged = '{}{}'.format(
                colorize(hashtag_token, 'grey_78'),
                colorize(tag.name, 'dark_olive_green_1b'),
            )
            if underlined:
                tagged = '{}{}{}'.format(
                    attr('underlined'), tagged, attr('res_underlined'),
                )
            if quote_tokens:
                tagged = '"{}"'.format(tagged)
            return tagged

        # NOTE: The returned string includes leading space if nonempty!
        tagnames = ''
        if self.tags:
            ordered_tagnames = [
                format_tagname(tag) for tag in self.tags_sorted
            ]
            tagnames = ' '.join(ordered_tagnames)
        return tagnames

    def tagnames_underlined(self):
        return self.tagnames(underlined=True)

    # ***

    def friendly_str(
        self,
        shellify=False,
        description_sep=', ',
        localize=False,
        truncate=False,
        include_id=False,
        colorful=False,
        cut_width=None,
        show_elapsed=False,
    ):
        """
        Flexible Fact serializer.
        """
        def _friendly_str(fact):
            was_coloring = set_coloring(colorful)
            parts = assemble_parts(fact)
            result = format_result(fact, parts)
            # (lb): EXPLAIN: Why do we cast here?
            result = text_type(result)
            set_coloring(was_coloring)
            return result

        def assemble_parts(fact):
            parts = [
                get_id_string(fact),
                get_times_string(fact),
                get_activity_string(fact),
                get_tags_string(fact),
            ]
            return parts

        def format_result(fact, parts):
            result = '{fact_meta}{description}'.format(
                fact_meta=' '.join(filter(None, parts)),
                description=get_description_string(fact),
            )
            return result

        def get_id_string(fact):
            if not include_id:
                return ''
            return colorize('(${})'.format(fact.pk), 'grey_78')

        def get_times_string(fact):
            times = ''
            times += get_times_string_start(fact)
            times += get_times_string_end(fact, times)
            times += get_times_duration(fact)
            return times

        def get_times_string_start(fact):
            if not fact.start:
                return ''
            if not localize:
                start_time = fact.start_fmt_utc
            else:
                start_time = fact.start_fmt_local
            start_time = colorize(start_time, 'sandy_brown')
            return start_time

        def get_times_string_end(fact, times):
            # NOTE: The CLI's DATE_TO_DATE_SEPARATORS[0] is 'to'.
            prefix = colorize(' to ', 'grey_85') if times else ''
            if not fact.end:
                # (lb): What's a good term here? '<ongoing>'? Or just 'now'?
                end_time = _('<now>')
            elif not localize:
                end_time = fact.end_fmt_utc
            else:
                end_time = fact.end_fmt_local
            end_time = colorize(end_time, 'sandy_brown')
            return prefix + end_time

        def get_times_duration(fact):
            if not show_elapsed:
                return ''
            duration = ' [{}]'.format(
                fact.get_string_delta('', localize),
            )
            return colorize(duration, 'grey_78')

        def get_activity_string(fact):
            # (lb): We can skip delimiter after time when using ISO 8601.
            if not self.activity_name:
                act_cat = '@'
            else:
                act_cat = (
                    '{}@{}'.format(
                        self.activity_name,
                        self.category_name,
                    )
                )
            act_cat = colorize(act_cat, 'cornflower_blue', 'bold', 'underlined')
            act_cat = '"{}"'.format(act_cat) if shellify else act_cat
            return act_cat

        def get_tags_string(fact):
            # (lb): There are three ways to "shellify" a Hamster hashtag token:
            #         1.) "#quote" it;
            #         2.) \#delimit it; or
            #         3.) use the inoffensive @ symbol instead of #.
            # Let's do 1.) by default, because most people associate the pound
            # sign with tags, because quotes are less offensive than a slash,
            # and because the @ symbol makes me think of "at'ing someone".
            #   Nope:  hashtag_token = '@' if shellify else '#'
            return fact.tagnames(quote_tokens=shellify)

        def get_description_string(fact):
            description = self.description or ''
            if description:
                if truncate:
                    description = format_value_truncate(description, cut_width)
                description = '{}{}'.format(description_sep, description)
            return description

        # ***

        return _friendly_str(self)

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

          - Note that Hamster is very unassuming with whitespace. It can be
            used in the Activity and Category names, as well as in tags.

        Attention:

            ``Fact.tags`` is a set and hence unordered. In order to provide
            a deterministic canonical return string, we sort tags by name.
            This is purely cosmetic and does not imply any actual ordering
            of those facts on the instance level.

        Returns:
            text_type: Canonical string encoding all available fact info.
        """
        return self.friendly_str(
            shellify=shellify,
            description_sep=', ',
            localize=False,
            truncate=False,
            include_id=False,
            colorful=False,
        )

    @property
    def brief(self):
        # (lb): This fcn. is not used! Delete it? Probably.
        assert(False)
        return self.friendly_str(
            description_sep=': ',
            localize=True,
            truncate=True,
            include_id=True,
            colorful=False,
        )

    # ***

    def friendly_diff(self, other, truncate=False):
        result = ''
        result += self.diff_other(other, 'start', 'start_fmt_local')
        result += self.diff_other(other, 'end', 'end_fmt_local')
        if (not truncate) or self.pk or other.pk:
            def beautify(self_val, other_val):
                if 'split' in other.dirty_reasons or 'split' in self.dirty_reasons:
                    pass
                if 'lsplit' in other.dirty_reasons:
                    other_val = 'New split fact, created before new fact'
                if 'rsplit' in other.dirty_reasons:
                    other_val = 'New split fact, created after new fact'
                return (self_val, other_val)
            result += self.diff_other(other, 'id', 'pk', beautify=beautify)
        result += self.diff_other(other, 'deleted', 'deleted')
        # MAYBE?: (lb): Would we even want to show the split_from fact?
        #  result += self.diff_other(other, 'split_from', 'split_from')
        result += self.diff_other(other, 'activity', 'activity_name')
        result += self.diff_other(other, 'category', 'category_name')
        result += self.diff_other(other, 'tags', 'tagnames_underlined')
        result += self.diff_other(
            other, 'description', 'description', truncate=truncate,
        )
        return result.rstrip()

    def diff_other(self, other, name, prop, truncate=False, beautify=None):
        self_val = resolve_attr_or_method(self, prop)
        other_val = ''
        if other is not None:
            other_val = resolve_attr_or_method(other, prop)
            if callable(other_val):
                other_val = other_val()
            self_val, other_val = self.diff_values_enhance(
                self_val, other_val, truncate=truncate, beautify=beautify,
            )
        elif truncate:
            self_val = format_value_truncate(self_val)
        attr_diff = self.diff_values_format(name, self_val, other_val)
        return attr_diff

    def diff_values_enhance(
        self, self_val, other_val, truncate=False, beautify=None,
    ):
        differ = False
        if self_val != other_val:
            differ = True
        if truncate:
            self_val = format_value_truncate(self_val)
            other_val = format_value_truncate(other_val)
        if beautify is not None:
            self_val, other_val = beautify(self_val, other_val)
            if self_val != other_val:
                differ = True
        if differ:
            self_val = self.format_edited_before(self_val)
            other_val = self.format_edited_after(other_val)
        else:
            other_val = ''
        return (self_val, other_val)

    def format_edited_before(self, before_val):
        return '{}{}{}'.format(
            fg('spring_green_3a'),
            before_val,
            attr('reset'),
        )

    def format_edited_after(self, after_val):
        return ' => {}{}{}{}{}'.format(
            attr('bold'),
            attr('underlined'),
            fg('light_salmon_3b'),
            after_val,
            attr('reset'),
        )

    def diff_values_format(self, name, self_val, other_val):
        prefix = '  '
        attr_diff = '{}{:.<19} : {}{}\n'.format(
            prefix, name, self_val, other_val,
        )
        return attr_diff

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
        Construct a new ``hamster_lib.Fact`` from a string of fact details,
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

            lenient (bool, optional): If False, parser raises errors on misssing
                mandatory components (such as time or activity). (Category,
                tags, and description are optional.)

        Returns:
            hamster_lib.Fact: New ``Fact`` object constructed from factoid.

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

        new_fact = cls.create_from_parsed_fact(parsed_fact, lenient=lenient)

        return new_fact, err

    @classmethod
    def create_from_parsed_fact(
        cls,
        parsed_fact,
        lenient=False,
    ):
        start = parsed_fact['start']
        end = parsed_fact['end']
        # Verify that start > end, if neither are None.
        start, end = time_helpers.validate_start_end_range((start, end))

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
            activity, start, end=end, description=description, tags=tags,
        )

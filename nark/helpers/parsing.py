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

"""This module provides nark raw fact parsing-related functions."""

from gettext import gettext as _

import logging
import os
import re

import lazy_import

from .parse_errors import (
    ParserException,
    ParserInvalidDatetimeException,
    ParserMissingActivityException,
    ParserMissingDatetimeOneException,
    ParserMissingDatetimeTwoException,
    ParserMissingSeparatorActivity
)
from .parse_time import HamsterTimeSpec, parse_datetime_iso8601

# Profiling: `import dateparser` takes ~ 0.2 seconds.
dateparser = lazy_import.lazy_module('dateparser')


__all__ = (
    'parse_factoid',
    'Parser',
)


# FIXME/MAYBE: (lb): New pattern? Can modules just get the logger here?
#   Or should we make a top-level module that just returns this? Probably
#   the latter, so we're not hard-coding 'nark.log' everywhere.
logger = logging.getLogger('nark.log')


# FIXME: (lb): What's the best way to handle module-scope vars like this?
#        Should this be from config?
#        From a "globals" module?
#        From a function-scoped sub-function?
#        Or is here fine?
DATE_TO_DATE_SEPARATORS__RAW = ['to', 'until', '-']


FACT_METADATA_SEPARATORS = [",", ":"]


# Map time_hint to minimum and maximum datetimes to seek.
TIME_HINT_CLUE = {
    'verify_start': (1, 2),  # end time is optional.
    'verify_end': (1, 1),  # exactly one is required.
    'verify_then': (0, 2),  # both times are optional.
    'verify_still': (0, 2),  # both times are optional.
    'verify_none': (0, 0),  # none is none is all alone.
    'verify_both': (2, 2),  # and both is both times two.
}


class Parser(object):
    """FIXME"""

    ACTEGORY_SEP = '@'

    RE_DATE_TO_DATE_SEP = None
    RE_SPLIT_CAT_AND_TAGS = None
    RE_SPLIT_TAGS_AND_TAGS = None

    def __init__(self):
        self.reset()

    def reset(self):
        self.reset_rules()
        self.reset_result()

    def reset_rules(self):
        self.raw = None
        self.flat = None
        self.rest = None

        self.time_hint = None
        self.re_item_sep = None
        self.hash_stamps = None
        self.lenient = None
        self.local_tz = None
        self.skip_dateparser = False

    def reset_result(self):
        self.datetime1 = None
        self.datetime2 = None
        self.raw_datetime1 = None
        self.raw_datetime2 = None
        self.type_datetime1 = None
        self.type_datetime2 = None
        self.activity_name = None
        self.category_name = None
        self.tags = None
        self.description = None
        self.warnings = []

    def __str__(self):
        return (
            'raw: {}'
            ' / flat: {}'
            ' / rest: {}'

            ' / time_hint: {}'
            ' / re_item_sep: {}'
            ' / hash_stamps: {}'
            ' / lenient: {}'
            ' / local_tz: {}'
            ' / skip_dateparser: {}'

            ' / datetime1: {}'
            ' / datetime2: {}'
            ' / raw_datetime1: {}'
            ' / raw_datetime2: {}'
            ' / type_datetime1: {}'
            ' / type_datetime2: {}'
            ' / activity_name: {}'
            ' / category_name: {}'
            ' / tags: {}'
            ' / description: {}'
            ' / warnings: {}'
            .format(
                self.raw,
                self.flat,
                self.rest,

                self.time_hint,
                self.re_item_sep,
                self.hash_stamps,
                self.lenient,
                self.local_tz,
                self.skip_dateparser,

                self.datetime1,
                self.datetime2,
                self.raw_datetime1,
                self.raw_datetime2,
                self.type_datetime1,
                self.type_datetime2,
                self.activity_name,
                self.category_name,
                self.tags,
                self.description,
                self.warnings,
            )
        )

    # **************************************
    # *** All the patterns we're gonna need!
    # **************************************

    def setup_patterns(self):
        self.re_setup_datatimes_separator()
        self.re_setup_category_and_tags()
        self.re_setup_tags_upon_tags()

    def re_setup_datatimes_separator(self):
        Parser.RE_DATE_TO_DATE_SEP = re.compile(
            r'\s(to|until|\-)\s|(?<=\d)(\-)(?=\d)'
        )

    def re_setup_category_and_tags(self):
        # FIXME/2018-05-15: (lb): Should #|@ be settable, like the other
        # two (DATE_TO_DATE_SEPARATORS and FACT_METADATA_SEPARATORS)?
        # Or does that make maintaining the parser that much harder?
        # HINT: Matches space(s) followed by hash.
        #   On split, removes whitespace (because matched).
        #   - First split element may be empty string.
        #   - Final split element may have trailing spaces.
        Parser.RE_SPLIT_CAT_AND_TAGS = re.compile(
            r'\s+[{hash_stamps}](?=\S)'
            .format(hash_stamps=self.hash_stamps)
        )

    def re_setup_tags_upon_tags(self):
        # HINT: Matches only on a hash starting the string.
        #   On split, leaves trailing spaces on each element.
        #   - First split element may be whitespace string.
        Parser.RE_SPLIT_TAGS_AND_TAGS = re.compile(
            r'(?<!\S)[{hash_stamps}](?=\S)'
            .format(hash_stamps=self.hash_stamps)
        )

    # **************************************
    # *** dissect_raw_fact: Main class entry
    # **************************************

    def dissect_raw_fact(self, *args, **kwargs):
        """
        FIXME: Document
        """
        # The raw_fact is a tuple. The user can use quotes or not, and it's
        # up to us to figure things out.

        self.prepare_parser(*args, **kwargs)

        err = None

        try:
            self.parse()
        except ParserException as perr:
            err = perr
            if not self.lenient:
                raise

        return err

    # ************************************
    # *** Helper fcns for dissect_raw_fact
    # ************************************

    def parse(self):
        self.reset_result()
        try:
            # If the date(s) are ISO 8601, find 'em fast.
            after_datetimes = self.parse_datetimes_easy()
            # Datetime(s) were 8601 (code did not raise),
            # so now look for the '@' and set the activity.
            rest_after_act, expect_category = self.lstrip_activity(after_datetimes)
        except ParserException:
            self.reset_result()
            rest_after_act, expect_category = self.parse_datetimes_hard()
        if expect_category:
            self.parse_cat_and_remainder(rest_after_act)
        else:
            self.parse_tags_and_remainder(rest_after_act)
        # Validation.
        self.hydrate_datetimes()
        if not self.activity_name:
            self.raise_missing_activity()
        # We could raise on missing-category; or
        #   maybe caller can deduce, so don't.
        # Don't care if tags or description are empty.

    def prepare_parser(self, *args, **kwargs):
        self.setup_rules(*args, **kwargs)
        self.setup_patterns()

    def setup_rules(
        self,
        factoid,
        time_hint='verify_none',
        separators=None,
        hash_stamps=None,
        lenient=False,
        # FIXME/2018-05-22 20:42: (lb): Implement: tz_local
        local_tz=None,  # Default to None, i.e., naive
    ):
        if isinstance(factoid, str):
            # Path from tests/nark/test_objects.py, but not from dob.
            factoid = (factoid,)
        else:
            # The user can get here on an empty --ask, e.g.,
            #   ``nark on --ask``
            factoid = factoid or ('',)

        # Parse a flat copy of the args.
        full = ' '.join(factoid)
        parts = full.split(os.linesep, 1)
        flat = parts[0]
        more_description = '' if len(parts) == 1 else parts[1].strip()

        # Items are separated by any one of the separator(s)
        # not preceded by whitespace, and followed by either
        # whitespace, or end of string/before newline.
        if not separators:
            separators = FACT_METADATA_SEPARATORS
        assert len(separators) > 0
        sep_group = '|'.join(separators)
        # Gobble whitespace as part of separator, to make it easier to pull
        # data apart and then part it back together if we need. E.g., if user
        # puts description on same line as meta data, and if description contains
        # separators, we'll split the line first to parse out the meta data, and
        # then we'll put it back together, so if a separator is part of the
        # description, we want to be sure to retain the whitespace around the
        # separator if we have to patch the description back together from its
        # parts that did not turn out to be meta data (like #tags).
        # This is how parser originally split, leaving whitespace in the last part:
        #   # C✗P✗: re.compile('(?:,|:)(?=\\s|$)')
        #   ..._sep = re.compile(r'({})(?=\s|$)'.format(sep_group))
        # We can pull whitespace into the separator with two Levenshtein moves.
        re_item_sep = re.compile(r'({}(?=\s+|$))'.format(sep_group))

        if not hash_stamps:
            hash_stamps = '#@'

        self.reset()
        self.raw = factoid
        self.flat = flat
        self.rest = more_description
        self.time_hint = time_hint
        self.re_item_sep = re_item_sep
        self.hash_stamps = hash_stamps
        self.lenient = lenient
        self.local_tz = local_tz

    def parse_datetimes_easy(self):
        rest = self.flat
        if self.time_hint == 'verify_end':
            rest, _sep = self.must_parse_datetime_from_rest(rest, 'datetime2')
        elif self.time_hint != 'verify_none':
            minmax = TIME_HINT_CLUE[self.time_hint]
            rest = self.parse_datetimes_easy_both(rest, minmax)
        # else, time_hint == 'verify_none', so rest is rest.
        return rest

    def parse_datetimes_easy_both(self, rest, minmax):
        try:
            rest, sep = self.must_parse_datetime_from_rest(rest, 'datetime1')
        except ParserMissingDatetimeOneException:
            if minmax[0] == 0:
                return rest
            raise
        strictly_two = (minmax[0] == 2)
        # If sep is nonempty (e.g., ':', or ','), do not expect datetime2.
        if not sep:
            # The next token in rest could be the "to"/"until"/"-" sep.
            parts = Parser.RE_DATE_TO_DATE_SEP.split(rest, 1)
            # ... however, the RE_DATE_TO_DATE_SEP regex matches anywhere in line.
            # So verify that first part of split is empty, otherwise to/until sep
            # does not start the rest of the factoid.
            if (parts[0].strip() == '') and (len(parts) > 1):
                # There are four capture groups:
                #   1. The stuff before the times;
                #   2. The 'to'/'until'/'-', if separator matched on word boundary,
                #        e.g., "X to Y"; otherwise, None.
                #   3. The '-', if separator matched on digit boundary,
                #        e.g., "9-5"; otherwise, None.
                #   4. The stuff after the (2.) or (3.) separator.
                assert len(parts) == 4
                assert (parts[1] is None) ^ (parts[2] is None)
                separator = parts[1] or parts[2]
                assert separator in DATE_TO_DATE_SEPARATORS__RAW
                after_dt2, _sep = self.must_parse_datetime_from_rest(
                    parts[3], 'datetime2', ok_if_missing=(not strictly_two),
                )
                if after_dt2 is not None:
                    rest = after_dt2
                # else, was not a datetime, so re-include DATE_TO_DATE_SEPARATOR.
            elif strictly_two:
                self.raise_missing_datetime_two()
        elif strictly_two:
            self.raise_missing_datetime_two()
        return rest

    def parse_datetimes_hard(self):
        expect_category = True
        if self.time_hint == 'verify_none':
            # There is no datetime(s). Just the act@cat.
            rest_after_act, expect_category = self.lstrip_activity(self.flat)
        else:
            minmax = TIME_HINT_CLUE[self.time_hint]
            rest_after_act = self.lstrip_datetimes(minmax)
        return (rest_after_act, expect_category)

    def lstrip_datetimes(self, minmax):
        two_is_okay = (minmax[1] == 2)
        strictly_two = (minmax[0] == 2)
        parts = self.lstrip_datetimes_delimited()
        datetimes_and_act, datetimes, rest_after_act = parts
        if datetimes:
            self.must_parse_datetimes_known(datetimes, two_is_okay, strictly_two)
            # We've processed datetime1, datetime2, and activity_name.
        else:
            # The user did not delimit the datetimes and the activity.
            # See if the user specified anything magically, otherwise, bye.
            self.must_parse_datetimes_magic(datetimes_and_act, two_is_okay, strictly_two)
        return rest_after_act

    def lstrip_datetimes_delimited(self):
        # If user wants to use friendly datetimes, they need to delimit, e.g.:
        #   `nark yesterday until today at 3 PM, act @ cat # tag 1, descrip`
        # Note that the special token 'now' could be considered okay:
        #   `nark yesterday at 3 PM until now act @ cat # tag 1 "descrip"`
        # First look for the activity@category separator, '@'. This is a simple
        # find (index) because we insist that neither the datetime, nor the datetimes
        # sep, include the `@` symbol; and that @tags follow the activity@category.
        act_cat_sep_idx = self.must_index_actegory_sep(self.flat, must=True)
        # Next, split the raw factoid into two: datetime(s) and activity; and the rest.
        datetimes_and_act = self.flat[:act_cat_sep_idx]
        rest_after_act = self.flat[act_cat_sep_idx + 1:]
        # Determine if the user delimited the datetime(s) from the activity
        # using, e.g., a comma, ',' (that follows not-whitespace, and is
        # followed by whitespace/end-of-string). (Note that ':' can also be
        # used as the delimiter -- even though it's used to delimit time --
        # because the item separator must be the last character of a word.)
        parts = self.re_item_sep.split(datetimes_and_act, 1)
        if len(parts) == 3:
            datetimes = parts[0]
            # parts[1] is the sep, e.g., ',' or ':'.
            self.activity_name = parts[2]
        else:
            assert len(parts) == 1
            datetimes = None
        return (datetimes_and_act, datetimes, rest_after_act)

    def must_index_actegory_sep(self, part, must=True):
        try:
            # Find the first '@' in the raw, flat factoid.
            return part.index(Parser.ACTEGORY_SEP)
        except ValueError:
            if must:
                # It's only mandatory that we find an activity if the
                # datetimes are not ISO 8601 (otherwise we cannot tell
                self.raise_missing_separator_activity()
            return -1

    # *** 1: Parse datetime(s) and activity.

    def must_parse_datetimes_known(self, datetimes, two_is_okay, strictly_two):
        assert self.raw_datetime1 is None
        assert self.raw_datetime2 is None
        assert two_is_okay or (not strictly_two)

        if two_is_okay:
            # Look for separator, e.g., " to ", or " until ", or " - "/"-", etc.
            parts = Parser.RE_DATE_TO_DATE_SEP.split(datetimes, 1)
            if len(parts) > 1:
                assert len(parts) == 4  # middle 2 parts are the separator
                assert (parts[1] is None) ^ (parts[2] is None)
                separator = parts[1] or parts[2]
                assert separator in DATE_TO_DATE_SEPARATORS__RAW

                self.raw_datetime1 = parts[0]  # first datetime
                self.raw_datetime2 = parts[3]  # other datetime
            elif strictly_two:
                self.raise_missing_datetime_two()

        if not self.raw_datetime1:
            # Maybe not two_is_okay; definitely not strictly_two.
            if self.time_hint == 'verify_end':
                self.datetime1 = ''
                self.raw_datetime2 = datetimes
            else:
                self.raw_datetime1 = datetimes
                self.datetime2 = ''

    def must_parse_datetimes_magic(self, datetimes_and_act, two_is_okay, strictly_two):
        assert self.raw_datetime1 is None
        assert self.raw_datetime2 is None
        assert two_is_okay or (not strictly_two)

        if two_is_okay:
            # Look for separator, e.g., " to ", or " until ", or " - ", etc.
            parts = Parser.RE_DATE_TO_DATE_SEP.split(datetimes_and_act, 1)
            if len(parts) > 1:
                assert len(parts) == 4
                assert (parts[1] is None) ^ (parts[2] is None)
                separator = parts[1] or parts[2]
                assert separator in DATE_TO_DATE_SEPARATORS__RAW

                self.raw_datetime1 = parts[0]
                dt_and_act = parts[3]
                dt_attr = 'datetime2'
            elif strictly_two:
                self.raise_missing_datetime_two()

        if not self.raw_datetime1:
            dt_and_act = datetimes_and_act
            if self.time_hint == 'verify_end':
                dt_attr = 'datetime2'
            else:
                dt_attr = 'datetime1'

        rest, _sep = self.must_parse_datetime_from_rest(dt_and_act, dt_attr)
        self.activity_name = rest

    def must_parse_datetime_from_rest(
        self, datetime_rest, datetime_attr, ok_if_missing=False,
    ):
        assert datetime_attr in ['datetime1', 'datetime2']
        assert not ok_if_missing or datetime_attr == 'datetime2'
        # See if datetime: '+/-n' mins, 'nn:nn' clock, or ISO 8601.
        dt, type_dt, sep, rest = HamsterTimeSpec.discern(datetime_rest)
        if dt is not None:
            assert type_dt
            if type_dt == 'datetime':
                self.warn_if_datetime_missing_clock_time(dt, rest)
                dt = parse_datetime_iso8601(dt, must=True, local_tz=self.local_tz)
            # else, relative time, or clock time; let caller handle.
            setattr(self, datetime_attr, dt)
            # Set either 'type_datetime1' or 'type_datetime2'.
            # (NOTE: (lb): No caller actually uses type_dt.)
            setattr(self, 'type_{}'.format(datetime_attr), type_dt)
        elif datetime_attr == 'datetime1':
            self.raise_missing_datetime_one()
        elif not ok_if_missing:
            assert datetime_attr == 'datetime2'
            self.raise_missing_datetime_two()
        else:
            rest = None
        return rest, sep

    def warn_if_datetime_missing_clock_time(self, raw_dt, after_dt):
        if HamsterTimeSpec.has_time_of_day(raw_dt):
            return
        # NOTE: re.match checks for a match only at the beginning of the string.
        looks_like_clock_abbrev = re.match(r'\s*(\d:\d{2}|\d{3})(\s+|$)', after_dt)
        warn_msg = _('The identified datetime is missing the time of day.')
        if looks_like_clock_abbrev:
            warn_msg += _(
                ' Perhaps those three digits after the date'
                ' should be a 4-digit clocktime?'
            )
        else:
            warn_msg += _(' Is that what you wanted? (Probably not!)')
        self.warnings.append(warn_msg)

    def lstrip_activity(self, act_and_rest):
        act_cat_sep_idx = self.must_index_actegory_sep(act_and_rest, must=False)
        if act_cat_sep_idx >= 0:
            just_the_activity = act_and_rest[:act_cat_sep_idx]
            rest_after_act = act_and_rest[act_cat_sep_idx + 1:]
            expect_category = True
            self.activity_name = just_the_activity
        else:
            # Assume no activity or category.
            rest_after_act = act_and_rest
            expect_category = False
        return (rest_after_act, expect_category)

    # *** 2: Parse category and tags.

    def parse_cat_and_remainder(self, cat_and_remainder):
        # NOTE: cat_and_remainder may contain leading whitespace, if input
        #       was of form ``act @ cat``, not ``act@cat`` or ``act @cat``.
        # Split on any delimiter: ,|:|\n
        parts = self.re_item_sep.split(cat_and_remainder, 2)
        tags_description_sep = ''
        description_prefix = ''
        if len(parts) == 1:
            cat_and_tags = parts[0]
            unseparated_tags = None
        else:
            self.category_name = parts[0]
            cat_and_tags = None
            # parts[1] and parts[3] are the separators, e.g., ',' or ':'.
            unseparated_tags = parts[2]
            if len(parts) == 5:
                # If there's a description with a separator on same line as
                # meta data, tags_description_sep may really be description
                # prefix. So keep whitespace until we know for sure (which
                # self.re_item_sep.split accomplishes -- it puts the whitespace
                # in tags_description_sep, not the last part).
                tags_description_sep = parts[3]
                # Any whitespace between parts should be part of the former,
                # and the last part can have any of its ending whitespace
                # stripped. (Or maybe don't strip at all? Don't really care
                # if user has trailing whitespace or not, I shouldn't think!
                # We only care to remove whitespace between separators/meta.)
                #   #description_prefix = parts[4].strip()
                #   #description_prefix = parts[4].rstrip()
                description_prefix = parts[4]
            else:
                assert len(parts) == 3

        if cat_and_tags:
            cat_tags = Parser.RE_SPLIT_TAGS_AND_TAGS.split(cat_and_tags, 1)
            self.category_name = cat_tags[0]
            if len(cat_tags) == 2:
                unseparated_tags = self.hash_stamps[0] + cat_tags[1]

        self.consume_tags_and_description_prefix(
            unseparated_tags, tags_description_sep, description_prefix,
        )

    def parse_tags_and_remainder(self, tags_and_remainder):
        parts = self.re_item_sep.split(tags_and_remainder, 1)
        tags_description_sep = ''
        description_middle = ''
        if len(parts) == 3:
            # parts[1] is the sep, e.g., ',' or ':'.
            tags_description_sep = parts[1]
            description_middle = parts[2]
        self.consume_tags_and_description_prefix(
            parts[0], tags_description_sep, description_middle,
        )

    def consume_tags_and_description_prefix(
        self, unseparated_tags, tags_description_sep='', description_middle='',
    ):
        description_prefix = ''
        if unseparated_tags:
            # NOTE: re.match checks for a match only at the beginning of the string.
            match_tags = Parser.RE_SPLIT_CAT_AND_TAGS.match(unseparated_tags)
            if match_tags is not None:
                split_tags = Parser.RE_SPLIT_TAGS_AND_TAGS.split(unseparated_tags)
                self.consume_tags(split_tags)
            else:
                description_prefix = unseparated_tags
                description_prefix += tags_description_sep

        self.description = description_prefix
        self.description += description_middle
        self.description += "\n" if self.rest else ""
        self.description += self.rest

    def consume_tags(self, tags):
        tags = [tag.strip() for tag in tags]
        tags = list(filter(None, tags))
        self.tags = tags

    # ***

    def hydrate_datetimes(self):
        self.datetime1 = self.hydrate_datetime_either(
            self.datetime1, self.raw_datetime1,
        )
        self.datetime2 = self.hydrate_datetime_either(
            self.datetime2, self.raw_datetime2,
        )

    def hydrate_datetime_either(self, the_datetime, raw_datetime):
        if the_datetime or not raw_datetime:
            return the_datetime
        # Remove any trailing separator that may have been left.
        raw_datetime = self.re_item_sep.sub('', raw_datetime)
        if not the_datetime:
            the_datetime = parse_datetime_iso8601(
                raw_datetime, must=False, local_tz=self.local_tz,
            )
            if the_datetime:
                # 2018-07-02: (lb): Is this path possible?
                #   Or would we have processed ISO dates already?
                logger.warning('hydrate_datetime_either: found ISO datetime?')
        if not the_datetime:
            the_datetime = self.hydrate_datetime_friendly(
                raw_datetime, must=False,
            )
        return the_datetime

    def hydrate_datetime_friendly(self, datepart, must=False):
        settings = {
            # PREFER_DATES_FROM:    defaults to current_period.
            #                       Options are future or past.
            # SUPPORT_BEFORE_COMMON_ERA: defaults to False.
            # PREFER_DAY_OF_MONTH:  defaults to current.
            #                       Could be first and last day of month.
            # SKIP_TOKENS:          defaults to [‘t’]. Can be any string.
            # TIMEZONE:             defaults to UTC. Can be timezone abbrev
            #                       or any of tz database name as given here:
            #     https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
            # RETURN_AS_TIMEZONE_AWARE: return tz aware datetime objects in
            #                       case timezone is detected in the date string.
            # RELATIVE_BASE:        count relative date from this base date.
            #                       Should be datetime object.

            # FIXME/2018-05-22 20:46: (lb): Use RELATIVE_BASE to support
            # friendlies relative to other time, e.g.,
            #       `from 1 hour ago to 2018-05-22 20:47`

            'RETURN_AS_TIMEZONE_AWARE': False,
        }
        if self.local_tz:
            # NOTE: Uses machine-local tz, unless TIMEZONE set.
            settings['RETURN_AS_TIMEZONE_AWARE'] = True
            settings['TIMEZONE'] = self.local_tz

        parsed = dateparser.parse(datepart, settings=settings)

        if not parsed:
            parsed = None
            if must:
                raise ParserInvalidDatetimeException(_(
                    'Unable to parse datetime: {}.'
                    .format(datepart)
                ))
        elif self.skip_dateparser:
            # FIXME: Implement use of this in import routine.
            #        Caller can use RELATIVE_BASE to resolve time correctly.

            # The caller is telling us that the date is not actually
            # relative to "now". It'll call dateparser later with the
            # correct context.
            parsed = datepart

        return parsed

    # ***

    def raise_missing_datetime_one(self):
        msg = _('Expected to find a datetime.')
        raise ParserMissingDatetimeOneException(msg)

    def raise_missing_datetime_two(self):
        def _raise_missing_datetime_two():
            sep_str = comma_or_join(DATE_TO_DATE_SEPARATORS__RAW)
            msg = _(
                'Expected to find the two datetimes separated by one of: {}.'
                .format(sep_str)
            )
            raise ParserMissingDatetimeTwoException(msg)

        def comma_or_join(seq):
            # Need os.linesep or is \n fine?
            seq = [part.replace('\n', '\\n') for part in seq]
            if len(seq) > 1:
                sep_str = '{} or {}'.format(', '.join(seq[:-1]), seq[-1])
            else:
                sep_str = seq[0]
            return sep_str

        _raise_missing_datetime_two()

    def raise_missing_separator_activity(self):
        msg = _('Expected to find an "@" indicating the activity.')
        raise ParserMissingSeparatorActivity(msg)

    def raise_missing_activity(self):
        msg = _('Expected to find an Activity name.')
        raise ParserMissingActivityException(msg)


# For args, see: Parser.setup_rules().
def parse_factoid(*args, **kwargs):
    """
    Just a little shimmy-shim-shim (to Parser.dissect_raw_fact).
    """
    parser = Parser()
    err = parser.dissect_raw_fact(*args, **kwargs)
    fact_dict = {
        'start': parser.datetime1 if parser.datetime1 else None,
        'end': parser.datetime2 if parser.datetime2 else None,
        'activity': parser.activity_name.strip() if parser.activity_name else '',
        'category': parser.category_name.strip() if parser.category_name else '',
        'description': parser.description.strip() if parser.description else '',
        'tags': parser.tags if parser.tags else [],
        'warnings': parser.warnings,
    }
    return fact_dict, err


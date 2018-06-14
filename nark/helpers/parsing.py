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

"""This module provides nark raw fact parsing-related functions."""

from __future__ import absolute_import, unicode_literals

import dateparser
import iso8601
import logging
import os
import re

from .dated import HamsterTimeSpec
from .strings import comma_or_join


__all__ = [
    'parse_factoid',
    'ParserException',
    'ParserMissingDatetimeException',
    'ParserMissingDatetimeOneException',
    'ParserMissingDatetimeTwoException',
    'ParserInvalidDatetimeException',
    'ParserMissingSeparatorActivity',
    'ParserMissingActivityException',
    'Parser',
]


# FIXME/MAYBE: (lb): New pattern? Can modules just get the logger here?
#   Or should we make a top-level module that just returns this? Probably
#   the latter, so we're not hard-coding 'nark.log' everywhere.
logger = logging.getLogger('nark.log')


# FIXME: (lb): What's the best way to handle module-scope vars like this?
#        Should this be from config?
#        From a "globals" module?
#        From a function-scoped sub-function?
#        Or is here fine?
DATE_TO_DATE_SEPARATORS = ['to', 'until', '\-', '\|']


FACT_METADATA_SEPARATORS = [",", ":", os.linesep]


TIME_HINT_MAP = {
    'on': 'verify_none',
    'now': 'verify_none',
    'at': 'verify_start',
    'to': 'verify_end',
    'until': 'verify_end',
    'from': 'verify_both',
    'between': 'verify_both',
}


class ParserException(Exception):
    """Raised if parser cannot decipher nark factoid string."""
    pass
# FIXME/LINTING/2018-05-15: (lb): I bet this needs to be double-spaced!

class ParserMissingDatetimeException(ParserException):  # noqa: E302
    """Raised if the raw_fact is missing one or both datetime tokens."""
    pass

class ParserMissingDatetimeOneException(ParserMissingDatetimeException):  # noqa: E302
    """Raised if the raw_fact is missing its start datetime token(s)."""
    pass

class ParserMissingDatetimeTwoException(ParserMissingDatetimeException):  # noqa: E302
    """Raised if the raw_fact is missing its end datetime token(s)."""
    pass

class ParserInvalidDatetimeException(ParserException):  # noqa: E302
    """Raised if a time from raw_fact in not parseworthy."""
    pass

class ParserMissingSeparatorActivity(ParserException):  # noqa: E302
    """Raised if activity@category separator not found."""
    pass

class ParserMissingActivityException(ParserException):  # noqa: E302
    """Raised if factoid is missing: act@cat, cat@, @cat, or just @."""
    pass


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
        # MAYBE/2018-05-20 17:39: (lb): Not sure the dt meta is necessary.
        self.raw_datetime1 = None
        self.raw_datetime2 = None
        self.type_datetime1 = None
        self.type_datetime2 = None
        self.activity_name = None
        self.category_name = None
        self.tags = None
        self.description = None

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
            r'\s({})\s'.format('|'.join(DATE_TO_DATE_SEPARATORS))
        )

    def re_setup_category_and_tags(self):
        # FIXME/2018-05-15: (lb): Should #|@ be settable, like the other
        # two (DATE_TO_DATE_SEPARATORS and FACT_METADATA_SEPARATORS)?
        # Or does that make maintaining the parser that much harder?
        Parser.RE_SPLIT_CAT_AND_TAGS = re.compile(
            r'\s+[{hash_stamps}](?=\S)'
            .format(hash_stamps=self.hash_stamps)
        )

    def re_setup_tags_upon_tags(self):
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
            # Datetimes were 8601 (code did not raise), so
            # now look for the '@' and set the activity.
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
        time_hint='',
        separators=None,
        hash_stamps=None,
        lenient=False,
        # FIXME/2018-05-22 20:42: (lb): Implement: tz_local
        local_tz=None,  # Default to None, i.e., naive
    ):
        # The user can get here on an empty --ask, e.g.,
        #   ``nark on --ask``
        factoid = factoid or ('',)

        # Keep a flat copy of the args.
        flat = ' '.join(factoid)

        # Items are separated by any one of the separator(s)
        # not preceded by whitespace, and followed by either
        # whitespace, or end of string/before newline.
        if not separators:
            separators = FACT_METADATA_SEPARATORS
        assert len(separators) > 0
        sep_group = '|'.join(separators)
        re_item_sep = re.compile(r'(?<=\S)({})(?=\s|$)'.format(sep_group))

        if not hash_stamps:
            hash_stamps = '#@'

        self.reset()
        self.raw = factoid
        self.flat = flat
        self.rest = factoid
        self.time_hint = time_hint
        self.re_item_sep = re_item_sep
        self.hash_stamps = hash_stamps
        self.lenient = lenient
        self.local_tz = local_tz

    def parse_datetimes_easy(self):
        rest = self.flat
        if self.time_hint == 'verify_start':
            # NOTE: Be nice and look for end, just in case it's there.
            rest = self.parse_datetimes_easy_both(rest, strictly_two=False)
        elif self.time_hint == 'verify_end':
            rest = self.must_parse_datetime_from_rest(rest, 'datetime2')
        elif self.time_hint == 'verify_both':
            rest = self.parse_datetimes_easy_both(rest, strictly_two=True)
        else:
            assert self.time_hint == 'verify_none'
        return rest

    def parse_datetimes_easy_both(self, rest, strictly_two=False):
        rest = self.must_parse_datetime_from_rest(rest, 'datetime1')
        # The next token in rest could be the ' to '/' until ' sep.
        match = Parser.RE_DATE_TO_DATE_SEP.match(rest)
        if match:
            parts = Parser.RE_DATE_TO_DATE_SEP.split(rest, 1)
            assert len(parts) == 3
            assert parts[0].strip() == ''
            assert parts[1].strip() in DATE_TO_DATE_SEPARATORS
            rest = self.must_parse_datetime_from_rest(
                parts[2], 'datetime2', ok_if_missing=strictly_two,
            )
        elif strictly_two:
            self.raise_missing_datetime_two()
        return rest

    def parse_datetimes_hard(self):
        expect_category = True
        if self.time_hint == 'verify_start':
            rest_after_act = self.lstrip_datetimes(expecting=2, strictly_two=False)
        elif self.time_hint == 'verify_end':
            rest_after_act = self.lstrip_datetimes(expecting=1)
        elif self.time_hint == 'verify_both':
            rest_after_act = self.lstrip_datetimes(expecting=2, strictly_two=True)
        elif self.time_hint == 'verify_none':
            # There is no datetime(s). Just the act@cat.
            rest_after_act, expect_category = self.lstrip_activity(self.flat)
        else:
            raise Exception('Parser detected missing or incorrect time_hint.')
        return (rest_after_act, expect_category)

    def lstrip_datetimes(self, expecting, strictly_two=False):
        assert expecting in (1, 2)
        (
            datetimes_and_act, datetimes, rest_after_act,
        ) = self.lstrip_datetimes_delimited()
        if datetimes:
            self.must_parse_datetimes_known(datetimes, expecting, strictly_two)
            # We've processed datetime1, datetime2, and activity_name.
        else:
            # The user did not delimit the datetimes and the activity.
            # See if the user specified anything magically, otherwise, bye.
            self.must_parse_datetimes_magic(datetimes_and_act, expecting, strictly_two)
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
        # followed by whitespace/end-of-string). (Note that ':' can be used
        # as the delimiter -- even though it's used to delimit time -- because
        # the item separator must be the last character of a word.)
        parts = self.re_item_sep.split(datetimes_and_act, 1)
        if len(parts) == 3:
            datetimes = parts[0]
            # Ignore: separator = parts[1]
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

    def must_parse_datetimes_known(self, datetimes, expecting, strictly_two=False):
        assert self.raw_datetime1 is None
        assert self.raw_datetime2 is None

        if expecting == 2:
            # Look for separator, e.g., ' to ', ' until ', etc.
            parts = Parser.RE_DATE_TO_DATE_SEP.split(datetimes, 1)
            if len(parts) > 1:
                assert len(parts) == 3  # middle part is the match
                self.raw_datetime1 = parts[0]  # first datetime
                self.raw_datetime2 = parts[2]  # other datetime
            elif strictly_two:
                self.raise_missing_datetime_two()

        if expecting == 1 or not self.raw_datetime1:
            if self.time_hint == 'verify_start':
                self.raw_datetime1 = datetimes
                self.datetime2 = ''
            else:
                assert self.time_hint == 'verify_end'
                assert not strictly_two
                self.datetime1 = ''
                self.raw_datetime2 = datetimes

    def must_parse_datetimes_magic(
        self,
        datetimes_and_act,
        expecting,
        strictly_two=False,
    ):
        assert self.raw_datetime1 is None  # ??
        assert self.raw_datetime2 is None  # ??

        if expecting == 2:
            # Look for separator, e.g., " to ", or " until ", or " - ", etc.
            parts = Parser.RE_DATE_TO_DATE_SEP.split(datetimes_and_act, 1)
            if len(parts) > 1:
                assert len(parts) == 3
                self.raw_datetime1 = parts[0]
                dt_and_act = parts[2]
                dt_attr = 'datetime2'
            elif strictly_two:
                self.raise_missing_datetime_two()

        if expecting == 1 or not self.raw_datetime1:
            dt_and_act = datetimes_and_act
            if self.time_hint == 'verify_start':
                dt_attr = 'datetime1'
            else:
                assert self.time_hint == 'verify_end'
                dt_attr = 'datetime2'

        rest = self.must_parse_datetime_from_rest(dt_and_act, dt_attr)
        self.activity_name = rest

    def must_parse_datetime_from_rest(
        self, datetime_rest, datetime_attr, ok_if_missing=False,
    ):
        assert datetime_attr in ['datetime1', 'datetime2']
        assert not ok_if_missing or datetime_attr == 'datetime2'
        # See if datetime: 'now', '+/-n' mins, 'nn:nn' clock, or ISO 8601.
        dt, type_dt, rest = HamsterTimeSpec.discern(datetime_rest)
        if dt is not None:
            assert type_dt
            if type_dt == 'datetime':
                dt = self.hydrate_datetime_iso8601(dt, must=True)
            # else, relative time, or clock time; let caller handle.
            setattr(self, datetime_attr, dt)
            setattr(self, 'type_{}'.format(datetime_attr), type_dt)
        elif datetime_attr == 'datetime1':
            self.raise_missing_datetime_one()
        elif not ok_if_missing:
            assert datetime_attr == 'datetime2'
            self.raise_missing_datetime_two()
        else:
            rest = datetime_rest
        return rest

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
        parts = self.re_item_sep.split(cat_and_remainder, 1)
        if len(parts) == 3:
            cat_and_tags = parts[0]
            # Ignore: separator = parts[1]
            self.description = parts[2]
            # Only split on hashtags preceded by a space,
            # because first part is still the category name.
            # (lb): Do not strip(), so that empty category works, e.g.,
            #   `nark on act@ @tag 1: Yee haw!
            #   NOPE: rest = cat_and_tags.strip()
            rest = cat_and_tags
            if Parser.RE_SPLIT_CAT_AND_TAGS.search(rest):
                category, *tags = Parser.RE_SPLIT_CAT_AND_TAGS.split(rest)
                self.consume_tags(tags)
            else:
                category = rest
            self.category_name = category
        else:
            self.skip_tags_no_sep(parts)

    def parse_tags_and_remainder(self, tags_and_remainder):
        parts = self.re_item_sep.split(tags_and_remainder, 1)
        if len(parts) == 3:
            self.description = ''
            tags = Parser.RE_SPLIT_TAGS_AND_TAGS.split(parts[0].strip())
            # If one or more tags were found, first item is empty string.
            if tags[0].strip() != '':
                if len(tags) == 1:
                    self.description += tags[0]
                else:
                    # (lb): I don't think this code path is possible!
                    assert False
            else:
                self.consume_tags(tags)
            # Append separator and second half of split.
            self.description += ''.join(parts[1:])
        else:
            self.skip_tags_no_sep(parts)

    def skip_tags_no_sep(self, parts):
        assert len(parts) == 1
        if Parser.RE_SPLIT_TAGS_AND_TAGS.match(parts[0].strip()):
            # FIXME/2018-05-18 16:50: (lb): Maybe not a warning, but a returned value?
            logger.warning(_(
                'The factoid is missing the metadata-description separator, .'
                'so skipping tags. But it looks like you were trying to tag.'
            ))
            # There's no separator (e.g., comma) after the '@'.
        self.description = parts[0]

    def consume_tags(self, tags):
        tags = [tag.strip() for tag in tags]
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
        if not the_datetime and raw_datetime:
            # Remove any trailing separator that may have been left.
            raw_datetime = self.re_item_sep.sub('', raw_datetime)
            if not the_datetime:
                the_datetime = self.hydrate_datetime_iso8601(
                    raw_datetime, must=False,
                )
            if not the_datetime:
                the_datetime = self.hydrate_datetime_friendly(
                    raw_datetime, must=False,
                )
        return the_datetime

    def hydrate_datetime_iso8601(self, datepart, must=False):
        try:
            # NOTE: Defaults to datetime.timezone.utc.
            #       Uses naive if we set default_timezone=None.
            parsed = iso8601.parse_date(
                datepart,
                default_timezone=self.local_tz,
            )
        except iso8601.iso8601.ParseError:
            parsed = None
            if must:
                raise ParserInvalidDatetimeException(_(
                    'Unable to parse iso8601 datetime: {}.'
                    .format(datepart)
                ))
        return parsed

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
            #                       https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
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
        sep_str = comma_or_join(DATE_TO_DATE_SEPARATORS)
        msg = _(
            'Expected to find the two datetimes separated by one of: {}.'
            .format(sep_str)
        )
        raise ParserMissingDatetimeTwoException(msg)

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
    }
    return fact_dict, err


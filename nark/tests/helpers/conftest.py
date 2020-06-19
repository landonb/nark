# This file exists within 'nark':
#
#   https://github.com/hotoffthehamster/nark
#
# Copyright © 2018-2020 Landon Bouma. All rights reserved.
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

"""Fixtures to help test nark.helpers and related."""

import datetime

factoid_fixture = (
    ('raw_fact', 'time_hint', 'expectation'),
    [
        # Use clock-to-clock format, the date inferred from now; with actegory.
        ('13:00 to 16:30: foo@bar', 'verify_both', {
            'start': datetime.datetime(2015, 12, 25, 13, 0, 0),
            'end': datetime.datetime(2015, 12, 25, 16, 30, 0),
            'activity': 'foo',
            'category': 'bar',
            'tags': [],
        }),
        # Test wrap-around relative clock times specified.
        ('12:00:11 - 11:01:59', 'verify_both', {
            'start': datetime.datetime(2015, 12, 25, 12, 0, 11),
            'end': datetime.datetime(2015, 12, 26, 11, 1, 59),
            'activity': '',
            'category': '',
            'tags': [],
        }),
        # Use datetime-to-datetime format, with actegory.
        ('2015-12-12 13:00 to 2015-12-12 16:30: foo@bar', 'verify_both', {
            'start': datetime.datetime(2015, 12, 12, 13, 0, 0),
            'end': datetime.datetime(2015, 12, 12, 16, 30, 0),
            'activity': 'foo',
            'category': 'bar',
            'tags': [],
        }),
        # The end date is inferred from start date.
        ('2015-12-12 13:00 - 18:00 foo@bar', 'verify_both', {
            'start': datetime.datetime(2015, 12, 12, 13, 0, 0),
            'end': datetime.datetime(2015, 12, 12, 18, 00, 0),
            'activity': 'foo',
            'category': 'bar',
            'tags': [],
        }),
        # actegory spanning day (straddles) midnight) and spanning multiple days.
        ('2015-12-12 13:00 - 2015-12-25 18:00 foo@bar', 'verify_both', {
            'start': datetime.datetime(2015, 12, 12, 13, 0, 0),
            'end': datetime.datetime(2015, 12, 25, 18, 00, 0),
            'activity': 'foo',
            'category': 'bar',
            'tags': [],
        }),
        # Create open/ongoing/un-ended fact.
        ('2015-12-12 13:00 foo@bar', 'verify_start', {
            'start': datetime.datetime(2015, 12, 12, 13, 0, 0),
            'end': None,
            'activity': 'foo',
            'category': 'bar',
            'tags': [],
        }),
        # Create ongoing fact starting at right now.
        ('foo@bar', 'verify_none', {
            'start': datetime.datetime(2015, 12, 25, 18, 0, 0),
            'end': None,
            'activity': 'foo',
            'category': 'bar',
            'tags': [],
        }),
        # Tags.
        (
            '2015-12-12 13:00 foo@bar: #precious #hashish, i like ike',
            'verify_start',
            {
                'start': datetime.datetime(2015, 12, 12, 13, 0, 0),
                'end': None,
                'activity': 'foo',
                'category': 'bar',
                'tags': ['precious', 'hashish'],
                'description': 'i like ike',
            },
        ),
        # Multiple Tags are identified by a clean leading delimiter character.
        (
            '2015-12-12 13:00 foo@bar, #just walk away "#not a tag", blah',
            'verify_start',
            {
                'start': datetime.datetime(2015, 12, 12, 13, 0, 0),
                'end': None,
                'activity': 'foo',
                'category': 'bar',
                'tags': ['just walk away "#not a tag"'],
                'description': 'blah',
            },
        ),
        # Alternative tag delimiter; and quotes are just consumed as part of tag.
        (
            '2015-12-12 13:00 foo@bar, #just walk away @"totes a tag", blah',
            'verify_start',
            {
                'start': datetime.datetime(2015, 12, 12, 13, 0, 0),
                'end': None,
                'activity': 'foo',
                'category': 'bar',
                'tags': ['just walk away', '"totes a tag"'],
                'description': 'blah',
            },
        ),
        # Test '#' in description, elsewhere, after command, etc.
        (
            '2015-12-12 13:00 baz@bat",'
            ' #tag1, #tag2 tags cannot come #too late, aha!'
            ' Time is also ignored at end: 12:59',
            'verify_start',
            {
                'start': datetime.datetime(2015, 12, 12, 13, 0, 0),
                'end': None,
                'activity': 'baz',
                'category': 'bat"',
                'tags': ['tag1'],
                'description': '#tag2 tags cannot come #too late, aha!'
                               ' Time is also ignored at end: 12:59',
            },
        ),
    ],
)


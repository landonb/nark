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

import datetime
from icalendar import Calendar


class TestICALWriter(object):
    """Make sure the iCal writer works as expected."""
    def test_init(self, ical_writer):
        """Make sure that init creates a new calendar instance to add events to."""
        assert ical_writer.calendar

    def test__fact_to_tuple(self, ical_writer, fact):
        """Make sure that our general expection about conversions are matched."""
        result = ical_writer._fact_to_tuple(fact)
        assert result.start == fact.start
        assert result.end == fact.end
        assert result.activity == fact.activity.name
        assert result.duration is None
        assert result.category == fact.category.name
        assert result.description == fact.description

    def test__fact_to_tuple_no_category(self, ical_writer, fact):
        """Make sure that ``None`` category values translate to ``empty strings``."""
        fact.activity.category = None
        result = ical_writer._fact_to_tuple(fact)
        assert result.category == ''

    def test__fact_to_tuple_with_category(self, ical_writer, fact):
        """Make sure that category references translate to their names."""
        result = ical_writer._fact_to_tuple(fact)
        assert result.category == fact.category.name

    def test_write_fact(self, ical_writer, fact, mocker):
        """Make sure that the fact attached to the calendar matches our expectations."""
        fact_tuple = ical_writer._fact_to_tuple(fact)
        mocker.patch.object(ical_writer.calendar, 'add_component')
        ical_writer._write_fact(fact_tuple)
        result = ical_writer.calendar.add_component.call_args[0][0]
        assert result.get('dtstart').dt == fact_tuple.start
        assert result.get('dtend').dt == fact_tuple.end + datetime.timedelta(seconds=1)
        assert result.get('summary') == fact_tuple.activity
        # Make lists of [vText] and [str], else comparison fails.
        #  NO: assert result.get('categories') == fact_tuple.category
        assert list(result.get('categories').cats) == list(fact_tuple.category)
        assert result.get('description') == fact_tuple.description

    def test__close(self, ical_writer, fact, path):
        """Make sure the calendar is actually written do disk before file is closed."""
        ical_writer.write_report((fact,))
        with open(path, 'rb') as fobj:
            result = Calendar.from_ical(fobj.read())
            assert result.walk()


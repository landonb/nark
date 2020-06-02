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

import lazy_import

from . import FactTuple, ReportWriter

__all__ = (
    'ICALWriter',
)

# Profiling: load icalendar: ~ 0.008 secs.
icalendar = lazy_import.lazy_module('icalendar')


class ICALWriter(ReportWriter):
    """A simple ical writer for fact export."""
    def __init__(self, path, datetime_format="%Y-%m-%d %H:%M:%S"):
        """
        Initiate new instance and open an output file like object.

        Args:
            path: File like object to be opend. This is where all output
                will be directed to. datetime_format (str): String specifying
                how datetime information is to be rendered in the output.
        """
        super(ICALWriter, self).__init__(path, datetime_format, output_b=True)
        self.calendar = icalendar.Calendar()

    def _fact_to_tuple(self, fact):
        """
        Convert a ``Fact`` to its normalized tuple.

        This is where all type conversion for ``Fact`` attributes to strings as
            well as any normalization happens.

        Note:
            Because different writers may require different types, we need to
                so this individualy.

        Args:
            fact (nark.Fact): Fact to be converted.

        Returns:
            FactTuple: Tuple representing the original ``Fact``.
        """
        # Fields that allow ``None`` values will be represented by empty ''s.
        # FIXME/DRY/2020-01-16: (lb): This block repeated throughout this file:
        if fact.activity:
            activity = fact.activity.name
        else:
            activity = ''
        if fact.category:
            category = fact.category.name
        else:
            category = ''
        description = fact.description or ''

        return FactTuple(
            start=fact.start,
            end=fact.end,
            duration=None,
            activity=activity,
            category=category,
            description=description,
            deleted=str(fact.deleted),
        )

    def _write_fact(self, fact_tuple):
        """
        Write a singular fact to our report.

        Note:
            * ``dtent`` is non-inclusive according to Page 54 of RFC 5545

        Returns:
            None: If everything worked out alright.
        """
        # [FIXME]
        # It apears that date/time requirements for VEVENT have changed between
        # RFCs. 5545 now seems to require a 'dstamp' and a 'uid'!
        event = icalendar.Event()
        event.add('dtstart', fact_tuple.start)
        event.add('dtend', fact_tuple.end + datetime.timedelta(seconds=1))
        event.add('categories', fact_tuple.category)
        event.add('summary', fact_tuple.activity)
        event.add('description', fact_tuple.description)
        self.calendar.add_component(event)

    def _close(self):
        """Custom close method to make sure the calendar is actually writen do disk."""
        self.file.write(self.calendar.to_ical())
        return super(ICALWriter, self)._close()


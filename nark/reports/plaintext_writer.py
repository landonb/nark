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

from gettext import gettext as _

import csv

from . import FactTuple, ReportWriter

__all__ = (
    'PlaintextWriter',
)


class PlaintextWriter(ReportWriter):
    # HINT: For list of dialects:
    #   >>> import csv
    #   >>> csv.list_dialects()
    #   ['excel-tab', 'excel', 'unix']
    def __init__(
        self,
        path,
        duration_fmt,
        datetime_format="%Y-%m-%d %H:%M:%S",
        output_b=False,
        dialect='excel',
        **fmtparams
    ):
        """
        Initialize a new instance.

        Besides our default behaviour we create a localized heading.
        Also, we need to make sure that our heading is UTF-8 encoded on python 2!
        In that case ``self.file`` will be openend in binary mode and ready to accept
        those encoded headings.
        """
        super(PlaintextWriter, self).__init__(
            path, datetime_format, output_b=output_b,
        )
        self.csv_writer = csv.writer(self.file, dialect=dialect, **fmtparams)
        # SYNC_ME: FactTuple and PlaintextWriter's headers.
        headers = (
            _("start time"),
            _("end time"),
            _("duration minutes"),
            _("activity"),
            _("category"),
            _("description"),
            _("deleted"),
        )
        results = []
        for header in headers:
            results.append(header)
        self.csv_writer.writerow(results)
        self.duration_fmt = duration_fmt

    def _fact_to_tuple(self, fact):
        """
        Convert a ``Fact`` to its normalized tuple.

        This is where all type conversion for ``Fact`` attributes to strings as well
        as any normalization happens.

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

        start = fact.start.strftime(self.datetime_format) if fact.start else ''
        end = fact.end.strftime(self.datetime_format) if fact.end else ''

        return FactTuple(
            start=start,
            end=end,
            duration=fact.format_delta(style=self.duration_fmt),
            activity=activity,
            category=category,
            description=description,
            deleted=str(fact.deleted),
        )

    def _write_fact(self, fact_tuple):
        """
        Write a single fact.

        On python 2 we need to make sure we encode our data accordingly so we
        can feed it to our file object which in this case needs to be opened in
        binary mode.
        """
        results = []
        for value in fact_tuple:
            results.append(value)
        self.csv_writer.writerow(results)


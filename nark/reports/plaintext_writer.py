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

"""Base class for CSVWriter and TSVWriter output formats."""

from gettext import gettext as _

import csv

from . import ReportWriter

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
        datetime_format="%Y-%m-%d %H:%M:%S",
        duration_fmt="%H:%M",
        output_b=False,
        dialect='excel',
        **fmtparams
    ):
        """
        Initialize a new instance.

        Besides our default behaviour we create a localized heading.
        Also, we need to make sure that our heading is UTF-8 encoded on python 2!
        In that case ``self.fileout`` will be openend in binary mode and ready to
        accept those encoded headings.
        """
        super(PlaintextWriter, self).__init__(
            path,
            datetime_format=datetime_format,
            output_b=output_b,
        )
        self.csv_writer = csv.writer(self.fileout, dialect=dialect, **fmtparams)
        results = []
        for header in self._report_headers():
            results.append(header)
        self.csv_writer.writerow(results)

    def _report_headers(self):
        """Export a tuple indicating the report column headers.

        Note that _report_headers and _report_row return matching
        sequences of Fact attributes.
        """
        headers = (
            _("start time"),
            _("end time"),
            _("duration minutes"),
            _("activity"),
            _("category"),
            _("description"),
            _("deleted"),
        )
        return headers

    def _report_row(self):
        """Export a tuple indicating a single report row values.

        Note that _report_headers and _report_row return matching
        sequences of Fact attributes.
        """
        row = (
            fact.start_fmt(self.datetime_format),
            fact.end_fmt(self.datetime_format),
            fact.format_delta(style=self.duration_fmt),
            fact.activity_name,
            fact.category_name,
            fact.description_or_empty,
            str(fact.deleted),
        )
        return row

    def _write_fact(self, fact_tuple):
        """
        Write a single fact.

        On python 2 we need to make sure we encode our data accordingly so we
        can feed it to our file object which in this case needs to be opened in
        binary mode.
        """
        results = []
        for value in self._report_row(fact):
            results.append(value)
        self.csv_writer.writerow(results)


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

import os.path

import pytest

from nark.reports import ReportWriter


class TestReportWriter(object):
    @pytest.mark.parametrize('datetime_format', [None, '%Y-%m-%d'])
    def test_init_stores_datetime_format(self, path, datetime_format):
        """Make sure that Writer initialization stores the ``datetime_format``."""
        writer = ReportWriter(path, datetime_format)
        assert writer.datetime_format == datetime_format

    def test_init_file_opened(self, path):
        """Make sure a file like object is beeing opened."""
        writer = ReportWriter(path)
        assert os.path.isfile(path)
        assert writer.file.closed is False

    def test__fact_to_tuple(self, report_writer, fact):
        with pytest.raises(NotImplementedError):
            report_writer._fact_to_tuple(fact)

    def test_write_report_write_lines(self, mocker, report_writer, list_of_facts):
        """Make sure that each ``Fact`` instances triggers a new line."""
        number_of_facts = 10
        facts = list_of_facts(number_of_facts)
        mocker.patch.object(report_writer, '_write_fact', return_value=None)
        mocker.patch.object(report_writer, '_fact_to_tuple', return_value=None)
        report_writer.write_report(facts)
        assert report_writer._write_fact.call_count == number_of_facts

    def test_write_report_file_closed(self, report_writer, list_of_facts):
        """Make sure our output file is closed at the end."""
        facts = list_of_facts(10)
        with pytest.raises(NotImplementedError):
            report_writer.write_report(facts)
        assert report_writer.file.closed is False

    def test__close(self, report_writer, path):
        """Ensure that the the output gets closed."""
        report_writer._close()
        assert report_writer.file.closed


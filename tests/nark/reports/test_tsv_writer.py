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

import csv


class TestTSVWriter(object):
    def test_init_csv_writer(self, tsv_writer):
        """Make sure that initialition provides us with a ``csv.writer`` instance."""
        assert tsv_writer.csv_writer
        assert tsv_writer.csv_writer.dialect == csv.get_dialect('excel-tab')

    def test_init_heading(self, path, tsv_writer):
        """Make sure that initialition writes header as expected."""

        expectations = (
            'start time',
            'end time',
            'duration minutes',
            'activity',
            'category',
            'description',
            'deleted',
        )

        tsv_writer._close()
        with open(path, 'r') as fobj:
            reader = csv.reader(fobj, dialect='excel-tab')
            header = next(reader)
        for field, expectation in zip(header, expectations):
            if isinstance(field, str):
                assert field == expectation
            else:
                assert field.decode('utf-8') == expectation

    def test__fact_to_tuple_no_category(self, tsv_writer, fact):
        """Make sure that ``None`` category values translate to ``empty strings``."""
        fact.activity.category = None
        result = tsv_writer._fact_to_tuple(fact)
        assert result.category == ''

    def test__fact_to_tuple_with_category(self, tsv_writer, fact):
        """Make sure that category references translate to their names."""
        result = tsv_writer._fact_to_tuple(fact)
        assert result.category == fact.category.name

    def test__write_fact(self, path, fact, tsv_writer):
        """Make sure the writen fact is what we expect."""
        fact_tuple = tsv_writer._fact_to_tuple(fact)
        tsv_writer._write_fact(fact_tuple)
        tsv_writer._close()
        with open(path, 'r') as fobj:
            reader = csv.reader(fobj, dialect='excel-tab')
            next(reader)
            line = next(reader)
            for field, expectation in zip(line, fact_tuple):
                if isinstance(field, str):
                    assert field == expectation
                else:
                    assert field.decode('utf-8') == expectation


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


class TestPlaintextWriter(object):
    def test_init_csv_writer(self, plaintext_writer):
        """Make sure that initialition provides us with a ``csv.writer`` instance."""
        assert plaintext_writer.csv_writer
        assert plaintext_writer.csv_writer.dialect == csv.get_dialect('excel')

    def test_init_heading(self, path, plaintext_writer):
        """Make sure that initialition writes header as expected."""

        expectations = (
            'Start time',
            'End time',
            'Duration',
            'Activity',
            'Category',
            'Description',
            'Deleted',
        )

        plaintext_writer._close()
        with open(path, 'r') as fobj:
            reader = csv.reader(fobj, dialect='excel')
            header = next(reader)
        for field, expectation in zip(header, expectations):
            if isinstance(field, str):
                assert field == expectation
            else:
                assert field.decode('utf-8') == expectation

    def test_fact_as_tuple_no_category(self, plaintext_writer, fact):
        """Make sure that ``None`` category values translate to ``empty strings``."""
        fact.activity.category = None
        result = plaintext_writer.fact_as_tuple(fact)
        cat_idx = plaintext_writer.facts_headers().index(_('Category'))
        assert result[cat_idx] == ''

    def test_fact_as_tuple_with_category(self, plaintext_writer, fact):
        """Make sure that category references translate to their names."""
        result = plaintext_writer.fact_as_tuple(fact)
        cat_idx = plaintext_writer.facts_headers().index(_('Category'))
        assert result[cat_idx] == fact.category.name

    def test__write_fact(self, path, fact, plaintext_writer):
        """Make sure the writen fact is what we expect."""
        fact_tuple = plaintext_writer.fact_as_tuple(fact)
        plaintext_writer._write_fact(fact_tuple)
        plaintext_writer._close()
        with open(path, 'r') as fobj:
            reader = csv.reader(fobj, dialect='excel-tab')
            next(reader)
            line = next(reader)
            for field, expectation in zip(line, fact_tuple):
                if isinstance(field, str):
                    assert field == expectation
                else:
                    assert field.decode('utf-8') == expectation


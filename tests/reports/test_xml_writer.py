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

import xml


class TestXMLWriter(object):
    """Make sure the XML writer works as expected."""

    def test_init_(self, xml_writer):
        """Make sure a XML main document and a facts list child element is set up."""
        assert xml_writer.document
        assert xml_writer.fact_list

    def test_fact_to_tuple(self, xml_writer, fact):
        """Make sure type conversion and normalization matches our expectations."""
        result = xml_writer._fact_to_tuple(fact)
        assert result.start == fact.start.strftime(xml_writer.datetime_format)
        assert result.end == fact.end.strftime(xml_writer.datetime_format)
        assert result.activity == fact.activity.name
        assert result.duration == fact.format_delta(style='%M')
        assert result.category == fact.category.name
        assert result.description == fact.description

    def test__fact_to_tuple_no_category(self, xml_writer, fact):
        """Make sure that ``None`` category values translate to ``empty strings``."""
        fact.activity.category = None
        result = xml_writer._fact_to_tuple(fact)
        assert result.category == ''

    def test_write_fact(self, xml_writer, fact, mocker):
        """Make sure that the attributes attached to the fact matche our expectations."""
        fact_tuple = xml_writer._fact_to_tuple(fact)
        mocker.patch.object(xml_writer.fact_list, 'appendChild')
        xml_writer._write_fact(fact_tuple)
        result = xml_writer.fact_list.appendChild.call_args[0][0]
        assert result.getAttribute('start') == fact_tuple.start
        assert result.getAttribute('end') == fact_tuple.end
        assert result.getAttribute('duration') == fact_tuple.duration
        assert result.getAttribute('activity') == fact_tuple.activity
        assert result.getAttribute('category') == fact_tuple.category
        assert result.getAttribute('description') == fact_tuple.description

    def test__close(self, xml_writer, fact, path):
        """Make sure the calendar is actually written do disk before file is closed."""
        xml_writer.write_report((fact,))
        with open(path, 'rb') as fobj:
            result = xml.dom.minidom.parse(fobj)
            assert result.toxml()


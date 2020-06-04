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

import pytest

from nark.reports import ReportWriter
from nark.reports.ical_writer import ICALWriter
from nark.reports.tsv_writer import TSVWriter
from nark.reports.xml_writer import XMLWriter


@pytest.fixture
def path(tmpdir):
    path = tmpdir.mkdir('reports').join('export.fmt').strpath
    return path


@pytest.fixture
def report_writer(path):
    return ReportWriter(path)


@pytest.fixture
def ical_writer(path):
    return ICALWriter(path)


@pytest.fixture
def tsv_writer(path):
    return TSVWriter(path)


@pytest.fixture
def xml_writer(path):
    return XMLWriter(path)


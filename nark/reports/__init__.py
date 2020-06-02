# This file exists within 'nark':
#
#   https://github.com/hotoffthehamster/nark
#
# Copyright © 2018-2020 Landon Bouma
# Copyright © 2015-2016 Eric Goller
# All rights reserved.
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

"""nark export reporter formatters.

This module defines a base output format class.

- The user will just have to instantiate the output class they desire, and
  then call its write_format() method with a collection of Fact tuples to use.
"""

import sys

from collections import namedtuple

__all__ = (
    'FactTuple',
    'ReportWriter',
)


# SYNC_ME: FactTuple and PlaintextWriter's headers.
FactTuple = namedtuple(
    'FactTuple',
    (
        'start',
        'end',
        'duration',
        'activity',
        'category',
        'description',
        'deleted',
    )
)


class ReportWriter(object):
    def __init__(
        self,
        path,
        datetime_format="%Y-%m-%d %H:%M:%S",
        output_b=False,
    ):
        """
        Initiate new instance and open an output file like object.

        Note:
            If you need added bells and wristels (like heading etc.) this would
            probably the method to extend.

        Args:
            path: File like object to be opened. This is where all output
              will be directed to. datetime_format (str): String specifying how
              datetime information is to be rendered in the output.
        """
        self.datetime_format = datetime_format
        # No matter through what loops we jump, at the end of the day py27
        # ``writerow`` will insist on casting our data to binary str()
        # instances. This clearly conflicts with any generic open() that provides
        # transparent text input/output and would take care of the encoding
        # instead.

        # [FIXME]
        # If it turns out that this is specific to csv handling we may move it
        # there and use a simpler default behaviour for our base method.
        if not path:
            self.file = sys.stdout
        else:
            self.open_file(path, output_b=output_b)

    def open_file(self, path, output_b=False):
        if not output_b:
            self.file = open(path, 'w', encoding='utf-8')
        else:
            self.file = open(path, 'wb')

    def write_report(self, facts):
        """
        Write facts to output file and close the file like object.

        Args:
            facts (Iterable): Iterable of ``nark.Fact`` instances to export.

        Returns:
            None: If everything worked as expected.
        """
        for fact in facts:
            self._write_fact(self._fact_to_tuple(fact))
        self._close()

    def _fact_to_tuple(self, fact):
        """
        Convert a ``Fact`` to its normalized tuple.

        This is where all type conversion for ``Fact`` attributes to strings as well
        as any normalization happens.

        Note:
            Because different writers may require different types, we need to so this
            individualy.

        Args:
            fact (nark.Fact): Fact to be converted.

        Returns:
            FactTuple: Tuple representing the original ``Fact``.
        """
        raise NotImplementedError

    def _write_fact(self, fact):
        """
        Represent one ``Fact`` in the output file.

        What this means exactly depends on the format and kind of output.
        At this point all type conversions and normalization have already been done.

        Args:
            fact (FactTuple): The individual fact to be written.

        Returns:
            None
        """
        raise NotImplementedError

    def _close(self):
        """Default teardown method."""
        if self.file is sys.stdout:
            return
        self.file.close()


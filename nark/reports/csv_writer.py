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

"""CSV writer output format module."""

import csv

from .plaintext_writer import PlaintextWriter

__all__ = (
    'CSVWriter',
)


class CSVWriter(PlaintextWriter):
    def __init__(self, path, datetime_format="%Y-%m-%d %H:%M:%S"):
        super(CSVWriter, self).__init__(
            path,
            # (lb): I figured using 'excel' dialect would be enough,
            #   but scientificsteve/mr_custom does it different... and
            #   I did not test dialect='excel'
            # MAYBE: (lb): Test dialect='excel' without remaining params.
            #   Or not. Depends how much you care about robustness in the
            #   CLI, or if you just want the dob-start command to work
            #   (that's all I'm really doing here! Except the perfectionist
            #   in me also wanted to make all tests work and to see how much
            #   coverage there is -- and I'm impressed! Project Hamster is so
            #   very well covered, it's laudatory!).
            #
            #  dialect='excel',
            #
            # EXPLAIN/2018-05-05: (lb): What did scientificsteve use '%M'
            #   and not '%H:%M'?
            duration_fmt='%M',
            datetime_format=datetime_format,
            # EXPLAIN/2018-05-05: (lb): ',' is also the default delimiter.
            #   How if this different than the default dialect='excel'?
            #   It's probably not....
            delimiter=str(','),
            quoting=csv.QUOTE_MINIMAL,
        )


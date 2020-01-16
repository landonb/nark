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

"""This module provides nark raw fact parsing-related functions."""


__all__ = (
    'comma_or_join',
)


def comma_or_join(seq):
    # Need os.linesep or is \n fine?
    seq = [part.replace('\n', '\\n') for part in seq]
    if len(seq) > 1:
        sep_str = '{} or {}'.format(', '.join(seq[:-1]), seq[-1])
    else:
        sep_str = seq[0]
    return sep_str


def format_value_truncate(val, trunc_width=None):
    if not val:
        return val
    # (lb): First attempt was to only short first line:
    #   vals = val.splitlines()
    #   if len(vals) > 1:
    #       val = vals[0] + '...'
    # but replacing newlines with representation of same
    # is more meaningful, and less confusing to end user.
    val = '\\n'.join(str(val).splitlines())
    if trunc_width is not None:
        if len(val) > trunc_width and trunc_width >= 0:
            val = val[:trunc_width - 3] + '...'
    return val


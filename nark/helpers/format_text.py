# This file exists within 'nark':
#
#   https://github.com/hotoffthehamster/nark
#
# Copyright © 2020 Landon Bouma. All rights reserved.
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

"""Provides string-related functional methods."""

__all__ = (
    'format_value_truncate',
)


# (lb): This function differs from textwrap/ansiwrap.shorten in at least two respects:
# - It truncates regardless of whitespace, i.e., inside words, e.g., "it'll trunca...".
# - It replaces each newline with its escape sequence ("\n"), to provide more context,
#   while also avoiding line breakages.
def format_value_truncate(val, trunc_width=None):
    if not val:
        return val
    val = '\\n'.join(str(val).splitlines())
    if trunc_width is not None:
        if len(val) > trunc_width and trunc_width >= 0:
            val = val[:trunc_width - 3] + '...'
    return val


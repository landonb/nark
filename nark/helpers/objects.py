# -*- coding: utf-8 -*-

# This file is part of 'hamster-lib'.
#
# 'hamster-lib' is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# 'hamster-lib' is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with 'hamster-lib'.  If not, see <http://www.gnu.org/licenses/>.

"""This module provides Hamster raw fact parsing-related functions."""

from __future__ import absolute_import, unicode_literals


__all__ = [
    'resolve_attr_or_method',
]


def resolve_attr_or_method(self, prop):
    self_val = getattr(self, prop)
    if callable(self_val):
        self_val = self_val()
    return self_val


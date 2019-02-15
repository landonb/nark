# -*- coding: utf-8 -*-

# This file is part of 'nark'.
#
# 'nark' is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# 'nark' is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with 'nark'. If not, see <http://www.gnu.org/licenses/>.

"""Base class for Nark item instances."""

from __future__ import absolute_import, unicode_literals

from future.utils import python_2_unicode_compatible

__all__ = ('BaseItem', )


@python_2_unicode_compatible
class BaseItem(object):
    """Base class for all items."""

    def __init__(self, pk, name):
        self.pk = pk
        self.name = name

    def __repr__(self):
        parts = []
        for key in sorted(self.__dict__.keys()):
            parts.append(
                "{key}={val}".format(key=key, val=repr(getattr(self, key)))
            )
        repred = "{cls}({parts})".format(
            cls=self.__class__.__name__, parts=', '.join(parts),
        )
        return repred

    @property
    def unstored(self):
        return (not self.pk) or (self.pk < 0)


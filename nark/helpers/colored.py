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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with 'nark'.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import, unicode_literals

import sys

import colored

__all__ = (
    'disable_colors',
    'enable_colors',
    'coloring',
    'set_coloring',
    'fg',
    'bg',
    'attr',
    'colorize',
    # Private:
    #  'map_color'
)


# (lb): Retrieve pointer to module object instance, so functions can set
# (otherwise function scope creates local variable). (I'll admit this feels a
# little weird, but we need to gait access to a package -- colored -- and it's
# either this; or use a module-level dictionary variable that module function
# can set; or make a Singleton class. Or fork colored and move this there.)
this = sys.modules[__name__]

this.ENABLE_COLORS = True


def disable_colors():
    this.ENABLE_COLORS = False


def enable_colors():
    this.ENABLE_COLORS = True


def coloring():
    return this.ENABLE_COLORS


def set_coloring(new_coloring):
    was_coloring = this.ENABLE_COLORS
    this.ENABLE_COLORS = new_coloring
    return was_coloring


def fg(color):
    if not coloring():
        return ''
    return colored.fg(map_color(color))


def bg(color):
    if not coloring():
        return ''
    return colored.bg(map_color(color))


def attr(color):
    if not coloring():
        return ''
    return colored.attr(map_color(color))


def colorize(text, color, *args):
    if not coloring():
        return text
    more_attrs = ''.join([colored.attr(attr) for attr in args])
    return '{}{}{}{}'.format(
        colored.fg(color), more_attrs, text, colored.attr('reset'),
    )


def map_color(color):
    # FIXME/2018-06-08: (lb): Need a way to easily change palette.
    # Should at least have two profiles, one for black on white; and t'other.
    # Search all uses of fg and bg, and maybe even map attr?
    return color


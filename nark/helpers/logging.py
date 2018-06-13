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

"""This module defines logging related function."""

from __future__ import absolute_import, unicode_literals

import logging
from colored import fg, attr


def formatter_basic(color=False):
    if not color:
        return formatter_basic_plain()
    return formatter_basic_color()


def formatter_basic_plain():
    formatter = logging.Formatter(
        '[%(levelname)s] '
        '%(asctime)s '
        '%(name)s '
        '%(funcName)s: '
        '%(message)s'
    )
    return formatter


def formatter_basic_color():
    formatter = logging.Formatter(
        '{grey_54}[{underlined}{magenta}%(levelname)s{reset}{grey_54}]{reset} '
        '{yellow}%(asctime)s{reset} '
        '{light_blue}%(name)s '
        '%(funcName)s{reset}: '
        '{bold}{green}%(message)s{reset}'.format(
            grey_54=fg('grey_54'),
            underlined=attr('underlined'),
            magenta=fg('magenta'),
            reset=attr('reset'),
            yellow=fg('yellow'),
            light_blue=fg('light_blue'),
            bold=attr('bold'),
            green=fg('green'),
        )
    )
    return formatter


def resolve_log_level(level):
    error = False
    try:
        try:
            log_level = int(level)
        except ValueError:
            log_level = logging.getLevelName(level)
    except KeyError:
        error = True
        log_level = logging.WARNING
    return log_level, error


def setupHandler(handler, formatter, *loggers):
    handler.setFormatter(formatter)
    for logger in loggers:
        logger.addHandler(handler)


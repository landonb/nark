# -*- encoding: utf-8 -*-

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

"""This module defines logging related function."""

from __future__ import absolute_import, unicode_literals

import logging

from colored import fg, bg, attr


def formatter_basic():
    formatter = logging.Formatter(
        '%s%s[%%(levelname)s]%s %s%%(asctime)s%s %s%%(name)s %%(funcName)s%s:  %s%s%%(message)s%s' %
        (
            attr('underlined'), fg('magenta'), attr('reset'),
            fg('yellow'), attr('reset'),
            fg('light_blue'), attr('reset'),
            attr('bold'), fg('green'), attr('reset'),
        )
    )
    return formatter


def setupHandler(handler, formatter, *loggers):
    handler.setFormatter(formatter)
    for logger in loggers:
        logger.addHandler(handler)


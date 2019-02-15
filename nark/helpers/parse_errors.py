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

"""This module provides nark raw fact parsing-related functions."""

from __future__ import absolute_import, unicode_literals

__all__ = (
    'ParserException',
    'ParserMissingDatetimeException',
    'ParserMissingDatetimeOneException',
    'ParserMissingDatetimeTwoException',
    'ParserInvalidDatetimeException',
    'ParserMissingSeparatorActivity',
    'ParserMissingActivityException',
)


class ParserException(Exception):
    """Raised if parser cannot decipher nark factoid string."""
    pass


class ParserMissingDatetimeException(ParserException):  # noqa: E302
    """Raised if the raw_fact is missing one or both datetime tokens."""
    pass


class ParserMissingDatetimeOneException(ParserMissingDatetimeException):  # noqa: E302
    """Raised if the raw_fact is missing its start datetime token(s)."""
    pass


class ParserMissingDatetimeTwoException(ParserMissingDatetimeException):  # noqa: E302
    """Raised if the raw_fact is missing its end datetime token(s)."""
    pass


class ParserInvalidDatetimeException(ParserException):  # noqa: E302
    """Raised if a time from raw_fact in not parseworthy."""
    pass


class ParserMissingSeparatorActivity(ParserException):  # noqa: E302
    """Raised if activity@category separator not found."""
    pass


class ParserMissingActivityException(ParserException):  # noqa: E302
    """Raised if factoid is missing: act@cat, cat@, @cat, or just @."""
    pass


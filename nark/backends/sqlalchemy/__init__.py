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

"""Submodule providing a SQLAlchemy storage backend for ``nark``."""

# Normally, to control lazy-loading, we wouldn't export classes from here,
# but the store is loaded dynamically, so we need to export classes here
# so that the factory generator doesn't have to explicitly import them all.
# (lb): Or something.
#   Search: importlib.import_module
from .storage import SQLAlchemyStore  # noqa: F401


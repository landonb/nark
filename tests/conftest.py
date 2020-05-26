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

"""Base fixtures available to all nark tests."""

import pytest

from nark.control import NarkControl
from nark.manager import BaseStore

from nark.tests import factories
from nark.tests.conftest import *


@pytest.yield_fixture
def controller(base_config):
    """Provide a basic controller."""
    # From hamster-lib: "[TODO] Parametrize over all available stores."
    # (lb): And yet in dob there's still just the one for SQLite.
    controller = NarkControl(base_config)
    yield controller
    controller.store.cleanup()


@pytest.fixture
def basestore(base_config):
    """Provide a generic ``storage.BaseStore`` instance using ``baseconfig``."""
    store = BaseStore(base_config)
    return store


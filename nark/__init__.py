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

"""nark provides generic time tracking functionality."""

import os
import time

__all__ = (
    '__package_name__',
    '__resolve_vers__',
    '__time_0__',
    '__PROFILING__',
)

__PROFILING__ = True
# DEVS: Comment this out to see load times summary.
__PROFILING__ = False
__time_0__ = time.time()

# (lb): Seems a little redundant (see setup.cfg:[metadata]name)
# but not sure if way to get programmatically. This is closest
# solution that avoids hardcoding the library name in strings
# (which is something linter or runtime won't catch if wrong).
__package_name__ = 'nark'


def __resolve_vers__():
    """Returns the installed package version, or '<none>'.

    In lieu of always setting __version__ -- and always loading pkg_resources --
    use a method to avoid incurring startup costs if the version is not needed.
    """
    try:
        import setuptools_scm
        # For whatever reason, relative_to does not work, (lb) thought it would.
        #   return setuptools_scm.get_version(relative_to=__file__)
        pkg_dirname = os.path.dirname(os.path.dirname(__file__))
        # See if parent directory (of this file) contains .git/.
        proj_git = os.path.join(pkg_dirname, '.git')
        if os.path.exists(proj_git):
            # Get version from setuptools_scm, and git tags.
            # This is similar to a developer running, e.g.,
            #   python setup.py --version
            return setuptools_scm.get_version(root=pkg_dirname)
    except ImportError:
        # ModuleNotFoundError added py3.6. Until then, ImportError.
        from pkg_resources import get_distribution, DistributionNotFound
        try:
            return get_distribution(__package_name__).version
        except DistributionNotFound:
            return '<none>'
    else:
        return '<none>'


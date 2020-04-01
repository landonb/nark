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
    'get_version',
    '__package_name__',
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


# MAYBE: (lb): This feels like a package one-off... which is exactly
# what we need, another PyPI package to manage....
def get_version(package_name=None, reference_file=None, include_head=False):
    """Returns the installed package version, or '<none>'.

    In lieu of always setting __version__ -- and always loading pkg_resources --
    use a method to avoid incurring startup costs if the version is not needed.
    """
    def resolve_vers():
        dist_version = version_installed()
        if include_head:
            repo_version = version_from_repo()
            if repo_version:
                dist_version = '{} ({})'.format(dist_version, repo_version)
        return dist_version

    def version_installed():
        # - This returns the version most recently pip-installed. That is, if
        #   you install local sources and have committed code but not run the
        #   pip-install again, this shows the older version.
        from pkg_resources import get_distribution, DistributionNotFound
        try:
            distrib_name = package_name or __package_name__
            return get_distribution(distrib_name).version
        except DistributionNotFound:
            # This would be really weird, no?
            return '<none!?>'

    def version_from_repo():
        try:
            return version_from_tags()
        # Note: ModuleNotFoundError in Py3.6+, so using less specific ImportError.
        except ImportError:
            # No setuptools_scm package installed.
            return ''
        except LookupError:
            # Path containing .git/ not a repo after all.
            return '<none?!>'

    def version_from_tags():
        # Try to get the version from SCM. Obvi, this is intended for devs,
        # as normal users will likely not have setuptools_scm installed.
        import setuptools_scm
        # For whatever reason, relative_to does not work, (lb) thought it would.
        #   return setuptools_scm.get_version(relative_to=__file__)
        # So figure out the root path of the repo. In lieu of something robust,
        # like `git rev-parse --show-toplevel`, look for '.git/' ourselves.
        cur_path = reference_file or __file__
        while cur_path and cur_path != os.path.dirname(cur_path):
            cur_path = os.path.dirname(cur_path)
            proj_git = os.path.join(cur_path, '.git')
            if os.path.exists(proj_git):
                # Get version from setuptools_scm, and git tags.
                # This is similar to a developer running, e.g.,
                #   python setup.py --version
                return setuptools_scm.get_version(root=cur_path)
        # Not .git/ found. Package probably installed to site-packages/.
        return ''

    return resolve_vers()


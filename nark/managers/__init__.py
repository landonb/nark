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

"""
Base classes for implementing storage backends.

Note:
    * This is propably going to be replaced by a ``ABC``-bases solution.
    * Basic sanity checks could be done here then. This would mean we just need
      to test them once and our actual backends focus on the CRUD implementation.
"""

from gettext import gettext as _

import datetime

from ..items.item_base import BaseItem

__all__ = ('BaseManager', )


class BaseManager(object):
    """Base class for all object managers."""

    def __init__(self, store):
        self.store = store

    @property
    def config(self):
        return self.store.config

    # ***

    def adding_item_must_not_have_pk(self, hamster_item):
        message = _("Adding item: {!r}.".format(hamster_item))
        self.store.logger.debug(message)
        if not hamster_item.pk:
            return
        message = _(
            "The {} item ({!r}) cannot be added because it already has a PK."
            " Perhaps call the ``_update`` method instead".format(
                self.__class__.__name__, hamster_item,
            )
        )
        self.store.logger.error(message)
        raise ValueError(message)

    # ***

    def save(self, item, cls=BaseItem, named=False, **kwargs):
        """
        Save a Nark object instance to user's selected backend.

        Will either ``_add`` or ``_update`` based on item PK.

        Args:
            tag (nark.BaseItem, i.e., Activity/Category/Fact/Tag):
                Nark instance to be saved.

        Returns:
            nark.BaseItem: Saved Nark instance.

        Raises:
            TypeError: If the ``item`` parameter is not a valid ``BaseItem`` instance.
        """

        if not isinstance(item, cls):
            message = _("You need to pass a {} object").format(cls.__name__)
            self.store.logger.debug(message)
            raise TypeError(message)

        # (lb): Not sure this is quite what we want, but Activity has been doing this,
        # and I just made this base class, so now all items will be doing this.
        if named and not item.name:
            raise ValueError(_("You must specify an item name."))

        self.store.logger.debug(_("'{}' has been received.".format(item)))

        # NOTE: Not assuming that PK is an int, i.e., not testing '> 0'.
        #       (Also, if pk really 0, this raises ValueError.)
        if item.pk or item.pk == 0:
            result = self._update(item, **kwargs)
        else:
            # PK is empty string, empty list, None, etc., but not 0.
            result = self._add(item, **kwargs)
        return result

    # ***

    def get_all(
        self,
        since=None,
        until=None,
        **kwargs
    ):
        """
        Return all facts within a given timeframe that match given search terms.

        # FIXME/2018-06-11: (lb): Update args help... this is stale:

        Args:
            since (datetime.datetime, optional): Consider only Facts
                starting at or after this date. If a time is not specified,
                "00:00:00" is used; otherwise the time of the object is used.
                Defaults to ``None``.

            until (datetime.datetime, optional): Consider only Facts ending
                before or at this date. If not time is specified, "00:00:00"
                is used. Defaults to ``None``.

            filter_term (str, optional): Only consider ``Facts`` with this
                string as part of their associated ``Activity.name``

            deleted (boolean, optional): False to restrict to non-deleted
                Facts; True to find only those marked deleted; None to find
                all.

            order (string, optional): 'asc' or 'desc'; re: Fact.start.

        Returns:
            list: List of ``Facts`` matching given specifications.

        Raises:
            TypeError: If ``since`` or ``until`` are not ``datetime.date``,
                ``datetime.time`` or ``datetime.datetime`` objects.

            ValueError: If ``until`` is before ``since``.

        Note:
            * This public function only provides some sanity checks and
                normalization. The actual backend query is handled by ``_get_all``.
            * ``search_term`` should be prefixable with ``not`` in order to
                invert matching.
            * This only returns completed facts and does not include the
                active Fact, whether or not it exists.
            * This method will not return facts that start before *and* end
                after (e.g. that span more than) the specified timeframe.
        """
        def _get_all_verify_since_until(since, until, **kwargs):
            self.store.logger.debug(
                _('since: {since} / until: {until}').format(
                    since=since, until=until
                )
            )
            since_dt = _get_all_verify_since(since)
            until_dt = _get_all_verify_until(until)
            if since_dt and until_dt and (until_dt <= since_dt):
                message = _("`until` cannot be earlier than `since`.")
                self.store.logger.debug(message)
                raise ValueError(message)
            return self._get_all(since=since_dt, until=until_dt, **kwargs)

        def _get_all_verify_since(since):
            if since is None:
                return since

            if isinstance(since, datetime.datetime):
                # isinstance(datetime.datetime, datetime.date) returns True,
                # which is why we need to catch this case first.
                since_dt = since
            elif isinstance(since, datetime.date):
                # The user specified a date, but not a time. Assume midnight.
                # MAYBE: Use config['day_start'] and subtract a day minus a minute?
                self.store.logger.debug(
                    _('Using midnight as clock time for `since` date.')
                )
                day_start = self.config['time.day_start']
                since_dt = datetime.datetime.combine(since, day_start)
            elif isinstance(since, datetime.time):
                since_dt = datetime.datetime.combine(datetime.date.today(), since)
            else:
                message = _(
                    'You need to pass either a datetime.date, datetime.time'
                    ' or datetime.datetime object.'
                )
                self.store.logger.debug(message)
                raise TypeError(message)
            return since_dt

        def _get_all_verify_until(until):
            if until is None:
                return until

            if isinstance(until, datetime.datetime):
                # isinstance(datetime.datetime, datetime.date) returns True,
                # which is why we need to except this case first.
                until_dt = until
            elif isinstance(until, datetime.date):
                # MAYBE: (lb): Feels weird that since defaults to midnight,
                #   but until defaults to 'day_start' plus a day...
                #   (need to TESTME to really feel what's going on).
                until_dt = self.day_end_datetime(until)
            elif isinstance(until, datetime.time):
                until_dt = datetime.datetime.combine(datetime.date.today(), until)
            else:
                message = _(
                    'You need to pass either a datetime.date, datetime.time'
                    ' or datetime.datetime object.'
                )
                raise TypeError(message)
            return until_dt

        return _get_all_verify_since_until(since, until, **kwargs)

    # ***


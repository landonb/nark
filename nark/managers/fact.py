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

import datetime

from future.utils import python_2_unicode_compatible

from . import BaseManager
from ..helpers import fact_time
from ..items.fact import Fact


@python_2_unicode_compatible
class BaseFactManager(BaseManager):
    """Base class defining the minimal API for a FactManager implementation."""
    def __init__(self, *args, localize=False, **kwargs):
        super(BaseFactManager, self).__init__(*args, **kwargs)
        # (lb): Setting a class variable makes me feel somewhat dirty. Somewhat.
        Fact.localize(localize)

    # ***

    def save(self, fact, **kwargs):
        """
        Save a Fact to our selected backend.

        Unlike the private ``_add`` and ``_update`` methods, ``save``
        requires that the config given ``fact_min_delta`` is enforced.

        Args:
            fact (nark.Fact): Fact to be saved. Needs to be complete otherwise
            this will fail.

        Returns:
            nark.Fact: Saved Fact.

        Raises:
            ValueError: If ``fact.delta`` is smaller than
              ``self.store.config['fact_min_delta']``
        """
        def _save():
            enforce_fact_min_delta()
            return super(BaseFactManager, self).save(
                fact, cls=Fact, named=False, **kwargs
            )

        def enforce_fact_min_delta():
            # BROKEN/DONT_CARE: (lb): The Facts Carousel does not check the
            # min delta, meaning you could violate fact_min_delta and end up
            # raising from herein. Oh, well, I don't delta, so I don't care.
            if not fact.end:
                # The ongoing fact.
                return

            fact_min_delta = int(self.store.config['fact_min_delta'])
            if not fact_min_delta:
                # User has not enabled min-delta behavior.
                return

            min_delta = datetime.timedelta(seconds=fact_min_delta)
            if fact.delta() >= min_delta:
                # Fact is at least as long as user's min-delta.
                return

            message = _(
                "The Fact duration is shorter than the mandatory value of "
                "{} seconds specified in your config.".format(fact_min_delta)
            )
            self.store.logger.error(message)
            raise ValueError(message)

        return _save()

    # ***

    def _add(self, fact):
        """
        Add a new ``Fact`` to the backend.

        Args:
            fact (nark.Fact): Fact to be added.

        Returns:
            nark.Fact: Added ``Fact``.

        Raises:
            ValueError: If passed fact has a PK. New facts should not have one.
            ValueError: If timewindow is already occupied.
        """
        raise NotImplementedError

    # ***

    def _update(self, fact):
        """
        Update and existing fact with new values.

        Args:
            fact (nark.fact): Fact instance holding updated values.

        Returns:
            nark.fact: Updated Fact

        Raises:
            KeyError: if a Fact with the relevant PK could not be found.
            ValueError: If the the passed activity does not have a PK assigned.
            ValueError: If the timewindow is already occupied.
        """
        raise NotImplementedError

    # ***

    def remove(self, fact, purge=False):
        """
        Remove a given ``Fact`` from the backend.

        Args:
            fact (nark.Fact): ``Fact`` instance to be removed.

        Returns:
            bool: Success status

        Raises:
            ValueError: If fact passed does not have an pk.
            KeyError: If the ``Fact`` specified could not be found in the backend.
        """
        raise NotImplementedError

    # ***

    def get(self, pk, deleted=None):
        """
        Return a Fact by its primary key.

        Args:
            pk (int): Primary key of the ``Fact to be retrieved``.

            deleted (boolean, optional): False to restrict to non-deleted
                Facts; True to find only those marked deleted; None to find
                all.

        Returns:
            nark.Fact: The ``Fact`` corresponding to the primary key.

        Raises:
            KeyError: If primary key not found in the backend.
        """
        raise NotImplementedError

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
            * This does only return proper facts and does not include any
                existing 'ongoing fact'.
            * This method will *NOT* return facts that start before and end
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
                day_start = self.store.config['day_start']
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

    def _get_all(
        self,
        since=None,
        until=None,
        endless=False,
        partial=False,
        include_usage=True,
        count_results=False,
        # QUESTION: (lb): Would a Fact ever be "hidden"?
        #   (Other than what momentaneous toggles.)
        hidden=False,
        deleted=False,
        key=None,
        search_term='',
        activity=False,
        category=False,
        sort_col='',
        sort_order='',
        limit='',
        offset='',
    ):
        """
        Return a list of ``Facts`` matching given criteria.

        Args:
            start_date (datetime.datetime, optional): Consider only Facts
                starting at or after this datetime. Defaults to ``None``.
            end_date (datetime.datetime): Consider only Facts ending before or at
                this datetime. Defaults to ``None``.
            search_term (text_type): Cases insensitive strings to match
                ``Activity.name`` or ``Category.name``.
            deleted (boolean, optional): False to restrict to non-deleted
                Facts; True to find only those marked deleted; None to find
                all.
            partial (bool): If ``False`` only facts which start *and* end
                within the timeframe will be considered.
            order (string, optional): 'asc' or 'desc', 'natch.

        Returns:
            list: List of ``Facts`` matching given specifications.

        Note:
            In contrast to the public ``get_all``, this method actually handles the
            backend query.
        """
        raise NotImplementedError

    # ***

    def get_today(self):
        """
        Return all facts for today, while respecting ``day_start``.

        Returns:
            list: List of ``Fact`` instances.

        Note:
            * This does only return proper facts and does not include any
              existing 'ongoing fact'.
        """
        self.store.logger.debug(_("Returning today's facts"))

        today = self.store.now.date()
        since = datetime.datetime.combine(today, self.store.config['day_start'])
        until = self.day_end_datetime(today)
        return self.get_all(since=since, until=until)

    def day_end_datetime(self, end_date=None):
        if end_date is None:
            end_date = self.store.now.date()
        start_time = self.store.config['day_start']
        return fact_time.day_end_datetime(end_date, start_time)

    # ***

    def stop_current_fact(self, end_hint=None):
        """
        Stop current 'ongoing fact'.

        Args:
            end_hint (datetime.timedelta or datetime.datetime, optional): Hint to be
                considered when setting ``Fact.end``. If no hint is provided
                ``Fact.end`` will be ``datetime.datetime.now()``. If a ``datetime`` is
                provided, this will be used as ``Fact.end`` value. If a ``timedelta``
                is provided it will be added to ``datetime.datetime.now()``.
                If you want the computed ``end`` to be *before* ``now()``
                you can pass negative ``timedelta`` values. Defaults to None.

        Returns:
            nark.Fact: The stored fact.

        Raises:
            TypeError: If ``end_hint`` is not a ``datetime.datetime`` or
                ``datetime.timedelta`` instance or ``None``.
            ValueError: If there is no currently 'ongoing fact' present.
            ValueError: If the final end value (due to the hint) is before
                the fact's start value.
        """
        self.store.logger.debug(_("Stopping 'ongoing fact'."))

        if not (
            (end_hint is None)
            or isinstance(end_hint, datetime.datetime)
            or isinstance(end_hint, datetime.timedelta)
        ):
            raise TypeError(_(
                "The 'end_hint' you passed needs to be either a"
                "'datetime.datetime' or 'datetime.timedelta' instance."
            ))

        if end_hint:
            if isinstance(end_hint, datetime.datetime):
                end = end_hint
            else:
                end = self.store.now + end_hint
        else:
            end = self.store.now

        fact = self.get_current_fact()
        if fact:
            if fact.start > end:
                raise ValueError(_(
                    'Cannot end the Fact before it started.'
                    ' Try editing the Fact instead.'
                ))
            else:
                fact.end = end
            new_fact = self.save(fact)
            self.store.logger.debug(_("Current fact is now history!"))
        else:
            message = _("Trying to stop a non existing ongoing fact.")
            self.store.logger.debug(message)
            raise ValueError(message)
        return new_fact

    # ***

    def get_current_fact(self):
        """
        Provide a way to retrieve any existing 'ongoing fact'.

        Returns:
            nark.Fact: An instance representing our current
                <ongoing fact>.

        Raises:
            KeyError: If no ongoing fact is present.
        """
        def _get_current_fact():
            self.store.logger.debug(_("Looking for the 'ongoing fact'."))
            # 2018-06-09: (lb): Ha! Why did I add endless arg when I had
            # months ago written an endless() method? Because I forgot!!
            #   facts = self.get_all(endless=True)
            facts = self.endless()
            ensure_one_or_fewer_ongoing(facts)
            ensure_one_or_more_ongoing(facts)
            return facts[0]

        def ensure_one_or_fewer_ongoing(facts):
            if len(facts) <= 1:
                return
            msg = '{} IDs: {}'.format(
                _('More than 1 ongoing Fact found. Your database is whacked out!!'),
                ', '.join([str(fact.pk) for fact in facts]),
            )
            self.store.logger.debug(msg)
            raise Exception(msg)

        def ensure_one_or_more_ongoing(facts):
            if facts:
                return
            # See also: NO_ACTIVE_FACT_HELP
            message = _("No ongoing Fact found.")
            self.store.logger.debug(message)
            raise KeyError(message)

        return _get_current_fact()

    # ***

    def cancel_current_fact(self, purge=False):
        """
        Delete the current, ongoing, endless Fact. (Really just mark it deleted.)

        Returns:
            None: If everything worked as expected.

        Raises:
            KeyError: If no ongoing fact is present.
        """
        self.store.logger.debug(_("Cancelling 'ongoing fact'."))

        fact = self.get_current_fact()
        if not fact:
            message = _("Trying to stop a non existing ongoing fact.")
            self.store.logger.debug(message)
            raise KeyError(message)
        self.remove(fact, purge)
        return fact

    # ***

    def starting_at(self, fact):
        """
        Return the fact starting at the moment in time indicated by fact.start.

        Args:
            fact (nark.Fact):
                The Fact to reference, with its ``start`` set.

        Returns:
            nark.Fact: The found Fact, or None if none found.

        Raises:
            IntegrityError: If more than one Fact found at given time.
        """
        raise NotImplementedError

    # ***

    def ending_at(self, fact):
        """
        Return the fact ending at the moment in time indicated by fact.end.

        Args:
            fact (nark.Fact):
                The Fact to reference, with its ``end`` set.

        Returns:
            nark.Fact: The found Fact, or None if none found.

        Raises:
            IntegrityError: If more than one Fact found at given time.
        """
        raise NotImplementedError

    # ***

    def antecedent(self, fact=None, ref_time=None):
        """
        Return the Fact immediately preceding the indicated Fact.

        Args:
            fact (nark.Fact):
                The Fact to reference, with its ``start`` set.

            ref_time (datetime.datetime):
                In lieu of fact, pass the datetime to reference.

        Returns:
            nark.Fact: The antecedent Fact, or None if none found.

        Raises:
            ValueError: If neither ``start`` nor ``end`` is set on fact.
        """
        raise NotImplementedError

    # ***

    def subsequent(self, fact=None, ref_time=None):
        """
        Return the Fact immediately following the indicated Fact.

        Args:
            fact (nark.Fact):
                The Fact to reference, with its ``end`` set.

            ref_time (datetime.datetime):
                In lieu of fact, pass the datetime to reference.

        Returns:
            nark.Fact: The subsequent Fact, or None if none found.

        Raises:
            ValueError: If neither ``start`` nor ``end`` is set on fact.
        """
        raise NotImplementedError

    # ***

    def strictly_during(self, start, end, result_limit=1000):
        """
        Return the fact(s) strictly contained within a start and end time.

        Args:
            start (datetime.datetime):
                Start datetime of facts to find.

            end (datetime.datetime):
                End datetime of facts to find.

            result_limit (int):
                Maximum number of facts to find, else log warning message.

        Returns:
            list: List of ``nark.Facts`` instances.
        """
        raise NotImplementedError

    # ***

    def surrounding(self, fact_time):
        """
        Return the fact(s) at the given moment in time.
        Note that this excludes a fact that starts or ends at this time.
        (See antecedent and subsequent for finding those facts.)

        Args:
            fact_time (datetime.datetime):
                Time of fact(s) to match.

        Returns:
            list: List of ``nark.Facts`` instances.

        Raises:
            IntegrityError: If more than one Fact found at given time.
        """
        raise NotImplementedError

    # ***

    def endless(self):
        """
        Return any facts without a fact.start or fact.end.

        Args:
            <none>

        Returns:
            list: List of ``nark.Facts`` instances.
        """
        raise NotImplementedError


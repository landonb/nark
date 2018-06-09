# -*- coding: utf-8 -*-

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

from __future__ import absolute_import, unicode_literals

import copy
import datetime
import os
import pickle

from future.utils import python_2_unicode_compatible

from . import BaseManager
from ..helpers import helpers
from ..helpers import time as time_helpers
from ..items.fact import Fact


@python_2_unicode_compatible
class BaseFactManager(BaseManager):
    """Base class defining the minimal API for a FactManager implementation."""
    def save(self, fact):
        """
        Save a Fact to our selected backend.

        Unlike the private ``_add`` and ``_update`` methods, ``save``
        requires that the config given ``fact_min_delta`` is enforced.

        Args:
            fact (hamster_lib.Fact): Fact to be saved. Needs to be complete otherwise
            this will fail.

        Returns:
            hamster_lib.Fact: Saved Fact.

        Raises:
            ValueError: If ``fact.delta`` is smaller than
              ``self.store.config['fact_min_delta']``
        """
        self.store.logger.debug(_("Fact: '{}' has been received.".format(fact)))

        fact_min_delta = datetime.timedelta(seconds=int(self.store.config['fact_min_delta']))

        if fact.delta and (fact.delta < fact_min_delta):
            message = _(
                "The passed facts delta is shorter than the mandatory value of {} seconds"
                " specified in your config.".format(fact_min_delta)
            )
            self.store.logger.error(message)
            raise ValueError(message)

        if fact.pk or fact.pk == 0:
            result = self._update(fact)
        elif fact.end is None:
            result = self._start_tmp_fact(fact)
        else:
            result = self._add(fact)
        return result

    def _add(self, fact):
        """
        Add a new ``Fact`` to the backend.

        Args:
            fact (hamster_lib.Fact): Fact to be added.

        Returns:
            hamster_lib.Fact: Added ``Fact``.

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
            fact (hamster_lib.fact): Fact instance holding updated values.

        Returns:
            hamster_lib.fact: Updated Fact

        Raises:
            KeyError: if a Fact with the relevant PK could not be found.
            ValueError: If the the passed activity does not have a PK assigned.
            ValueError: If the timewindow is already occupied.
        """
        raise NotImplementedError

    def remove(self, fact):
        """
        Remove a given ``Fact`` from the backend.

        Args:
            fact (hamster_lib.Fact): ``Fact`` instance to be removed.

        Returns:
            bool: Success status

        Raises:
            ValueError: If fact passed does not have an pk.
            KeyError: If the ``Fact`` specified could not be found in the backend.
        """
        raise NotImplementedError

    def get(self, pk):
        """
        Return a Fact by its primary key.

        Args:
            pk (int): Primary key of the ``Fact to be retrieved``.

            deleted (boolean, optional): False to restrict to non-deleted
                Facts; True to find only those marked deleted; None to find
                all.

        Returns:
            hamster_lib.Fact: The ``Fact`` corresponding to the primary key.

        Raises:
            KeyError: If primary key not found in the backend.
        """
        raise NotImplementedError

    # ***

    def get_all(
        self,
        start=None,
        end=None,
        filter_term='',
        order='desc',
        **kwargs
    ):
        """
        Return all facts within a given timeframe (beginning of start_date
        end of end_date) that match given search terms.

        # FIXME/2018-06-11: (lb): Update args help... this is stale:

        Args:
            start_date (datetime.datetime, optional): Consider only Facts
                starting at or after this date. If a time is not specified,
                "00:00:00" is used; otherwise the time of the object is used.
                Defaults to ``None``.

            end_date (datetime.datetime, optional): Consider only Facts ending
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
            TypeError: If ``start`` or ``end`` are not ``datetime.date``,
                ``datetime.time`` or ``datetime.datetime`` objects.

            ValueError: If ``end`` is before ``start``.

        Note:
            * This public function only provides some sanity checks and normalization. The actual
                backend query is handled by ``_get_all``.
            * ``search_term`` should be prefixable with ``not`` in order to invert matching.
            * This does only return proper facts and does not include any existing 'ongoing fact'.
            * This method will *NOT* return facts that start before and end after
              (e.g. that span more than) the specified timeframe.
        """
        self.store.logger.debug(_(
            "Start: '{start}', end: {end} with filter: {filter} has been received.".format(
                start=start, end=end, filter=filter_term)
        ))

        if start is not None:
            if isinstance(start, datetime.datetime):
                # isinstance(datetime.datetime, datetime.date) returns True,
                # which is why we need to catch this case first.
                pass
            elif isinstance(start, datetime.date):
                start = datetime.datetime.combine(start, self.store.config['day_start'])
            elif isinstance(start, datetime.time):
                start = datetime.datetime.combine(datetime.date.today(), start)
            else:
                message = _(
                    'You need to pass either a datetime.date, datetime.time'
                    ' or datetime.datetime object.'
                )
                self.store.logger.debug(message)
                raise TypeError(message)

        if end is not None:
            if isinstance(end, datetime.datetime):
                # isinstance(datetime.datetime, datetime.date) returns True,
                # which is why we need to except this case first.
                pass
            elif isinstance(end, datetime.date):
                end = time_helpers.end_day_to_datetime(end, self.store.config)
            elif isinstance(end, datetime.time):
                end = datetime.datetime.combine(datetime.date.today(), end)
            else:
                message = _(
                    'You need to pass either a datetime.date, datetime.time'
                    ' or datetime.datetime object.'
                )
                raise TypeError(message)

        if start and end and (end <= start):
            message = _("End value can not be earlier than start!")
            self.store.logger.debug(message)
            raise ValueError(message)

        return self._get_all(
            start, end, filter_term, order=order, limit=limit, offset=offset,
        )

    def _get_all(
        self,
        start=None,
        end=None,
        search_terms='',
        partial=False,
        order='desc',
        **kwargs
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

        today = datetime.date.today()
        return self.get_all(
            datetime.datetime.combine(today, self.store.config['day_start']),
            time_helpers.end_day_to_datetime(today, self.store.config),
        )

    def _start_tmp_fact(self, fact):
        """
        Store new ongoing fact in persistent tmp file

        Args:
            fact (hamster_lib.Fact): Fact to be stored.

        Returns:
            hamster_lib.Fact: Fact stored.

        Raises:
            ValueError: If we already have a ongoing fact running.
            ValueError: If the fact passed does have an end and hence does not
                qualify for an 'ongoing fact'.
        """
        self.store.logger.debug(_("Fact: '{}' has been received.".format(fact)))
        if fact.end:
            message = _("The passed fact has an end specified.")
            self.store.logger.debug(message)
            raise ValueError(message)

        tmp_fact = helpers._load_tmp_fact(self._get_tmp_fact_path())
        if tmp_fact:
            message = _("Trying to start with ongoing fact already present.")
            self.store.logger.debug(message)
            raise ValueError(message)
        else:
            with open(self._get_tmp_fact_path(), 'wb') as fobj:
                pickle.dump(fact, fobj)
            self.store.logger.debug(_("New temporary fact started."))
        return fact

    def update_tmp_fact(self, fact):
        """
        Update an ongoing fact.

        Args:
            fact (hamster_lib.Fact): Fact with new values.

        Returns:
            fact (hamster_lib.Fact): The updated ``Fact`` instance.

        Raises:
            TypeError: If passed fact is not an instance of ``hamster_lib.Fact``.
            ValueError: If passed fact already has an ``end`` value and hence is
                not a valid *ongoing fact*.
        """
        if not isinstance(fact, Fact):
            raise TypeError(_(
                "Passed fact is not a proper instance of 'hamster_lib.Fact'."
            ))

        if fact.end:
            raise ValueError(_(
                "The passed fact seems to have an end and hence is an invalid"
                " 'ongoing fact'."
            ))
        old_fact = self.get_tmp_fact()

        for attribute in ('activity', 'start', 'description', 'tags'):
            value = getattr(fact, attribute)
            setattr(old_fact, attribute, value)

        with open(self._get_tmp_fact_path(), 'wb') as fobj:
            pickle.dump(old_fact, fobj)
        self.store.logger.debug(_("Temporary fact updated."))

        return old_fact

    def stop_tmp_fact(self, end_hint=None):
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
            hamster_lib.Fact: The stored fact.

        Raises:
            TypeError: If ``end_hint`` is not a ``datetime.datetime`` or
                ``datetime.timedelta`` instance or ``None``.
            ValueError: If there is no currently 'ongoing fact' present.
            ValueError: If the final end value (due to the hint) is before
                the fact's start value.
        """
        self.store.logger.debug(_("Stopping 'ongoing fact'."))

        if not ((end_hint is None) or isinstance(end_hint, datetime.datetime) or (
                isinstance(end_hint, datetime.timedelta))):
            raise TypeError(_(
                "The 'end_hint' you passed needs to be either a"
                "'datetime.datetime' or 'datetime.timedelta' instance."
            ))

        if end_hint:
            if isinstance(end_hint, datetime.datetime):
                end = end_hint
            else:
                end = datetime.datetime.now() + end_hint
        else:
            end = datetime.datetime.now()

        fact = helpers._load_tmp_fact(self._get_tmp_fact_path())
        if fact:
            if fact.start > end:
                raise ValueError(_("The indicated 'end' value seem to be before its 'start'."))
            else:
                fact.end = end
            result = self.save(fact)
            os.remove(self._get_tmp_fact_path())
            self.store.logger.debug(_("Temporary fact stopped."))
        else:
            message = _("Trying to stop a non existing ongoing fact.")
            self.store.logger.debug(message)
            raise ValueError(message)
        return result

    def get_tmp_fact(self):
        """
        Provide a way to retrieve any existing 'ongoing fact'.

        Returns:
            hamster_lib.Fact: An instance representing our current
                <ongoing fact>.

        Raises:
            KeyError: If no ongoing fact is present.
        """
        self.store.logger.debug(_("Trying to get 'ongoing fact'."))

        fact = helpers._load_tmp_fact(self._get_tmp_fact_path())
        if not fact:
            message = _("Tried to retrieve an 'ongoing fact' when there is none present.")
            self.store.logger.debug(message)
            raise KeyError(message)
        return fact

    def cancel_tmp_fact(self):
        """
        Delete the current, ongoing, endless Fact. (Really just mark it deleted.)

        Returns:
            None: If everything worked as expected.

        Raises:
            KeyError: If no ongoing fact is present.
        """
        self.store.logger.debug(_("Cancelling 'ongoing fact'."))

        fact = helpers._load_tmp_fact(self._get_tmp_fact_path())
        if not fact:
            message = _("Trying to stop a non existing ongoing fact.")
            self.store.logger.debug(message)
            raise KeyError(message)
        os.remove(self._get_tmp_fact_path())
        self.store.logger.debug(_("Temporary fact stoped."))

    def _get_tmp_fact_path(self):
        """Convenience function to assemble the tmpfile_path from config settings."""
        return self.store.config['tmpfile_path']

    # FIXME/2018-05-12: (lb): insert_forcefully does not respect tmp_fact!
    def insert_forcefully(self, fact):
        """
        Insert the possibly open-ended Fact into the set of logical
        (chronological) Facts, possibly changing the time frames of,
        or removing, other Facts.

        Args:
            fact (hamster_lib.Fact):
                The Fact to insert, with either or both ``start`` and ``end`` set.

        Returns:
            list: List of ``Facts``, ordered by ``start``.

        Raises:
            ValueError: If start or end time is not specified and cannot be
                deduced by other Facts in the system.
        """
        def _insert_forcefully(facts, fact):
            # Steps:
            #   Find fact overlapping start.
            #   Find fact overlapping end.
            #   Find facts wholly contained between start and end.
            #   Return unique set of facts indicating edits and deletions.

            conflicts = []
            conflicts += find_conflict(facts, fact, 'start')
            conflicts += find_conflict(facts, fact, 'end')
            if fact.start and fact.end:
                conflicts += facts.strictly_during(fact.start, fact.end)
            resolve_overlapping(fact, conflicts)
            return conflicts

        def find_conflict(facts, fact, ref_time):
            conflicts = []
            find_edge = False
            fact_time = getattr(fact, ref_time)
            if fact_time:  # fact.start or fact.end
                conflicts = facts.surrounding(fact_time)
                conflicts = [(fact, copy.deepcopy(fact)) for fact in conflicts]
                if not conflicts:
                    find_edge = True
            else:
                find_edge = True
            if find_edge:
                conflicts = inspect_time_boundary(facts, fact, ref_time)
            return conflicts

        def inspect_time_boundary(facts, fact, ref_time):
            conflict = None
            if ref_time == 'start':
                if fact.start is None:
                    set_start_per_antecedent(facts, fact)
                else:
                    conflict = facts.starting_at(fact)
            else:
                assert ref_time == 'end'
                if fact.end is None:
                    set_end_per_subsequent(facts, fact)
                else:
                    conflict = facts.ending_at(fact)
            conflicts = [(conflict, copy.deepcopy(conflict))] if conflict else []
            return conflicts

        # FIXME/2018-05-12: (lb): insert_forcefully does not respect tmp_fact!
        #   if 'hamster-to', and tmp fact, then start now, and end tmp_fact.
        #   if 'hamster-from', and tmp fact, then either close tmp at now,
        #     or at from time, or complain (add to conflicts) if overlapped.
        def set_start_per_antecedent(facts, fact):
            assert fact.start is None
            # Find a Fact with start < fact.end.
            ref_fact = facts.antecedent(fact)
            if not ref_fact:
                raise ValueError(_(
                    'Please specify `start` for fact being added before time existed.'
                ))
            # Because we called surrounding and got nothing,
            # we know that found_fact.end < fact.end,
            # so we can set fact.start accordingly.
            assert ref_fact.end < fact.end
            fact.start = ref_fact.end

        def set_end_per_subsequent(facts, fact):
            assert fact.end is None
            ref_fact = facts.subsequent(fact)
            if not ref_fact:
                # FIXME/MAYBE: (lb): Probably want to set to 'now' automatically?
                raise ValueError(_(
                    'Please specify `end` for fact being added after time existed.'
                ))
            assert ref_fact.start > fact.start
            fact.end = ref_fact.start

        def resolve_overlapping(fact, conflicts):
            seen = set()
            resolved = []
            for conflict, original in conflicts:
                assert conflict.pk > 0
                if conflict.pk in seen:
                    next
                seen.add(conflict.pk)
                resolved += resolve_fact_conflict(fact, conflict)
            return resolved

        def resolve_fact_conflict(fact, conflict):
            resolved = []
            if fact.start <= conflict.start:
                resolve_fact_starts_before(fact, conflict, resolved)
            elif fact.end >= conflict.end:
                resolve_fact_ends_after(fact, conflict, resolved)
            else:
                # The new fact is contained *within* the conflict!
                resolve_fact_is_inside(fact, conflict, resolved)
            return resolved

        def resolve_fact_starts_before(fact, conflict, resolved):
            if fact.end >= conflict.end:
                conflict.deleted = True
                conflict.dirty_reasons.add('deleted')
            else:
                assert conflict.start < fact.end
                conflict.start = fact.end
                conflict.dirty_reasons.add('start')
            resolved.append(conflict)

        def resolve_fact_ends_after(fact, conflict, resolved):
            assert fact.start < conflict.end
            conflict.end = fact.start
            conflict.dirty_reasons.add('end')
            resolved.append(conflict)

        def resolve_fact_is_inside(fact, conflict, resolved):
            resolve_fact_split_prior(fact, conflict, resolved)
            resolve_fact_split_after(fact, conflict, resolved)

        def resolve_fact_split_prior(fact, conflict, resolved):
            lconflict = copy.deepcopy(conflict)
            lconflict.end = fact.start
            lconflict.dirty_reasons.add('end')
            resolved.append(lconflict)

        def resolve_fact_split_after(fact, conflict, resolved):
            rconflict = copy.deepcopy(conflict)
            rconflict.start = fact.end
            rconflict.dirty_reasons.add('start')
            resolved.append(rconflict)

        # The actual insert_forcefully function.

        return _insert_forcefully(self, fact)

    def starting_at(self, fact):
        """
        Return the fact starting at the moment in time indicated by fact.start.

        Args:
            fact (hamster_lib.Fact):
                The Fact to reference, with its ``start`` set.

        Returns:
            hamster_lib.Fact: The found Fact, or None if none found.

        Raises:
            IntegrityError: If more than one Fact found at given time.
        """
        raise NotImplementedError

    # ***

    def ending_at(self, fact):
        """
        Return the fact ending at the moment in time indicated by fact.end.

        Args:
            fact (hamster_lib.Fact):
                The Fact to reference, with its ``end`` set.

        Returns:
            hamster_lib.Fact: The found Fact, or None if none found.

        Raises:
            IntegrityError: If more than one Fact found at given time.
        """
        raise NotImplementedError

    def antecedent(self, fact):
        """
        Return the Fact immediately preceding the indicated Fact.

        Args:
            fact (hamster_lib.Fact):
                The Fact to reference, with its ``start`` set.

        Returns:
            hamster_lib.Fact: The antecedent Fact, or None if none found.

        Raises:
            ValueError: If neither ``start`` nor ``end`` is set on fact.
        """
        raise NotImplementedError

    def subsequent(self, fact):
        """
        Return the Fact immediately following the indicated Fact.

        Args:
            fact (hamster_lib.Fact):
                The Fact to reference, with its ``end`` set.

        Returns:
            hamster_lib.Fact: The subsequent Fact, or None if none found.

        Raises:
            ValueError: If neither ``start`` nor ``end`` is set on fact.
        """
        raise NotImplementedError

    # ***

    def strictly_during(self, start, end, result_limit=10):
        """
        Return the fact(s) strictly contained within a start and end time.

        Args:
            start (datetime.datetime):
                Start datetime of facts to find.

            end (datetime.datetime):
                End datetime of facts to find.

            result_limit (int):
                Maximum number of facts to find, else raise OverflowError.

        Returns:
            list: List of ``hamster_lib.Facts`` instances.
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
            list: List of ``hamster_lib.Facts`` instances.

        Raises:
            IntegrityError: If more than one Fact found at given time.
        """
        raise NotImplementedError


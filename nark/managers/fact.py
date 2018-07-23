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
from future.utils import python_2_unicode_compatible

import copy
import datetime

from . import BaseManager
from ..helpers import time as time_helpers
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
                self.store.logger.debug(_('Using midnight as since date clock time!'))
                day_start = '00:00:00'
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
                until_dt = time_helpers.end_day_to_datetime(until, self.store.config)
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

        today = datetime.date.today()
        start = datetime.datetime.combine(today, self.store.config['day_start'])
        end = time_helpers.end_day_to_datetime(today, self.store.config)
        return self.get_all(start=start, end=end)

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

    def insert_forcefully(self, fact, squash_sep=''):
        """
        Insert the possibly open-ended Fact into the set of logical
        (chronological) Facts, possibly changing the time frames of,
        or removing, other Facts.

        Args:
            fact (nark.Fact):
                The Fact to insert, with either or both ``start`` and ``end`` set.

        Returns:
            list: List of edited ``Facts``, ordered by ``start``.

        Raises:
            ValueError: If start or end time is not specified and cannot be
                deduced by other Facts in the system.
        """
        allow_momentaneous = self.store.config['allow_momentaneous']

        def _insert_forcefully(facts, fact):
            # Steps:
            #   Find fact overlapping start.
            #   Find fact overlapping end.
            #   Find facts wholly contained between start and end.
            #   Return unique set of facts indicating edits and deletions.

            conflicts = []
            conflicts += find_conflict_at_edge(facts, fact, 'start')
            conflicts += find_conflict_at_edge(facts, fact, 'end')
            conflicts += find_conflicts_during(facts, fact)

            edited_conflicts = resolve_overlapping(fact, conflicts)

            return edited_conflicts

        # ***

        def find_conflict_at_edge(facts, fact, ref_time):
            conflicts = []
            find_edge = False
            fact_time = getattr(fact, ref_time)
            if fact_time:  # fact.start or fact.end
                conflicts = facts.surrounding(fact_time)
                if conflicts:
                    if len(conflicts) != 1:
                        self.store.logger.warning(_(
                            "Found more than one Fact ({} total) at: '{}'"
                            .format(len(conflicts), fact_time))
                        )
                else:
                    find_edge = True
            else:
                find_edge = True
            if find_edge:
                assert not conflicts
                conflicts = inspect_time_boundary(facts, fact, ref_time)
            return conflicts

        def inspect_time_boundary(facts, fact, ref_time):
            conflict = None
            if ref_time == 'start':
                if fact.start is None:
                    conflict = set_start_per_antecedent(facts, fact)
                else:
                    conflict = facts.starting_at(fact)
            else:
                assert ref_time == 'end'
                if fact.end is None:
                    set_end_per_subsequent(facts, fact)
                else:
                    conflict = facts.ending_at(fact)
            conflicts = [conflict] if conflict else []
            return conflicts

        # FIXME/2018-05-12: (lb): insert_forcefully does not respect tmp_fact!
        #   if 'dob-to', and tmp fact, then start now, and end tmp_fact.
        #   if 'dob-from', and tmp fact, then either close tmp at now,
        #     or at from time, or complain (add to conflicts) if overlapped.
        def set_start_per_antecedent(facts, fact):
            assert fact.start is None
            # Find a Fact with start < fact.end.
            ref_fact = facts.antecedent(fact)
            if not ref_fact:
                raise ValueError(_(
                    'Please specify `start` for fact being added before time existed.'
                ))
            # Because we called surrounding and got nothing, we know that
            # found_fact.end < fact.end; or that found_fact.end is None,
            # a/k/a, the ongoing Fact.
            conflict = None
            if ref_fact.end is not None:
                assert ref_fact.end < fact.end
                fact.start = ref_fact.end
            else:
                # There's an ongoing Fact, and the new Fact has no start, which
                # indicates that these two facts should be squashed. (We'll create
                # an intermediate conflict now, and we'll squash the Facts later,
                # so that we include the ongoing Fact in the list of edited Facts
                # we return later.)
                assert ref_fact.start < fact.end
                conflict = ref_fact
            return conflict

        def set_end_per_subsequent(facts, fact):
            assert fact.end is None
            ref_fact = facts.subsequent(fact)
            if ref_fact:
                assert ref_fact.start > fact.start
                fact.end = ref_fact.start
            else:
                # This is ongoing fact/current.
                self.store.logger.debug(_("No end specified for Fact; assuming now."))
                fact.end = self.store.now
                # NOTE: for dob-on, we'll start start, then end will be
                #       a few micros later... but the caller knows to unset
                #       this Fact's end later (see: leave_open).
                #       (lb): I wrote this code and I can't quite remember
                #       why we fact to do this. I think so comparing against
                #       other Facts works....

        # ***

        def find_conflicts_during(facts, fact):
            conflicts = []
            if fact.start and fact.end:
                found_facts = facts.strictly_during(fact.start, fact.end)
                conflicts += found_facts
            return conflicts

        def resolve_overlapping(fact, conflicts):
            seen = set()
            resolved = []
            for conflict in conflicts:
                assert conflict.pk > 0
                if fact.pk == conflict.pk:
                    # Editing existing Fact may find itself in db.
                    continue
                if conflict.pk in seen:
                    continue
                seen.add(conflict.pk)
                original = conflict.copy()
                edited_conflicts = resolve_fact_conflict(fact, conflict)
                for edited in edited_conflicts:
                    resolved.append((edited, original,))
            return resolved

        def resolve_fact_conflict(fact, conflict):
            # If the conflict is contained within another Fact, that
            # other Fact will be split in twain, so we may end up
            # with more conflicts.
            resolved = []
            if fact.start is None and conflict.end is None:
                resolve_fact_squash_fact(fact, conflict, resolved)
            elif fact.start <= conflict.start:
                resolve_fact_starts_before(fact, conflict, resolved)
            elif conflict.end is None or fact.end >= conflict.end:
                resolve_fact_ends_after(fact, conflict, resolved)
            else:
                # The new fact is contained *within* the conflict!
                resolve_fact_is_inside(fact, conflict, resolved)
            return cull_duplicates(resolved)

        def resolve_fact_squash_fact(fact, conflict, resolved):
            conflict.dirty_reasons.add('stopped')
            conflict.dirty_reasons.add('end')
            conflict.dirty_reasons.add('squash')
            conflict.squash(fact, squash_sep)
            resolved.append(conflict)

        def resolve_fact_starts_before(fact, conflict, resolved):
            if fact.end <= conflict.start:
                # Disparate facts.
                return
            elif conflict.end and fact.end >= conflict.end:
                if (
                    allow_momentaneous
                    and (fact.start == conflict.start)
                    and (conflict.start == conflict.end)
                ):
                    # (lb): 0-length Fact is not surrounded by new Fact.
                    #   As they say in Futurama, I'm going to allow this.
                    return
                conflict.deleted = True
                conflict.dirty_reasons.add('deleted-starts_before')
            else:
                # This is either the last Fact in the database, which is still
                # open (if conflict.end is None); or fact ends before conflict
                # ends. And in either case, fact ends after conflict starts,
                # so move conflict's start to no longer conflict.
                assert conflict.start < fact.end
                conflict.start = fact.end
                conflict.dirty_reasons.add('start')
            resolved.append(conflict)

        def resolve_fact_ends_after(fact, conflict, resolved):
            if conflict.end is not None and fact.start >= conflict.end:
                # Disparate facts.
                return
            elif fact.start <= conflict.start:
                if (
                    allow_momentaneous
                    and (fact.end == conflict.end)
                    and (conflict.start == conflict.end)
                ):
                    # 0-length Fact is not surrounded by new Fact; I'll allow it.
                    return
                conflict.deleted = True
                conflict.dirty_reasons.add('deleted-ends_after')
            else:
                # (lb): Here's where we might stop an ongoing fact
                # when adding a new fact.
                assert conflict.end is None or conflict.end > fact.start
                # A little hack: signal the caller if this is/was ongoing fact.
                if conflict.end is None:
                    conflict.dirty_reasons.add('stopped')
                conflict.end = fact.start
                conflict.dirty_reasons.add('end')
            resolved.append(conflict)

        def resolve_fact_is_inside(fact, conflict, resolved):
            resolve_fact_split_prior(fact, conflict, resolved)
            resolve_fact_split_after(fact, conflict, resolved)

        def resolve_fact_split_prior(fact, conflict, resolved):
            # Make a copy of the conflict, to not affect resolve_fact_split_after.
            lconflict = copy.deepcopy(conflict)
            lconflict.split_from = conflict.pk
            # Leave lconflict.pk set so the old fact is marked deleted.
            lconflict.end = fact.start
            lconflict.dirty_reasons.add('lsplit')
            resolved.append(lconflict)

        def resolve_fact_split_after(fact, conflict, resolved):
            rconflict = copy.deepcopy(conflict)
            rconflict.split_from = conflict.pk
            rconflict.pk = None
            rconflict.start = fact.end
            rconflict.dirty_reasons.add('rsplit')
            resolved.append(rconflict)

        def cull_duplicates(resolved):
            seen = set()
            culled = []
            for conflict in resolved:
                if conflict in seen:
                    continue
                seen.add(conflict)
                culled.append(conflict)
            return culled

        # The actual insert_forcefully function.

        return _insert_forcefully(self, fact)

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


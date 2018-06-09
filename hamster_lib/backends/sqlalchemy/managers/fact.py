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

from __future__ import unicode_literals

from builtins import str

from future.utils import python_2_unicode_compatible
from sqlalchemy import asc, desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql.expression import and_, or_

from . import query_apply_limit_offset
from ..objects import AlchemyActivity, AlchemyCategory, AlchemyFact
from ....managers.fact import BaseFactManager


@python_2_unicode_compatible
class FactManager(BaseFactManager):
    def _timeframe_available_for_fact(self, fact):
        """
        Determine if a timeframe given by the passed fact is already occupied.

        This method takes also such facts into account that start before and end
        after the fact in question. In that regard it exceeds what ``_get_all``
        would return.

        Args:
            fact (Fact): The fact to check. Please note that the fact is expected to
                have a ``start`` and ``end``.

        Returns:
            bool: ``True`` if the timeframe is available, ``False`` if not.

        Note:
            If the given fact is the only fact instance within the given timeframe
            the timeframe is considered available (for this fact)!
        """
        start, end = fact.start, fact.end
        query = self.store.session.query(AlchemyFact)

        condition = and_(AlchemyFact.start < end, AlchemyFact.end > start)

        if fact.pk:
            condition = and_(condition, AlchemyFact.pk != fact.pk)

        query = query.filter(condition)

        return not bool(query.count())

    def _add(self, fact, raw=False):
        """
        Add a new fact to the database.

        Args:
            fact (hamster_lib.Fact): Fact to be added.
            raw (bool): If ``True`` return ``AlchemyFact`` instead.

        Returns:
            hamster_lib.Fact: Fact as stored in the database

        Raises:
            ValueError: If the passed fact has a PK assigned.
                New facts should not have one.

            ValueError: If the timewindow is already occupied.
        """

        self.store.logger.debug(_("Received '{!r}', 'raw'={}.".format(fact, raw)))

        if fact.pk:
            message = _(
                "The fact ('{!r}') you are trying to add already has an PK."
                " Are you sure you do not want to ``_update`` instead?".format(fact)
            )
            self.store.logger.error(message)
            raise ValueError(message)

        if not self._timeframe_available_for_fact(fact):
            message = _("Our database already contains facts for this facts timewindow."
                        "There can ever only be one fact at any given point in time")
            self.store.logger.error(message)
            raise ValueError(message)

        alchemy_fact = AlchemyFact(None, None, fact.start, fact.end, fact.description)
        alchemy_fact.activity = self.store.activities.get_or_create(fact.activity, raw=True)
        alchemy_fact.tags = [self.store.tags.get_or_create(tag, raw=True) for tag in fact.tags]
        self.store.session.add(alchemy_fact)
        self.store.session.commit()
        self.store.logger.debug(_("Added {!r}.".format(alchemy_fact)))
        return alchemy_fact

    # ***

    def _update(self, fact, raw=False):
        """
        Update and existing fact with new values.

        Args:
            fact (hamster_lib.fact): Fact instance holding updated values.

            raw (bool): If ``True`` return ``AlchemyFact`` instead.
              ANSWER: (lb): "instead" of what? raw is not used by Fact...

        Returns:
            hamster_lib.fact: Updated Fact

        Raises:
            KeyError: if a Fact with the relevant PK could not be found.
            ValueError: If the the passed activity does not have a PK assigned.
            ValueError: If the timewindow is already occupied.
        """

        self.store.logger.debug(_("Received '{!r}', 'raw'={}.".format(fact, raw)))

        if not fact.pk:
            message = _(
                "{!r} does not seem to have a PK. We don't know"
                "which entry to modify.".format(fact)
            )
            self.store.logger.error(message)
            raise ValueError(message)

        # Check for valid time range.
        if fact.start >= fact.end:
            message = _(
                'Invalid time range of {!r}.'
                ' The start is large or equal than the end.'.format(fact)
            )
            self.store.logger.error(message)
            raise ValueError(message)

        if not self._timeframe_available_for_fact(fact):
            message = _("Our database already contains facts for this facts timewindow."
                        " There can ever only be one fact at any given point in time")
            self.store.logger.error(message)
            raise ValueError(message)

        alchemy_fact = self.store.session.query(AlchemyFact).get(fact.pk)
        if not alchemy_fact:
            message = _("No fact with PK: {} was found.".format(fact.pk))
            self.store.logger.error(message)
            raise KeyError(message)

        alchemy_fact.start = fact.start
        alchemy_fact.end = fact.end
        alchemy_fact.description = fact.description
        alchemy_fact.activity = self.store.activities.get_or_create(fact.activity, raw=True)
        tags = [self.store.tags.get_or_create(tag, raw=True) for tag in fact.tags]
        alchemy_fact.tags = tags
        self.store.session.commit()
        self.store.logger.debug(_("{!r} has been updated.".format(fact)))
        return fact

    def remove(self, fact):
        """
        Remove a fact from our internal backend.

        Args:
            fact (hamster_lib.Fact): Fact to be removed

        Returns:
            bool: Success status

        Raises:
            ValueError: If fact passed does not have an pk.

            KeyError: If no fact with passed PK was found.
        """

        self.store.logger.debug(_("Received '{!r}'.".format(fact)))

        if not fact.pk:
            message = _(
                "The fact passed ('{!r}') does not seem to havea PK. We don't know"
                "which entry to remove.".format(fact)
            )
            self.store.logger.error(message)
            raise ValueError(message)

        alchemy_fact = self.store.session.query(AlchemyFact).get(fact.pk)
        if not alchemy_fact:
            message = _('No fact with given pk was found!')
            self.store.logger.error(message)
            raise KeyError(message)
        self.store.session.delete(alchemy_fact)
        self.store.session.commit()
        self.store.logger.debug(_('{!r} has been removed.'.format(fact)))
        return True

    def get(self, pk, raw=False):
        """
        Retrieve a fact based on its PK.

        Args:
            pk: PK of the fact to be retrieved

        Returns:
            hamster_lib.Fact: Fact matching given PK

        Raises:
            KeyError: If no Fact of given key was found.
        """

        self.store.logger.debug(_("Received PK: {}', 'raw'={}.".format(pk, raw)))

        result = self.store.session.query(AlchemyFact).get(pk)
        if not result:
            message = _("No fact with given PK found.")
            self.store.logger.error(message)
            raise KeyError(message)
        if not raw:
            # Explain: Why is as_hamster optionable, when act/cat/tag do it always?
            result = result.as_hamster(self.store)
        self.store.logger.debug(_("Returning {!r}.".format(result)))
        return result

    # ***

    def _get_all(
        self,
        start=None,
        end=None,
        search_term='',
        partial=False,
        order='desc',
        **kwargs
    ):
        """
        Return all facts within a given timeframe that match given search terms.

        ``get_all`` already took care of any normalization required.

        If no timeframe is given, return all facts.

        Args:
            start (datetime.datetime, optional):
                Start of timeframe.
            end (datetime.datetime, optional):
                End of timeframe.
            search_term (text_type):
                Case-insensitive strings to match ``Activity.name`` or
                ``Category.name``.
            partial (bool):
                If ``False`` only facts which start *and* end within the
                timeframe will be considered. If ``False`` facts with
                either ``start``, ``end`` or both within the timeframe
                will be returned.

        Returns:
            list: List of ``hamster_lib.Facts`` instances.

        Note:
            This method will *NOT* return facts that start before and end after
            (e.g. that span more than) the specified timeframe.
        """

        def get_complete_overlaps(query, start, end):
            """Return all facts with start and end within the timeframe."""
            if start:
                query = query.filter(AlchemyFact.start >= start)
            if end:
                query = query.filter(AlchemyFact.end <= end)
            return query

        # NOTE: (lb): Nothing calls get_partial_overlaps except tests.
        def get_partial_overlaps(query, start, end):
            """Return all facts where either start or end falls within the timeframe."""
            if start and not end:
                # (lb): Checking AlchemyFact.end >= start is sorta redundant,
                # because AlchemyFact.start >= start should guarantee that.
                query = query.filter(
                    or_(AlchemyFact.start >= start, AlchemyFact.end >= start),
                )
            elif not start and end:
                # (lb): Checking AlchemyFact.start <= end is sorta redundant,
                # because AlchemyFact.end <= end should guarantee that.
                query = query.filter(
                    or_(AlchemyFact.start <= end, AlchemyFact.end <= end),
                )
            elif start and end:
                query = query.filter(or_(
                    and_(AlchemyFact.start >= start, AlchemyFact.start <= end),
                    and_(AlchemyFact.end >= start, AlchemyFact.end <= end),
                ))
            else:
                pass
            return query

        def filter_search_term(query, term):
            """
            Limit query to facts that match the search terms.

            Terms are matched against ``Category.name`` and ``Activity.name``.
            The matching is not case-sensitive.
            """
            query = query.join(AlchemyActivity).join(AlchemyCategory).filter(
                or_(AlchemyActivity.name.ilike('%{}%'.format(search_term)),
                    AlchemyCategory.name.ilike('%{}%'.format(search_term))
                    )
            )
            return query

        self.store.logger.debug(_(
            "Received start: '{}', end: '{}' and search_term='{}'.".format(
                start, end, search_term)
        ))

        # [FIXME] Figure out against what to match search_terms
        query = self.store.session.query(AlchemyFact)

        if partial:
            query = get_partial_overlaps(query, start, end)
        else:
            query = get_complete_overlaps(query, start, end)

        if search_term:
            query = filter_search_term(query, search_term)

        if order == 'desc':
            query = query.order_by(desc(AlchemyFact.start))
        elif order == 'asc':
            query = query.order_by(asc(AlchemyFact.start))
        query = query_apply_limit_offset(query, **kwargs)

        self.store.logger.debug(_('query: {}'.format(str(query))))
        return [fact.as_hamster(self.store) for fact in query.all()]

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
        query = self.store.session.query(AlchemyFact)

        if fact.start is None:
            raise ValueError('No `start` for starting_at(fact).')

        condition = and_(AlchemyFact.start == fact.start)

        if fact.pk:
            condition = and_(condition, AlchemyFact.pk != fact.pk)

        query = query.filter(condition)

        self.store.logger.debug(_('fact: {} / query: {}'.format(fact, str(query))))

        n_facts = query.count()
        if n_facts > 1:
            message = 'More than one fact found starting at "{}": {} facts found'.format(
                fact.start, n_facts
            )
            raise IntegrityError(message)

        found = query.one_or_none()
        found_fact = found.as_hamster(self.store) if found else None
        return found_fact

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
        query = self.store.session.query(AlchemyFact)

        if fact.end is None:
            raise ValueError('No `end` for ending_at(fact).')

        condition = and_(AlchemyFact.end == fact.end)

        if fact.pk:
            condition = and_(condition, AlchemyFact.pk != fact.pk)

        query = query.filter(condition)

        self.store.logger.debug(_('fact: {} / query: {}'.format(fact, str(query))))

        n_facts = query.count()
        if n_facts > 1:
            message = 'More than one fact found ending at "{}": {} facts found'.format(
                fact.end, n_facts
            )
            raise IntegrityError(message)

        found = query.one_or_none()
        found_fact = found.as_hamster(self.store) if found else None
        return found_fact

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
        query = self.store.session.query(AlchemyFact)

        ref_time = fact.start
        if ref_time is None:
            ref_time = fact.end
        if ref_time is None:
            raise ValueError('No `start` or `end` for antecedent(fact).')

        condition = and_(AlchemyFact.start < ref_time)

        if fact.pk:
            condition = and_(condition, AlchemyFact.pk != fact.pk)

        query = query.filter(condition).order_by(desc(AlchemyFact.start)).limit(1)

        self.store.logger.debug(_('fact: {} / query: {}'.format(fact, str(query))))

        found = query.one_or_none()
        found_fact = found.as_hamster(self.store) if found else None
        return found_fact

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
        query = self.store.session.query(AlchemyFact)

        ref_time = fact.end
        if ref_time is None:
            ref_time = fact.start
        if ref_time is None:
            raise ValueError(_('No `start` or `end` for subsequent(fact).'))

        condition = and_(AlchemyFact.end > ref_time)

        if fact.pk:
            condition = and_(condition, AlchemyFact.pk != fact.pk)

        query = query.filter(condition).order_by(asc(AlchemyFact.end)).limit(1)

        self.store.logger.debug(_('fact: {} / query: {}'.format(fact, str(query))))

        found = query.one_or_none()
        found_fact = found.as_hamster(self.store) if found else None
        return found_fact

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
                Maximum number of facts to find, else raise OverflowError.

        Returns:
            list: List of ``hamster_lib.Facts`` instances.
        """
        query = self.store.session.query(AlchemyFact)

        query = query.filter(
            and_(AlchemyFact.start >= start, AlchemyFact.end <= end),
        )

        self.store.logger.debug(_(
            'start: {} / end: {} / query: {}'
            .format(start, end, str(query))
        ))

        # LATER: (lb): We'll let the client ask for as many records as they
        # want. But we might want to offer ways to deal more gracefully with
        # it, like via pagination; or a fetch_one callback, so that only item
        # gets loaded in memory at a time, rather than everything. For now, we
        # can at least warn, I suppose.
        during_count = query.count()
        if during_count > result_limit:
            message = (_(
                'This is your alert that lots of Facts were found between '
                'the two dates specified: found {}.'
                .factor(during_count)
            ))
            self.store.logger.warning(message)

        facts = query.all()
        found_facts = [fact.as_hamster(self.store) for fact in facts]
        return found_facts

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
        query = self.store.session.query(AlchemyFact)

        query = query.filter(
            and_(AlchemyFact.start < fact_time, AlchemyFact.end > fact_time),
        )

        self.store.logger.debug(_(
            'fact_time: {} / query: {}'.format(
                fact_time, str(query)
            )
        ))

        n_facts = query.count()
        if n_facts > 1:
            message = 'Broken time frame found at "{}": {} facts found'.format(
                fact_time, n_facts
            )
            raise IntegrityError(message)

        facts = query.all()
        found_facts = [fact.as_hamster(self.store) for fact in facts]
        return found_facts


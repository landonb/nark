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

"""XML writer output format module."""

from . import FactTuple, ReportWriter

__all__ = (
    'XMLWriter',
)


class XMLWriter(ReportWriter):
    """Writer for a basic xml export."""
    # (lb): @elbenfreund noted that XMLWriter copied from 'legacy hamster':
    #   Authored by tstriker <https://github.com/tstriker>. Docstrings by elbenfreund.
    #   https://github.com/projecthamster/hamster/blame/66ed9270c6f0070a4548aca9f070517cc13c85ae
    #       /src/hamster/reports.py#L159
    #   (Other than this class, the nark code authors are either:
    #    landonb (2018-2020); or elbenfreund (2015-2017).)

    def __init__(self, path, datetime_format="%Y-%m-%d %H:%M:%S"):
        """Setup the writer including a main xml document."""
        super(XMLWriter, self).__init__(path, datetime_format, output_b=True)
        # Profiling: load Document: ~ 0.004 secs.
        from xml.dom.minidom import Document
        self.document = Document()
        self.fact_list = self.document.createElement("facts")

    def _fact_to_tuple(self, fact):
        """
        Convert a ``Fact`` to its normalized tuple.

        This is where all type conversion for ``Fact`` attributes to strings as
        well as any normalization happens.

        Note:
            Because different writers may require different types, we need to
            do this individually.

        Args:
            fact (nark.Fact): Fact to be converted.

        Returns:
            FactTuple: Tuple representing the original ``Fact``.
        """
        # Fields that allow ``None`` values will be represented by empty ''s.
        # FIXME/DRY/2020-01-16: (lb): This block repeated throughout this file:
        if fact.activity:
            activity = fact.activity.name
        else:
            activity = ''
        if fact.category:
            category = fact.category.name
        else:
            category = ''
        description = fact.description or ''

        return FactTuple(
            start=fact.start.strftime(self.datetime_format),
            end=fact.end.strftime(self.datetime_format),
            duration=fact.format_delta(style='%M'),
            activity=activity,
            category=category,
            description=description,
            deleted=str(fact.deleted),
        )

    def _write_fact(self, fact_tuple):
        """
        Create new fact element and populate attributes.

        Once the child is prepared append it to ``fact_list``.
        """
        fact = self.document.createElement("fact")

        # MAYBE/2018-04-22: (lb): Should this be start, or start_time? end, or end_time?
        fact.setAttribute('start', fact_tuple.start)
        fact.setAttribute('end', fact_tuple.end)
        fact.setAttribute('activity', fact_tuple.activity)
        fact.setAttribute('duration', fact_tuple.duration)
        fact.setAttribute('category', fact_tuple.category)
        fact.setAttribute('description', fact_tuple.description)
        self.fact_list.appendChild(fact)

    def _close(self):
        """
        Append the xml fact list to the main document write file and cleanup.

        ``toxml`` should take care of encoding everything with UTF-8.
        """

        self.document.appendChild(self.fact_list)
        self.file.write(self.document.toxml(encoding='utf-8'))
        return super(XMLWriter, self)._close()


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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with 'nark'. If not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import, unicode_literals
from future.utils import python_2_unicode_compatible

from six import text_type

from ..helpers.colored import attr, fg
from ..helpers.objects import resolve_attr_or_method
from ..helpers.strings import format_value_truncate

__all__ = [
    'FactsDiff',
]


@python_2_unicode_compatible
class FactsDiff(object):
    """"""
    def __init__(self, orig_fact, edit_fact, formatted=False):
        self.orig_fact = orig_fact
        self.edit_fact = edit_fact
        self.formatted = formatted
        self.exclude_attrs = None

    # ***

    def friendly_diff(
        self,
        truncate=False,
        exclude=None,
        show_elapsed=False,
        show_midpoint=False,
    ):
        def _friendly_diff():
            self.exclude_attrs = exclude

            if not self.formatted:
                result = ''
            else:
                result = []

            result += self.diff_values_format('interval', None, self.time_humanize())
            if show_midpoint:
                result += self.diff_values_format('midpoint', None, self.time_midpoint())
            if show_elapsed:
                self_val, other_val = self.diff_time_elapsed()
                result += self.diff_values_format('duration', self_val, other_val)
            result += self.diff_attrs('start', 'start_fmt_local')
            result += self.diff_attrs('end', 'end_fmt_local')
            if (not truncate) or self.orig_fact.pk or self.edit_fact.pk:
                result += self.diff_attrs('id', 'pk', beautify=self.beautify_pk)
            result += self.diff_attrs('deleted', 'deleted')
            # MAYBE?: (lb): Would we even want to show the split_from fact?
            #  result += self.diff_attrs('split_from', 'split_from')
            result += self.diff_attrs('activity', 'activity_name')
            result += self.diff_attrs('category', 'category_name')
            if not self.formatted:
                result += self.diff_attrs('tags', 'tagnames_underlined')
            else:
                # (lb): Ug... this 'formatted' business is crazy.
                result += self.diff_attrs('tags', 'tagnames_underlined_f')
            result += self.diff_attrs('description', 'description', truncate=truncate)

            self.exclude_attrs = None

            if not self.formatted:
                result = result.rstrip()
            return result

        # ***

        return _friendly_diff()

    # ***

    def diff_attrs(self, name, prop, truncate=False, beautify=None):
        if (self.exclude_attrs is not None) and (name in self.exclude_attrs):
            return ''
        self_val = resolve_attr_or_method(self.orig_fact, prop)
        other_val = ''
        if self.edit_fact is not None:
            other_val = resolve_attr_or_method(self.edit_fact, prop)
            if callable(other_val):
                other_val = other_val()
            self_val, other_val = self.diff_values_enhance(
                self_val, other_val, truncate=truncate, beautify=beautify,
            )
        elif truncate:
            self_val = format_value_truncate(self_val)
            self_val = self.format_prepare(self_val)
            other_val = self.format_prepare(other_val)
        attr_diff = self.diff_values_format(name, self_val, other_val)
        return attr_diff

    def diff_values_enhance(
        self, self_val, other_val, truncate=False, beautify=None,
    ):
        differ = False
        if self_val != other_val:
            differ = True
        if truncate:
            self_val = format_value_truncate(self_val)
            other_val = format_value_truncate(other_val)
        if beautify is not None:
            self_val, other_val = beautify(self_val, other_val)
            if self_val != other_val:
                differ = True
        if differ:
            self_val = self.format_edited_before(self_val)
            self_val, other_val = self.format_edited_after(self_val, other_val)
        else:
            self_val = self.format_prepare(self_val)
            other_val = self.format_prepare('')
        return (self_val, other_val)

    def format_prepare(self, some_val):
        if not self.formatted or not isinstance(some_val, text_type):
            return some_val
        return [('', some_val)]

    # ***

    def diff_time_elapsed(self):
        self_val = self.time_elapsed(self.orig_fact)
        other_val = self.time_elapsed(self.edit_fact)
        if not self_val:
            # Make 'em the same, i.e., show no diff, no styling.
            self_val = other_val
        return self.diff_values_enhance(self_val, other_val)

    def time_elapsed(self, fact):
        # NOTE: start and/or end might be string; e.g., clock or rel. time.
        if not fact.times_ok:
            return None
        time_val = fact.get_string_delta('HHhMMm', localize=True)
        return time_val

    def time_midpoint(self):
        return self.format_prepare(self.edit_fact.time_of_day_midpoint())

    def time_humanize(self):
        return self.format_prepare(self.edit_fact.time_of_day_humanize())

    def beautify_pk(self, self_val, other_val):
        if (
            'split' in self.edit_fact.dirty_reasons
            or 'split' in self.orig_fact.dirty_reasons
        ):
            pass
        if 'lsplit' in self.edit_fact.dirty_reasons:
            other_val = 'New split fact, created before new fact'
        if 'rsplit' in self.edit_fact.dirty_reasons:
            other_val = 'New split fact, created after new fact'
        return (self_val, other_val)

    # ***

    def format_edited_before(self, before_val):
        if not self.formatted:
            return '{}{}{}'.format(
                fg('spring_green_3a'),
                before_val,
                attr('reset'),
            )
        spring_green_3a = '00AF5F'
        style = 'fg:#{}'.format(spring_green_3a)
        before_parts = []
        if isinstance(before_val, text_type):
            before_parts += [(style, before_val)]
        elif before_val is not None:
            for tup in before_val:
                before_parts.append((style, tup[1]))
        return before_parts

    def format_edited_after(self, self_val, other_val):
        if not self.formatted:
            return '{}{}{}{}{} | was: '.format(
                attr('bold'),
                attr('underlined'),
                fg('light_salmon_3b'),
                other_val,
                attr('reset'),
                # (lb): What, colored has no italic option?
            ), self_val
        light_salmon_3b = 'D7875F'
        style = 'fg:#{} bold underline'.format(light_salmon_3b)
        after_parts = []
        if isinstance(other_val, text_type):
            after_parts += [(style, other_val)]
        elif other_val is not None:
            for tup in other_val:
                after_parts.append((style, tup[1]))
        # (lb): Swap the order, for display purposes.
        #   (These formatting functions are so janky!)
        if self_val and self_val[0][1]:
            after_parts += [('italic', ' | was: ')]
        return after_parts, self_val

    # ***

    def diff_values_format(self, name, self_val, other_val):
        prefix = '  '
        left_col = '{}{:.<19} : '.format(prefix, name)
        if not self.formatted:
            return '{}{}{}\n'.format(
                left_col, self_val or '', other_val or '',
            )
        left_col = ('', left_col)
        newline = ('', '\n')
        format_tuples = [left_col]
        if self_val:
            format_tuples += self_val
        if other_val:
            format_tuples += other_val
        format_tuples += [newline]
        return format_tuples


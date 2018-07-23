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

    # ***

    def friendly_diff(
        self,
        other,
        truncate=False,
        exclude=None,
        formatted=False,
        show_elapsed=False,
        show_midpoint=False,
    ):
        def _friendly_diff():
            if not formatted:
                result = ''
            else:
                result = []

            result += diff_values_format('interval', None, time_humanize())
            if show_midpoint:
                result += diff_values_format('midpoint', None, time_midpoint())
            if show_elapsed:
                self_val, other_val = diff_elapsed()
                result += diff_values_format('duration', self_val, other_val)
            result += diff_other('start', 'start_fmt_local')
            result += diff_other('end', 'end_fmt_local')
            if (not truncate) or self.pk or other.pk:
                result += diff_other('id', 'pk', beautify=beautify_pk)
            result += diff_other('deleted', 'deleted')
            # MAYBE?: (lb): Would we even want to show the split_from fact?
            #  result += diff_other('split_from', 'split_from')
            result += diff_other('activity', 'activity_name')
            result += diff_other('category', 'category_name')
            if not formatted:
                result += diff_other('tags', 'tagnames_underlined')
            else:
                # (lb): Ug... this 'formatted' business is crazy.
                result += diff_other('tags', 'tagnames_underlined_f')
            result += diff_other('description', 'description', truncate=truncate)

            if not formatted:
                result = result.rstrip()
            return result

        def diff_elapsed():
            self_val = time_elapsed(self)
            other_val = time_elapsed(other)
            if not self_val:
                # Make 'em the same, i.e., show no diff, no styling.
                self_val = other_val
            return diff_values_enhance(self_val, other_val)

        def time_elapsed(fact):
            # NOTE: start and/or end might be string; e.g., clock or rel. time.
            if not fact.times_ok:
                return None
            time_val = fact.get_string_delta('HHhMMm', localize=True)
            return time_val

        def time_midpoint():
            return format_prepare(other.time_of_day_midpoint())

        def time_humanize():
            return format_prepare(other.time_of_day_humanize())

        def beautify_pk(self_val, other_val):
            if (
                'split' in other.dirty_reasons
                or 'split' in self.dirty_reasons
            ):
                pass
            if 'lsplit' in other.dirty_reasons:
                other_val = 'New split fact, created before new fact'
            if 'rsplit' in other.dirty_reasons:
                other_val = 'New split fact, created after new fact'
            return (self_val, other_val)

        def diff_other(name, prop, truncate=False, beautify=None):
            if exclude is not None and name in exclude:
                return ''
            self_val = resolve_attr_or_method(self, prop)
            other_val = ''
            if other is not None:
                other_val = resolve_attr_or_method(other, prop)
                if callable(other_val):
                    other_val = other_val()
                self_val, other_val = diff_values_enhance(
                    self_val, other_val, truncate=truncate, beautify=beautify,
                )
            elif truncate:
                self_val = format_value_truncate(self_val)
                self_val = format_prepare(self_val)
                other_val = format_prepare(other_val)
            attr_diff = diff_values_format(name, self_val, other_val)
            return attr_diff

        def diff_values_enhance(
            self_val, other_val, truncate=False, beautify=None,
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
                self_val = format_edited_before(self_val)
                self_val, other_val = format_edited_after(self_val, other_val)
            else:
                self_val = format_prepare(self_val)
                other_val = format_prepare('')
            return (self_val, other_val)

        def format_prepare(some_val):
            if not formatted or not isinstance(some_val, text_type):
                return some_val
            return [('', some_val)]

        def format_edited_before(before_val):
            if not formatted:
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

        def format_edited_after(self_val, other_val):
            if not formatted:
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

        def diff_values_format(name, self_val, other_val):
            prefix = '  '
            left_col = '{}{:.<19} : '.format(prefix, name)
            if not formatted:
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

        return _friendly_diff()


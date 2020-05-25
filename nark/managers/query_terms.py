# This file exists within 'nark':
#
#   https://github.com/hotoffthehamster/nark
#
# Copyright © 2018-2020 Landon Bouma. All rights reserved.
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

"""Query class module."""


class QueryTerms(object):
    """
    The QueryTerms encapsulate all the input and output parameters of an item lookup.

    This class is a standalone class so that it's easy for frontends to use, too.
    """

    def __init__(self, **kwargs):
        self.setup_terms(**kwargs)

    def setup_terms(
        self,
        # - If specified, look for an Activity with this PK.
        key=None,
        # - If True, include count of Facts that use this Activity, as
        #   well as the cumulative duration (end - start) of those Facts.
        include_usage=False,
        # - If True, return only a count of query matches (an integer).
        #   Otherwise, the method returns a list of result rows.
        count_results=False,
        # - Use since and/or until to find Activities used by Facts from a
        #   specific time range.
        since=None,
        until=None,
        # - Use endless and partial to further influence the time range query.
        endless=False,
        partial=False,
        # FIXME/2020-05-19: (lb): What's the status of the 'deleted' feature?
        # - There's code wired to 'delete' an Activity, but what does that mean?
        # - Really, the user should be able to 'orphan' an Activity (by removing
        #   it from all Facts), but if an Activity is still being used by Facts,
        #   what would delete do? Would we want to remove the Activity from all
        #   the Facts it's applied to?
        #   - I think an 'orphaned' option makes sense here. And maybe a feature
        #     to "rename" an Activity, or really to assign a different Activity
        #     to some collection of Facts. Then maybe 'delete' is okay, i.e.,
        #     once a Activity is orphaned, then it can be deleted.
        #   - In the meantime, the user can hide Activities from the CLI front
        #     end using the ignore feature, which omits matching Activities
        #     from the auto-complete and suggestion widgets.
        # In any case, this 'deleted' option is still wired in the CLI, so
        # maintaining support here. For now.
        deleted=False,
        # - Specify one or_ more search terms to match against the Activity name.
        #   - Note that if more than one term is supplied, they're ORed together,
        #     so an Activity only has to match one term.
        #   - Note also that the search is loose: It ignores case and will match
        #     in the middle of the Activity name.
        search_term=None,
        # - Specify an Activity object to restrict to that specific Activity.
        #   Note that the CLI does not expose this option.
        activity=False,
        # - Specify a name or Category object to restrict to that specific Category.
        #   - Note that this match is strict -- case and exactness count.
        category=False,
        match_activities=[],
        match_categories=[],
        # - MEH: (lb): For parity, could add a 'tags' option to restrict the
        #   search to Activities used on Facts with specific 'tags', but how
        #   complicated and useless does that sound.
        # - (lb): I added grouping support to FactManager.get_all via the options:
        #     group_activity
        #     group_category
        #     group_tags
        #   We could add them to this query, but it'd make it much more complex,
        #   and you'd get essentially the same results as using Fact.get_all (save
        #   for any Activities that are not applied to any Facts, but we can live
        #   with that gap in support). (tl;dr, use `dob list fact` or `dob usage fact`
        #   to group query results, and use the --column option if you want to tweak
        #   the output report columns, e.g., to match this method's output.)
        # - The user can specify one or more columns on which to sort,
        #   and an 'asc' or 'desc' modifier for each column under sort.
        sort_cols=[],
        sort_orders=[],
        # - The user can request a subset of results.
        limit=None,
        offset=None,
        # - The user can request raw SQLAlchemy results (where each result
        #   has a leading AlchemyActivity object, and then the 'uses' and
        #   'span' columns; and the result object has object attributes,
        #   e.g., result.uses, result.span); or the user can expect tuple
        #   results (with a proper Activity object as the first item in
        #   the tuple, and the extra columns following). Note that when
        #   raw=False, it is up to the caller to know the tuple layout.
        raw=False,
    ):
        """
        Args:
            include_usage (int, optional): If true, include count of Facts that reference
                each Activity.
            search_term (list of str, optional): Limit activities to those matching a
                substring in their name. Defaults to None/disabled.
            activity (nark.Activity, optional): Limit activities to this activity.
                Defaults to ``False``. If ``activity=None`` only activities with a
                matching name will be considered.
            category (nark.Category or str, optional): Limit activities to this
                category. Defaults to ``False``. If ``category=None`` only activities
                without a category will be considered.
            sort_cols (list of str, optional): Which column(s) to sort by. Defaults to
                'activity'. Choices: 'activity, 'category', 'start', 'usage'.
                Note that 'start' and 'usage' only apply if include_usage.
            sort_orders (list of str, optional): Each element one of:
                'asc': Whether to search the results in ascending order.
                'desc': Whether to search the results in descending order.
            limit (int, optional): Query "limit".
            offset (int, optional): Query "offset".
        """
        self.key = key
        self.include_usage = include_usage
        self.count_results = count_results
        self.since = since
        self.until = until
        self.endless = endless
        self.partial = partial
        self.deleted = deleted
        self.search_term = search_term
        self.activity = activity
        self.category = category
        self.match_activities = match_activities
        self.match_categories = match_categories
        self.sort_cols = sort_cols
        self.sort_orders = sort_orders
        self.limit = limit
        self.offset = offset
        self.raw = raw


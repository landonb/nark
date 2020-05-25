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

        key=None,

        include_usage=False,

        count_results=False,

        since=None,
        until=None,
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
        search_term=None,

        # Note that item name matching is strict -- case and exactness count.
        activity=False,
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

        sort_cols=[],
        sort_orders=[],

        limit=None,
        offset=None,

        raw=False,
    ):
        """
        Configures query parameters for item.get_all() and item.get_all_by_usage().

        Some of the settings affect the query, and some affect the returned results.

        Each of the query parameters is optional. Defaults are such that each
        argument default is falsey: it's either False, None, or an empty list.

        Args:
            key: If specified, look for an item with this PK. See also the get()
                method, if you do not need aggregate results.

            include_usage: If True, computes additional details for each item or set
                of grouped items, and returns a list of tuples (with the item or
                aggregated item as the first element). Otherwise, if False, returns
                a list of matching items only. For Attribute, Category, and Tag
                queries, enable include_usage to receive a count of Facts that use
                the item, as well as the cumulative duration (end - start) of those
                Facts. For Facts, includes additional aggregate details.

            count_results: If True, return only a count of query matches (an integer).
                By default, count_results is False, and the method returns a list of
                results (of either items or tuples, depending on include_usage).

            since: Restrict Facts to those that start at or after this time.
            until: Restrict Facts to those that end at or before this time.
            endless: If True, include the active Fact, if any, in the query.
            partial: If True, restrict Facts to those that start or end within the
                since-to-until time window.
            deleted: If True, include items marked 'deleted'.
            search_term (None, or str list): Use to restrict to items whose name
                matches any on the specified search terms. Each comparison is case
                insensitive, and the match can occur in the middle of a string. If
                an item name matches one or more of the search terms, if any, it
                will be included in the results.
                * Use ``not`` before a search term to exclude its matches from the
                  results.

            activity (nark.Activity, str, or False; optional): Matches only the
                Activity or the Facts assigned the Activity with this exact name.
                The activity name can be specified as a string, or by passing a
                ``nark.Activity`` object whose name will be used. Defaults to
                ``False``. To match Facts without an Activity assigned, set
                ``activity=None``.
            category (nark.Category, str, or False; optional): Matches only the
                Category or the Activities assigned the Category with this exact
                name. The category name can be specified as a string, or by
                passing a ``nark.Caetgory`` object whose name will be used.
                Defaults to ``False``. To match Activities without a Category
                assigned, set ``category=None``.
            match_activities: Use to specify more than one exact Activity name
                to match. Activities that exactly match any of the specified
                names will be included.
            match_categories: Use to specify more than one exact Category name
                to match. Categories that exactly match any of the specified
                names will be included.

            sort_cols (str list, optional): Which column(s) to sort by.
                - If not aggregating results, defaults to 'name' and orders
                  by item name.
                - When aggregating results (include_usage=True) or searching
                  Facts, defaults to 'start', and orders results by Fact start.
                - Choices include: 'start', 'time', 'day', 'name', 'activity,
                  'category', 'tag', 'usage', and 'fact'.
                - Note that 'start' and 'usage' only apply if include_usage,
                  and 'day' is only valid when group_days is True.
            sort_orders (str list, optional): Specifies the direction of each
                sort specified by sort_cols. Use the string 'asc' or 'desc'
                in the corresponding index of sort_orders that you want applied
                to the corresponding entry in soft_cols. If there is no
                corresponding entry in sort_orders for a specific sort_cols
                entry, that sort column is ordered in ascending order.

            limit (int, optional): Query "limit".
            offset (int, optional): Query "offset".

            raw: If True, returns 'raw' SQLAlchemy items (e.g., AlchemyFact).
                If False, returns first-class nark objects (e.g., Fact).
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


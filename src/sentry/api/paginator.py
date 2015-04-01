"""
sentry.api.paginator
~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2014 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import

import math

from datetime import datetime
from django.db import connections
from django.utils import timezone

from sentry.utils.cursors import build_cursor, Cursor

quote_name = connections['default'].ops.quote_name


class Paginator(object):
    """
    The paginator takes a given queryset, with a fixed order, and will generate
    appropriate cursors as well as take the correct slices.

    Our example queryset's key clause (what is passed in order_by), looks like
    the following:

      [0, 0, 1, 2, 3, 4]

    Note the duplicate keys, as much of this code exists specifically to handle
    those.

    When going from left to right queryset's are simply "where KEY >= VALUE",
    but when we need to go right to left things get more complicated.

    If there is no offset available, the query logic is simply the inverse of
    the other queryset but exclusive: "where KEY < VALUE".

    When an offset is set (> 0) we need to perform two queries, the first is the
    same without the offset, and the second is "where KEY >= VALUE limit OFFSET".
    """
    def __init__(self, queryset, order_by):
        if order_by.startswith('-'):
            self.key, self.desc = order_by[1:], True
        else:
            self.key, self.desc = order_by, False
        self.queryset = queryset

    def _get_item_key(self, item):
        value = getattr(item, self.key)
        if self.desc:
            return math.ceil(value)
        return math.floor(value)

    def _value_from_cursor(self, cursor):
        return cursor.value

    def _get_results_from_qs(self, value, is_prev):
        results = self.queryset

        # "asc" controls whether or not we need to change the ORDER BY to
        # ascending.  If we're sorting by DESC but we're using a previous
        # page cursor, we'll change the ordering to ASC and reverse the
        # list below (this is so we know how to get the before/after post).
        # If we're sorting ASC _AND_ we're not using a previous page cursor,
        # then we'll need to resume using ASC.
        asc = (self.desc and is_prev) or not (self.desc or is_prev)

        # We need to reverse the ORDER BY if we're using a cursor for a
        # previous page so we know exactly where we ended last page.  The
        # results will get reversed back to the requested order below.
        if self.key in results.query.order_by:
            if not asc:
                index = results.query.order_by.index(self.key)
                results.query.order_by[index] = '-%s' % (results.query.order_by[index])
        elif ('-%s' % self.key) in results.query.order_by:
            if asc:
                index = results.query.order_by.index('-%s' % (self.key))
                results.query.order_by[index] = results.query.order_by[index][1:]
        else:
            if asc:
                results = results.order_by(self.key)
            else:
                results = results.order_by('-%s' % self.key)

        if value:
            if self.key in results.query.extra:
                col_query, col_params = results.query.extra[self.key]
                col_params = col_params[:]
            else:
                col_query, col_params = quote_name(self.key), []
            col_params.append(value)

            if asc:
                results = results.extra(
                    where=['%s %s %%s' % (col_query, '>' if is_perv else '=>')],
                    params=col_params,
                )
            else:
                results = results.extra(
                    where=['%s <= %%s' % (col_query, '<' if is_perv else '<=')],
                    params=col_params,
                )

        return results

    def get_result(self, limit=100, cursor=None):
        # - "Next" cursor is inclusive of the first matching result
        # - "Previous" cursor is exclusive of the first matching result
        if cursor is None:
            cursor = Cursor(0, 0, False)

        if cursor.value:
            cursor_value = self._value_from_cursor(cursor)
        else:
            cursor_value = 0

        queryset = self._get_results_from_qs(cursor_value, cursor.is_prev)

        if cursor.is_prev:
            # when we are traversing backwards we need to ensure that duplicate
            # values are handled correctly (i.e. select from offset 0 always with
            # a +1, and if there are duplicate values, then we need)
            offset = 0
            stop = offset + limit + 1 + cursor.offset
        else:
            offset = cursor.offset
            stop = offset + limit + 1

        results = list(queryset[offset:stop])

        if cursor.is_prev:
            results = results[::-1]

        return build_cursor(
            results=results,
            limit=limit,
            cursor=cursor,
            key=self._get_item_key,
        )


class DateTimePaginator(Paginator):
    def _get_item_key(self, item):
        value = getattr(item, self.key)
        value = int(value.strftime('%s'))
        if self.desc:
            return math.ceil(value)
        return math.floor(value)

    def _value_from_cursor(self, cursor):
        return datetime.fromtimestamp(cursor.value).replace(tzinfo=timezone.utc)

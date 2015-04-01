"""
sentry.utils.cursors
~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2014 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import

from collections import Sequence


class Cursor(object):
    """
    The cursor contains three attributes:

    - The item's value (an item within the set).
    - The offset of the value. This *always* indicates the position in the stack
      from left to right in a fixed sort order (the sort order does not change).
    - An indicator if we're traversing from right to left (this requires more
      work from the manager of the result set).

    Some example cursors (ignoring the navigational flag):

      [0, 0, 1, 1, 2]
       ^ 0:0

      [0, 0, 1, 1, 2]
          ^ 0:1

      [0, 0, 1, 1, 2]
             ^ 1:0

      [0, 0, 1, 1, 2]
                ^ 1:1

      [0, 0, 1, 1, 2]
                   ^ 2:0
    """
    def __init__(self, value, offset=0, is_prev=False, has_results=None):
        # XXX: ceil is not entirely correct here, but it's a simple hack
        # that solves most problems
        self.value = long(value)
        self.offset = int(offset)
        self.is_prev = bool(is_prev)
        self.has_results = has_results

    def __str__(self):
        return '%s:%s:%s' % (self.value, self.offset, int(self.is_prev))

    def __repr__(self):
        return '<%s: value=%s offset=%s is_prev=%s>' % (
            type(self), self.value, self.offset, int(self.is_prev))

    def __nonzero__(self):
        return self.has_results

    @classmethod
    def from_string(cls, value):
        bits = value.split(':')
        if len(bits) != 3:
            raise ValueError
        try:
            bits = float(bits[0]), int(bits[1]), int(bits[2])
        except (TypeError, ValueError):
            raise ValueError
        return cls(*bits)


class CursorResult(Sequence):
    def __init__(self, results, next, prev):
        self.results = results
        self.next = next
        self.prev = prev

    def __len__(self):
        return len(self.results)

    def __iter__(self):
        return iter(self.results)

    def __getitem__(self, key):
        return self.results[key]

    def __repr__(self):
        return '<%s: results=%s>' % (type(self).__name__, len(self.results))

    @classmethod
    def from_ids(self, id_list, key=None, limit=100, cursor=None):
        from sentry.models import Group

        group_map = Group.objects.in_bulk(id_list)

        results = []
        for g_id in id_list:
            try:
                results.append(group_map[g_id])
            except KeyError:
                pass

        return build_cursor(
            results=results,
            key=key,
            cursor=cursor,
            limit=limit,
        )


def build_cursor(results, key, limit=100, cursor=None, has_next=None,
                 has_prev=None):
    """
    The result set should **always** be sorted left-to-right (no matter what
    direction the cursor is sorted).
    """
    if cursor is None:
        cursor = Cursor(0, 0, 0)

    is_prev = cursor.is_prev

    num_results = len(results)

    # Default cursor if not present
    if is_prev:
        next_value = cursor.value
        next_offset = cursor.offset
        # TODO(dcramer): this is incorrect
        has_next = num_results > limit
    elif num_results:
        value = long(key(results[0]))

        # Are there more results than whats on the current page?
        has_next = num_results > limit

        # Determine what our next cursor is by ensuring we have a unique offset
        next_value = long(key(results[-1]))

        if next_value == value:
            next_offset = cursor.offset + limit
        else:
            next_offset = 0
            result_iter = reversed(results)
            # skip the last result
            result_iter.next()
            for result in result_iter:
                if long(key(result)) == next_value:
                    next_offset += 1
                else:
                    break
    else:
        next_value = cursor.value
        next_offset = cursor.offset
        has_next = False

    # Determine what our pervious cursor is by ensuring we have a unique offset
    if not is_prev:
        # TODO(dcramer): this is incorrect
        has_prev = bool(cursor.offset or cursor.value)
        prev_value = cursor.value
        prev_offset = cursor.offset
    elif num_results:
        # TODO(dcramer): this is incorrect
        has_prev = True
        prev_value = long(key(results[-1]))

        if prev_value == cursor.value:
            prev_offset = cursor.offset + limit
        else:
            prev_offset = 0
            result_iter = reversed(results)
            # skip the last result
            result_iter.next()
            for result in result_iter:
                if long(key(result)) == prev_value:
                    prev_offset += 1
                else:
                    break
    else:
        has_prev = False
        prev_value = cursor.value
        prev_offset = cursor.offset

    # Truncate the list to our original result size now that we've determined the next page
    results = results[:limit]

    next_cursor = Cursor(next_value or 0, next_offset, False, has_next)
    prev_cursor = Cursor(prev_value or 0, prev_offset, True, has_prev)

    if cursor.is_prev:
        results = results[::-1]

    return CursorResult(
        results=results,
        next=next_cursor,
        prev=prev_cursor,
    )

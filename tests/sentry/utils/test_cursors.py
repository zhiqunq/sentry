from __future__ import absolute_import

import math

from mock import Mock

from sentry.utils.cursors import build_cursor, Cursor


def build_mock(**attrs):
    obj = Mock()
    for key, value in attrs.items():
        setattr(obj, key, value)
    obj.__repr__ = lambda x: repr(attrs)
    return obj


def test_build_cursor_unique_values():
    event1 = build_mock(id=1, message='one')
    event2 = build_mock(id=2, message='two')
    event3 = build_mock(id=3, message='three')

    results = [event1, event2, event3]

    cursor_kwargs = {
        'key': lambda x: math.floor(x.id),
        'limit': 1,
    }

    cursor = build_cursor(results[0:2], **cursor_kwargs)
    assert isinstance(cursor.next, Cursor)
    assert cursor.next.value == 2
    assert cursor.next.offset == 0
    assert isinstance(cursor.prev, Cursor)
    assert list(cursor) == [event1]

    cursor = build_cursor(results[1:3], cursor=cursor.next, **cursor_kwargs)
    assert isinstance(cursor.next, Cursor)
    assert cursor.next.value == 3
    assert cursor.next.offset == 0
    assert isinstance(cursor.prev, Cursor)
    assert cursor.prev.value == 2
    assert cursor.prev.offset == 0
    assert list(cursor) == [event2]

    cursor = build_cursor(results[2:4], cursor=cursor.next, **cursor_kwargs)
    assert isinstance(cursor.next, Cursor)
    assert cursor.next.value == 3
    assert cursor.next.offset == 1
    assert isinstance(cursor.prev, Cursor)
    assert cursor.prev.value == 3
    assert cursor.prev.offset == 0
    assert list(cursor) == [event3]

    # the previous and next cursor should be identical here as there are no
    # results to branch off of
    cursor = build_cursor(results[3:5], cursor=cursor.next, **cursor_kwargs)
    assert isinstance(cursor.next, Cursor)
    assert cursor.next.value == 3
    assert cursor.next.offset == 1
    assert isinstance(cursor.prev, Cursor)
    assert cursor.prev.value == 3
    assert cursor.prev.offset == 1
    assert list(cursor) == []

    cursor = build_cursor(results[2:4], cursor=cursor.prev, **cursor_kwargs)
    assert isinstance(cursor.next, Cursor)
    # TODO(dcramer): this behavior is currently invalid
    # assert not cursor.next
    assert cursor.next.value == 3
    assert cursor.next.offset == 1
    assert isinstance(cursor.prev, Cursor)
    assert cursor.prev.value == 3
    assert cursor.prev.offset == 0
    assert list(cursor) == [event3]

    cursor = build_cursor(results[1:3], cursor=cursor.prev, **cursor_kwargs)
    assert isinstance(cursor.next, Cursor)
    assert cursor.next.value == 3
    assert cursor.next.offset == 0
    assert isinstance(cursor.prev, Cursor)
    assert cursor.prev.value == 2
    assert cursor.prev.offset == 0
    assert list(cursor) == [event2]

    cursor = build_cursor(results[0:2], cursor=cursor.prev, **cursor_kwargs)
    assert isinstance(cursor.next, Cursor)
    assert cursor.next.value == 2
    assert cursor.next.offset == 0
    assert isinstance(cursor.prev, Cursor)
    assert cursor.prev.value == 1
    assert cursor.prev.offset == 0
    assert list(cursor) == [event1]

    cursor = build_cursor(results[0:1], cursor=cursor.prev, **cursor_kwargs)
    assert isinstance(cursor.next, Cursor)
    assert cursor.next.value == 1
    assert cursor.next.offset == 0
    assert isinstance(cursor.prev, Cursor)
    assert cursor.prev.value == 1
    assert cursor.prev.offset == 0
    assert list(cursor) == []


def test_build_cursor_duplicate_values():
    event1 = build_mock(id=1, message='one')
    event2 = build_mock(id=1, message='two')
    event3 = build_mock(id=2, message='three')

    results = [event1, event2, event3]

    cursor_kwargs = {
        'key': lambda x: math.floor(x.id),
        'limit': 1,
    }

    cursor = build_cursor(results[0:2], **cursor_kwargs)
    assert isinstance(cursor.next, Cursor)
    assert cursor.next.value == 1
    assert cursor.next.offset == 1
    assert isinstance(cursor.prev, Cursor)
    assert list(cursor) == [event1]

    cursor = build_cursor(results[1:3], cursor=cursor.next, **cursor_kwargs)
    assert isinstance(cursor.next, Cursor)
    assert cursor.next.value == 2
    assert cursor.next.offset == 0
    assert isinstance(cursor.prev, Cursor)
    assert cursor.prev.value == 1
    assert cursor.prev.offset == 1
    assert list(cursor) == [event2]

    cursor = build_cursor(results[2:4], cursor=cursor.next, **cursor_kwargs)
    assert isinstance(cursor.next, Cursor)
    assert cursor.next.value == 2
    assert cursor.next.offset == 1
    assert isinstance(cursor.prev, Cursor)
    assert cursor.prev.value == 2
    assert cursor.prev.offset == 0
    assert list(cursor) == [event3]

    # the previous and next cursor should be identical here as there are no
    # results to branch off of
    cursor = build_cursor(results[3:5], cursor=cursor.next, **cursor_kwargs)
    assert isinstance(cursor.next, Cursor)
    assert cursor.next.value == 2
    assert cursor.next.offset == 1
    assert isinstance(cursor.prev, Cursor)
    assert cursor.prev.value == 2
    assert cursor.prev.offset == 1
    assert list(cursor) == []

    cursor = build_cursor(results[2:4], cursor=cursor.prev, **cursor_kwargs)
    assert isinstance(cursor.next, Cursor)
    assert cursor.next.value == 2
    assert cursor.next.offset == 1
    assert isinstance(cursor.prev, Cursor)
    assert cursor.prev.value == 2
    assert cursor.prev.offset == 0
    assert list(cursor) == [event3]

    cursor = build_cursor(results[1:3], cursor=cursor.prev, **cursor_kwargs)
    assert isinstance(cursor.next, Cursor)
    assert cursor.next.value == 2
    assert cursor.next.offset == 0
    assert isinstance(cursor.prev, Cursor)
    assert cursor.prev.value == 1
    assert cursor.prev.offset == 1
    assert list(cursor) == [event2]

    cursor = build_cursor(results[0:2], cursor=cursor.prev, **cursor_kwargs)
    assert isinstance(cursor.next, Cursor)
    assert cursor.next.value == 1
    assert cursor.next.offset == 1
    assert isinstance(cursor.prev, Cursor)
    assert cursor.prev.value == 1
    assert cursor.prev.offset == 0
    assert list(cursor) == [event1]

    cursor = build_cursor(results[0:1], cursor=cursor.prev, **cursor_kwargs)
    assert isinstance(cursor.next, Cursor)
    assert cursor.next.value == 1
    assert cursor.next.offset == 0
    assert isinstance(cursor.prev, Cursor)
    assert cursor.prev.value == 1
    assert cursor.prev.offset == 0
    assert list(cursor) == []

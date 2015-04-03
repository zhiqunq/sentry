from __future__ import absolute_import

from django.utils import timezone

from sentry.api.paginator import DateTimePaginator, Paginator
from sentry.models import Group
from sentry.testutils import TestCase


class PaginatorTest(TestCase):
    def setUp(self):
        now = timezone.now()
        project = self.project

        self.group1 = self.create_group(
            checksum='a' * 32,
            last_seen=now,
        )
        self.group2 = self.create_group(
            checksum='b' * 32,
            last_seen=now,
        )
        self.queryset = Group.objects.filter(project=project)

    def test_unique_sort_key(self):
        paginator = Paginator(self.queryset, order_by='id')

        result = paginator.get_result(limit=1)
        assert len(result) == 1
        assert result[0].id == self.group1.id

        print(result.next)
        result = paginator.get_result(limit=1, cursor=result.next)
        assert len(result) == 1
        assert result[0].id == self.group2.id

        print(result.next)
        result = paginator.get_result(limit=1, cursor=result.next)
        assert len(result) == 0

        print(result.prev)
        result = paginator.get_result(limit=1, cursor=result.prev)
        assert len(result) == 1
        assert result[0].id == self.group2.id

        print(result.prev)
        result = paginator.get_result(limit=1, cursor=result.prev)
        assert len(result) == 1
        assert result[0].id == self.group1.id

        print(result.prev)
        result = paginator.get_result(limit=1, cursor=result.prev)
        assert len(result) == 0

    def test_duplicate_sort_key(self):
        paginator = DateTimePaginator(self.queryset, order_by='last_seen')

        result = paginator.get_result(limit=1)
        assert len(result) == 1
        assert result[0].id == self.group1.id

        print(result.next)
        result = paginator.get_result(limit=1, cursor=result.next)
        assert len(result) == 1
        assert result[0].id == self.group2.id

        print(result.next)
        result = paginator.get_result(limit=1, cursor=result.next)
        assert len(result) == 0

        print(result.prev)
        result = paginator.get_result(limit=1, cursor=result.prev)
        assert len(result) == 1
        assert result[0].id == self.group2.id

        print(result.prev)
        result = paginator.get_result(limit=1, cursor=result.prev)
        assert len(result) == 1
        assert result[0].id == self.group1.id

        print(result.prev)
        result = paginator.get_result(limit=1, cursor=result.prev)
        assert len(result) == 0

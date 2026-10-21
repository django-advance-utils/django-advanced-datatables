"""Columns put to the project's permission check (``django_datatables.permissions``)."""

import django
import pytest
from django.conf import settings

if not settings.configured:
    settings.configure(
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth', 'django_datatables'],
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        USE_TZ=True,
    )
    django.setup()

from django.test import override_settings  # noqa: E402

from django_datatables.columns import ColumnBase  # noqa: E402
from django_datatables.datatables import DatatableTable  # noqa: E402

CHECK = f'{__name__}.check'
ASKED = []
REFUSED = set()


def check(request, kind, name, obj=None):
    ASKED.append((kind, name, obj.table_id))
    return name not in REFUSED


@pytest.fixture(autouse=True)
def reset():
    ASKED.clear()
    REFUSED.clear()


def table():
    return DatatableTable('orders').add_columns(
        ColumnBase(column_name='name'), ColumnBase(column_name='price'), ColumnBase(column_name='margin')
    )


def names(t):
    return [c.column_name for c in t.columns]


def test_with_no_check_set_every_column_is_added():
    assert names(table()) == ['name', 'price', 'margin']


@override_settings(DJANGO_ADVANCED_PERMISSION_CHECK=CHECK)
def test_a_refused_column_is_left_out_and_each_is_asked_about_with_its_table():
    REFUSED.add('margin')

    t = table()

    assert names(t) == ['name', 'price']
    assert ('column', 'margin', 'orders') in ASKED


@override_settings(DJANGO_ADVANCED_PERMISSION_CHECK=CHECK)
def test_sorting_on_a_refused_column_skips_it_and_keeps_positions_right():
    REFUSED.add('name')
    t = table()

    t.sort('-name', 'margin')

    assert t.table_options['order'] == [[1, 'asc']]


@override_settings(DJANGO_ADVANCED_PERMISSION_CHECK=CHECK)
def test_removing_a_refused_column_is_not_an_error():
    REFUSED.add('margin')
    t = table()

    t.remove_columns('margin', 'price')

    assert names(t) == ['name']

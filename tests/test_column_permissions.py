import logging
from types import SimpleNamespace

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

from django.core.exceptions import ImproperlyConfigured  # noqa: E402
from django.test import override_settings  # noqa: E402

from django_datatables.columns import ColumnBase  # noqa: E402
from django_datatables.datatables import DatatableError, DatatableTable, RefusedColumnError  # noqa: E402
from django_datatables.filters import DatatableFilter  # noqa: E402
from django_datatables.plugins.colour_rows import ColourRows  # noqa: E402
from django_datatables.reorder_datatable import OrderedDatatable  # noqa: E402

CHECK = f'{__name__}.check'
ASKED = []
REFUSED = set()


def check(request, kind, name, obj=None):
    ASKED.append((kind, name, obj.table_id, request))
    return name not in REFUSED


@pytest.fixture(autouse=True)
def reset():
    ASKED.clear()
    REFUSED.clear()


def table(*columns, view=None):
    columns = columns or ('name', 'price', 'margin')
    return DatatableTable('orders', view=view).add_columns(*[ColumnBase(column_name=c) for c in columns])


def names(t):
    return [c.column_name for c in t.columns]


def test_with_no_check_set_every_column_is_added():
    assert names(table()) == ['name', 'price', 'margin']


@override_settings(DJANGO_ADVANCED_PERMISSION_CHECK=CHECK)
def test_a_refused_column_is_left_out_and_each_is_asked_about_with_its_table():
    REFUSED.add('margin')

    t = table()

    assert names(t) == ['name', 'price']
    assert ('column', 'margin', 'orders', None) in ASKED


@override_settings(DJANGO_ADVANCED_PERMISSION_CHECK=CHECK)
def test_the_check_is_given_the_views_request():
    request = object()

    table(view=SimpleNamespace(request=request))

    assert {a[3] for a in ASKED} == {request}


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


@override_settings(DJANGO_ADVANCED_PERMISSION_CHECK=CHECK)
def test_a_refused_column_named_by_its_last_part_is_skipped_too():
    REFUSED.add('Company/name')
    t = table('Company/name', 'price')

    t.sort('name', 'price')
    t.remove_columns('name')

    assert t.table_options['order'] == [[0, 'asc']]
    assert names(t) == ['price']


@override_settings(DJANGO_ADVANCED_PERMISSION_CHECK=CHECK)
def test_a_permitted_column_wins_over_a_refused_one_with_the_same_last_part():
    REFUSED.add('Company/name')
    t = table('Company/name', 'name', 'price')

    t.remove_columns('name')

    assert names(t) == ['price']


@override_settings(DJANGO_ADVANCED_PERMISSION_CHECK=CHECK)
def test_looking_up_a_refused_column_raises_a_refused_column_error():
    REFUSED.add('margin')
    t = table()

    with pytest.raises(RefusedColumnError):
        t.column('margin')
    with pytest.raises(DatatableError) as e:
        t.column('missing')
    assert not isinstance(e.value, RefusedColumnError)


@override_settings(DJANGO_ADVANCED_PERMISSION_CHECK=CHECK)
def test_js_filters_on_or_summing_a_refused_column_are_left_out_quietly(caplog):
    REFUSED.add('margin')
    t = table()

    with caplog.at_level(logging.WARNING):
        t.add_js_filters('pivot', 'margin', 'price')
        t.add_js_filters('totals', 'name', sum_column='margin')
        t.add_js_filters('totals', sum_column='margin')

    assert [f.column.column_name for f in t.js_filter_list] == ['price']
    assert caplog.records == []


@override_settings(DJANGO_ADVANCED_PERMISSION_CHECK=CHECK)
def test_a_filters_columns_leave_out_a_refused_one():
    REFUSED.add('margin')
    t = table()

    f = DatatableFilter('pivot', t, columns=['name', 'margin', 'price'])

    assert [c[1:] for c in f.column_titles()] == [('name', 0), ('price', 1)]


@override_settings(DJANGO_ADVANCED_PERMISSION_CHECK=CHECK)
def test_a_refused_id_column_is_warned_about(caplog):
    REFUSED.add('id')
    t = table('id', 'name')

    with caplog.at_level(logging.WARNING):
        assert t.setup_column_id() is None

    assert 'refused the id column' in caplog.text


@override_settings(DJANGO_ADVANCED_PERMISSION_CHECK='no_such_module.check')
def test_a_check_that_cannot_be_imported_names_the_setting():
    with pytest.raises(ImproperlyConfigured, match='DJANGO_ADVANCED_PERMISSION_CHECK'):
        table()


@override_settings(DJANGO_ADVANCED_PERMISSION_CHECK=CHECK)
def test_a_cached_table_is_cached_apart_for_each_set_of_refused_columns():
    everything = table()
    REFUSED.add('margin')
    without_margin = table()

    assert everything.cache_key == 'orders'
    assert without_margin.cache_key == 'orders:refused:margin'


@override_settings(DJANGO_ADVANCED_PERMISSION_CHECK=CHECK)
def test_columns_added_without_checking_permissions_are_not_asked_about():
    REFUSED.add('margin')
    t = DatatableTable('orders')

    t.add_columns(ColumnBase(column_name='margin'), check_permissions=False)

    assert names(t) == ['margin']
    assert ASKED == []


@override_settings(DJANGO_ADVANCED_PERMISSION_CHECK=CHECK)
def test_an_ordered_tables_own_columns_are_not_asked_about():
    REFUSED.update({'pk', '_handle', '_index'})

    t = OrderedDatatable('orders', order_field='order')

    assert len(t.columns) == 3
    assert ASKED == []


@override_settings(DJANGO_ADVANCED_PERMISSION_CHECK=CHECK)
def test_a_colour_rule_on_a_refused_column_is_left_out():
    REFUSED.add('margin')
    t = table()

    plugin = ColourRows(t, [{'column': 'margin', 'values': {}}, {'column': 'price', 'values': {}}])

    assert [c['column'] for c in plugin.colour_dict] == [1]

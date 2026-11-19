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

from django.core.exceptions import BadRequest, PermissionDenied  # noqa: E402
from django.db import connection, models  # noqa: E402
from django.db.models.signals import post_save  # noqa: E402

from django_datatables.reorder_datatable import OrderedDatatable, ReorderDatatableView, reorder  # noqa: E402


class Stage(models.Model):
    name = models.CharField(max_length=20)
    order = models.IntegerField(default=0)

    class Meta:
        app_label = 'django_datatables'


@pytest.fixture(autouse=True)
def stages():
    with connection.schema_editor() as editor:
        editor.create_model(Stage)
    yield
    with connection.schema_editor() as editor:
        editor.delete_model(Stage)


def make(*names, order=0):
    return [Stage.objects.create(name=name, order=order) for name in names]


def shown(order_by=('order', 'pk')):
    return list(Stage.objects.order_by(*order_by).values_list('name', flat=True))


def sort_data(*rows):
    """What the table sends after a drag: each row's new position, with its pk."""
    return [[position, row.pk] for position, row in enumerate(rows)]


def test_a_drag_saves_the_new_positions():
    a, b, c = make('a', 'b', 'c')

    reorder(Stage, 'order', sort_data(c, a, b))

    assert shown() == ['c', 'a', 'b']


def test_rows_sharing_a_value_are_read_in_the_order_they_were_shown():
    a, b, c = make('a', 'b', 'c')

    # The table showed a, b, c (order 0 each, then pk). Moving b to the top must leave c after a.
    reorder(Stage, 'order', sort_data(b, a, c))

    assert shown() == ['b', 'a', 'c']


def test_a_handle_let_go_in_place_writes_nothing():
    rows = make('a', 'b', 'c')

    assert reorder(Stage, 'order', sort_data(*rows), order_by=('order', 'pk')) == 0
    assert list(Stage.objects.values_list('order', flat=True)) == [0, 0, 0]


def test_without_the_shown_order_a_drag_between_tied_rows_is_saved():
    # Shown by name, b (made first) after a. Dragging b above a sends b, a: the order of their primary keys,
    # which is no reason to think nothing moved.
    b, a = make('b', 'a')

    assert reorder(Stage, 'order', sort_data(b, a)) == 1
    assert shown(('order', 'name')) == ['b', 'a']


def test_each_row_is_saved_so_signals_hear_of_it():
    a, b = make('a', 'b')
    saved = []

    def note(sender, instance, **kwargs):
        saved.append(instance.name)

    post_save.connect(note, sender=Stage)
    try:
        reorder(Stage, 'order', sort_data(b, a))
    finally:
        post_save.disconnect(note, sender=Stage)

    # Both held 0: b already holds its new position, so only a is written.
    assert saved == ['a']


def test_a_malformed_payload_writes_nothing():
    a, b = make('a', 'b')

    assert reorder(Stage, 'order', [['x', a.pk], [0, b.pk]]) == 0
    assert reorder(Stage, 'order', [[0]]) == 0
    assert reorder(Stage, 'order', None) == 0
    assert reorder(Stage, 'order', [[float('inf'), a.pk], [0, b.pk]]) == 0
    assert shown() == ['a', 'b']


def test_a_position_outside_the_rows_sent_writes_nothing():
    a, b = make('a', 'b')

    assert reorder(Stage, 'order', [[2, a.pk], [0, b.pk]]) == 0
    assert reorder(Stage, 'order', [[-1, a.pk], [0, b.pk]]) == 0
    assert list(Stage.objects.values_list('order', flat=True)) == [0, 0]


def test_a_failed_save_writes_none_of_the_drag(monkeypatch):
    a, b, c = make('a', 'b', 'c')
    real_save = Stage.save

    def save(self, *args, **kwargs):
        if self.name == 'c':
            raise RuntimeError('refused')
        real_save(self, *args, **kwargs)

    monkeypatch.setattr(Stage, 'save', save)
    with pytest.raises(RuntimeError):
        reorder(Stage, 'order', sort_data(b, c, a))
    assert list(Stage.objects.order_by('pk').values_list('order', flat=True)) == [0, 0, 0]


def test_a_row_that_no_longer_exists_is_skipped():
    a, b = make('a', 'b')

    assert reorder(Stage, 'order', [[0, b.pk], [1, a.pk], [2, 999]]) == 1
    assert shown() == ['b', 'a']


def test_the_shown_order_can_break_ties_by_another_field():
    make('c', 'a', 'b')

    table = OrderedDatatable('stages', model=Stage, order_field='order', row_order=('order', 'name'))

    assert table.row_order == ('order', 'name')
    assert shown(table.row_order) == ['a', 'b', 'c']


def test_table_options_passed_in_are_added_to_the_ordered_ones():
    table = OrderedDatatable('stages', model=Stage, order_field='order', table_options={'scrollX': True})

    assert table.table_options['scrollX'] is True
    assert table.table_options['rowReorder'] is True
    assert table.table_options['dom'] == 't'


def test_a_table_that_cannot_be_reordered_has_no_handle_and_no_drag():
    table = OrderedDatatable('stages', model=Stage, order_field='order', reorderable=False)

    assert table.table_options['rowReorder'] is False
    assert [c.column_name for c in table.columns] == ['index', 'pk']


class StageOrder(ReorderDatatableView):
    model = Stage
    order_field = 'order'
    allowed = True

    def can_reorder(self):
        return self.allowed

    def command_response(self, command, **kwargs):
        return command


def view(allowed=True):
    v = StageOrder()
    v.request = SimpleNamespace(user=None)
    v.allowed = allowed
    v.tables = {}
    v.add_tables()
    return v


def test_the_view_gives_its_table_the_view():
    v = view()

    assert v.tables['stageorder'].view is v


def test_a_view_that_refuses_reordering_gives_no_handles_and_refuses_a_sort():
    a, b = make('a', 'b')
    v = view(allowed=False)

    assert v.tables['stageorder'].reorderable is False
    with pytest.raises(PermissionDenied):
        v.datatable_sort(table_id='stageorder', sort=sort_data(b, a))
    assert shown() == ['a', 'b']


def test_a_saved_column_order_does_not_move_the_position_and_pk_columns(monkeypatch):
    from django_datatables.datatables import DatatableTable

    saved = SimpleNamespace(column_order=['name', 'pk', 'index'], column_visibility={'index': False})
    monkeypatch.setattr(DatatableTable, 'get_saved_state', lambda self, name: saved)
    table = OrderedDatatable('stages', model=Stage, order_field='order', view=SimpleNamespace(request=None))
    table.add_columns('name')

    assert [c.column_name for c in table.columns][:2] == ['index', 'pk']


def test_the_view_saves_a_drag():
    a, b = make('a', 'b')

    view().datatable_sort(table_id='stageorder', sort=sort_data(b, a))

    assert shown() == ['b', 'a']


def test_a_sort_for_another_table_or_with_nothing_sent_is_a_bad_request():
    a, b = make('a', 'b')
    v = view()

    with pytest.raises(BadRequest):
        v.datatable_sort(table_id='other', sort=sort_data(b, a))
    with pytest.raises(BadRequest):
        v.datatable_sort(sort=sort_data(b, a))
    assert v.datatable_sort(table_id='stageorder') == 'reload_table'
    assert shown() == ['a', 'b']

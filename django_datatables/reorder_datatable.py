from django.core.exceptions import BadRequest, PermissionDenied, ValidationError
from django.db import router, transaction

from django_datatables.datatables import DatatableView, DatatableTable


def reorder(model, order_field, sort_data, order_by=None):
    """Save the order a drag left the rows in, and return how many rows were written.

    ``sort_data`` is what the table sends after a drag: ``[position, pk]`` for each of its rows, the position
    being where that row now stands. Each row whose value differs from its position is saved with it, through
    ``save()``, so ``auto_now`` fields and signals see the change, all in one transaction.

    ``order_by`` is the order the table showed the rows in. When it is given and the positions sent leave the
    rows in that same order, nothing moved and nothing is written: rows sharing a value are not renumbered by a
    handle let go where it was. Without it the order the rows were shown in is not known, so the positions are
    always saved.

    A payload that is not a list of ``[position, pk]`` pairs, each position a whole number of 0 or more, writes
    nothing and returns 0. Positions are saved as sent, gaps and all.
    """
    pk_field = model._meta.pk
    try:
        positions = {pk_field.to_python(pk): int(position) for position, pk in sort_data}
    except (TypeError, ValueError, OverflowError, ValidationError):
        return 0
    if any(position < 0 for position in positions.values()):
        return 0

    rows = list(model.objects.filter(pk__in=positions).order_by(*(order_by or (order_field, 'pk'))))
    if order_by:
        shown = [row.pk for row in rows]
        if sorted(shown, key=lambda pk: positions[pk]) == shown:
            return 0

    written = 0
    with transaction.atomic(using=router.db_for_write(model)):
        for row in rows:
            position = positions[row.pk]
            if getattr(row, order_field) != position:
                setattr(row, order_field, position)
                row.save()
                written += 1
    return written


class OrderedDatatable(DatatableTable):
    """A table whose rows are put in order by dragging them.

    ``order_field`` is the model field that holds the order. ``row_order`` is the order the rows are shown in,
    which is also the order a drag is read against: by default the order field and then the primary key, so rows
    that share a value are always shown, and read, in the same order. Pass ``reorderable=False`` to show the rows
    in that order with no handles and no dragging.
    """

    handle_html = '<i class="btn btn-sm btn-outline-secondary fas fa-arrows-alt-v"></i>'

    def __init__(self, *args, order_field=None, row_order=None, reorderable=True, **kwargs):
        self.order_field = order_field
        self.row_order = tuple(row_order) if row_order else (order_field, 'pk')
        self.reorderable = reorderable
        table_options = {
            'dom': 't',
            'no_col_search': True,
            'no_footer': True,
            'pageLength': 400,
            'stateSave': False,
            'rowReorder': reorderable,
        }
        table_options.update(kwargs.get('table_options') or {})
        kwargs['table_options'] = table_options
        super().__init__(*args, **kwargs)
        self.table_classes = ['display', 'compact', 'smalltext', 'table-sm', 'table']
        columns = ['._index', '.pk']
        if reorderable:
            columns.append(('_handle', {'title': '', 'column_defs': {'width': '30px', 'className': 'button-cell'}}))
        self.add_columns(*columns, check_permissions=False)

    def get_saved_state(self, name):
        # A drag sends the first two columns of each row as its position and pk, so a saved column order (one
        # kept for this view from before its table could be reordered) must not move them.
        return None

    def get_query(self, **kwargs):
        data = super().get_query(**kwargs).order_by(*self.row_order)
        handle = self.handle_html if self.reorderable else ''
        for i, d in enumerate(data):
            d['index'] = i
            d['handle'] = handle
        return data

    def col_def_str(self):
        for c in self.columns:
            c.column_defs['orderable'] = False
        return super().col_def_str()


class ReorderDatatableView(DatatableView):

    order_field: str
    row_order = None
    ordered_table_class = OrderedDatatable
    ajax_commands = ['datatable']

    def can_reorder(self):
        """Whether this request may drag the rows. When not, the rows are shown in order with no handles, and a
        sort sent anyway is refused."""
        return True

    def add_sortable_table(self, table_id, order_field, **kwargs):
        kwargs.setdefault('row_order', self.row_order)
        kwargs.setdefault('reorderable', self.can_reorder())
        self.tables[table_id] = self.ordered_table_class(
            table_id, table_options=self.table_options, order_field=order_field, view=self, **kwargs)

    def datatable_sort(self, **kwargs):
        if not self.can_reorder():
            raise PermissionDenied
        table_id = kwargs.get('table_id')
        table = self.tables.get(table_id) if isinstance(table_id, str) else None
        if table is None:
            raise BadRequest('Unknown table')
        reorder(table.model, table.order_field, kwargs.get('sort'), order_by=table.row_order)
        # noinspection PyUnresolvedReferences
        return self.command_response('reload_table', table_id=kwargs['table_id'])

    def add_tables(self):
        self.add_sortable_table(type(self).__name__.lower(), model=self.model, order_field=self.order_field)

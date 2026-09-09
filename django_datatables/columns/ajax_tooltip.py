"""A column whose cells open a large tooltip window filled by an ajax call.

Clicking (or hovering) a cell posts the table id, the row and the column number back to the
view, and whatever html comes back is shown in a floating window beside the cell. Nothing is
fetched until a cell is asked about, so an expensive summary - a related queryset, a rendered
template, a call to another service - costs one request for the one row the user cares about
rather than one per row of the table.
"""
from django_datatables.columns.column_base import ColumnBase, DatatableColumnError


# Something to click on for a column with no field of its own.
TOOLTIP_ICON = '<i class="far fa-comment-alt"></i>'

# Cells in a tooltip column carry this class - the css gives them a pointer and a hover tint.
TOOLTIP_CELL_CLASS = 'dt-tooltip-cell'


class AjaxTooltipColumn(ColumnBase):
    """Cells that open a large tooltip window whose contents come from an ajax call.

    The post carries ``table_id``, ``row_no`` (the row's html id, ``i`` + primary key),
    ``row_index`` and ``column`` (the DataTables row and column numbers), ``column_name`` and
    the row's data, and is dispatched by ajax-helpers to ``tooltip_<command>`` on the view.
    ``command`` defaults to ``column``, which :class:`DatatableView` implements by calling
    ``get_tooltip`` on this column.

    Supply the content either with a ``tooltip=`` callable::

        AjaxTooltipColumn(column_name='notes', title='Notes',
                          tooltip=lambda **kwargs: f'<b>Row {kwargs["row_no"]}</b>')

    or by subclassing and overriding ``get_tooltip``.
    """

    # The cell is a trigger, not data - the value behind it is only the row's id.
    def xl_dont_show(self):
        return self.field is None

    def __init__(self, *, tooltip=None, command='column', trigger='click', tooltip_title=None,
                 width=400, max_height=320, tooltip_class=None, cache=True, delay=250, placement='auto',
                 cell_html=None, send_row_data=True, **kwargs):
        """
        :param tooltip: callable returning the tooltip's html - called with the ajax kwargs
        :param command: posted as ``tooltip``, so the view method is ``tooltip_<command>``
        :param trigger: ``click`` (stays open until dismissed) or ``hover``
        :param tooltip_title: heading shown in the window; None for a window with no header
        :param width: window width in px (or any css length as a string)
        :param max_height: window height in px before its body scrolls
        :param tooltip_class: extra css class put on the window, for per-column styling
        :param cache: keep each cell's html, so a second look does not post again
        :param delay: ms the pointer must rest on a cell before a ``hover`` window opens
        :param placement: ``auto``, ``bottom`` or ``top``
        :param cell_html: html rendered in every cell - defaults to an icon when there is
                          no field, or to the field's value when there is
        :param send_row_data: include the row's values in the post
        """
        if not self.initialise(locals()):
            return
        self.tooltip_function = self.kwargs.pop('tooltip')
        self.tooltip_options = {
            'command': self.kwargs.pop('command'),
            'trigger': self.kwargs.pop('trigger'),
            'title': self.kwargs.pop('tooltip_title'),
            'width': self.kwargs.pop('width'),
            'max_height': self.kwargs.pop('max_height'),
            'css_class': self.kwargs.pop('tooltip_class'),
            'cache': self.kwargs.pop('cache'),
            'delay': self.kwargs.pop('delay'),
            'placement': self.kwargs.pop('placement'),
            'send_row_data': self.kwargs.pop('send_row_data'),
        }
        cell_html = self.kwargs.pop('cell_html')
        super().__init__(**self.kwargs)
        self.options['tooltip'] = self.tooltip_options
        if cell_html is None and self.field is None:
            cell_html = TOOLTIP_ICON
        if cell_html is not None:
            self.options['render'] = [{'html': cell_html, 'function': 'Html'}]
            self.column_defs['orderable'] = False
            self.add_class('dt-center')
        self.add_class(TOOLTIP_CELL_CLASS)

    def add_class(self, css_class):
        """Add a css class to every cell of the column, keeping any already set."""
        classes = self.column_defs.get('className', '').split()
        if css_class not in classes:
            classes.append(css_class)
        self.column_defs['className'] = ' '.join(classes)

    def get_tooltip(self, **kwargs):
        """Return the html for one cell's tooltip window.

        Called with everything the browser posted - ``table_id``, ``row_no``, ``row_index``,
        ``column``, ``column_name`` and ``row_data`` - plus the ``view`` and ``table`` it came
        from, and this column as ``column_instance`` (``column`` is the column *number*).
        Override in a subclass, or pass a ``tooltip=`` callable to the column.
        """
        if self.tooltip_function is None:
            raise DatatableColumnError(
                f'{type(self).__name__} {self.column_name} has no tooltip. Pass a tooltip= callable to the '
                f'column, override get_tooltip in a subclass, or add a tooltip_{self.tooltip_options["command"]} '
                f'method to the view.')
        return self.tooltip_function(column_instance=self, **kwargs)


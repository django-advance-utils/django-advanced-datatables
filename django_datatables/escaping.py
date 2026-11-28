"""Escaping a table's cells where they are written for the page.

DataTables writes each cell into the page as HTML, and a column hands it what it read as it is stored. So text
somebody typed, holding a tag, ran in the browser of everyone who opened the table, unless that column escaped it.
With ``DATATABLES_ESCAPE_CELLS = True`` the tables escape every cell on its way to the page instead, unless the code
that built it marked it safe -- ``format_html``, ``mark_safe`` and ``escape`` all return a ``SafeString`` -- or its
column opts out with ``page_escape = False``. A forgotten mark then shows its tags as text rather than running. It is
the default Django templates use.

A lookup's labels go the same way: the ``[key, label]`` pairs a column hands the page for its ``ReplaceLookup``
render are escaped with its cells (``DatatableTable.page_options``), the keys as the cells are, so they still
match.

Only the page is escaped. ``DatatableTable.get_table_array`` still hands everything else -- an Excel download, the
clipboard, a spreadsheet -- what the columns read.

Off unless the setting turns it on, so a project can take this release and turn it on when its own markup is marked.
"""

from django.conf import settings
from django.utils.html import conditional_escape
from django.utils.safestring import SafeData


def escape_cells_setting():
    """Whether tables escape their cells for the page, unless a table says otherwise (``DatatableTable.escape_cells``)."""
    return bool(getattr(settings, 'DATATABLES_ESCAPE_CELLS', False))


def page_cell(value):
    """A cell as the page gets it: text escaped unless it is marked safe; a number, a bool or None as it is.

    A column reading several fields hands the page a list, for a client-side render to put together, so each of its
    items is escaped the same way.
    """
    if isinstance(value, str):
        return value if isinstance(value, SafeData) else conditional_escape(value)
    if isinstance(value, (list, tuple)):
        return [page_cell(item) for item in value]
    return value

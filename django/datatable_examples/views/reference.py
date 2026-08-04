from django.views.generic import TemplateView

from datatable_examples.column_docs import COLUMN_SECTIONS
from datatable_examples.views.base import ManualPage


class ColumnReference(ManualPage, TemplateView):
    """Reference documentation rather than a live example - the content is in column_docs.py."""

    template_name = 'datatable_examples/column_reference.html'
    page_title = 'Column Reference'
    # ManualPage defaults to ['setup_table']; there is no table on this page.
    code_examples = []

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # add_to_context is only merged by DatatableView, so a TemplateView page sets context here.
        context['sections'] = COLUMN_SECTIONS
        context['description'] = (
            'Every column class in <b>django_datatables</b>: what it renders, the kwargs it takes and an '
            'example. Columns with an amber badge link to the page that demonstrates them on a live table. '
            'Aliases kept for backwards compatibility are noted against the column they are equivalent to '
            'rather than listed separately.'
        )
        return context

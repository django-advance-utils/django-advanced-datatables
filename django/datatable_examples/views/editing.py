import json

from django.utils.html import format_html, format_html_join

from datatable_examples import models
from datatable_examples.views.base import ManualPage
from django_datatables.columns import (AjaxTooltipColumn, ColumnBase, DatatableColumn, DateColumn,
                                       ManyToManyColumn)
from django_datatables.datatables import DatatableView
from django_datatables.helpers import render_replace, row_button


class NumberEdit(DatatableColumn):
    """A column rendered as a number input; the value posts back on blur."""

    def row_result(self, data_dict, _page_results):
        return ('<form><input style="text-align:right" type="number" name="count" '
                'onblur=django_datatables.b_r(this) ></form>')


class InlineEditing(ManualPage, DatatableView):
    model = models.Person
    page_title = 'Inline Editing'
    ajax_commands = ['row', 'column']
    code_examples = ['setup_table', 'row_column']

    @staticmethod
    def setup_table(table):
        table.edit_fields = ['first_name', 'title', 'company__name']
        table.edit_options = {'company__name': {'select2': True}}
        table.add_columns(
            'id',
            'first_name',
            'title_model',
            ('company__name', {'title': 'Company Name'}),
            DateColumn('date_entered', column_name='Date'),
            NumberEdit(column_name='number_edit', title='Number input'),
            'surname',
        )

    def row_column(self, row_data, inputs, **kwargs):
        row = json.loads(row_data)
        return self.command_response('message', text=f'Row id {row[0]} sent {dict(inputs)}')

    def add_to_context(self, **kwargs):
        return {'description': (
            'Fields listed in <code>edit_fields</code> become editable in place — double-click a first '
            'name, title, or company. A <code>ChoiceColumn</code> edits with a dropdown of its choices, '
            'and <code>edit_options</code> upgrades a field to a select2 search. The save posts back '
            'through the view\'s <code>row_edit</code> handler and the row refreshes. '
            'The last column is a custom column that renders an <code>&lt;input&gt;</code> in every '
            'row; on blur <code>django_datatables.b_r(this)</code> posts the value and the row data to '
            'the view\'s <code>row_column</code> method.'
        )}


class RowButtons(ManualPage, DatatableView):
    model = models.Company
    page_title = 'Row Buttons'
    ajax_commands = ['row']
    code_examples = ['setup_table', 'row_toggle_tag', 'row_delete']

    def row_delete(self, **kwargs):
        # Could delete from the database here, but for the demo only the displayed row is removed
        return self.command_response('delete_row', row_no=kwargs['row_no'], table_id=kwargs['table_id'])

    def row_toggle_tag(self, **kwargs):
        row_data = json.loads(kwargs['row_data'])
        table = self.tables[kwargs['table_id']]
        self.setup_tables(table_id=table.table_id)

        company = models.Company.objects.get(id=row_data[0])
        tag = models.Tags.objects.get(id=1)
        if tag in company.tags_set.all():
            company.tags_set.remove(tag)
        else:
            company.tags_set.add(tag)
        return table.refresh_row(self.request, kwargs['row_no'])

    @staticmethod
    def setup_table(table):
        table.add_columns(
            'id',
            ColumnBase(column_name='idx', field=['id', 'name'], title='Rendered with helper', render=[
                render_replace(html='<b>%1%</b>&nbsp;<i>%2%</i>', column='idx:0'),
                render_replace(var='%2%', column='idx:1'),
            ]),
            ColumnBase(column_name='BasicButton', render=[row_button('toggle_tag', 'toggle TAG1')]),
            ColumnBase(column_name='FormattedButton', render=[row_button('toggle_tag', 'toggle TAG1',
                                                              button_classes='btn %1% btn-sm',
                                                              var='%1%',
                                                              value=1,
                                                              column='CompanyTags',
                                                              choices=['btn-success', ''],
                                                              function='ValueInColumn')]),
            ColumnBase(column_name='Delete', render=[row_button('delete', 'Delete Row')]),
            ManyToManyColumn(column_name='CompanyTags', field='tags__tag', model=models.Company,
                             html='<span class="badge badge-primary"> %1% </span>'),
        )
        table.ajax_data = False

    def add_to_context(self, **kwargs):
        return {'description': (
            'The <code>row_button</code> helper renders a button in every row that posts the row back '
            'to a <code>row_&lt;name&gt;</code> method on the view. <i>toggle TAG1</i> adds or removes '
            'a tag and refreshes just that row with <code>table.refresh_row</code>; the formatted '
            'variant styles itself green when the tag is present by checking the '
            '<code>CompanyTags</code> column with the <code>ValueInColumn</code> function. '
            '<i>Delete Row</i> responds with the <code>delete_row</code> command, which removes the '
            'row client-side.'
        )}


class AjaxTooltips(ManualPage, DatatableView):
    model = models.Person
    page_title = 'Ajax Tooltip Column'
    code_examples = ['setup_table', 'person_tooltip', 'sent_tooltip']

    @staticmethod
    def person_tooltip(row_no, **_kwargs):
        """Build the window's html for one row - row_no is 'i' + the row's primary key."""
        person = models.Person.objects.select_related('company').get(pk=row_no[1:])
        colleagues = models.Person.objects.filter(company=person.company).exclude(pk=person.pk)
        rows = format_html_join(
            '', '<tr><td class="pr-3">{}</td><td>{}</td></tr>',
            (('Title', person.get_title_display() or '-'),
             ('Name', f'{person.first_name} {person.surname}'),
             ('Company', person.company.name or '-'),
             ('Date entered', person.date_entered.strftime('%d/%m/%Y')),
             ('Colleagues', colleagues.count())))
        return format_html('<table class="table table-sm mb-2">{}</table>{}', rows, format_html_join(
            '', '<span class="badge badge-secondary mr-1">{}</span>',
            ((f'{c.first_name} {c.surname}',) for c in colleagues[:20])))

    @staticmethod
    def sent_tooltip(row_no, row_index, column, column_name, row_data, **_kwargs):
        """Everything the browser posted - the row and the column it was hovering over."""
        return format_html(
            '<div>row_no <b>{}</b> (row {}), column <b>{}</b> ({})</div><div class="mt-1">{}</div>',
            row_no, row_index, column, column_name, row_data)

    @staticmethod
    def setup_table(table):
        table.add_columns(
            'id',
            'first_name',
            'surname',
            ('company__name', {'title': 'Company'}),
            AjaxTooltipColumn(column_name='details', title='Details', tooltip_title='Person',
                              tooltip=AjaxTooltips.person_tooltip, width=460),
            AjaxTooltipColumn(column_name='sent', field='date_entered', title='Date Entered (hover)',
                              trigger='hover', tooltip_title='Posted to the view',
                              tooltip=AjaxTooltips.sent_tooltip, width=420, placement='top'),
        )

    def add_to_context(self, **kwargs):
        return {'description': (
            'An <code>AjaxTooltipColumn</code> turns its cells into a trigger for a large tooltip window. '
            'Clicking the <i>Details</i> icon posts the table id, the row number and the column number to the '
            'view, and the html that comes back fills a floating window beside the cell - so the query behind '
            'it runs once, for the one row asked about, rather than for every row of the table. '
            'The <i>Date Entered</i> column uses <code>trigger=\'hover\'</code> and shows exactly what the '
            'browser sent. The default <code>command</code> hands the post to the column\'s '
            '<code>get_tooltip</code>, which here is the <code>tooltip=</code> callable; a view can answer for '
            'itself instead by overriding <code>tooltip_column</code>, or by giving the column a '
            '<code>command=</code> of its own and adding a matching <code>tooltip_&lt;command&gt;</code> method.'
        )}

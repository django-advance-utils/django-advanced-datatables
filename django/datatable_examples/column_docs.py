"""Content for the Column Reference page.

Hand written documentation for every column class in django_datatables, grouped into the
sections the reference page renders. Adding a column to the package means adding a ColumnDoc
here - tests.TestColumnReference fails until it is documented (or listed in ALIAS_COLUMNS).

Entries hold the column *class*, never an instance: several columns do real work in __init__
(ManyToManyColumn needs a model, MenuColumn renders a menu needing a request), so building one
at import time would break the whole demo site.
"""
from dataclasses import dataclass, field as dataclass_field

from django_datatables.columns import (AlignColumnLink, BooleanColumn, CallableColumn, ChoiceColumn, ColumnBase,
                                       ColumnLink, CurrencyColumn, CurrencyPenceColumn, DatatableColumn, DateColumn,
                                       DateTimeColumn, ExcelDatatableColumn, GroupedColumn, JsonBooleanColumn,
                                       JsonKeyColumn, LambdaColumn, LocaleCurrencyColumn, ManyToManyColumn,
                                       MenuColumn, MonthColumn, MultiCurrencyColumn, MultiMenuColumnBase,
                                       NoHeadingColumn, SelectColumn, SelectColumnNoTitle, TableRowColour,
                                       TextFieldColumn, TickColumn, ViewLink, XlColumnLink, YearMonthColumn,
                                       ZeroPenceColumn)
from django_datatables.columns.modal_columns import ColumnLinkCoalesce, ModalLink


# Kept for backwards compatibility. Each is the same column with a kwarg set, and says so in its
# own docstring, so it is mentioned in its parent's notes instead of getting an entry of its own.
ALIAS_COLUMNS = (SelectColumnNoTitle, YearMonthColumn, TableRowColour, AlignColumnLink, XlColumnLink)


@dataclass(frozen=True)
class KwargDoc:
    name: str
    default: str  # '' renders as "required"
    description: str


@dataclass(frozen=True)
class ColumnDoc:
    column: type  # the class itself - never an instance
    summary: str
    kwargs: tuple = ()
    example: str = ''
    demo: str = ''  # url_name of the manual page demonstrating it
    demo_title: str = ''
    notes: str = ''

    # Django templates cannot reach __name__ etc., so expose what the page needs as properties.
    @property
    def name(self):
        return self.column.__name__

    @property
    def base_name(self):
        base = self.column.__bases__[0]
        return '' if base is object else base.__name__

    @property
    def module_name(self):
        return self.column.__module__.rsplit('.', 1)[-1] + '.py'

    @property
    def anchor(self):
        return self.column.__name__


@dataclass(frozen=True)
class Section:
    slug: str
    title: str
    intro: str
    columns: tuple = dataclass_field(default_factory=tuple)


COLUMN_SECTIONS = (

    Section('basics', 'Basics',
            'Every column inherits from <code>ColumnBase</code>, which fetches one or more ORM fields and '
            'renders their value. Most tables are built from these plus plain field names.', (

        ColumnDoc(
            column=ColumnBase,
            summary='The base column, and a perfectly good column in its own right: it renders the value of '
                    '<code>field</code> for each row. Every kwarg below is available on every other column.',
            kwargs=(
                KwargDoc('column_name', '', 'Identifies the column. Defaults <code>field</code> and '
                                            '<code>title</code>. A leading <code>.</code> hides the column, '
                                            '<code>_</code> makes it calculated (no ORM field), <code>$</code> '
                                            'marks it secure.'),
                KwargDoc('field', 'column_name', 'ORM path fetched for the column. A list fetches several, and '
                                                 'makes the row value a list.'),
                KwargDoc('title', 'from column_name', 'Header text.'),
                KwargDoc('annotations', 'None', 'Dict of ORM annotations added to the query for this column.'),
                KwargDoc('render', 'None', 'Client-side render functions - see <code>render_replace</code>.'),
                KwargDoc('width', 'None', "Column width, e.g. <code>'80px'</code>."),
                KwargDoc('hidden', 'False', 'Hide by default. Saved state may override. Same as a '
                                            '<code>.</code> prefix.'),
                KwargDoc('enabled', 'True', 'False leaves the column out of the table altogether.'),
                KwargDoc('blank', 'None', 'Rendered when the value is None or empty.'),
                KwargDoc('choices', 'None', 'Dict mapping stored value to label.'),
                KwargDoc('no_col_search', 'False', 'Hide this column\'s header search box.'),
                KwargDoc('column_defs', '{}', 'Raw DataTables.js columnDef entries for the column.'),
                KwargDoc('search_field', 'field', 'ORM path(s) used by server-side search and sorting. '
                                                  '<code>False</code> makes the column unsearchable.'),
                KwargDoc('search', 'None', 'Callable taking the search text and returning a <code>Q</code> '
                                           '(or a dict of filter kwargs) for full control of the search.'),
            ),
            example="""\
table.add_columns(
    'name',                                  # a plain field needs no column object
    ColumnBase(column_name='people', field='people',
               annotations={'people': Count('person__id')}),
    ColumnBase(column_name='.order', field='order'),   # '.' prefix = hidden
)""",
            demo='first_table', demo_title='A First Table',
            notes='<code>TableRowColour</code> is a hidden column under another name - the '
                  '<code>.</code> prefix above is the preferred spelling.',
        ),

        ColumnDoc(
            column=DatatableColumn,
            summary='<code>ColumnBase</code> under a second name. It adds nothing, but it is the conventional '
                    'base for a custom column: subclass it and override <code>col_setup()</code> to configure '
                    'the column, or <code>row_result()</code> to compute each cell.',
            example="""\
class IdColumn(DatatableColumn):

    def col_setup(self):
        self.field = 'id'
        self.title = 'Class'

table.add_columns(IdColumn(column_name='class_id'))""",
            demo='column_definitions', demo_title='Ways to Define Columns',
        ),

        ColumnDoc(
            column=TextFieldColumn,
            summary='Long text, truncated to <code>max_chars</code> with an ellipsis. Newlines render as '
                    '<code>&lt;br&gt;</code> in the table and are restored for the Excel export.',
            kwargs=(KwargDoc('max_chars', '8000', 'Truncate the text beyond this length.'),),
            example="TextFieldColumn(column_name='notes', max_chars=200)",
        ),

        ColumnDoc(
            column=NoHeadingColumn,
            summary='A column with no header, not sortable and with no search box - the base for button and '
                    'action columns. Sets <code>title=\'\'</code>, <code>no_col_search=True</code> and '
                    '<code>orderable: False</code> for you.',
            example="NoHeadingColumn(column_name='actions', field='id', render=[...])",
        ),
    )),

    Section('links', 'Links & Navigation',
            'Columns whose cell is an anchor or a button. The URL is built from a url name with the row\'s '
            'reference value - usually its id - substituted in.', (

        ColumnDoc(
            column=ColumnLink,
            summary='Renders the cell as a link. The URL comes from <code>url_name</code> (or the model\'s '
                    '<code>url_name</code> attribute) with the value of <code>link_ref_column</code> put into it.',
            kwargs=(
                KwargDoc('url_name', 'model.url_name', 'Django url name to reverse for the link.'),
                KwargDoc('link_ref_column', 'column_name', 'Column supplying the value placed in the URL.'),
                KwargDoc('link_html', "'%1%'", 'HTML for the anchor body. <code>%1%</code> is the cell value.'),
                KwargDoc('link_css', 'None', 'class attribute for the anchor.'),
                KwargDoc('var', "'%1%'", 'The placeholder used inside <code>link_html</code>.'),
                KwargDoc('new_tab', 'False', 'Open the link with <code>target="_blank"</code>.'),
                KwargDoc('qs_url', "''", 'Append the current page path, base64 encoded, as this query argument '
                                         'so the linked view can offer a back link.'),
                KwargDoc('align', 'None', 'Cell alignment: <code>left</code>, <code>center</code> or '
                                          '<code>right</code>.'),
            ),
            example="""\
table.add_columns(
    ColumnLink(column_name='name', url_name='company_detail'),
    # field=[ref, text]: the id builds the URL, the name is displayed
    ColumnLink(column_name='company', field=['id', 'name'],
               url_name='company_detail', new_tab=True),
)""",
            demo='column_links', demo_title='Column Links',
            notes='<code>AlignColumnLink</code> is <code>ColumnLink(align=\'center\')</code>. '
                  '<code>XlColumnLink</code> is deprecated - ColumnLink now exports the display text of a '
                  '<code>[ref, text]</code> value to Excel itself.',
        ),

        ColumnDoc(
            column=ViewLink,
            summary='A <code>ColumnLink</code> preset: a small right-aligned <i>View</i> button linking to the '
                    'row, using the row id as the link reference.',
            example="ViewLink(column_name='view', url_name='company_detail')",
        ),

        ColumnDoc(
            column=ModalLink,
            summary='Renders the cell as a link or button opening a <b>django-modals</b> modal for the row. '
                    'Import from <code>django_datatables.columns.modal_columns</code> - it is kept out of the '
                    'columns package so django-modals stays an optional dependency.',
            kwargs=(
                KwargDoc('modal_name', 'model.modal_name', 'Url name of the modal to open.'),
                KwargDoc('field', "'id'", 'The row value passed to the modal. Use <code>[ref, text]</code> to '
                                          'display something other than the reference.'),
                KwargDoc('button_text', 'None', 'Render a fixed button label instead of the cell value.'),
                KwargDoc('css_class', 'None', 'class attribute for the anchor.'),
                KwargDoc('modal_args', '()', 'Extra positional slug arguments for the modal URL.'),
                KwargDoc('row_modify', 'False', 'Let the modal update the row it was opened from.'),
                KwargDoc('base64', 'False', 'Base64 encode the slug.'),
            ),
            example="""\
from django_datatables.columns.modal_columns import ModalLink

ModalLink(column_name='company', field=['id', 'name'],
          modal_name='company_modal')""",
        ),

        ColumnDoc(
            column=ColumnLinkCoalesce,
            summary='A modal link whose display text is the first non-null of several <code>display_fields</code> '
                    '- e.g. show a trading name, falling back to the registered name.',
            kwargs=(
                KwargDoc('url_name', '', 'Url name of the modal to open.'),
                KwargDoc('display_fields', '', 'Fields tried in order; the first non-null is displayed.'),
                KwargDoc('link_ref_column', 'column_name', 'Column supplying the value placed in the URL.'),
                KwargDoc('link_html', "'%1%'", 'HTML for the anchor body.'),
                KwargDoc('link_css', 'None', 'class attribute for the anchor.'),
            ),
            example="""\
from django_datatables.columns.modal_columns import ColumnLinkCoalesce

ColumnLinkCoalesce(column_name='name', field='id',
                   display_fields=['trading_name', 'name'],
                   url_name='company_modal')""",
        ),
    )),

    Section('dates', 'Dates',
            'A model <code>DateField</code> or <code>DateTimeField</code> added by name becomes a '
            '<code>DateColumn</code> automatically - use these explicitly to change the format. All three '
            'export a real date to Excel, not the formatted string.', (

        ColumnDoc(
            column=DateColumn,
            summary='Renders a date with <code>date_str</code>, by default <code>dd/mm/yyyy</code>. Override '
                    '<code>get_date_format()</code> for a per-user or locale format, and '
                    '<code>get_date_format_xl()</code> to match it in the Excel export.',
            kwargs=(KwargDoc('date_str', "'%d/%m/%Y'", 'strftime format. A class attribute, so it can be set '
                                                       'per column or on a subclass.'),),
            example="""\
table.add_columns(
    DateColumn('date_entered', column_name='Date'),
    DateColumn('date_entered', column_name='us_date', date_str='%m/%d/%Y'),
)

class UsDate(DateColumn):
    date_str = '%m/%d/%Y'""",
            demo='date_filter', demo_title='Date Filter',
            notes='<code>YearMonthColumn</code> is a hidden <code>MonthColumn</code> - a <code>.</code> '
                  'prefixed column_name is the preferred spelling.',
        ),

        ColumnDoc(
            column=DateTimeColumn,
            summary='A <code>DateColumn</code> that also renders the time as <code>HH:MM</code>.',
            kwargs=(KwargDoc('date_str', "'%d/%m/%Y'", 'strftime format for the date part; the time is always '
                                                       '<code>%H:%M</code>.'),),
            example="DateTimeColumn('created', column_name='Created')",
        ),

        ColumnDoc(
            column=MonthColumn,
            summary="Renders a date as <code>'YYYY MM'</code> - useful as a hidden column to group or sort rows "
                    'by month.',
            example="""\
table.add_columns(
    MonthColumn(column_name='month', field='date'),
    MonthColumn(column_name='.sort_month', field='date'),   # hidden, for sorting
)""",
        ),
    )),

    Section('currency', 'Currency',
            'Money columns are right aligned and export to Excel as numbers with a currency number format. '
            'Choose a server-rendered column for a fixed 2dp format, or <code>LocaleCurrencyColumn</code> to '
            'let the browser format the value for a locale.', (

        ColumnDoc(
            column=CurrencyColumn,
            summary='Right aligned, rendered server-side to two decimal places. <code>divisor</code> scales the '
                    'stored value first; the default of 1 suits a value already held in whole units.',
            kwargs=(KwargDoc('divisor', '1', 'Divide the stored value by this before rendering. A class '
                                             'attribute.'),),
            example="CurrencyColumn(column_name='amount', field='amount')",
        ),

        ColumnDoc(
            column=CurrencyPenceColumn,
            summary='A <code>CurrencyColumn</code> for a value stored in pennies (<code>divisor = 100</code>).',
            example="CurrencyPenceColumn(column_name='amount', field='amount')",
            demo='aggregations_horizontal', demo_title='Aggregations (Horizontal)',
        ),

        ColumnDoc(
            column=ZeroPenceColumn,
            summary='A <code>CurrencyPenceColumn</code> that renders <code>0.00</code> rather than an empty cell '
                    'when the value is null or missing.',
            example="ZeroPenceColumn(column_name='amount', field='amount')",
        ),

        ColumnDoc(
            column=LocaleCurrencyColumn,
            summary='Formatted in the browser by the datatables <code>currency</code> render function, so the '
                    'thousands separator and symbol placement follow the locale. Subclass it and set '
                    '<code>default_currency_code</code> / <code>default_locale</code> from your site config to '
                    'avoid passing them every time.',
            kwargs=(
                KwargDoc('pennies', 'False', 'True when the stored value is already in whole units.'),
                KwargDoc('currency_code', "'GBP'", 'ISO currency code. The table\'s <code>currency_code</code> '
                                                   'attribute is used when this is not given.'),
                KwargDoc('locale', "'en_GB'", 'Locale used to format the number.'),
                KwargDoc('decimal_places', '2', 'Decimal places displayed.'),
            ),
            example="""\
LocaleCurrencyColumn(column_name='amount', field='amount',
                     currency_code='USD', locale='en_US')""",
        ),

        ColumnDoc(
            column=MultiCurrencyColumn,
            summary='A <code>LocaleCurrencyColumn</code> where each row carries its own currency: pass '
                    '<code>field=[amount, currency]</code>. Override <code>get_symbols()</code> to map a currency '
                    'onto the symbol used in the Excel number format.',
            kwargs=(
                KwargDoc('field', '', 'Two fields: the amount and the row\'s currency.'),
                KwargDoc('pennies', 'False', 'True when the stored amount is already in whole units.'),
            ),
            example="""\
class Money(MultiCurrencyColumn):

    @classmethod
    def get_symbols(cls):
        return {'GBP': '£', 'USD': '$'}

Money(column_name='amount', field=['amount', 'currency'])""",
        ),
    )),

    Section('booleans', 'Booleans & Choices',
            'A model <code>BooleanField</code> becomes a <code>BooleanColumn</code> automatically, and an '
            'integer field with <code>choices</code> becomes a <code>ChoiceColumn</code> - add these explicitly '
            'to control what is rendered.', (

        ColumnDoc(
            column=BooleanColumn,
            summary='Renders a boolean as <code>choices = [true_value, false_value, none_value]</code>. Pass '
                    '<code>replace</code> to render each choice as HTML instead - the value stays as the choice '
                    'text, so filters and the Excel export still read cleanly.',
            kwargs=(
                KwargDoc('choices', "['true', 'false', None]", 'Values for true, false and null.'),
                KwargDoc('replace', 'None', 'HTML rendered client-side in place of each choice.'),
            ),
            example="""\
BooleanColumn(column_name='dissolved', choices=['Yes', 'No', ''])""",
        ),

        ColumnDoc(
            column=TickColumn,
            summary='A <code>BooleanColumn</code> preset: a green tick for true, blank for false.',
            example="TickColumn(column_name='dissolved')",
        ),

        ColumnDoc(
            column=ChoiceColumn,
            summary='Maps a stored value onto its label. When the column is listed in the table\'s '
                    '<code>edit_fields</code> it edits in place as a dropdown of its choices.',
            kwargs=(KwargDoc('choices', '', 'Sequence of <code>(value, label)</code> pairs.'),),
            example="""\
ChoiceColumn('title', choices=((0, 'Mr'), (1, 'Mrs'), (2, 'Miss')))""",
            demo='inline_editing', demo_title='Inline Editing',
        ),
    )),

    Section('json', 'JSON Fields',
            'Read one key out of a model <code>JSONField</code>. The field itself may be null - both columns '
            'cope.', (

        ColumnDoc(
            column=JsonBooleanColumn,
            summary='Renders a boolean key from a JSON field as a tick or blank.',
            kwargs=(
                KwargDoc('json_key', '', 'Key read from the JSON field.'),
                KwargDoc('field', "'options'", 'The model\'s JSONField.'),
                KwargDoc('choices', "['Yes', 'No']", 'Values for true and false.'),
            ),
            example="""\
JsonBooleanColumn(column_name='newsletter', json_key='newsletter',
                  field='options')""",
            demo='server_side_json', demo_title='JSON Column Filter',
        ),

        ColumnDoc(
            column=JsonKeyColumn,
            summary='Renders any key from a JSON field as-is.',
            kwargs=(KwargDoc('json_key', '', 'Key read from the JSON field.'),),
            example="""\
JsonKeyColumn(column_name='nickname', field='options',
              json_key='nickname')""",
        ),
    )),

    Section('relations', 'Relations',
            'Rendering a to-many relation needs one extra query rather than a join, so the table stays one row '
            'per object.', (

        ColumnDoc(
            column=ManyToManyColumn,
            summary='Renders a many-to-many or reverse foreign key as a list of related values, looked up '
                    'client-side so the same lookup serves the table, its tag filter and the Excel export. '
                    'The relation is fetched once per request, not once per row. <code>model</code> is '
                    'required - <code>add_columns</code> supplies it when the column is declared on the model.',
            kwargs=(
                KwargDoc('field', '', 'Path through the relation to the displayed value, e.g. '
                                      "<code>'tags__tag'</code>."),
                KwargDoc('html', "' %1% '", 'HTML rendered for each related value - a badge, for instance.'),
                KwargDoc('blank', 'None', 'Text rendered when a row has no related rows.'),
                KwargDoc('sort_results', 'False', 'Sort each row\'s values.'),
                KwargDoc('query_manager', "'objects'", 'Manager used to fetch the relation.'),
                KwargDoc('filter', 'None', 'Filter kwargs limiting the related rows.'),
                KwargDoc('exclude', 'None', 'Exclude kwargs for the related rows.'),
                KwargDoc('lookup', 'from the db', 'Fixed <code>(pk, label)</code> list. Supplying it stops the '
                                                  'lookup being refreshed from the database each render.'),
            ),
            example="""\
table.add_columns(
    ManyToManyColumn(column_name='tags', field='tags__tag',
                     html='<span class="badge badge-primary">%1%</span>',
                     blank='No tags', sort_results=True),
)
table.add_js_filters('tag', 'tags')""",
            demo='tag_columns', demo_title='Tags & Badges',
        ),
    )),

    Section('actions', 'Actions & Selection',
            'Columns holding controls rather than data. All of them are left out of the Excel and clipboard '
            'exports, since their cell value is only the row id.', (

        ColumnDoc(
            column=SelectColumn,
            summary='A checkbox per row, with select-all and clear buttons in the header. Pair it with the '
                    '<code>selected</code> filter to narrow the table to ticked rows, and '
                    '<code>send_selected</code> to post the ticked ids to a view method.',
            kwargs=(
                KwargDoc('field', "'id'", 'Value used as the checkbox name.'),
                KwargDoc('title', 'select buttons', "Pass <code>''</code> for no header buttons."),
            ),
            example="""\
table.add_columns(
    SelectColumn(hidden=True),
    'name',
)
table.add_js_filters('selected', 'SelectColumn')""",
            demo='selection', demo_title='Row Selection',
            notes='<code>SelectColumnNoTitle</code> is <code>SelectColumn(title=\'\')</code>, which is the '
                  'preferred spelling.',
        ),

        ColumnDoc(
            column=MenuColumn,
            summary='Renders a <b>django-tab-menus</b> menu in every row. The menu is rendered once and the '
                    'row id substituted per row, so <code>DUMMY_ID</code> in a url kwarg becomes that row\'s id.',
            kwargs=(
                KwargDoc('menu', '', 'An <code>HtmlMenu</code>. Positional, not a keyword.'),
                KwargDoc('field', '', 'Row value substituted for <code>DUMMY_ID</code>. A second field '
                                      'substitutes <code>DUMMY_ID2</code>.'),
            ),
            example="""\
MenuColumn(column_name='menu', field='id',
           menu=HtmlMenu(self.request, 'button_group').add_items(
               ('company_detail', 'View', {'url_kwargs': {'pk': DUMMY_ID}}),
           ))""",
        ),

        ColumnDoc(
            column=MultiMenuColumnBase,
            summary='Base class for a column rendering <i>one of several</i> menus, chosen per row - e.g. a '
                    'different button set for an archived row. Subclass it and build the menus with '
                    '<code>add_menu(row_id, *items)</code> inside <code>col_setup()</code>, which is late enough '
                    'for the table and its view to be attached.',
            example="""\
class RowMenu(MultiMenuColumnBase):

    def col_setup(self):
        for company in Company.objects.all():
            self.add_menu(company.id, self.some_menu('company_detail'))
        super().col_setup()""",
        ),
    )),

    Section('computed', 'Computed Values',
            'Columns whose value is calculated rather than read straight from a field. For a value the database '
            'can compute, an <code>annotations</code> kwarg on <code>ColumnBase</code> is cheaper than any of '
            'these.', (

        ColumnDoc(
            column=LambdaColumn,
            summary='Passes the field value through a callable.',
            kwargs=(KwargDoc('lambda_function', '', 'Callable taking the field value, returning the cell value.'),),
            example="""\
LambdaColumn(column_name='initials', field='first_name',
             lambda_function=lambda v: v[0].upper() if v else '')""",
        ),

        ColumnDoc(
            column=CallableColumn,
            summary='Calls a method on the model. The fields the method needs are declared as '
                    '<code>parameters</code> so the query fetches them, and the method is called on a '
                    'reconstructed object per row. Adding a model method by name creates one of these for you.',
            kwargs=(KwargDoc('parameters', '', 'Fields the method reads, fetched for each row.'),),
            example="""\
class Person(models.Model):
    def id_and_title(self):
        return f'{self.id} - {self.title}'

    class Datatable(DatatableModel):
        id_and_title = {'parameters': ['id', 'title']}

# then, in setup_table:
table.add_columns('id_and_title')""",
            demo='column_parameters', demo_title='Column Parameters',
        ),

        ColumnDoc(
            column=GroupedColumn,
            summary='Base class for a column whose values are fetched once for the whole page and then looked up '
                    'per row. Subclass it, set <code>page_key</code>, and build the lookup in '
                    '<code>initial_column_data()</code> - useful when the value cannot be reached with a join.',
            example="""\
class LatestPayment(GroupedColumn):
    page_key = 'latest_payment'

    @staticmethod
    def initial_column_data(_request):
        return dict(Payment.objects.values_list('company_id', 'amount'))""",
        ),
    )),

    Section('export', 'Excel Export',
            'The <code>ExcelDownload</code> mixin writes what each column\'s <code>excel()</code> returns, and '
            'applies its <code>xl_style()</code> to the cell. <code>CurrencyColumn</code>, '
            '<code>DateColumn</code>, <code>ManyToManyColumn</code>, <code>ChoiceColumn</code> and '
            '<code>ColumnLink</code> already handle their own values; this one is for when <i>your</i> column '
            'renders HTML server-side.', (

        ColumnDoc(
            column=ExcelDatatableColumn,
            summary='Exports the plain text of an HTML cell value - tags are stripped and the remaining text '
                    'joined with commas.',
            example="""\
class Tags(ExcelDatatableColumn):

    def row_result(self, data_dict, _page_results):
        return '<span class="badge">Red</span><span class="badge">Blue</span>'

# exports as: Red, Blue""",
        ),
    )),
)


def documented_columns():
    """Every column class with an entry, in page order."""
    return [doc.column for section in COLUMN_SECTIONS for doc in section.columns]

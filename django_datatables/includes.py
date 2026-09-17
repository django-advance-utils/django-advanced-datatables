from importlib.metadata import PackageNotFoundError

from ajax_helpers.html_include import SourceBase, pip_version

try:
    version = pip_version('django-filtered-datatables')
except PackageNotFoundError:
    version = 'local'


class DataTables(SourceBase):
    cdn_path = 'cdn.datatables.net/v/dt/dt-3.0.2/rg-2.0.0/rr-2.0.0/'
    filename = 'datatables.min'
    static_path = 'django_datatables/datatables/'
    cdn_js_path = ''
    cdn_css_path = ''


class FilteredDataTables(SourceBase):
    static_path = 'django_datatables/'
    js_filename = 'filtered-datatable.js'
    css_filename = 'datatables.css'


# DataTable.datetime() uses Moment to parse formatted dates for sorting
class Moment(SourceBase):
    cdn_path = 'cdnjs.cloudflare.com/ajax/libs/moment.js/2.30.1/'
    js_filename = 'moment.min.js'
    cdn_js_path = ''


class JSpreadsheet(SourceBase):
    static_path = 'django_datatables/jspreadsheet/'
    css_path = js_path = ''
    js_filename = 'index.js'
    css_filename = 'jspreadsheet.css'


class JSuites(SourceBase):
    static_path = 'django_datatables/jsuites/'
    css_path = js_path = ''
    js_filename = 'jsuites.js'
    css_filename = 'jsuites.css'


class Spreadsheet(SourceBase):
    static_path = 'django_datatables/'
    js_filename = 'spreadsheet.js'


packages = {
    'datatable': [DataTables, FilteredDataTables, Moment],
    'JSpreadsheet': [JSpreadsheet, JSuites]
}

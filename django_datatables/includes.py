from importlib.metadata import PackageNotFoundError

from ajax_helpers.html_include import SourceBase, pip_version

try:
    version = pip_version('django-advanced-datatables')
except PackageNotFoundError:
    version = 'local'


# Every asset is served from this package's static files; no class sets cdn_path, so html_include never
# points at a CDN, even when called with cdn=True.


class DataTables(SourceBase):
    filename = 'datatables.min'
    static_path = 'django_datatables/datatables/'


class FilteredDataTables(SourceBase):
    static_path = 'django_datatables/'
    js_filename = 'filtered-datatable.js'
    css_filename = 'datatables.css'
    legacy_js = ['runtime.js', 'filtered_datatables_legacy.js']


class Moment(SourceBase):
    # moment.js 2.8.4
    static_path = 'django_datatables/moment/'
    js_filename = 'moment.min.js'


class MomentDatatable(SourceBase):
    # DataTables sorting plug-in datetime-moment.js (as served at cdn.datatables.net/plug-ins/1.10.16/)
    static_path = 'django_datatables/datatables-plugins/'
    js_filename = 'datetime-moment.js'


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
    'datatable': [DataTables, FilteredDataTables, Moment, MomentDatatable],
    'JSpreadsheet': [JSpreadsheet, JSuites]
}

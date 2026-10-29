from django.template.loader import render_to_string

from django_datatables.datatables import DatatableError, RefusedColumnError


class ColourRows:

    def __init__(self, datatable, colour_dict):
        if not isinstance(colour_dict, list):
            colour_dict = [colour_dict]
        self.colour_dict = []
        for c in colour_dict:
            try:
                c['column'] = datatable.find_column(c['column'])[1]
            except RefusedColumnError:
                continue
            except DatatableError:
                pass
            self.colour_dict.append(c)
        self.datatable = datatable

    def render(self):
        return render_to_string('datatables/plugins/colour_rows.html',
                                {'datatable': self.datatable, 'colour_dict': self.colour_dict})

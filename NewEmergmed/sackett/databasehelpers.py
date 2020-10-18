from django.db.models.query import QuerySet
from pprint import PrettyPrinter


def dprint(obj, stream=None, indent=1, width=80, depth=None):
    # Catch any Django QuerySets that might get passed in
    if isinstance(obj, QuerySet):
        # Convert it to a list of dictionaries
        obj = [i.__dict__ for i in obj]
    else:
        if getattr(obj, '__dict__', None):
            obj = obj.__dict__

    # Pass everything through pprint in the typical way
    printer = PrettyPrinter(stream=stream, indent=indent, width=width, depth=depth)
    printer.pprint(obj)


def get_field_max_length(model, field_name):
    fields = [f for f in model._meta.get_fields() if f.name == field_name]

    if fields is not None and len(fields) > 0:
        field = fields[0]
    else:
        field = None

    try:
        return field.max_length
    except AttributeError:
        return -1

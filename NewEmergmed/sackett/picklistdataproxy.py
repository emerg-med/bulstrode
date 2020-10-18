from django.utils.translation import get_language
import itertools
from .models import PickListData


class PickListDataProxy:
    @staticmethod
    def find_by_description(table_number, search_string):
        lang_code = get_language()
        startswith = [(x.code, x.description)
                      for x in PickListData.objects
                      .filter(table_number=table_number)
                      .filter(language_code=lang_code)
                      .filter(description__istartswith=search_string)
                      .order_by('description')]
        contains = [(x.code, x.description)
                    for x in PickListData.objects
                    .filter(table_number=table_number)
                    .filter(language_code=lang_code)
                    .filter(description__icontains=search_string)
                    .order_by('description')
                    if not x.description.upper().startswith(search_string.upper())]
        return startswith + contains


    @staticmethod
    def load_for_choice_field(table_number, extra_fields=(), extra_field_converters=()):
        lang_code = get_language()
        return [(x.code, x.description) +
                tuple(PickListDataProxy.map_fields(extra_fields, extra_field_converters, x))
                for x in PickListData.objects
                .filter(table_number=table_number)
                .filter(language_code=lang_code)
                .order_by('sort1', 'sort2', 'description')]

    @staticmethod
    def load_raw_for_choice_field(table_number):
        lang_code = get_language()
        return list(PickListData.objects\
                    .filter(table_number=table_number)\
                    .filter(language_code=lang_code)
                    .order_by('sort1', 'sort2', 'description'))

    @staticmethod
    def lookup_code(table_number, code):
        lookup_result = PickListDataProxy.lookup_code_raw(table_number, code)
        if lookup_result is None:
            return ''
        return lookup_result.description

    @staticmethod
    def lookup_code_raw(table_number, code):
        lang_code = get_language()
        return PickListData.objects.filter(table_number=table_number).filter(code=code)\
            .filter(language_code=lang_code).first()

    @staticmethod
    def map_fields(field_list, field_converter_list, obj):
        if field_list is None or len(field_list) < 1:
            return ()
        return [c(getattr(obj, f))
                for f, c in itertools.zip_longest(field_list, field_converter_list, fillvalue=lambda x: x)]

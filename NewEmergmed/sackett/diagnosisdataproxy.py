from django.utils.translation import get_language
from .models import DiagnosisData


class DiagnosisDataProxy:
    @staticmethod
    def clean_terms_string(terms_string):
        return terms_string\
            .replace(':', ' ')\
            .replace('(', ' ')\
            .replace(')', ' ')\
            .replace('/', ' ')\
            .replace('\'', ' ')\
            .replace(',', ' ')\
            .lower()

    @staticmethod
    def lookup_by_terms_string(terms_string, max_results=15, max_partials_per_keyword=10):
        matched_diagnoses = {}
        match_weighting = 3
        contains_weighting = 1
        lang_code = get_language()
        for term in DiagnosisDataProxy.clean_terms_string(terms_string).split():
            lower_term = term.lower()
            for diagnosis in DiagnosisData.objects.filter(search_terms__term=lower_term)\
                    .filter(language_code=lang_code):
                if matched_diagnoses.get(diagnosis.id, None) is None:
                    matched_diagnoses[diagnosis.id] = (diagnosis, match_weighting)
                else:
                    current = matched_diagnoses[diagnosis.id]
                    matched_diagnoses[diagnosis.id] = (diagnosis, current[1] + match_weighting)

            # also match terms that contain the supplied string, with a lesser weighting:
            partial_count = 0
            for diagnosis in DiagnosisData.objects.filter(search_terms__term__contains=lower_term)\
                    .filter(language_code=lang_code):
                if partial_count >= max_partials_per_keyword:
                    break

                partial_count += 1

                if matched_diagnoses.get(diagnosis.id, None) is None:
                    matched_diagnoses[diagnosis.id] = (diagnosis, contains_weighting)
                else:
                    current = matched_diagnoses[diagnosis.id]
                    matched_diagnoses[diagnosis.id] = (diagnosis, current[1] + contains_weighting)

        return sorted([v for v in matched_diagnoses.values()],
                      key=lambda x: (0-x[1], x[0].sort1, x[0].sort2, x[0].sort3, x[0].description))[:max_results]

    @staticmethod
    def lookup_code(code):
        lookup_result = DiagnosisDataProxy.lookup_code_raw(code)
        if lookup_result is None:
            return ''
        return lookup_result.description

    @staticmethod
    def lookup_code_raw(code):
        return DiagnosisData.objects.filter(code=code).filter(language_code=get_language()).first()

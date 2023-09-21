import csv
import mmap
import multiprocessing as mp
import os
from .diagnosisdataproxy import DiagnosisDataProxy
from .models import DiagnosisData, DiagnosisDataSearchTerm
from NewEmergmed import settings


class DiagnosisDataImporter:
    column_name_mappings = {'ECDS_Group1': 'group1',
                            'ECDS_Group2': 'group2',
                            'ECDS_Group3': 'group3',
                            'Sort1': 'sort1',
                            'Sort2': 'sort2',
                            'Sort3': 'sort3',
                            'ECDS_Description': 'description',
                            'SNOMED_Code': 'code',
                            'Inj_Flag': 'injury',
                            'AEC_Flag': 'aec',
                            'NotifiableDisease_Flag': 'notifiable_disease'
                            }

    @staticmethod
    def start_background(lang_code):
        with open("/tmp/sackett-diag-status.txt", "wb") as f:
            f.write(bytes([0, 0, 0, 0, 0, 0, 0, 0, 0]))     # action, rows loaded (x4), rows written (x4)

        p = mp.Process(target=DiagnosisDataImporter.do_import, args=(lang_code,))
        p.start()

    @staticmethod
    def update_status(action=-1, rows_loaded=-1, rows_written=-1):
        with open("/tmp/sackett-diag-status.txt", "r+b") as f:
            status_map = mmap.mmap(f.fileno(), 0)
            if action > -1:
                status_map.seek(0)
                status_map.write_byte(action)

            if rows_loaded > -1:
                status_map.seek(1)
                status_map.write(rows_loaded.to_bytes(4, 'little'))

            if rows_written > -1:
                status_map.seek(5)
                status_map.write(rows_written.to_bytes(4, 'little'))

    @staticmethod
    def read_from_file(filename):
        return_val = []

        with open(filename, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=',', quotechar='"', )
            rows_loaded = 0

            for row in reader:
                return_val.append(row)
                rows_loaded += 1
                if rows_loaded % 100 == 0:
                    DiagnosisDataImporter.update_status(rows_loaded=rows_loaded)

            DiagnosisDataImporter.update_status(rows_loaded=rows_loaded)    # final total

        return return_val

    @staticmethod
    def import_to_db(lang_code, filename):
        DiagnosisDataImporter.update_status(action=1)   # TODO: magic constant: 1 = loading rows

        rows = DiagnosisDataImporter.read_from_file(filename)

        DiagnosisDataImporter.update_status(action=2)   # TODO: magic constant: 2 = writing rows

        rows_written = 0

        for row in rows:
            search_terms = []       # should be set later but just in case
            diagnosis = DiagnosisData()

            # enforce some sensible defaults
            diagnosis.aec = False
            diagnosis.injury = False
            diagnosis.notifiable_disease = False

            # TODO use get_field_max_length to enforce database field length constraints - report errors and/or truncate
            for key in row.keys():
                if len(row[key].strip()) > 0:       # empty values can be ignored as they will be null in the db
                    field_val = row[key].strip()
                    col_name = DiagnosisDataImporter.column_name_mappings.get(key.strip(), '')
                    if col_name != '':
                        if col_name == 'notifiable_disease' or col_name == 'injury' or col_name == 'aec':
                            field_val = (field_val == '1')    # fixup bool values since bool('0') == True
                        setattr(diagnosis, col_name, field_val)
                    elif key == 'ECDS_SearchTerms':
                        search_terms = DiagnosisDataImporter.get_or_create_search_terms(field_val)

            diagnosis.language_code = lang_code
            diagnosis.save()

            for search_term in search_terms:
                diagnosis.search_terms.add(search_term)

            diagnosis.save()
            rows_written += 1

            if rows_written % 100 == 0:
                DiagnosisDataImporter.update_status(rows_written=rows_written)

        DiagnosisDataImporter.update_status(rows_written=rows_written)      # final total

    @staticmethod
    def get_or_create_search_terms(search_terms_string):
        search_terms = []

        # remove punctuation
        for search_term_string in DiagnosisDataProxy.clean_terms_string(search_terms_string).split():
            search_term = DiagnosisDataSearchTerm.objects.filter(term=search_term_string).first()

            if search_term is None:
                search_term = DiagnosisDataSearchTerm()
                search_term.term = search_term_string
                search_term.save()

            search_terms.append(search_term)

        return search_terms

    @staticmethod
    def do_import(lang_code):
        DiagnosisDataImporter.import_to_db(lang_code, os.path.join(settings.BASE_DIR,
                                                                   'picklistdatatables',
                                                                   lang_code,
                                                                   'EmCareDiagnosis.csv'))

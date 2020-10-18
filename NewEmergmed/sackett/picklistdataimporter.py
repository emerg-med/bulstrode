import csv
import mmap
import multiprocessing as mp
import os
from .models import PickListData
from .enumerations import PickListTableTypes
from NewEmergmed import settings


class PickListDataImporter:
    column_name_mappings = {'ECDS_Group': 'group',
                            'ECDS_Description': 'description',
                            'ECDS_Code': 'code',
                            'Sort1': 'sort1',
                            'Sort2': 'sort2',
                            'Injury_Flag': 'bool1',
                            'Male_Flag': 'bool2',
                            'Female_Flag': 'bool3',
                            }

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
                    PickListDataImporter.update_status(table_rows_loaded=rows_loaded)

            PickListDataImporter.update_status(table_rows_loaded=rows_loaded)   # final total

        return return_val

    @staticmethod
    def read_from_ods_file(filename):
        return_val = []

        with open(filename, newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile, delimiter=',', quotechar='"', )
            rows_loaded = 0

            for row in reader:
                return_val.append(row)
                rows_loaded += 1
                if rows_loaded % 100 == 0:
                    PickListDataImporter.update_status(table_rows_loaded=rows_loaded)

            PickListDataImporter.update_status(table_rows_loaded=rows_loaded)   # final total

        return return_val

    @staticmethod
    def import_to_db(table_number, lang_code, filename):
        PickListDataImporter.update_status(action=1)   # TODO: magic constant: 1 = loading rows

        rows = PickListDataImporter.read_from_file(filename)

        PickListDataImporter.update_status(action=2)   # TODO: magic constant: 2 = writing rows

        rows_written = 0

        for row in rows:
            table_data = PickListData()
            # print('----')

            for key in row.keys():
                # print(str(key) + ": '" + str(row[key]) + "'")
                if len(row[key].strip()) > 0:       # empty values can be ignored as they will be null in the db
                    colname = PickListDataImporter.column_name_mappings.get(key.strip())

                    if colname is None:
                        continue

                    fieldval = row[key].strip()
                    if colname == 'bool1':
                        fieldval = (fieldval == '1')    # fixup bool values since bool('0') == True
                    setattr(table_data, colname, fieldval)

            table_data.table_number = table_number
            table_data.language_code = lang_code
            # dprint(table_data)
            table_data.save()
            rows_written += 1

            if rows_written % 100 == 0:
                PickListDataImporter.update_status(table_rows_written=rows_written)

        PickListDataImporter.update_status(table_rows_written=rows_written)      # final total

    @staticmethod
    def import_ods_to_db(table_number, lang_code, filename):
        PickListDataImporter.update_status(action=1)   # TODO: magic constant: 1 = loading rows

        rows = PickListDataImporter.read_from_ods_file(filename)

        PickListDataImporter.update_status(action=2)   # TODO: magic constant: 2 = writing rows

        rows_written = 0

        for row in rows:
            table_data = PickListData()

            table_data.code = row[0]
            table_data.description = row[1]
            table_data.table_number = table_number
            table_data.language_code = lang_code
            table_data.save()
            rows_written += 1

            if rows_written % 100 == 0:
                PickListDataImporter.update_status(table_rows_written=rows_written)

        PickListDataImporter.update_status(table_rows_written=rows_written)      # final total

# TODO for each table, try/catch and rollback; also, check for presence of rows
# in the db with corresponding table number

    @staticmethod
    def import_all(lang_code):
        PickListDataImporter.update_status(total_tables=len(PickListTableTypes))
        table_count = 0
        for table_type in PickListTableTypes:
            # print(str(table_type.value), " ", table_type.name)
            if table_type.value < 900:
                PickListDataImporter.import_to_db(table_type.value, lang_code, os.path.join(settings.BASE_DIR,
                                                                                            'picklistdatatables',
                                                                                            lang_code,
                                                                                            table_type.name + '.csv'))
            else:
                PickListDataImporter.import_ods_to_db(table_type.value, lang_code,
                                                      os.path.join(settings.BASE_DIR,
                                                                   'picklistdatatables',
                                                                   lang_code,
                                                                   'org',
                                                                   table_type.name + '.csv'))
            table_count += 1
            PickListDataImporter.update_status(completed_tables=table_count, table_rows_loaded=0, table_rows_written=0)

    @staticmethod
    def start_background(lang_code):
        with open("/tmp/sackett-pick-status.txt", "wb") as f:
            f.write(bytes([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]))
            # action, total tables, completed tables, table rows (x4), saved table rows (x4)
        p = mp.Process(target=PickListDataImporter.import_all, args=(lang_code,))
        p.start()

    @staticmethod
    def update_status(action=-1, total_tables=-1, completed_tables=-1, table_rows_loaded=-1, table_rows_written=-1):
        with open("/tmp/sackett-pick-status.txt", "r+b") as f:
            status_map = mmap.mmap(f.fileno(), 0)
            if action > -1:
                status_map.seek(0)
                status_map.write_byte(action)

            if total_tables > -1:
                status_map.seek(1)
                status_map.write_byte(total_tables)

            if completed_tables > -1:
                status_map.seek(2)
                status_map.write_byte(completed_tables)

            if table_rows_loaded > -1:
                status_map.seek(3)
                status_map.write(table_rows_loaded.to_bytes(4, 'little'))

            if table_rows_written > -1:
                status_map.seek(7)
                status_map.write(table_rows_written.to_bytes(4, 'little'))

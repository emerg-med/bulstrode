import os
import json
from NewEmergmed import settings


def get_available_templates():
    template_path = os.path.join(settings.BASE_DIR, 'templates', 'sackett', 'zone')
    template_files = [f for f in os.listdir(template_path) if f.lower().endswith('.json')]
    available_templates = [json_load(os.path.join(template_path, t)) for t in template_files]
    available_templates.sort(key=lambda x: x['name'])
    return available_templates


def get_bed_list(template_name):
    return []


def json_load(filename):
    file = open(filename)
    obj = json.load(file)
    file.close()
    return obj

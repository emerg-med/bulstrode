try:
    import xml.etree.cElementTree as eT     # try to import the faster C-based library
except ImportError:
    import xml.etree.ElementTree as eT
import json
from django.db import models


# convert nested data to or from an xml string in the database
# xml_tags is a nested structure specifying how to convert the Python data object into xml, e.g.:
# Python object: { 'diagnoses': [{'index': 1, 'code': 'abcde', 'mod': 9}, {'index': 2, 'code': 'fghij', 'mod': 6}],
#                  'injuries': ['leg', 'arm', 'head'],
#                  'details': {'name': ['Rita', 'Jones'], 'age': 35} }
# xml_tags: ('record',
#            {'diagnoses': ('diags', ('diag', {'index': 'idx', 'code': 'cde', 'mod': 'mod'} ) ),
#             'injuries': ('injs', 'inj'),
#             'details': ('dtls', {'name': ('name_parts', 'name_part'), 'age': 'age'})
#            }
#           )
# that is: a tuple of (tag, definition) for each node, where definition is recursively either
#   a dictionary of { key: definition, ... }, to match a dictionary in the data,
#   a tuple of (item tag, definition) to match a list in the data, where tag is a collection of item tag, or
#   a string 'tag name' to match any other type, on which str() is called
# resultant xml: <record>
#                 <diags>
#                  <diag><idx>1</idx><cde>abcde</cde><mod>9</mod></diag>
#                  <diag><idx>2</idx><cde>fghij</cde><mod>6</mod></diag>
#                 </diags>
#                 <injs>
#                  <inj>leg</inj>
#                  <inj>arm</inj>
#                  <inj>head</inj>
#                 </injs>
#                 <dtls><name_parts><name_part>Rita</name_part><name_part>Jones</name_part></name_parts><age>35</age></dtls>
#                </record>
class MappedXmlField():
    # converts a python object (probably a collection of some sort) into an XML node according to the node definition
    # TODO very optimistic coding here at the moment - throw some errors when the data and the schema don't match
    @staticmethod
    def build_node(node_def, data, populate_fully=False):
        if isinstance(node_def, tuple):
            if isinstance(node_def[1], dict):
                node = eT.Element(node_def[0])
                for key in data:        # TODO assuming data is also a dictionary
                    child_node_def = node_def[1][key]       # TODO ...and that the keys match
                    node.append(MappedXmlField.build_node(child_node_def, data[key]))
                if populate_fully:
                    # add blank entries for every remaining node tag in the result:
                    for node_def_key in node_def[1]:
                        if node_def_key not in data:
                            child_node_def = node_def[1][node_def_key]
                            node.append(MappedXmlField.build_node(child_node_def, None))
            else:
                node = eT.Element(node_def[0])
                item_child_node_def = node_def[1]
                for item in data:       # TODO assuming data is a list
                    node.append(MappedXmlField.build_node(item_child_node_def, item))
        else:
            node = eT.Element(node_def)
            node.text = '' if data is None else str(data)

        return node

    # converts an XML node into a python object according to the node definition; inverse of __build_node().
    @staticmethod
    def build_python_object(node_def, node, populate_fully=False):
        return MappedXmlField.build_python_object_and_key(node_def, node, populate_fully)[1]

    @staticmethod
    def build_python_object_and_key(node_def, node, populate_fully=False):
        if isinstance(node_def, tuple):
            key = node_def[0]
            if isinstance(node_def[1], dict):
                obj = {}
                if populate_fully:
                    # first add blank entries for every possible key in the result:
                    for node_def_key in node_def[1]:
                        child_node_def = node_def[1][node_def_key]
                        child_key, child_obj = MappedXmlField.build_python_object_and_key(child_node_def,
                                                                                          eT.Element(node_def_key))
                        obj[child_key] = child_obj

                # now process the actual XML
                for child_node in node:
                    child_node_def = node_def[1][child_node.tag]
                    child_key, child_obj = MappedXmlField.build_python_object_and_key(child_node_def, child_node)
                    obj[child_key] = child_obj
            else:
                obj = []
                item_child_node_def = node_def[1]
                for child_node in node:
                    child_key, child_obj = MappedXmlField.build_python_object_and_key(item_child_node_def, child_node)
                    obj.append(child_obj)
        else:
            key = node_def
            obj = node.text

        return key, obj

    # takes a node definition and inverts it to make it suitable for use in __build_python_object()
    @staticmethod
    def invert_node_definition(node_def):
        if isinstance(node_def, tuple):
            new_node_def = (node_def[0], MappedXmlField.invert_node_definition(node_def[1]))
        elif isinstance(node_def, dict):
            new_node_def = {}

            for node_def_key in node_def:
                sub_node_def = node_def[node_def_key]

                if isinstance(sub_node_def, tuple):
                    new_node_def[sub_node_def[0]] = (node_def_key,
                                                     MappedXmlField.invert_node_definition(sub_node_def[1]))
                else:
                    new_node_def[node_def[node_def_key]] = node_def_key         # exchange key and value
        else:
            new_node_def = ''

        return new_node_def


class XmlCharField(models.CharField):
    def __init__(self, xml_tags, populate_fully=False, *args, **kwargs):
        self.node_def = xml_tags
        self.populate_fully = populate_fully
        self.inverse_node_def = MappedXmlField.invert_node_definition(xml_tags)
        super(XmlCharField, self).__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super(XmlCharField, self).deconstruct()
        # Only include kwarg if it's not the default
        kwargs['xml_tags'] = self.node_def
        return name, path, args, kwargs

    def from_db_value(self, value, expression, connection, context=None):
        if value is None:
            return value

        return MappedXmlField.build_python_object(self.inverse_node_def, eT.fromstring(value), self.populate_fully)

    def to_python(self, value):
        if not isinstance(value, str):
            return value

        if value is None:
            return value

        return json.loads(value)

    def value_to_string(self, obj):
        value = self.value_from_object(obj)
        return json.dumps(value)

    def get_prep_value(self, value):
        if value is None:
            return None

        node = MappedXmlField.build_node(self.node_def, value)
        return eT.tostring(node, encoding='unicode')


class XmlTextField(models.TextField):
    def __init__(self, xml_tags, populate_fully=False, *args, **kwargs):
        self.node_def = xml_tags
        self.populate_fully = populate_fully
        self.inverse_node_def = MappedXmlField.invert_node_definition(xml_tags)
        super(XmlTextField, self).__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super(XmlTextField, self).deconstruct()
        # Only include kwarg if it's not the default
        kwargs['xml_tags'] = self.node_def
        return name, path, args, kwargs

    def from_db_value(self, value, expression, connection, context=None):
        if value is None:
            return value

        return MappedXmlField.build_python_object(self.inverse_node_def, eT.fromstring(value), self.populate_fully)

    def to_python(self, value):
        if not isinstance(value, str):
            return value

        if value is None:
            return value

        return json.loads(value)

    def value_to_string(self, obj):
        value = self.value_from_object(obj)
        return json.dumps(value)

    def get_prep_value(self, value):
        if value is None:
            return None

        node = MappedXmlField.build_node(self.node_def, value)
        return eT.tostring(node, encoding='unicode')


class ValueConverterCharField(models.CharField):
    def __init__(self, from_db, to_db, *args, **kwargs):
        self.from_db = from_db
        self.to_db = to_db
        # self.coerce_ui_value = coerce_ui_value
        super(ValueConverterCharField, self).__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super(ValueConverterCharField, self).deconstruct()
        # Only include kwarg if it's not the default
        kwargs['from_db'] = self.from_db
        kwargs['to_db'] = self.to_db
        # kwargs['coerce_ui_value'] = self.coerce_ui_value
        return name, path, args, kwargs

    def from_db_value(self, value, expression, connection, context=None):
        if value is None:
            return value

        return self.from_db(value)

    # def to_python(self, value):
    #     return value
#        return self.coerce_ui_value(value)

    def value_to_string(self, obj):
        return str(self.value_from_object(obj))

    def get_prep_value(self, value):
        if value is None:
            return None

        return self.to_db(value)

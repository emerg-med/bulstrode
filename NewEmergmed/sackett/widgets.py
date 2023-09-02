from itertools import chain, groupby
from django.forms import Select
from django.forms.utils import flatatt
from django.utils.encoding import force_str
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _
from .utils import multi_group_by


class SUSelect(Select):
    """ A variant of the Select widget that renders as a SemanticUI menu dropdown """

    def __init__(self, searchable=False, fill_parent=True, default_text=None, index_items=False,
                 attrs=None, choices=()):
        super(SUSelect, self).__init__(attrs, choices)
        self.searchable = searchable
        self.fill_parent = fill_parent
        self.default_text = default_text
        self.index_items = index_items

    def render(self, name, value, attrs=None, choices=(), renderer=None):
        if value is None:
            value = ''
        final_attrs = self.build_attrs(self.attrs if 'id' not in attrs.keys() else attrs, {'name': name})
        control_id = final_attrs['id']

        output = [format_html('<div class="ui{} inline{} dropdown" id="{}_outer_dropdown">',
                              ' fluid' if self.fill_parent else '',
                              ' search' if self.searchable else '',
                              control_id),
                  format_html('<input type="hidden"{} value="{}">', flatatt(final_attrs), value),
                  format_html('<div class="default text">{}</div>', self.default_text or
                              _('choose') if not self.searchable
                              else (_('choose or type to search') if len(choices) > 0 else _('type to search'))),
                  '<i class="dropdown icon"></i>']

        options = self.render_options(choices, [value])
        if options:
            output.append(options)
        output.append('</div>')
        return mark_safe('\n'.join(output))

    def render_option(self, selected_choices, option_value, option_label, option_index):    # TODO method signature
        if option_value is None:
            option_value = ''
        option_value = force_str(option_value)

        if self.index_items:
            index_text = format_html(' data-index="{}"', option_index)
        else:
            index_text = ''

        return format_html('<div class="item" data-value="{}"{}>{}</div>',
                           option_value,
                           index_text,
                           force_str(option_label))

    def render_options(self, choices, selected_choices):
        # Normalize to strings.
        selected_choices = set(force_str(v) for v in selected_choices)
        output = ['<div class="right menu">']
        option_index = 0
        for option_value, option_label in chain(self.choices, choices):
            output.append(self.render_option(selected_choices, option_value, option_label, option_index))
            option_index += 1

        output.append('</div>')

        return '\n'.join(output)


class MultiLevelSUSelect(Select):
    """ A variant of the Select widget that renders as a multi-level SemanticUI menu dropdown """

    def __init__(self, levels=(), display_members=(), value_member='', item_data_members=(),
                 searchable=False, fill_parent=True, attrs=None, choices=()):
        # passing [("null", "null")] here because the input choices value is not a list of tuples so we can't use that;
        # the value we pass in here doesn't matter otherwise, because we are using custom render code
        super(MultiLevelSUSelect, self).__init__(attrs, [("null", "null")])
        self.choices_raw = choices
        self.levels = levels        # e.g. ['group', 'description']
        self.display_members = display_members
        self.value_member = value_member
        self.item_data_members = item_data_members
        self.searchable = searchable
        self.fill_parent = fill_parent

    def render(self, name, value, attrs=None, choices=(), renderer=None):
        if value is None:
            value = ''
        final_attrs = self.build_attrs(attrs, {'name': name})
        control_id = final_attrs['id']

        output = [format_html('<div class="ui{} inline{} dropdown" id="{}_outer_dropdown">',
                              ' fluid' if self.fill_parent else '',
                              ' search' if self.searchable else '',
                              control_id),
                  format_html('<input type="hidden"{}>', flatatt(final_attrs)),
                  format_html('<div class="default text">{}</div>', _('choose')),
                  '<i class="dropdown icon"></i>']

        options = self.render_options(chain(self.choices_raw, choices), [value])
        if options:
            output.append(options)
        output.append('</div>')
        return mark_safe('\n'.join(output))

    def render_options(self, choices, selected_choices):
        grouped_choices = multi_group_by(choices, self.levels, self.display_members)
        output = self.render_sub_menu(grouped_choices, selected_choices)

        return '\n'.join(output)

    def render_sub_menu(self, choices, selected_choices):
        output = ['<div class="right menu">']
        for choice in choices:
            if isinstance(choice, tuple):
                output += self.render_item(choice[0], choice[1], selected_choices)
            else:
                output += self.render_item('', choice, selected_choices)

        output.append('</div>')
        return output

    def render_item(self, header, content, selected_choices):
        if isinstance(content, list):
            output = ['<div class="item">', '<i class="dropdown icon"></i>',
                      format_html('<span class="text">{}</span>', header)]
            output += self.render_sub_menu(content, selected_choices)
            output.append('</div>')
        else:
            # item_data_members should be dictionary of either
            # {data-* key: value member}, or
            # {data-* key: (value member, format function)}
            if self.item_data_members is not None and len(self.item_data_members) > 0:
                data_text = ' '.join(['data-%(k)s=%(v)s'%{"k": k,
                                                          "v": self.item_data_members[k][1](
                                                                  getattr(content, self.item_data_members[k][0]))
                                                          if isinstance(self.item_data_members[k], tuple)
                                                          else getattr(content, self.item_data_members[k])}
                                     for k in self.item_data_members])
            else:
                data_text = ''

            if getattr(content, self.value_member) in selected_choices:
                selected_text = ' active selected'
            else:
                selected_text = ''

            output = [format_html('<div class="item{}" data-value="{}" {}>{}</div>',
                                  selected_text,
                                  getattr(content, self.value_member),
                                  data_text,
                                  getattr(content, self.display_members[-1]))]
        return output


class SelectWithData(Select):
    def __init__(self, attrs=None, choices=()):
        # passing [("null", "null")] here because the input choices value is not a list of tuples so we can't use that;
        # the value we pass in here doesn't matter otherwise, because we are using custom render code
        super(SelectWithData, self).__init__(attrs, [("null", "null")])
        self.choices_raw = choices

    """ A variant of the Select widget that includes data-* attributes on the generated <option>s """
    def render_options(self, choices, selected_choices):
        # Normalize to strings.
        selected_choices = set(force_str(v) for v in selected_choices)
        output = []
        for single_option in chain(self.choices_raw, choices):
            option_value = single_option['value']
            option_label = single_option['label']
            option_data = single_option['data']

            if isinstance(option_label, (list, tuple)):
                output.append(format_html('<optgroup label="{}">', force_str(option_value)))
                for option in option_label:
                    output.append(self.render_option(selected_choices, option['value'],
                                                     option['label'],
                                                     option['data']))
                output.append('</optgroup>')
            else:
                output.append(self.render_option(selected_choices, option_value, option_label, option_data))
        return '\n'.join(output)

    def render_option(self, selected_choices, option_value, option_label, option_data=()):
        if option_value is None:
            option_value = ''
        option_value = force_str(option_value)
        if option_value in selected_choices:
            selected_html = mark_safe(' selected="selected"')
            if not self.allow_multiple_selected:
                # Only allow for a single selection.
                selected_choices.remove(option_value)
        else:
            selected_html = ''

        if len(option_data) > 0:
            data_html = mark_safe(''.join((format_html(' data-{}="{}"', *o) for o in option_data)))
        else:
            data_html = ''

        return format_html('<option value="{}"{}{}>{}</option>',
                           option_value,
                           selected_html,
                           data_html,
                           force_str(option_label))


    def render(self, name, value, attrs=None, choices=(), renderer=None):
        if value is None:
            value = ''
        final_attrs = self.build_attrs(self.attrs if 'id' not in attrs.keys() else attrs, {'name': name})
        control_id = final_attrs['id']

        output = [format_html('<div class="ui{} inline{} dropdown" id="{}_outer_dropdown">',
                              '',
                              '',
                              control_id),
                  format_html('<input type="hidden"{} value="{}">', flatatt(final_attrs), value),
                  format_html('<div class="default text">{}</div>', ('choose')),
                  '<i class="dropdown icon"></i>']

        options = self.render_options(choices, [value])
        if options:
            output.append(options)
        output.append('</div>')
        return mark_safe('\n'.join(output))

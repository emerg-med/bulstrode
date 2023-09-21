from math import floor
from django.utils import timezone
from django.utils.translation import gettext as _, ngettext
from .enumerations import PickListTableTypes
from .picklistdataproxy import PickListDataProxy


STATE_ICON_DEFAULT_SIZE = 3


def get_display_name(episode):
    return _('%(surname)s, %(forename)s') % {'forename': episode.person_given_name,
                                             'surname': episode.person_family_name.upper()}


def get_gender_icon(episode):
    gender_label = PickListDataProxy.lookup_code(PickListTableTypes.PersonStatedGender.value,
                                                 episode.person_stated_gender)

    # Translators: 'Male' and 'Female' MUST match the corresponding picklist data table entries
    return ({_('Male'): 'man icon',
             _('Female'): 'woman icon'}.get(gender_label, 'other gender icon'),
            gender_label)


def get_icon_set_for_bed_episode(episode, icon_size_base):
    icon_set, icon_tooltip = __get_full_icon_set_for_episode(episode, icon_size_base)
    return [(icon_set[i], icon_tooltip[i]) for i in ['triage', 'wait', 'attend', 'bed']]


def get_icon_set_for_waiting_episode(episode):
    icon_set, icon_tooltip = __get_full_icon_set_for_episode(episode, STATE_ICON_DEFAULT_SIZE - 1)
    return [(icon_set[i], icon_tooltip[i]) for i in ['triage', 'wait', 'attend', 'bed']]


def __get_full_icon_set_for_episode(episode, icon_size_base):
    icon_names = {'wait': 'wait', 'triage': 'add', 'attend': 'doctor', 'bed': 'building'}
    icon_set = {}
    icon_tooltip = {}
    now = timezone.now()
    arrive_date_time = episode.em_care_arrive_date_time or now
    triage_cat = get_triage_category(episode) or 0
    bed_requested = episode.bed_requested or False

    wait_index = 0
    wait_time_minutes = 0
    wait_time_hours = 0

    if episode.em_care_assess_date_time is None:
        wait_time = now - arrive_date_time
        wait_time_minutes = floor(wait_time.seconds / 60.0) + (wait_time.days * 60*24)
        wait_time_hours = floor(wait_time.seconds / 3600.0) + (wait_time.days * 24)
        wait_index = min(int(wait_time_hours), 4)     # time in hours, in the range 0-4

    icon_wait_tuple = {0: (1, 'green', ''),
                       1: (1, 'green', ''),
                       2: (1, 'yellow', ''),
                       3: (1, 'red', ''),
                       4: (-1, 'black', 'inverted circular')}[wait_index]

    icon_set['wait'] = __build_icon(icon_size_base + icon_wait_tuple[0],
                                    icon_wait_tuple[1],
                                    icon_names['wait'],
                                    icon_wait_tuple[2])

    # wait_time_quantity, wait_time_quantity_label =\
    #     (wait_time_minutes, _('minute') if wait_time_minutes == 1 else _('minutes')) if wait_time_minutes < 60\
    #     else (wait_time_hours, _('hour') if wait_time_hours == 1 else _('hours'))

    # icon_tooltip['wait'] = _('Waiting time: %(wait_time)d %(wait_time_label)s') %\
    #     {'wait_time': wait_time_quantity,
    #      'wait_time_label': wait_time_quantity_label}

    if wait_time_minutes < 60:
        icon_tooltip['wait'] = ngettext(
            'Waiting time: %(wait_time_quantity)d minute',
            'Waiting time: %(wait_time_quantity)d minutes',
            wait_time_minutes) % {
            'wait_time_quantity': wait_time_minutes,
        }
    else:
        icon_tooltip['wait'] = ngettext(
            'Waiting time: %(wait_time_quantity)d hour',
            'Waiting time: %(wait_time_quantity)d hours',
            wait_time_hours) % {
            'wait_time_quantity': wait_time_hours,
        }

    icon_triage_tuple = {0: (-1, 'red', 'inverted bordered'),
                         1: (-1, 'red', 'inverted bordered'),
                         2: (-1, 'yellow', 'inverted bordered'),
                         3: (-1, 'green', 'inverted bordered'),
                         4: (-1, 'blue', 'inverted bordered'),
                         5: (1, 'black', '')}[triage_cat]

    icon_set['triage'] = __build_icon(icon_size_base + icon_triage_tuple[0],
                                      icon_triage_tuple[1],
                                      icon_names['triage'],
                                      icon_triage_tuple[2])

    icon_tooltip['triage'] = _('Triage category %(triage_category)s') %\
        {'triage_category': _('unknown') if triage_cat == 0 else str(triage_cat)}

    attend_late = False

    if episode.em_care_assess_date_time is None:
        attend_delay = now - arrive_date_time
        attend_delay_minutes = int(floor(attend_delay.seconds / 60.0))
        attend_late = {0: True,
                       1: True,
                       2: attend_delay_minutes >= 10,
                       3: attend_delay_minutes >= 30,
                       4: attend_delay_minutes >= 60,
                       5: attend_delay_minutes >= 120}[triage_cat]

    icon_attend_tuple = {True: (-1, 'red', 'inverted circular'),
                         False: (1, 'disabled', '')}[attend_late]

    icon_set['attend'] = __build_icon(icon_size_base + icon_attend_tuple[0],
                                      icon_attend_tuple[1],
                                      icon_names['attend'],
                                      icon_attend_tuple[2])

    icon_tooltip['attend'] = _('Clinician must see patient') if attend_late \
        else (_('Patient awaiting clinician') if episode.em_care_assess_date_time is None
              else _('Seen by clinician'))

    # lab icon is greyed out to start with then goes black when the blood results are sent [and could go green when the
    # results are back]

    # use the photo one for the XR - same

    # checkmark box icon starts off greyed out - goes green when patient first referred. half an hour later it goes red.
    # When the patient is accepted for admission the box becomes solid green (check square)

    icon_bed_tuple = {True: (1, 'green', ''),
                      False: (1, 'disabled', '')}[bed_requested]

    icon_set['bed'] = __build_icon(icon_size_base + icon_bed_tuple[0],
                                   icon_bed_tuple[1],
                                   icon_names['bed'],
                                   icon_bed_tuple[2])

    icon_tooltip['bed'] = _('Bed requested') if (episode.bed_requested or False) else _('Bed not requested')

    return icon_set, icon_tooltip


def get_triage_category(episode):
    return int(episode.em_care_assessment)\
        if episode.em_care_assessment is not None and episode.em_care_assessment.isdecimal()\
        else None


def __build_icon(size, colour, icon_type, shape=''):
    size_string = {0: 'mini',
                   1: 'tiny',
                   2: 'small',
                   3: '',
                   4: 'large',
                   5: 'big',
                   6: 'huge',
                   7: 'massive'}[min(max(size, 0), 7)]

    align_string = {0: 'low-align',
                    1: '',
                    2: 'mid-align',
                    3: 'mid-align',
                    4: 'mid-align',
                    5: 'mid-align',
                    6: 'mid-align',
                    7: 'mid-align'}[min(max(size, 0), 7)]

    shape_padded = shape + ' ' if len(shape) > 0 else ''

    return '%(shape)s%(colour)s %(size)s %(type)s icon %(align)s' % {'shape': shape_padded, 'colour': colour,
                                                                     'size': size_string, 'type': icon_type,
                                                                     'align': align_string}

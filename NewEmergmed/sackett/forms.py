import json
from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.forms import CheckboxInput, HiddenInput, TextInput
from django.utils.translation import gettext_lazy as _
from itertools import chain
from .constants import ZONE_WAITING_LIST_BED_INDEX
from .databasehelpers import get_field_max_length
from .enumerations import PickListTableTypes
from .models import Bed, Episode, Expected, Zone
from .picklistdataproxy import PickListDataProxy
from .templatehelpers import get_available_templates
from .utils import Expando, multi_group_by
from .widgets import MultiLevelSUSelect, SelectWithData, SUSelect
from .zonehelpers import get_zones_list


class AddZoneForm(forms.Form):
    label = forms.CharField(label=_('Clinical area name'),
                            max_length=get_field_max_length(Zone, 'label'))
    #                            max_length=get_field_max_length(Zone, 'template'),

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.available_templates = get_available_templates()
        self.fields['label'].widget.attrs.update({
            'id': 'zone_form_zone_label'        # force the id as we refer to it in the javascript
        })
        self.fields['template'] = forms.ChoiceField(label=_('Template'),
                                                    choices=[(t['template'], t['name'])
                                                             for t in self.available_templates],
                                                    widget=SUSelect(index_items=True,
                                                                    attrs={'id': 'zone_form_template'}))


class EpisodeBreachForm(forms.Form):
    detail = forms.CharField(label='', required=True)

    def __init__(self, *args, **kwargs):
        super(EpisodeBreachForm, self).__init__(*args, **kwargs)
        self.fields['detail'].widget.attrs = {'id': 'breach_detail', 'autocomplete': 'off'}


class EpisodeDischargeForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(EpisodeDischargeForm, self).__init__(*args, **kwargs)

        if self.instance.early_discharge:
            self.fields['em_care_discharge_status'].widget.choices =\
                [x for x in
                 PickListDataProxy.load_raw_for_choice_field(
                         PickListTableTypes.EmCareDischargeStatus.value)
                 if int(x.sort1) >= 51       # TODO magic number
                 # if int(x.code) >= 71
                 ]
        else:
            self.fields['em_care_discharge_status'].widget.choices_raw = PickListDataProxy.load_raw_for_choice_field(
                    PickListTableTypes.EmCareDischargeStatus.value)
        self.fields['em_care_discharge_follow_up'].widget.choices_raw = PickListDataProxy.load_raw_for_choice_field(
                PickListTableTypes.EmCareDischargeFollowUp.value)
        self.fields['em_care_discharge_safeguarding'].widget.choices_raw = PickListDataProxy.load_raw_for_choice_field(
                PickListTableTypes.EmCareDischargeSafeguarding.value)
        self.fields['em_care_transfer_destination'].widget.default_text =\
            PickListDataProxy.lookup_code(
                    PickListTableTypes.HealthCareFacility.value, self.instance.em_care_transfer_destination) or\
            _('type to search')
        self.fields['em_care_admit_speciality'].widget.choices_raw = PickListDataProxy.load_raw_for_choice_field(
                PickListTableTypes.EmCareAdmitSpecialty.value)
        self.fields['em_care_discharge_medication'].widget.attrs.update({'class': 'track-value-changes'})
        self.fields['em_care_discharge_instructions'].widget.attrs.update({'class': 'track-value-changes'})

    class Meta:
        model = Episode
        fields = ['em_care_discharge_status', 'em_care_discharge_follow_up', 'em_care_discharge_medication',
                  'em_care_discharge_instructions', 'em_care_discharge_safeguarding', 'em_care_transfer_destination',
                  'em_care_admit_speciality']
        labels = {
            'em_care_discharge_status': _('Status'),
            'em_care_discharge_follow_up': _('Follow up'),
            'em_care_discharge_medication': _('Medication'),
            'em_care_discharge_instructions': _('Instructions'),
            'em_care_discharge_safeguarding': _('Safeguarding'),
            'em_care_transfer_destination': _('Destination'),
            'em_care_admit_speciality': _('Admitted to'),
        }
        widgets = {
            # TODO: switch to two-stage pickers
            'em_care_discharge_status': MultiLevelSUSelect(levels=['sort1', 'sort2'], value_member='code',
                                                           display_members=['group', 'description'],
                                                           attrs={'class': 'track-value-changes'}),
            'em_care_discharge_follow_up': MultiLevelSUSelect(levels=['sort1'], value_member='code',
                                                              display_members=['description'],
                                                              attrs={'class': 'track-value-changes'}),
            'em_care_discharge_safeguarding': MultiLevelSUSelect(levels=['sort1', 'sort2'], value_member='code',
                                                                 display_members=['group', 'description'],
                                                                 attrs={'class': 'track-value-changes'}),
            'em_care_transfer_destination': SUSelect(fill_parent=True, searchable=True,
                                                     attrs={'class': 'track-value-changes'}),   # choices set in client
            'em_care_admit_speciality': MultiLevelSUSelect(levels=['sort1', 'sort2'], value_member='code',
                                                           display_members=['group', 'description'],
                                                           attrs={'class': 'track-value-changes'}),
        }


class EpisodeInvestigationForm(forms.Form):
    investigation = forms.CharField(label='',
                                    widget=MultiLevelSUSelect(levels=['sort1', 'sort2'], value_member='code',
                                                              display_members=['group', 'description'],
                                                              attrs={'id': 'new_investigation_select'}),
                                    required=False)        # TODO max length?

    def __init__(self, *args, **kwargs):
        super(EpisodeInvestigationForm, self).__init__(*args, **kwargs)
        self.fields['investigation'].widget.choices_raw = PickListDataProxy.load_raw_for_choice_field(
                PickListTableTypes.EmCareInvestigations.value)


class EpisodeTreatmentForm(forms.Form):
    treatment = forms.CharField(label='',
                                widget=MultiLevelSUSelect(levels=['sort1', 'sort2'], value_member='code',
                                                          display_members=['group', 'description'],
                                                          attrs={'id': 'new_treatment_select'}),
                                required=False)        # TODO max length?

    def __init__(self, *args, **kwargs):
        super(EpisodeTreatmentForm, self).__init__(*args, **kwargs)
        self.fields['treatment'].widget.choices_raw = PickListDataProxy.load_raw_for_choice_field(
                PickListTableTypes.EmCareTreatments.value)


class EpisodePreDiagnosisForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        instance = kwargs.get('instance', None)     # get it but leave it there for super()

        super(EpisodePreDiagnosisForm, self).__init__(*args, **kwargs)
        self.fields['em_care_chief_complaint'].widget.choices_raw = PickListDataProxy.load_raw_for_choice_field(
                PickListTableTypes.EmCareChiefComplaint.value)
        self.fields['bed'].widget.choices_raw = [Expando(zone_label=b.zone.label,
                                                     bed_label=_("%(zone)s: %(bed)s") %
                                                               {'zone': b.zone.label,
                                                                'bed': b.label
                                                                if b.template_index != ZONE_WAITING_LIST_BED_INDEX
                                                                else _("Waiting list")},
                                                     template_index=b.template_index,
                                                     bed_id=b.id)
                                             for b in Bed.objects.filter(zone__deleted=False)
                                             ]

        if (self.user and self.user.is_active and self.user.has_perm('can_clear_consultant')) or\
                (instance.assigned_clinician is None):      # allow 'not set' if the clinician has not yet been set
            blank_clinician = [(None, _('not set'))]
        else:
            blank_clinician = []

        selected_clinician_id = instance.assigned_clinician.id if instance.assigned_clinician is not None else None

        x = list(chain(blank_clinician,
                       [(u.id, _('%(surname)s, %(forename)s') % {'forename': u.first_name, 'surname': u.last_name})
                        for u in get_user_model().objects.filter(is_active=True)
                        if u.id == selected_clinician_id or
                        (u.has_perm('sackett.is_consultant') and u.has_perm('sackett.can_consult')
                         and not u.is_superuser)]))
        self.fields['assigned_clinician'].widget.choices = x

    class Meta:
        model = Episode
        fields = ['em_care_chief_complaint',
                  'em_care_assessment',
                  'assigned_clinician',
                  'action',
                  'bed_requested',
                  'bed'
                  ]
        labels = {'em_care_chief_complaint': _('Chief complaint'),
                  'em_care_assessment':_('Acuity'),
                  'assigned_clinician': _('Doctor'),
                  'action': _('Action & time'),
                  'bed_requested': _('Bed requested'),
                  'bed': _('Bed')
                  }
        widgets = {
            # TODO: switch to two-stage picker
            'em_care_chief_complaint': MultiLevelSUSelect(levels=['sort1', 'sort2'], value_member='code',
                                                          display_members=['group', 'description'],
                                                          attrs={'class': 'track-value-changes'}),
            'em_care_assessment': SUSelect(choices=[(str(n), str(n)) for n in range(1, 6)],
                                           attrs={'class': 'track-value-changes'}),
            'assigned_clinician': SUSelect(attrs={'class': 'track-value-changes'}),
            'action': TextInput(attrs={'class': 'track-value-changes'}),
            'bed_requested': CheckboxInput(attrs={'class': 'track-value-changes'}),
            'bed': MultiLevelSUSelect(levels=['zone_label', 'template_index'], value_member='bed_id',
                                      display_members=['zone_label', 'bed_label'],
                                      attrs={'class': 'track-value-changes'})
        }


class ExpectedArrivalForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ExpectedArrivalForm, self).__init__(*args, **kwargs)
        self.fields['person_stated_gender'].widget.choices_raw = PickListDataProxy.load_raw_for_choice_field(
                PickListTableTypes.PersonStatedGender.value)
        self.fields['em_care_chief_complaint'].widget.choices_raw = PickListDataProxy.load_raw_for_choice_field(
                PickListTableTypes.EmCareChiefComplaint.value)

    class Meta:
        model = Expected
        fields = ['person_given_name', 'person_family_name', 'em_care_chief_complaint', 'person_stated_gender',
                  'person_age_at_attendance']
        labels = {'person_given_name': _('Given name'),
                  'person_family_name': _('Family name'),
                  'em_care_chief_complaint': _('Chief complaint'),
                  'person_stated_gender': _('Stated gender'),
                  'person_age_at_attendance': _('Age (approx)')}
        widgets = {
            'person_stated_gender': MultiLevelSUSelect(levels=['sort1'], value_member='code',
                                                       display_members=['description']),
            'em_care_chief_complaint': MultiLevelSUSelect(levels=['sort1', 'sort1'], value_member='code',
                                                          display_members=['group', 'description']),
        }


class InjuryDetailForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(InjuryDetailForm, self).__init__(*args, **kwargs)
        # self.drugs_alcohol_choices =\
        #     PickListDataProxy.load_for_choice_field(PickListTableTypes.EmCareInjDrugAlcohol.value)
        self.drugs_alcohol_choices = multi_group_by(
                PickListDataProxy.load_raw_for_choice_field(PickListTableTypes.EmCareInjDrugAlcohol.value),
                ['sort1', 'sort2'],
                ['group', 'description'])

        self.fields['em_care_inj_activity_type'].widget.choices_raw = PickListDataProxy.load_raw_for_choice_field(
                PickListTableTypes.EmCareInjActivity.value)
        self.fields['em_care_inj_mechanism'].widget.choices_raw = PickListDataProxy.load_raw_for_choice_field(
                PickListTableTypes.EmCareInjMechanism.value)
        self.fields['em_care_inj_intent'].widget.choices_raw = PickListDataProxy.load_raw_for_choice_field(
                PickListTableTypes.EmCareInjIntent.value)
        self.fields['em_care_inj_place_type'].widget.choices_raw = PickListDataProxy.load_raw_for_choice_field(
                PickListTableTypes.EmCareInjPlaceType.value)
        self.fields['em_care_inj_date_time'].widget.attrs.update({'class': 'track-value-changes'})
        self.fields['em_care_inj_activity_detail'].widget.attrs.update({'class': 'track-value-changes'})
        self.fields['em_care_inj_place_exact'].widget.attrs.update({'class': 'track-value-changes'})
        self.fields['em_care_inj_place_lat_long'].widget.attrs.update({'class': 'track-value-changes'})

    def clean_em_care_inj_drug_alcohol(self):
        if self.cleaned_data['em_care_inj_drug_alcohol'] is None\
                or len(self.cleaned_data['em_care_inj_drug_alcohol']) == 0:
            return []

        # need to replace \' with " since the code outputting the injury form converts the drugs/alcohol list
        # into a string using single quoting, but that's not valie JSON - should be double quoted - so the parse
        # here fails during save. TODO find a neater solution to this - should output the correct format to begin with
        return json.loads(self.cleaned_data['em_care_inj_drug_alcohol'].replace('\'', '"'))

    class Meta:
        model = Episode
        fields = ['em_care_inj_date_time', 'em_care_inj_activity_type', 'em_care_inj_activity_detail',
                  'em_care_inj_mechanism', 'em_care_inj_intent', 'em_care_inj_drug_alcohol',
                  'em_care_inj_place_type', 'em_care_inj_place_exact', 'em_care_inj_place_lat_long']
        labels = {
            'em_care_inj_date_time': _('Date & time of injury'),
            'em_care_inj_activity_type': _('Activity type'),
            'em_care_inj_activity_detail': _('Activity detail'),
            'em_care_inj_mechanism': _('Mechanism'),
            'em_care_inj_intent': _('Intent'),
            'em_care_inj_drug_alcohol': _('Drugs/alcohol'),
            'em_care_inj_place_type': _('Type of location'),
            'em_care_inj_place_exact': _('Location'),
            'em_care_inj_place_lat_long': _('Lat/long'),
        }
        widgets = {
            # TODO: switch to two-stage pickers
            'em_care_inj_activity_type':  MultiLevelSUSelect(levels=['sort1', 'sort2'], value_member='code',
                                                             display_members=['group', 'description'],
                                                             attrs={'class': 'track-value-changes'}),
            'em_care_inj_mechanism': MultiLevelSUSelect(levels=['sort1', 'sort2'], value_member='code',
                                                        display_members=['group', 'description'],
                                                        attrs={'class': 'track-value-changes'}),
            'em_care_inj_intent': MultiLevelSUSelect(levels=['sort1'], value_member='code',
                                                     display_members=['description'],
                                                     attrs={'class': 'track-value-changes'}),
            'em_care_inj_drug_alcohol': HiddenInput(),
            'em_care_inj_place_type': MultiLevelSUSelect(levels=['sort1', 'sort2'], value_member='code',
                                                         display_members=['group', 'description'],
                                                         attrs={'class': 'track-value-changes'}),
        }


class PatientDetailsForm(forms.ModelForm):
    person_preferred_contact_home = forms.CharField(label=_('Phone'), required=False)
    person_preferred_contact_mobile = forms.CharField(label=_('Mobile'), required=False)
    person_preferred_contact_email = forms.CharField(label=_('Email'), required=False)
    withhold_identity = forms.BooleanField(label=_('Withhold identity'), required=False)

    def __init__(self, *args, **kwargs):
        super(PatientDetailsForm, self).__init__(*args, **kwargs)
        if self.instance.person_preferred_contact is not None:
            self.fields['person_preferred_contact_home'].initial = self.instance.person_preferred_contact['home']
            self.fields['person_preferred_contact_mobile'].initial = self.instance.person_preferred_contact['mobile']
            self.fields['person_preferred_contact_email'].initial = self.instance.person_preferred_contact['email']

        self.fields['withhold_identity'].initial = (self.instance.person_identity_withheld_reason is not None)

        self.fields['person_stated_gender'].widget.choices = PickListDataProxy.load_for_choice_field(
                PickListTableTypes.PersonStatedGender.value)
        self.fields['em_care_arrive_transport_mode'].widget.choices = PickListDataProxy.load_for_choice_field(
                PickListTableTypes.EmCareArriveTransportMode.value)
        self.fields['em_care_attendance_type'].widget.choices = PickListDataProxy.load_for_choice_field(
                PickListTableTypes.EmCareAttendanceType.value)
        self.fields['em_care_referral_source'].widget.choices = PickListDataProxy.load_for_choice_field(
                PickListTableTypes.EmCareReferralSource.value)
        self.fields['em_care_arrive_transfer_source'].widget.default_text =\
            PickListDataProxy.lookup_code(
                    PickListTableTypes.HealthCareFacility.value, self.instance.em_care_arrive_transfer_source) or\
            _('type to search')
        self.fields['person_comm_lang'].widget.choices = PickListDataProxy.load_for_choice_field(
                PickListTableTypes.PersonCommLang.value)
        self.fields['person_interpreter_lang'].widget.choices = PickListDataProxy.load_for_choice_field(
                PickListTableTypes.PersonInterpreterLang.value)
        self.fields['person_identity_withheld_reason'].widget.choices = PickListDataProxy.load_for_choice_field(
                PickListTableTypes.PersonIdentityWithheldReason.value)
        self.fields['person_usual_residence_type'].widget.choices = PickListDataProxy.load_for_choice_field(
                PickListTableTypes.PersonUsualResidenceType.value)
        self.fields['person_ethnic_category'].widget.choices = PickListDataProxy.load_for_choice_field(
                PickListTableTypes.PersonEthnicCategory.value)
        self.fields['person_gp_practice_code'].widget.default_text =\
            PickListDataProxy.lookup_code(
                     PickListTableTypes.GeneralPractice.value, self.instance.person_gp_practice_code) or\
            _('type to search')
        self.fields['person_school'].widget.default_text =\
            PickListDataProxy.lookup_code(
                     PickListTableTypes.School.value, self.instance.person_school) or\
            _('type to search')

    class Meta:
        model = Episode
        fields = ['person_global_number', 'person_local_number', 'person_given_name', 'person_family_name',
                  'person_stated_gender', 'person_birth_date', 'em_care_arrive_transport_mode',
                  'em_care_attendance_type', 'em_care_referral_source', 'em_care_arrive_transfer_source',
                  'person_comm_lang', 'person_interpreter_rqd', 'person_interpreter_lang',
                  'person_identity_withheld_reason', 'person_usual_address_1', 'person_usual_address_2',
                  'person_usual_address_postcode', 'person_usual_residence_type', 'person_ethnic_category',
                  'person_gp_practice_code', 'person_school', 'person_companion']
        # person_preferred_contact not shown
        labels = {
            'person_global_number': _('NHS number'),
            'person_local_number': _('Local number'),
            'person_given_name': _('Given name'),
            'person_family_name': _('Family name'),
            'person_stated_gender': _('Gender'),
            'person_birth_date': _('Date of birth'),
            'em_care_arrive_transport_mode': _('Means of arrival'),
            'em_care_attendance_type': _('Attendance type'),
            'em_care_referral_source': _('Referral source'),
            'em_care_arrive_transfer_source': _('Transfer from'),
            'person_comm_lang': _('Preferred language'),
            'person_interpreter_rqd': _('Interpreter reqd.'),
            'person_interpreter_lang': '',
            'person_identity_withheld_reason': _('Reason'),
            'person_usual_address_1': _('Usual address'),
            'person_usual_address_2': '',
            'person_usual_address_postcode': _('Postcode'),
            'person_usual_residence_type': _('Residence type'),
            'person_ethnic_category': _('Ethnic category'),
            'person_gp_practice_code': _('GP'),
            'person_school': _('School'),
            'person_companion': _('Companion')
        }
        widgets = {
            'person_stated_gender': SUSelect(fill_parent=True,
                                             attrs={'class': 'track-value-changes'}),
            'em_care_arrive_transport_mode': SUSelect(fill_parent=True,
                                                      attrs={'class': 'track-value-changes'}),
            'em_care_attendance_type': SUSelect(fill_parent=True,
                                                attrs={'class': 'track-value-changes'}),
            'em_care_referral_source': SUSelect(fill_parent=True,
                                                attrs={'class': 'track-value-changes'}),
            'em_care_arrive_transfer_source': SUSelect(fill_parent=True, searchable=True,
                                                       attrs={'class': 'track-value-changes'}),
            'person_comm_lang': SUSelect(fill_parent=True, searchable=True,
                                         attrs={'class': 'track-value-changes'}),
            'person_interpreter_rqd': CheckboxInput(),
            'person_interpreter_lang': SUSelect(fill_parent=True, searchable=True,
                                                attrs={'class': 'track-value-changes'}),
            'person_identity_withheld_reason': SUSelect(fill_parent=True,
                                                        attrs={'class': 'track-value-changes'}),
            'person_usual_residence_type': SUSelect(fill_parent=True,
                                                    attrs={'class': 'track-value-changes'}),
            'person_ethnic_category': SUSelect(fill_parent=True,
                                               attrs={'class': 'track-value-changes'}),
            'person_gp_practice_code': SUSelect(fill_parent=True, searchable=True,
                                                attrs={'class': 'track-value-changes'}),
            'person_school': SUSelect(fill_parent=True, searchable=True,
                                      attrs={'class': 'track-value-changes'}),
        }


class TriageArrivalForm(forms.ModelForm):
    zone_id = forms.IntegerField(label=_('Clinical area'),
                                 widget=MultiLevelSUSelect(levels=['label'], value_member='id',
                                                           display_members=['label']))
    expected_arrival = forms.IntegerField(label=_('Expected patients'),
                                          widget=SelectWithData(attrs={'size': '10'}),
                                          required=False)

    def __init__(self, *args, **kwargs):
        super(TriageArrivalForm, self).__init__(*args, **kwargs)
        expected_models = Expected.objects.filter(removed=False, linked_episode__isnull=True)
        expected_list = [{'value': x.id,
                          'label': x.person_family_name + ", " + x.person_given_name,   # TODO name combiner function
                          'data': [('given-name', x.person_given_name),
                                   ('family-name', x.person_family_name),
                                   ('complaint', x.em_care_chief_complaint),
                                   ('gender', x.person_stated_gender),
                                   ('age', x.person_age_at_attendance),
                                   ]} for x in expected_models]      # TODO leaking db ids
        self.fields['expected_arrival'].widget.choices_raw = expected_list
        self.fields['expected_arrival'].widget.attrs.update({
            'id': 'triage_expected_list'
        })
        self.fields['person_stated_gender'].widget.choices_raw =\
            PickListDataProxy.load_raw_for_choice_field(PickListTableTypes.PersonStatedGender.value)
        self.fields['em_care_chief_complaint'].widget.choices_raw =\
            PickListDataProxy.load_raw_for_choice_field(PickListTableTypes.EmCareChiefComplaint.value)
        self.fields['em_care_arrive_transport_mode'].widget.choices_raw =\
            PickListDataProxy.load_raw_for_choice_field(PickListTableTypes.EmCareArriveTransportMode.value)
        self.fields['em_care_attendance_type'].widget.choices_raw =\
            PickListDataProxy.load_raw_for_choice_field(PickListTableTypes.EmCareAttendanceType.value)
        # self.fields['person_interpreter_lang'].widget.choices =\
        #     PickListDataProxy.load_raw_for_choice_field(PickListTableTypes.PersonInterpreterLang.value)
        self.fields['person_interpreter_lang'].widget.choices = PickListDataProxy.load_for_choice_field(
                PickListTableTypes.PersonInterpreterLang.value)
        self.fields['zone_id'].widget.choices_raw = get_zones_list()
        self.fields['em_care_assessment'].required = True

    def clean_person_interpreter_lang(self):
        return self.cleaned_data['person_interpreter_lang']\
                if self.cleaned_data['person_interpreter_lang'] is not None and len(self.cleaned_data['person_interpreter_lang']) > 0\
                else None

    class Meta:
        model = Episode
        fields = ['person_given_name', 'person_family_name', 'person_stated_gender',
                  'person_age_at_attendance', 'em_care_arrive_transport_mode', 'em_care_chief_complaint',
                  'em_care_attendance_type', 'person_interpreter_rqd', 'person_interpreter_lang',
                  'em_care_assessment']
        labels = {'person_given_name': _('Given name'),
                  'person_family_name': _('Family name'),
                  'person_stated_gender': _('Stated gender'),
                  'person_age_at_attendance': _('Age (approx)'),
                  'em_care_arrive_transport_mode': _('Arrival transport mode'),
                  'em_care_chief_complaint': _('Chief complaint'),
                  'em_care_attendance_type': _('Attendance type'),
                  'person_interpreter_rqd': _('Interpreter reqd.'),
                  'person_interpreter_lang': '',
                  'em_care_assessment': _('Acuity'),
                  }
        widgets = {
            'person_stated_gender': MultiLevelSUSelect(levels=['sort1'], value_member='code',
                                                       display_members=['description']),
            'em_care_chief_complaint': MultiLevelSUSelect(levels=['sort1', 'sort2'], value_member='code',
                                                          display_members=['group', 'description'],
                                                          item_data_members={
                                                              'injury': ('bool1', lambda x: 1 if x else 0)
                                                          }),
            'em_care_arrive_transport_mode': MultiLevelSUSelect(levels=['sort1'], value_member='code',
                                                                display_members=['description']),
            'em_care_attendance_type': MultiLevelSUSelect(levels=['description'], value_member='code',
                                                          display_members=['description']),
            'person_interpreter_rqd': forms.CheckboxInput(),    # attrs={'id': 'triage_person_interpreter_rqd'}),
            'person_interpreter_lang': SUSelect(searchable=True, attrs={'class': 'track-value-changes'}),
            'em_care_assessment': SUSelect(choices=[(str(n), str(n)) for n in range(1, 6)]),
        }


class UserManagementAddDoctorForm(forms.Form):
    first_name = forms.CharField(label=_('First name'), max_length=30)
    last_name = forms.CharField(label=_('Last name'), max_length=30)


class UserManagementAddEditUserForm(forms.Form):
    is_editing = False
    username = forms.CharField(label=_('Username'), max_length=30)
    password = forms.CharField(label=_('Password'), widget=forms.PasswordInput(), required=False)
    confirm_password = forms.CharField(label=_('Confirm password'), widget=forms.PasswordInput(), required=False)
    login_enabled = forms.BooleanField(label=_('User account enabled'), initial=True, required=False)
    perm_user_admin = forms.BooleanField(label=_('Administer other user accounts'), required=False)
    perm_sys_admin = forms.BooleanField(label=_('Configure system settings (e.g. branding)'), required=False)
    perm_clear_consultant = forms.BooleanField(label=_('Clear the assigned doctor for a patient'), required=False)
    perm_undischarge = forms.BooleanField(label=_('View recent discharged patients and undo discharge'), required=False)
    perm_breaches = forms.BooleanField(label=_('Review quality breach reports'), required=False)
    perm_view_dashboard = forms.BooleanField(label=_('View dashboard'), required=False)
    perm_export_data = forms.BooleanField(label=_('Export anonymised data'), required=False)

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        self.is_editing = not kwargs.pop('new_user', False)

        super(UserManagementAddEditUserForm, self).__init__(*args, **kwargs)

        if user is not None:
            self.is_editing = True
            self.fields['username'].initial = user.username
            self.fields['login_enabled'].initial = user.is_active
            self.fields['perm_user_admin'].initial = user.has_perm('sackett.can_administer_users')
            self.fields['perm_sys_admin'].initial = user.has_perm('sackett.can_modify_org') and\
                user.has_perm('sackett.can_administer_zones')
            self.fields['perm_clear_consultant'].initial = user.has_perm('sackett.can_clear_consultant')
            self.fields['perm_undischarge'].initial = user.has_perm('sackett.can_undischarge')
            self.fields['perm_breaches'].initial = user.has_perm('sackett.can_review_breaches')
            self.fields['perm_view_dashboard'].initial = user.has_perm('sackett.can_view_dashboard')
            self.fields['perm_export_data'].initial = user.has_perm('sackett.can_export_data')

    def clean(self):
        cleaned_data = super(UserManagementAddEditUserForm, self).clean()
        username_cleaned = cleaned_data.get("username")
        password_cleaned = cleaned_data.get("password")
        confirm_password_cleaned = cleaned_data.get("confirm_password")

        if (password_cleaned or confirm_password_cleaned) and password_cleaned != confirm_password_cleaned:
            raise forms.ValidationError(_("Passwords don't match"))

        if not self.is_editing:
            if username_cleaned and password_cleaned and confirm_password_cleaned:
                # Only do something if main fields are valid so far.
                existing_user = get_user_model().objects.filter(username=username_cleaned).first()

                if existing_user is not None:
                    raise forms.ValidationError(_("User name already in use"))
                elif password_cleaned != confirm_password_cleaned:
                    raise forms.ValidationError(_("Passwords don't match"))
            else:
                raise forms.ValidationError(_("Please specify a username and password"))

        return cleaned_data


class UserManagementLoginForm(forms.Form):
    username = forms.CharField(label=_('Username'))
    password = forms.CharField(label=_('Password'), widget=forms.PasswordInput())
    authenticated_user = None

    def clean(self):
        cleaned_data = super(UserManagementLoginForm, self).clean()
        username_cleaned = cleaned_data.get("username")
        password_cleaned = cleaned_data.get("password")

        if username_cleaned and password_cleaned:
            # Only do something if both fields are valid so far.
            authenticated_user = authenticate(username=username_cleaned, password=password_cleaned)

            if authenticated_user is None or not authenticated_user.is_active:
                self.authenticated_user = None
                raise forms.ValidationError(_("Username or password incorrect, or user is disabled"))
            else:
                self.authenticated_user = authenticated_user


class UserManagementPersonalForm(forms.Form):
    old_password = forms.CharField(label=_('Old password'), widget=forms.PasswordInput())
    new_password = forms.CharField(label=_('New password'), widget=forms.PasswordInput())
    repeat_new_password = forms.CharField(label=_('Confirm new password'), widget=forms.PasswordInput())
    authenticated_user = None

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(UserManagementPersonalForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super(UserManagementPersonalForm, self).clean()
        old_password_cleaned = cleaned_data.get("old_password")
        new_password_cleaned = cleaned_data.get("new_password")
        repeat_new_password_cleaned = cleaned_data.get("repeat_new_password")

        if self.user and old_password_cleaned:
            # Only do something if both fields are valid so far.
            authenticated_user = authenticate(username=self.user.username, password=old_password_cleaned)

            if authenticated_user is None or not authenticated_user.is_active:
                self.authenticated_user = None
                raise forms.ValidationError(_("Old password incorrect, or user is disabled"))
            elif new_password_cleaned != repeat_new_password_cleaned:
                self.authenticated_user = None
                raise forms.ValidationError(_("New passwords don't match"))
            else:
                self.authenticated_user = authenticated_user


class ZoneDragDropForm(forms.Form):
    source_id = forms.CharField(widget=forms.HiddenInput(attrs={'id': 'zone_drag_drop_source_id'}))
    destination_id = forms.CharField(widget=forms.HiddenInput(attrs={'id': 'zone_drag_drop_destination_id'}))

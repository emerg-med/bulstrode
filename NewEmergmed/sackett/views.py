from datetime import date, timedelta
from decimal import Decimal
import os
import mimetypes
from django.contrib.auth import get_user_model, login, logout, update_session_auth_hash
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.template import loader
from django.urls import reverse
from django.utils.safestring import SafeString
from django.utils.translation import get_language
from django.utils.translation import gettext as _
from itertools import groupby
import sackett.recordlocking as recordlocking
from NewEmergmed import settings
from . import uniqueid
from .authhelpers import is_user_authorised_for_zone
from .constants import *
from .diagnosisdataimporter import DiagnosisDataImporter
from .diagnosisdataproxy import DiagnosisDataProxy
from .enumerations import LockAcquireResult
from .episodehelpers import *
from .forms import *
from .models import Bed, Breach, Episode, Expected, UserPermissionSupport, Zone
from .picklistdataimporter import PickListDataImporter
from .picklistdataproxy import PickListDataProxy
from .utils import Expando, utc_now
from .zonehelpers import move_episode


# TODO: remove
def debug_import_diagnoses(request):
    if request.method == 'GET':
        context = {}
        return render(request, 'sackett/debug_import_diagnoses.html', context)
    elif request.method == 'POST':
        DiagnosisDataImporter.start_background(get_language())  # do_import(get_language())
        return HttpResponseRedirect(reverse('sackett:debug_import_diagnoses'))


def debug_import_tables(request):
    if request.method == 'GET':
        context = {}
        return render(request, 'sackett/debug_import_tables.html', context)
    elif request.method == 'POST':
        PickListDataImporter.start_background(get_language())   # import_all(get_language())
        return HttpResponseRedirect(reverse('sackett:debug_import_tables'))

# end temporary debugging views


def add_zone(request):
    if request.method == 'POST':
        form = AddZoneForm(request.POST)

        result_template = loader.get_template('sackett/add_zone_result.html')

        if form.is_valid():
            zone_template = next((t for t in form.available_templates
                                 if t['template'] == form.cleaned_data['template']), None)

            if zone_template is not None:
                new_zone = Zone(label=form.cleaned_data['label'],
                                template=zone_template['template'],
                                summary_template=zone_template['summary_template'],
                                deleted=False)
                new_zone.save()

                # add special bed for the waiting list
                waiting_bed = Bed(zone=new_zone,
                                  template_index=-1,
                                  name=ZONE_WAITING_LIST_BED_NAME,
                                  label='')
                waiting_bed.save()

                # add the other beds
                bed_count = 1
                for bed in zone_template['beds']:
                    new_bed = Bed(zone=new_zone,
                                  template_index=bed_count,
                                  name=bed['name'],
                                  label=bed['label'])   # zone_template['beds'][bed])
                    new_bed.save()
                    bed_count += 1

                return HttpResponse(result_template.render({'new_zone_url': 'sackett/area/' + str(new_zone.id),
                                                            'success': True},
                                                           request))
            # TODO: report error
            else:
                return HttpResponse(result_template.render({'success': False}, request))
        else:
            return HttpResponse(result_template.render({'success': False}, request))
    # if a GET (or any other method) we'll create a blank form
    else:
        form = AddZoneForm()

    template_list = [{'template': t, 'index': idx} for idx, t in enumerate(form.available_templates)]

    return render(request, 'sackett/add_zone.html', {'form': form,
                                                     'template_list': template_list,
                                                     'template_count': len(template_list), })


# TODO: allow language selection
# def config_choose_language(request):
#     return render(request, 'sackett/config_choose_language.html')


# AJAX callback point for the diagnosis search function - expects one (space delimited) string with a key of 'search'
def diagnosis_search(request, search):
    if request.method == 'GET':
        diagnoses = DiagnosisDataProxy.lookup_by_terms_string(search)
        return HttpResponse(json.dumps({"success": True,
                                        "results": [{"value": d.code, "name": d.description}
                                                    for d, w in diagnoses]}),
                            content_type='application/json')
    else:
        raise Http404


def episode(request, episode_id):
    episode_object = get_object_or_404(Episode, id=episode_id)

    pre_diagnosis_form = EpisodePreDiagnosisForm(instance=episode_object, user=request.user)

    additional_content = __episode_additional(request, episode_object)
    accordion_content, collapsed_panels = __episode_accordion(request, episode_object)
    state_icon_content = __episode_state_icons(request, episode_object)
    return render(request, 'sackett/episode.html', {'full_name': get_display_name(episode_object),
                                                    'gender': get_gender_icon(episode_object),
                                                    'age': episode_object.person_age_at_attendance or _("??"),
                                                    'unique_id': episode_object.em_care_unique_id,
                                                    'local_number': episode_object.person_local_number,
                                                    'breach_form': EpisodeBreachForm(), # always an empty form
                                                    'pre_diagnosis_form': pre_diagnosis_form,
                                                    'additional_content': additional_content,
                                                    'accordion_content': accordion_content,
                                                    'collapsed_panels': collapsed_panels,
                                                    'episode_id': episode_id,
                                                    'is_discharged':
                                                        episode_object.em_care_depart_date_time is not None,
                                                    'state_icons': state_icon_content
                                                    },
                  )


# AJAX callback point for the breach 'submit' button - expects data in the form { "field": "value", ... }
def episode_breach(request, episode_id):
    if request.method == 'POST':
        episode_object = get_object_or_404(Episode, id=episode_id)
        today_utc = utc_now()
        one_day = timedelta(days=-1)
        last_day_breaches = Breach.objects.filter(episode_id=episode_id, added_date_time__gte=today_utc+one_day)
        if last_day_breaches.count() > 50:      # TODO magic constant
            return HttpResponseBadRequest()

        form = EpisodeBreachForm(request.POST)

        if form.is_valid():
            if len(form.cleaned_data['detail']) > 0:
                breach = Breach(episode=episode_object, narrative=form.cleaned_data['detail'],
                                added_date_time=today_utc)
                breach.save()

            return HttpResponse()
        else:
            return HttpResponseBadRequest()
    else:
        return HttpResponseBadRequest()


# AJAX callback point for the Episode 'save' button - expects data in the form { "field": "value", ... }
def episode_update(request, episode_id):
    if request.method == 'POST':
        episode_object = get_object_or_404(Episode, id=episode_id)
        old_episode_object = get_object_or_404(Episode, id=episode_id)      # for later comparison to update page

        # hack to allow us to setattr() in the lambda below
        complete_discharge = Expando()
        complete_discharge.value = False
        early_discharge = Expando()
        early_discharge.value = False
        undo_early_discharge = Expando()
        undo_early_discharge.value = False

        field_fns = {       # f = field name in model, p = POST data, pf = key in POST data ('POST field')
                '__complete_discharge__': lambda f, p, pf: setattr(complete_discharge, 'value', True),
                '__early_discharge__': lambda f, p, pf: setattr(early_discharge, 'value', True),
                '__undo_early_discharge__': lambda f, p, pf: setattr(undo_early_discharge, 'value', True),
                'assigned_clinician': lambda f, p, pf: setattr(episode_object, f,
                                                               get_user_model().objects.get(id=p[pf]) if
                                                               p[pf].isdigit() else None),
                'em_care_clinical_narrative':
                lambda f, p, pf: setattr(episode_object, 'em_care_clinical_narrative',
                                         ';'.join((episode_object.em_care_clinical_narrative, p[pf]))),
                'bed': lambda f, p, pf: setattr(episode_object, f,
                                                Bed.objects.get(id=p[pf]))
        }
        def default_field_fn(f, p, pf): setattr(episode_object, f, p[pf])

        updated_field_names = set()
        data_dict = json.loads(request.POST['data'])
        for field in data_dict:
            episode_field_name = field[len('id_'):]     # strip off the leading 'id_' from the field name

            # TODO magic constant
            if data_dict[field] == '__delete_marker__':      # can't send empty arrays so must do this instead
                setattr(episode_object, episode_field_name, None)
            else:
                field_fn = field_fns.get(episode_field_name, default_field_fn)

                field_fn(episode_field_name, data_dict, field)

                if episode_field_name[0:2] != '__':
                    updated_field_names.add(episode_field_name)

        if undo_early_discharge.value and episode_object.early_discharge:
            episode_object.early_discharge = False
            updated_field_names.add('early_discharge')
            early_discharge.value = False     # cancel this if it's also set
            complete_discharge.value = False

        if early_discharge.value and __episode_can_discharge_early(episode_object):
            episode_object.early_discharge = True
            updated_field_names.add('early_discharge')
            complete_discharge.value = False      # cancel this if it's also set

        if complete_discharge.value and __episode_ready_for_discharge(episode_object):
            episode_object.em_care_depart_date_time = timezone.now()
            episode_object.em_care_complete_date_time = None if episode_object.early_discharge else timezone.now()
            if 21 <= int(episode_object.em_care_discharge_status) <= 59:        # TODO magic numbers
                episode_object.em_care_dta_date_time = timezone.now()
            else:
                episode_object.em_care_dta_date_time = None
            episode_object.bed = None
            updated_field_names.add('bed')
            updated_field_names.add('em_care_depart_date_time')
            updated_field_names.add('em_care_complete_date_time')
            updated_field_names.add('em_care_dta_date_time')

        if episode_object.assigned_clinician is not None and old_episode_object.assigned_clinician is None:
            episode_object.em_care_assess_date_time = timezone.now()
            updated_field_names.add('em_care_assess_date_time')

        episode_object.save(update_fields=updated_field_names)       # TODO validate

        page_changes_json = json.dumps(__episode_page_changes(request, episode_object, old_episode_object))

        return HttpResponse(page_changes_json, content_type='application/json')
    else:
        raise Http404


# calculate the change in HTML required to render the page following the latest Episode save call
# this will be delivered as the client-side result of the AJAX post
def __episode_page_changes(request, episode_object, old_episode_object):
    accordion = __episode_accordion(request, episode_object)

    # TODO reinstate code to clear page if assigned clinician set to None?
    # if old_episode_object.assigned_clinician is None:
    #     if episode_object.assigned_clinician is not None:
    #         changes['additional_content'], changes['expanded_panels'] = __episode_additional(request, episode_object)
    # else:
    #     if episode_object.assigned_clinician is None:       # was set, now not
    #         changes['additional_content'] = ''      # clear it
    #     else:
    #         changes['additional_content'], changes['expanded_panels'] = __episode_additional(request, episode_object)

    return {
        'additional_content': __episode_additional(request, episode_object),
        'state_icon_content': __episode_state_icons(request, episode_object),
        'accordion_content': accordion[0],
        'collapsed_panels': accordion[1]
    }


def __episode_additional(request, episode_object):
    additional_content = []

    if __episode_can_discharge_early(episode_object):
        discharge_early_template = loader.get_template('sackett/episode_discharge_early.html')
        additional_content.append(discharge_early_template.render({}, request))

    if episode_object.assigned_clinician is not None:
        clinical_narrative_template = loader.get_template('sackett/episode_clinical_narrative.html')
        clinical_narrative_context = {
            'em_care_clinical_narrative': episode_object.em_care_clinical_narrative if
            episode_object.em_care_clinical_narrative is not None else '',
        }

        additional_content.append(clinical_narrative_template.render(clinical_narrative_context, request))

    return SafeString(''.join(additional_content))


# the extra sections after the basic header section in the Episode page
def __episode_accordion(request, episode_object):
    accordion_content = []
    expanded_panels = []
    accordion_panel_ids = {}

    is_discharging = False

    # Discharge
    if __episode_can_discharge(episode_object):
        discharge_template = loader.get_template('sackett/episode_discharge.html')
        discharge_form = EpisodeDischargeForm(instance=episode_object)
        discharge_context = {
            'form': discharge_form,
            'discharge_button_visible': __episode_show_complete_discharge_button(episode_object),
            'transfer_destination_visible': False if episode_object.em_care_discharge_status is None
            else int(episode_object.em_care_discharge_status) == 2018412100,    # TODO magic numbers
            'admit_speciality_visible': False if episode_object.em_care_discharge_status is None
            else 2018211100 <= int(episode_object.em_care_discharge_status) <= 2018511100 and
            int(episode_object.em_care_discharge_status) != 2018412100,
            'is_discharged': episode_object.em_care_depart_date_time is not None,
            'discharged_message': '' if episode_object.em_care_depart_date_time is None
            else episode_object.em_care_depart_date_time.strftime(
                    _('Discharged at %H:%M, %d %b %Y')),
            'is_early_discharge': episode_object.early_discharge,
        }

        expanded_panels.append(len(accordion_content))        # 'discharge')
        accordion_content.append(discharge_template.render(discharge_context, request))
        is_discharging = True

    if episode_object.assigned_clinician is not None:
        # TODO research panel

        # Injury
        if __episode_is_injury(episode_object):
            injury_template = loader.get_template('sackett/injury_detail.html')
            injury_form = InjuryDetailForm(instance=episode_object)
            drugs_alcohol_items = [] if episode_object.em_care_inj_drug_alcohol is None else\
                [{'item_id': d,
                  'item_name': PickListDataProxy.lookup_code(PickListTableTypes.EmCareInjDrugAlcohol.value, d)}
                 for d in episode_object.em_care_inj_drug_alcohol]
            injury_context = {
                'form': injury_form,
                'drugs_alcohol_items': drugs_alcohol_items,
            }
            expanded_panels.append(len(accordion_content))        # 'discharge')
            accordion_content.append(injury_template.render(injury_context, request))
            # expanded_panels.append('injury')

        # Diagnoses
        diagnoses_template = loader.get_template('sackett/episode_diagnoses.html')
        diagnoses, diagnoses_count = __episode_diagnoses(request, episode_object)
        diagnoses_context = {
            'new_diagnosis_select': diagnoses[0],
            'diagnoses': diagnoses[1:-1],
            'new_diagnosis_template': diagnoses[-1]
        }
        accordion_panel_ids['diagnoses'] = len(accordion_content)
        accordion_content.append(diagnoses_template.render(diagnoses_context, request))

        # Treatments
        treatments_template = loader.get_template('sackett/episode_treatments.html')
        treatments, treatments_count = __episode_treatments(request, episode_object)
        treatments_context = {
            'treatments': treatments,
            }

        accordion_panel_ids['treatments'] = len(accordion_content)
        accordion_content.append(treatments_template.render(treatments_context, request))

        # Investigations
        investigations_template = loader.get_template('sackett/episode_investigations.html')
        investigations, investigations_count = __episode_investigations(request, episode_object)
        investigations_context = {
            'investigations': investigations,
            }

        if not is_discharging:
            # if we have treatments, show them; if we have investigations, show the treatments panel ready for the
            # next step
            if diagnoses_count > 0 or treatments_count > 0:
                expanded_panels.append(accordion_panel_ids['diagnoses'])

            # if we have treatments, show them; if we have investigations, show the treatments panel ready for the
            # next step
            if treatments_count > 0 or investigations_count > 0:
                expanded_panels.append(accordion_panel_ids['treatments'])

            accordion_panel_ids['diagnoses'] = len(accordion_content)
            expanded_panels.append(len(accordion_content))      # regardless of investigations_count

        accordion_content.append(investigations_template.render(investigations_context, request))

    collapsed_panels = [x for x in range(len(accordion_content)) if x not in expanded_panels]
    return SafeString(''.join(accordion_content)), collapsed_panels


# Diagnosis section of Episode page
def __episode_diagnoses(request, episode_object):
    diagnoses = []
    diagnoses_count = 0

    new_diagnosis_template = loader.get_template('sackett/episode_new_single_diagnosis.html')

    diagnosis_template = loader.get_template('sackett/episode_single_diagnosis.html')

    # add one entry for new items
    diagnoses.append(new_diagnosis_template.render({'diagnoses': []}, request))

    if episode_object.em_care_diagnosis is not None and len(episode_object.em_care_diagnosis) > 0:
        decoded_diagnoses = {}
        for diagnosis in episode_object.em_care_diagnosis:
            diagnoses_count += 1
            code = diagnosis['code']
            description = DiagnosisDataProxy.lookup_code(code)
            modifier = diagnosis['mod']
            index = int(diagnosis['index'])
            decoded_diagnoses[index] = (code, description, modifier)

        for idx in sorted(decoded_diagnoses.keys()):
            diagnoses.append(diagnosis_template.render({'diagnosis_name': decoded_diagnoses[idx][1],
                                                        'diagnosis_id': decoded_diagnoses[idx][0],
                                                        'diagnosis_proven':      # TODO magic constant
                                                        True if decoded_diagnoses[idx][2] == '9' else False,
                                                        'hidden': False}, request))

    # add one blank entry for copying client-side when new diagnoses are added
    diagnoses.append(diagnosis_template.render({'diagnosis_name': '', 'diagnosis_id': '',
                                                'diagnosis_proven': False, 'hidden': True},
                                               request))

    return diagnoses, diagnoses_count


# Investigations and Treatments sections of the Episode page - basically identical functionality
def __episode_investigations_treatments(request, episode_items, picklist_type, new_item_form,
                                        new_item_template_name, item_template_name):
    items = []
    items_count = 0

    new_item_template = loader.get_template(new_item_template_name)

    item_template = loader.get_template(item_template_name)

    # add one entry for new items
    items.append(new_item_template.render({'form': new_item_form}, request))

    if episode_items is not None and len(episode_items) > 0:
        for episode_item in episode_items:
            items_count += 1
            description = PickListDataProxy.lookup_code(picklist_type,
                                                        episode_item)
            items.append(item_template.render({'item_name': description,
                                               'item_id': episode_item,
                                               'hidden': False}, request))

    # add one blank entry for copying client-side when new items are added
    items.append(item_template.render({'item_id': '', 'item_name': '', 'hidden': True}, request))

    return items, items_count


def __episode_investigations(request, episode_object):
    return __episode_investigations_treatments(request, episode_object.em_care_investigations,
                                               PickListTableTypes.EmCareInvestigations.value,
                                               EpisodeInvestigationForm(),
                                               'sackett/episode_new_single_investigation.html',
                                               'sackett/episode_single_investigation.html')


def __episode_state_icons(request, episode_object):
    return SafeString(''.join(
            ['<i class="%(class)s" data-content="%(tooltip)s"></i>' % {'class': i[0], 'tooltip': i[1]}
             for i in get_icon_set_for_bed_episode(episode_object, STATE_ICON_DEFAULT_SIZE)]
    ))


def __episode_treatments(request, episode_object):
    return __episode_investigations_treatments(request, episode_object.em_care_treatments,
                                               PickListTableTypes.EmCareTreatments.value,
                                               EpisodeTreatmentForm(),
                                               'sackett/episode_new_single_treatment.html',
                                               'sackett/episode_single_treatment.html')


def __episode_can_discharge(episode_object):
    if episode_object.early_discharge or\
            (episode_object.assigned_clinician is not None and
             episode_object.em_care_diagnosis is not None and
             len(episode_object.em_care_diagnosis) > 0):
        return True

    return False


def __episode_can_discharge_early(episode_object):
    # return episode_object.assigned_clinician is not None and\
    return not __episode_can_discharge(episode_object) and\
           episode_object.em_care_depart_date_time is None


def __episode_ready_for_discharge(episode_object):
    if episode_object.em_care_discharge_status is None:
        return False

    return __episode_show_complete_discharge_button(episode_object)


def __episode_show_complete_discharge_button(episode_object):
    if episode_object.em_care_depart_date_time is not None:
        return False

    if episode_object.early_discharge or\
            (episode_object.em_care_discharge_status is not None and
                # ((int(episode_object.em_care_discharge_status) < 2018211100 and         # TODO implement this in JS too
                #     episode_object.em_care_discharge_information_given) or      # to hide the discharge button
                ((int(episode_object.em_care_discharge_status) < 2018211100) or     # TODO magic numbers
                 int(episode_object.em_care_discharge_status) >= 2018211100)):
        return True

    return False


def __episode_is_injury(episode_object):
    # chief_complaint = PickListDataProxy.lookup_code_raw(PickListTableTypes.EmCareChiefComplaint.value,
    #                                                     episode_object.em_care_chief_complaint)
    # if chief_complaint is not None and chief_complaint.bool1:
    #     return True

    if episode_object.em_care_diagnosis is not None and len(episode_object.em_care_diagnosis) > 0:
        for diagnosis in episode_object.em_care_diagnosis:
            diagnosis_lookup = DiagnosisDataProxy.lookup_code_raw(diagnosis['code'])

            if diagnosis_lookup is not None and diagnosis_lookup.injury:
                return True

    return False


def expected_arrival(request):
    if request.method == 'POST':
        form = ExpectedArrivalForm(request.POST)

        if form.is_valid():
            new_expected = Expected(person_given_name=form.cleaned_data['person_given_name'],
                                    person_family_name=form.cleaned_data['person_family_name'],
                                    em_care_chief_complaint=form.cleaned_data['em_care_chief_complaint'],
                                    person_stated_gender=form.cleaned_data['person_stated_gender'],
                                    person_age_at_attendance=form.cleaned_data['person_age_at_attendance'],
                                    removed=False)
            new_expected.save()

            return HttpResponseRedirect(reverse('sackett:expected_arrival'))
    else:
        form = ExpectedArrivalForm()

    expected_models = Expected.objects.filter(removed=False, linked_episode__isnull=True)

    expected = [{'name': x.person_family_name + ", " + x.person_given_name,
                 'information': PickListDataProxy.lookup_code(PickListTableTypes.EmCareChiefComplaint.value,
                                                              x.em_care_chief_complaint),
                 'gender': PickListDataProxy.lookup_code(PickListTableTypes.PersonStatedGender.value,
                                                         x.person_stated_gender),
                 'age': x.person_age_at_attendance} for x in expected_models]

    return render(request, 'sackett/expected_arrival.html', {'form': form, 'expected': expected})


def gp_search(request, search):
    if request.method == 'GET':
        if len(search) <= 0:
            return HttpResponse(json.dumps({"success": False, "results": []}), content_type='application/json')

        gps = PickListDataProxy.find_by_description(PickListTableTypes.GeneralPractice.value,
                                                    search)
        return HttpResponse(json.dumps({"success": True,
                                        "results": [{"value": g[0], "name": g[1]} for g in gps]}),
                            content_type='application/json')
    else:
        raise Http404


def healthcare_facility_search(request, search):
    if request.method == 'GET':
        if len(search) <= 0:
            return HttpResponse(json.dumps({"success": False, "results": []}), content_type='application/json')

        destinations = PickListDataProxy.find_by_description(PickListTableTypes.HealthCareFacility.value,
                                                             search)
        return HttpResponse(json.dumps({"success": True,
                                        "results": [{"value": d[0], "name": d[1]} for d in destinations]}),
                            content_type='application/json')
    else:
        raise Http404


def lock_acquire(request):
    if request.method == 'POST':
        data_dict = json.loads(request.POST['data'])
        lock_uuid = recordlocking.try_acquire_lock(int(data_dict['id']), int(data_dict['type']),
                                                   int(data_dict.get('force')) == 1)

        result_json = json.dumps({'result': LockAcquireResult.Success.value if lock_uuid is not None
                                  else LockAcquireResult.Failure.value,
                                  'id': lock_uuid or ''})
        return HttpResponse(result_json, content_type='application/json')
    else:
        raise Http404


def lock_refresh(request):
    if request.method == 'POST':
        data_dict = json.loads(request.POST['data'])
        refresh_result = recordlocking.try_refresh_lock(int(data_dict['type']), data_dict['id'])

        result_json = json.dumps({'result': refresh_result})
        return HttpResponse(result_json, content_type='application/json')
    else:
        raise Http404


def lock_release(request):
    if request.method == 'POST':
        data_dict = json.loads(request.POST['data'])
        recordlocking.release_lock(int(data_dict['type']), data_dict['id'])

        return HttpResponse('', content_type='application/json')
    else:
        raise Http404


def patient_details(request, episode_id):
    episode_object = get_object_or_404(Episode, id=episode_id)

    chief_complaint = PickListDataProxy.lookup_code_raw(PickListTableTypes.EmCareChiefComplaint.value,
                                                        episode_object.em_care_chief_complaint)

    show_injury = chief_complaint.bool1 if chief_complaint is not None else False
    injury_context = {}

    if request.method == 'POST':
        form = PatientDetailsForm(request.POST)

        if form.is_valid():
            updated_field_names = set()

            episode_object.person_global_number = form.cleaned_data['person_global_number']
            updated_field_names.add('person_global_number')
            episode_object.person_local_number = form.cleaned_data['person_local_number']
            updated_field_names.add('person_local_number')
            episode_object.person_given_name = form.cleaned_data['person_given_name']
            updated_field_names.add('person_given_name')
            episode_object.person_family_name = form.cleaned_data['person_family_name']
            updated_field_names.add('person_family_name')
            episode_object.person_stated_gender = form.cleaned_data['person_stated_gender']
            updated_field_names.add('person_stated_gender')
            episode_object.person_birth_date = form.cleaned_data['person_birth_date']
            updated_field_names.add('person_birth_date')

            if episode_object.person_birth_date is not None:
                episode_object.person_age_at_attendance = __calculate_age(episode_object.person_birth_date,
                                                                          episode_object.em_care_arrive_date_time)
                updated_field_names.add('person_age_at_attendance')

            episode_object.em_care_arrive_transport_mode = form.cleaned_data['em_care_arrive_transport_mode']
            updated_field_names.add('em_care_arrive_transport_mode')
            episode_object.em_care_attendance_type = form.cleaned_data['em_care_attendance_type']
            updated_field_names.add('em_care_attendance_type')
            episode_object.em_care_referral_source = form.cleaned_data['em_care_referral_source']
            updated_field_names.add('em_care_referral_source')
            episode_object.em_care_arrive_transfer_source = form.cleaned_data['em_care_arrive_transfer_source']
            updated_field_names.add('em_care_arrive_transfer_source')
            episode_object.person_comm_lang = form.cleaned_data['person_comm_lang']
            updated_field_names.add('person_comm_lang')
            episode_object.person_interpreter_rqd = form.cleaned_data['person_interpreter_rqd']
            updated_field_names.add('person_interpreter_rqd')
            episode_object.person_interpreter_lang = form.cleaned_data['person_interpreter_lang']
            updated_field_names.add('person_interpreter_lang')

            if form.cleaned_data['withhold_identity']:
                episode_object.person_identity_withheld_reason = form.cleaned_data['person_identity_withheld_reason']
            else:
                episode_object.person_identity_withheld_reason = None
            updated_field_names.add('person_identity_withheld_reason')

            episode_object.person_usual_address_1 = form.cleaned_data['person_usual_address_1']
            updated_field_names.add('person_usual_address_1')
            episode_object.person_usual_address_2 = form.cleaned_data['person_usual_address_2']
            updated_field_names.add('person_usual_address_2')
            episode_object.person_usual_address_postcode = form.cleaned_data['person_usual_address_postcode']
            updated_field_names.add('person_usual_address_postcode')
            episode_object.person_usual_residence_type = form.cleaned_data['person_usual_residence_type']
            updated_field_names.add('person_usual_residence_type')
            episode_object.person_preferred_contact = {
                'home': form.cleaned_data['person_preferred_contact_home'],
                'mobile': form.cleaned_data['person_preferred_contact_mobile'],
                'email': form.cleaned_data['person_preferred_contact_email']}
            updated_field_names.add('person_preferred_contact')
            episode_object.person_ethnic_category = form.cleaned_data['person_ethnic_category']
            updated_field_names.add('person_ethnic_category')
            episode_object.person_gp_practice_code = form.cleaned_data['person_gp_practice_code']
            updated_field_names.add('person_gp_practice_code')
            episode_object.person_school = form.cleaned_data['person_school']
            updated_field_names.add('person_school')
            episode_object.person_companion = form.cleaned_data['person_companion']
            updated_field_names.add('person_companion')

            data_valid = True

            if show_injury:
                injury_form = InjuryDetailForm(request.POST)
                injury_context = {'form': injury_form}

                if injury_form.is_valid():
                    episode_object.em_care_inj_date_time = injury_form.cleaned_data['em_care_inj_date_time']
                    updated_field_names.add('em_care_inj_date_time')
                    episode_object.em_care_inj_activity_type = injury_form.cleaned_data['em_care_inj_activity_type']
                    updated_field_names.add('em_care_inj_activity_type')
                    episode_object.em_care_inj_activity_detail = injury_form.cleaned_data['em_care_inj_activity_detail']
                    updated_field_names.add('em_care_inj_activity_detail')
                    episode_object.em_care_inj_mechanism = injury_form.cleaned_data['em_care_inj_mechanism']
                    updated_field_names.add('em_care_inj_mechanism')
                    episode_object.em_care_inj_intent = injury_form.cleaned_data['em_care_inj_intent']
                    updated_field_names.add('em_care_inj_intent')
                    episode_object.em_care_inj_drug_alcohol = injury_form.cleaned_data['em_care_inj_drug_alcohol']
                    updated_field_names.add('em_care_inj_drug_alcohol')
                    episode_object.em_care_inj_place_type = injury_form.cleaned_data['em_care_inj_place_type']
                    updated_field_names.add('em_care_inj_place_type')
                    episode_object.em_care_inj_place_exact = injury_form.cleaned_data['em_care_inj_place_exact']
                    updated_field_names.add('em_care_inj_place_exact')
                    episode_object.em_care_inj_place_lat_long = injury_form.cleaned_data['em_care_inj_place_lat_long']
                    updated_field_names.add('em_care_inj_place_lat_long')
                else:
                    drugs_alcohol_items = [] if injury_form.cleaned_data['em_care_inj_drug_alcohol'] is None else\
                        [{'item_id': d,
                          'item_name': PickListDataProxy.lookup_code(PickListTableTypes.EmCareInjDrugAlcohol.value, d)}
                         for d in injury_form.cleaned_data['em_care_inj_drug_alcohol']]
                    injury_context['drugs_alcohol_items'] = drugs_alcohol_items
                    data_valid = False

            if data_valid:
                episode_object.save(update_fields=updated_field_names)

                # TODO return result instead
                return HttpResponseRedirect(reverse('sackett:patient_details', args=[episode_id]))
    else:
        if show_injury:
            injury_form = InjuryDetailForm(instance=episode_object)
            injury_context = {'form': injury_form}
            drugs_alcohol_items = [] if episode_object.em_care_inj_drug_alcohol is None else\
                [{'item_id': d,
                  'item_name': PickListDataProxy.lookup_code(PickListTableTypes.EmCareInjDrugAlcohol.value, d)}
                 for d in episode_object.em_care_inj_drug_alcohol]
            injury_context['drugs_alcohol_items'] = drugs_alcohol_items

    form = PatientDetailsForm(instance=episode_object)

    injury_panel_template = loader.get_template('sackett/injury_detail.html')
    injury_panel = '' if not show_injury else injury_panel_template.render(injury_context, request)

    context = {'form': form, 'breach_form': EpisodeBreachForm(),    # always an empty form; this is posted elsewhere
               'episode_id': episode_id,
               'age': _('%(y)d y %(m)d m') %
               {'y': int(episode_object.person_age_at_attendance or 0),
                'm': int(100 * ((episode_object.person_age_at_attendance or 0) -
                                int(episode_object.person_age_at_attendance or 0)))},
               'age_est': episode_object.person_birth_date is None,
               'full_name': get_display_name(episode_object),
               'injury_panel': injury_panel,
               'show_injury': show_injury}

    return render(request, 'sackett/patient_details.html', context)


def patient_details_overview(request):
    # depart date/time not set => patient not discharged
    patients = Episode.objects.filter(em_care_depart_date_time__isnull=True)\
                              .order_by('person_family_name', 'person_given_name')\
                              .all()

    grouped_patients = groupby(patients, lambda x: x.person_family_name[0])

    context = {
        'grouped_patients': [(g[0].upper(),
                              [{'name': get_display_name(p),
                                'arrival_date': p.em_care_arrive_date_time,
                                'chief_complaint':
                                    PickListDataProxy.lookup_code(PickListTableTypes.EmCareChiefComplaint.value,
                                                                  p.em_care_chief_complaint),
                                'id': p.id}
                               for p in g[1]])
            for g in grouped_patients],
        'first_patient_id': patients[0].id if len(patients) > 0 else 0
    }

    return render(request, 'sackett/patient_details_overview.html', context)


def school_search(request, search):
    if request.method == 'GET':
        if len(search) <= 0:
            return HttpResponse(json.dumps({"success": False, "results": []}), content_type='application/json')

        schools = PickListDataProxy.find_by_description(PickListTableTypes.School.value,
                                                        search)
        return HttpResponse(json.dumps({"success": True,
                                        "results": [{"value": s[0], "name": s[1]} for s in schools]}),
                            content_type='application/json')
    else:
        raise Http404


def triage_arrival(request):
    if request.method == 'POST':
        # injury_form = InjuryDetailForm(request.POST)
        # injury_context = {'form': injury_form}
        form = TriageArrivalForm(request.POST)
        if form.is_valid():
            zone = Zone.objects.get(id=int(form.cleaned_data['zone_id']))   # TODO validate
            waiting_list_bed = zone.bed_set.get(template_index=ZONE_WAITING_LIST_BED_INDEX)

            new_episode = Episode(person_given_name=form.cleaned_data['person_given_name'],
                                  person_family_name=form.cleaned_data['person_family_name'],
                                  person_stated_gender=form.cleaned_data['person_stated_gender'],
                                  person_age_at_attendance=form.cleaned_data['person_age_at_attendance'],
                                  em_care_arrive_transport_mode=form.cleaned_data['em_care_arrive_transport_mode'],
                                  em_care_chief_complaint=form.cleaned_data['em_care_chief_complaint'],
                                  em_care_attendance_type=form.cleaned_data['em_care_attendance_type'],
                                  person_interpreter_rqd=form.cleaned_data['person_interpreter_rqd'],
                                  em_care_assessment=form.cleaned_data['em_care_assessment'],
                                  bed=waiting_list_bed,
                                  em_care_arrive_date_time=timezone.now(),
                                  em_care_unique_id=uniqueid.generate_next())

            if new_episode.person_interpreter_rqd:
                new_episode.person_interpreter_lang = form.cleaned_data['person_interpreter_lang']

            if new_episode.person_age_at_attendance is not None:
                age_months = 100 * (new_episode.person_age_at_attendance - int(new_episode.person_age_at_attendance))

                if (20 <= age_months <= 90) and (age_months % 10 == 0):     # assume that e.g. 32.7 is really 32.07
                    new_episode.person_age_at_attendance = Decimal(int(new_episode.person_age_at_attendance)) +\
                                                           (Decimal(int(age_months / 10)) / 100)
                elif age_months > 11:           # TODO report an error if age_months in (13, 19) or > 90
                    new_episode.person_age_at_attendance = Decimal(int(new_episode.person_age_at_attendance)) +\
                                                           (Decimal(int(age_months / 10)) / 100)

            # chief_complaint = PickListDataProxy.lookup_code_raw(PickListTableTypes.EmCareChiefComplaint.value,
            #                                                     new_episode.em_care_chief_complaint)

            # data_valid = True

            # if chief_complaint.bool1:
            #     if injury_form.is_valid():
            #         new_episode.em_care_inj_date_time = injury_form.cleaned_data['em_care_inj_date_time']
            #         new_episode.em_care_inj_activity_type = injury_form.cleaned_data['em_care_inj_activity_type']
            #         new_episode.em_care_inj_activity_detail = injury_form.cleaned_data['em_care_inj_activity_detail']
            #         new_episode.em_care_inj_mechanism = injury_form.cleaned_data['em_care_inj_mechanism']
            #         new_episode.em_care_inj_intent = injury_form.cleaned_data['em_care_inj_intent']
            #         new_episode.em_care_inj_drug_alcohol = injury_form.cleaned_data['em_care_inj_drug_alcohol']
            #         new_episode.em_care_inj_place_type = injury_form.cleaned_data['em_care_inj_place_type']
            #         new_episode.em_care_inj_place_exact = injury_form.cleaned_data['em_care_inj_place_exact']
            #         new_episode.em_care_inj_place_lat_long = injury_form.cleaned_data['em_care_inj_place_lat_long']
            #     else:
            #         drugs_alcohol_items = [] if injury_form.cleaned_data['em_care_inj_drug_alcohol'] is None else\
            #             [{'item_id': d,
            #               'item_name': PickListDataProxy.lookup_code(PickListTableTypes.EmCareInjDrugAlcohol.value, d)}
            #              for d in injury_form.cleaned_data['em_care_inj_drug_alcohol']]
            #         injury_context['drugs_alcohol_items'] = drugs_alcohol_items
            #         data_valid = False

            # if data_valid:
            new_episode.save()

            if form.cleaned_data['expected_arrival'] is not None:   # \
                    # and form.cleaned_data['expected_arrival'].isdecimal():
                # TODO validate
                expected = Expected.objects.get(id=int(form.cleaned_data['expected_arrival']))

                if expected is not None:
                    expected.linked_episode = new_episode
                    expected.save()

            return HttpResponseRedirect(reverse('sackett:triage_arrival'))      # TODO return result instead
    else:
        form = TriageArrivalForm()
        # injury_form = InjuryDetailForm()
        # injury_context = {'form': injury_form}

    # injury_panel_template = loader.get_template('sackett/injury_detail.html')
    # injury_panel = injury_panel_template.render(injury_context, request)

    return render(request, 'sackett/triage_arrival.html', {'form': form})   # , 'injury_panel': injury_panel})


def user_management_all(request, show_inactive=0):
    users = [Expando(first_name=u.first_name, last_name=u.last_name, username=u.username, is_enabled=u.is_active,
                     id=u.id)
             for u in get_user_model().objects.filter(is_active=True)
             if not u.has_perm('sackett.is_consultant') and (show_inactive == 1 or u.is_active) and
             not u.is_superuser]

    consultants = [Expando(first_name=u.first_name, last_name=u.last_name, username=u.username,
                           is_enabled=u.has_perm('sackett.can_consult'), id=u.id)
                   for u in get_user_model().objects.filter(is_active=True)
                   if u.has_perm('sackett.is_consultant') and (show_inactive == 1 or u.is_active) and
                   not u.is_superuser]

    return render(request, 'sackett/user_management_all.html', {'users': users, 'consultants': consultants})


def user_management_add(request, is_doctor):
    if is_doctor == '0':
        return user_management_add_user(request)
    else:
        return user_management_add_doctor(request)


def user_management_add_doctor(request):
    saved = False
    saved_first_name = ''
    saved_last_name = ''

    if request.method == 'POST':
        form = UserManagementAddDoctorForm(request.POST)

        if form.is_valid():
            stub = '%(first_name)s%(last_name)s' % {'first_name': form.cleaned_data['first_name'],
                                                    'last_name': form.cleaned_data['last_name']}
            stub_count = get_user_model().objects.filter(username__startswith=stub).count()

            generated_username = '%(stub)s-%(stub_count)s' % {'stub': stub, 'stub_count': stub_count}

            while get_user_model().objects.filter(username=generated_username).count() > 0:
                stub_count += 1
                generated_username = '%(stub)s-%(stub_count)s' % {'stub': stub, 'stub_count': stub_count}

            # note: password left intentionally unset, as this will leave the user unable to login
            new_user = get_user_model().objects.create_user(username=generated_username)
            new_user.first_name = form.cleaned_data['first_name']
            new_user.last_name = form.cleaned_data['last_name']

            content_type = ContentType.objects.get_for_model(UserPermissionSupport)
            new_user.user_permissions.add(Permission.objects.get(content_type=content_type, codename='is_consultant'))
            new_user.user_permissions.add(Permission.objects.get(content_type=content_type, codename='can_consult'))
            new_user.save()

            form = UserManagementAddDoctorForm()
            saved = True
            saved_first_name = new_user.first_name
            saved_last_name = new_user.last_name
    else:
        form = UserManagementAddDoctorForm()

    return render(request, 'sackett/user_management_add_doctor.html', {'form': form, 'saved': saved,
                                                                       'saved_first_name': saved_first_name,
                                                                       'saved_last_name': saved_last_name})


def user_management_add_user(request):
    saved = False
    saved_username = ''

    if request.method == 'POST':
        form = UserManagementAddEditUserForm(request.POST, new_user=True)

        if form.is_valid():
            new_user = get_user_model().objects.create_user(username=form.cleaned_data['username'],
                                                            password=form.cleaned_data['password'])
            if new_user:
                content_type = ContentType.objects.get_for_model(UserPermissionSupport)

                if not form.cleaned_data['login_enabled']:
                    new_user.is_active = False

                if form.cleaned_data['perm_user_admin']:
                    new_user.user_permissions.add(Permission.objects.get(content_type=content_type,
                                                                         codename='can_administer_users'))
                if form.cleaned_data['perm_sys_admin']:
                    new_user.user_permissions.add(Permission.objects.get(content_type=content_type,
                                                                         codename='can_modify_org'))
                    new_user.user_permissions.add(Permission.objects.get(content_type=content_type,
                                                                         codename='can_administer_zones'))
                if form.cleaned_data['perm_clear_consultant']:
                    new_user.user_permissions.add(Permission.objects.get(content_type=content_type,
                                                                         codename='can_clear_consultant'))
                if form.cleaned_data['perm_undischarge']:
                    new_user.user_permissions.add(Permission.objects.get(content_type=content_type,
                                                                         codename='can_undischarge'))
                if form.cleaned_data['perm_breaches']:
                    new_user.user_permissions.add(Permission.objects.get(content_type=content_type,
                                                                         codename='can_review_breaches'))
                if form.cleaned_data['perm_view_dashboard']:
                    new_user.user_permissions.add(Permission.objects.get(content_type=content_type,
                                                                         codename='can_view_dashboard'))
                if form.cleaned_data['perm_export_data']:
                    new_user.user_permissions.add(Permission.objects.get(content_type=content_type,
                                                                         codename='can_export_data'))

                new_user.save()

                form = UserManagementAddEditUserForm()
                saved = True
                saved_username = new_user.username
    else:
        form = UserManagementAddEditUserForm()

    return render(request, 'sackett/user_management_add_edit_user.html', {'form': form, 'adding': True, 'saved': saved,
                                                                          'saved_username': saved_username})


def user_management_delete_doctor(request, user_id):
    user = get_user_model().objects.filter(id=user_id).first()

    if user is not None and not user.has_usable_password() and not user.is_superuser\
            and user.has_perm('sackett.is_consultant'):
        user.is_active = False
        user.save()

    return user_management_all(request)


def user_management_disable_doctor(request, user_id):
    user = get_user_model().objects.filter(id=user_id).first()

    if user is not None and not user.has_usable_password() and not user.is_superuser\
            and user.has_perm('sackett.can_consult') and user.has_perm('sackett.is_consultant'):
        content_type = ContentType.objects.get_for_model(UserPermissionSupport)
        user.user_permissions.remove(Permission.objects.get(content_type=content_type,
                                                            codename='can_consult'))
        user.save()

    return user_management_all(request)


def user_management_edit_user(request, user_id):
    saved = False
    saved_username = ''

    if request.method == 'POST':
        form = UserManagementAddEditUserForm(request.POST)

        if form.is_valid():
            editing_user = get_user_model().objects.filter(id=user_id).first()

            if editing_user and user_id != request.user.id:
                if form.cleaned_data['password'] and\
                                form.cleaned_data['password'] == form.cleaned_data['confirm_password']:
                    editing_user.password = make_password(form.cleaned_data['password'])

                content_type = ContentType.objects.get_for_model(UserPermissionSupport)

                if not form.cleaned_data['login_enabled']:
                    editing_user.is_active = False

                if form.cleaned_data['perm_user_admin'] and not editing_user.has_perm('sackett.can_administer_users'):
                    editing_user.user_permissions.add(Permission.objects.get(content_type=content_type,
                                                                             codename='can_administer_users'))
                elif not form.cleaned_data['perm_user_admin'] and\
                        editing_user.has_perm('sackett.can_administer_users'):
                    editing_user.user_permissions.delete(Permission.objects.get(content_type=content_type,
                                                                                codename='can_administer_users'))

                if form.cleaned_data['perm_sys_admin']:
                    if not editing_user.has_perm('sackett.can_modify_org'):
                        editing_user.user_permissions.add(Permission.objects.get(content_type=content_type,
                                                                                 codename='can_modify_org'))
                    if not editing_user.has_perm('sackett.can_administer_zones'):
                        editing_user.user_permissions.add(Permission.objects.get(content_type=content_type,
                                                                                 codename='can_administer_zones'))
                else:
                    if editing_user.has_perm('sackett.can_modify_org'):
                        editing_user.user_permissions.delete(Permission.objects.get(content_type=content_type,
                                                                                    codename='can_modify_org'))
                    if editing_user.has_perm('sackett.can_administer_zones'):
                        editing_user.user_permissions.delete(Permission.objects.get(content_type=content_type,
                                                                                    codename='can_administer_zones'))

                if form.cleaned_data['perm_clear_consultant'] and\
                        not editing_user.has_perm('sackett.can_clear_consultant'):
                    editing_user.user_permissions.add(Permission.objects.get(content_type=content_type,
                                                                             codename='can_clear_consultant'))
                elif not form.cleaned_data['perm_clear_consultant'] and\
                        editing_user.has_perm('sackett.can_clear_consultant'):
                    editing_user.user_permissions.delete(Permission.objects.get(content_type=content_type,
                                                                                codename='can_clear_consultant'))

                if form.cleaned_data['perm_undischarge'] and\
                        not editing_user.has_perm('sackett.can_undischarge'):
                    editing_user.user_permissions.add(Permission.objects.get(content_type=content_type,
                                                                             codename='can_undischarge'))
                elif form.cleaned_data['perm_undischarge'] and\
                        editing_user.has_perm('sackett.can_undischarge'):
                    editing_user.user_permissions.delete(Permission.objects.get(content_type=content_type,
                                                                                codename='can_undischarge'))

                if form.cleaned_data['perm_breaches'] and\
                        not editing_user.has_perm('sackett.can_review_breaches'):
                    editing_user.user_permissions.add(Permission.objects.get(content_type=content_type,
                                                                             codename='can_review_breaches'))
                elif form.cleaned_data['perm_breaches'] and\
                        editing_user.has_perm('sackett.can_review_breaches'):
                    editing_user.user_permissions.delete(Permission.objects.get(content_type=content_type,
                                                                                codename='can_review_breaches'))

                if form.cleaned_data['perm_view_dashboard'] and\
                        not editing_user.has_perm('sackett.can_view_dashboard'):
                    editing_user.user_permissions.add(Permission.objects.get(content_type=content_type,
                                                                             codename='can_view_dashboard'))
                elif form.cleaned_data['perm_view_dashboard'] and\
                        editing_user.has_perm('sackett.can_view_dashboard'):
                    editing_user.user_permissions.delete(Permission.objects.get(content_type=content_type,
                                                                                codename='can_view_dashboard'))

                if form.cleaned_data['perm_export_data'] and\
                        not editing_user.has_perm('sackett.can_export_data'):
                    editing_user.user_permissions.add(Permission.objects.get(content_type=content_type,
                                                                             codename='can_export_data'))
                elif form.cleaned_data['perm_export_data'] and\
                        editing_user.has_perm('sackett.can_export_data'):
                    editing_user.user_permissions.delete(Permission.objects.get(content_type=content_type,
                                                                                codename='can_export_data'))

                editing_user.save()

                saved = True
                saved_username = editing_user.username
    else:
        editing_user = get_object_or_404(get_user_model(), id=user_id)

        if not editing_user.is_superuser:
            form = UserManagementAddEditUserForm(user=editing_user)
        else:
            return Http404()

    return render(request, 'sackett/user_management_add_edit_user.html', {'form': form, 'adding': False, 'saved': saved,
                                                                          'saved_username': saved_username})


def user_management_enable_doctor(request, user_id):
    user = get_user_model().objects.filter(id=user_id).first()

    if user is not None and not user.has_usable_password() and not user.is_superuser\
            and not user.has_perm('sackett.can_consult') and user.has_perm('sackett.is_consultant'):
        content_type = ContentType.objects.get_for_model(UserPermissionSupport)
        user.user_permissions.add(Permission.objects.get(content_type=content_type,
                                                         codename='can_consult'))
        user.save()

    return user_management_all(request)


def user_management_login(request):
    if request.method == 'POST':
        form = UserManagementLoginForm(request.POST)

        if form.is_valid():
            user = form.authenticated_user

            if user is not None and user.is_active:
                login(request, user)

                return redirect('sackett:default')
    else:
        form = UserManagementLoginForm()

    return render(request, 'sackett/user_management_login.html', {'form': form})


def user_management_logout(request):
    logout(request)
    return redirect('sackett:default')


def user_management_personal(request):
    password_updated = False

    if request.method == 'POST':
        form = UserManagementPersonalForm(request.POST, user=request.user)

        if form.is_valid():
            user = form.authenticated_user

            if user is not None and user.is_active:
                user.password = make_password(form.cleaned_data['new_password'])
                user.save()
                update_session_auth_hash(request, user)
                form = UserManagementPersonalForm()
                password_updated = True
    else:
        form = UserManagementPersonalForm()

    return render(request, 'sackett/user_management_personal.html', {'form': form,
                                                                     'current_user': request.user.username,
                                                                     'password_updated': password_updated})


def zone_image(request, image_path):
    try:
        full_image_path = os.path.join(settings.BASE_DIR, 'templates', 'sackett', 'zone', image_path)

        with open(full_image_path, "rb") as f:
            return HttpResponse(f.read(), mimetypes.MimeTypes().guess_type(full_image_path)[0])
    except IOError:
        return Http404()


def zone_overview(request, zone_id):
    zone = get_object_or_404(Zone, id=zone_id)

    if request.method == 'POST':
        drag_drop_form = ZoneDragDropForm(request.POST)

        if drag_drop_form.is_valid():
            move_episode(zone_id,
                         drag_drop_form.cleaned_data['source_id'],
                         drag_drop_form.cleaned_data['destination_id'])
            return zone_overview_content_only(request, zone_id)
    else:
        drag_drop_form = ZoneDragDropForm()

    page_context = {
        'content': __zone_overview_core(request, zone),
        'drag_drop_form': drag_drop_form,
        'page_title': _('Clinical areas :: %(zone_label)s') % {'zone_label': zone.label},
        'refresh_url': reverse('sackett:zone_overview_content_only', args=[zone_id]),
        # 'zone_header': _('%(zone_label)s') % {'zone_label': zone.label}, TODO: why did I do this? translation not req.
        'zone_header': zone.label,
        'zone_id': zone_id,     # for the drag-drop form action url
    }

    return render(request, 'sackett/zone_frame.html', page_context)


def zone_overview_content_only(request, zone_id):
    zone = get_object_or_404(Zone, id=zone_id)

    return HttpResponse(__zone_overview_core(request, zone))


def zone_summary(request):
    zones = get_zones_list()

    context = {
        'zones': [{'label': z.label, 'id': z.id, 'content': __zone_summary_core(request, z)}
                  for z in zones],
        'refresh_url': reverse('sackett:zone_summary_content_only'),
    }

    return render(request, 'sackett/zone_summary.html', context)


def zone_summary_content_only(request):
    zones = get_zones_list()

    context = {
        'zones': [{'label': z.label, 'id': z.id, 'content': __zone_summary_core(request, z)}
                  for z in zones]
    }

    return render(request, 'sackett/zone_summary_content_only.html', context)


def __calculate_age(birth_date, arrival_date):
    birth_date_only = date(birth_date.year, birth_date.month, birth_date.day)
    birth_date_this_year = date(arrival_date.year, birth_date.month, birth_date.day)
    arrival_date_only = date(arrival_date.year, arrival_date.month, arrival_date.day)
    gross_age = arrival_date_only.year - birth_date_only.year
    delta_months = (arrival_date_only - birth_date_this_year).days / (365.25 / 12)

    if delta_months < 0:
        gross_age -= 1
        delta_months += 12

    return Decimal(gross_age) + (Decimal(int(delta_months)) / 100)


def __zone_overview_core(request, zone):
    return __zone_render_core(request, zone, 'sackett/empty_bed_template.html', 'sackett/occupied_bed_template.html',
                              'sackett/waiting_list_item_template.html', 'template', STATE_ICON_DEFAULT_SIZE)


def __zone_summary_core(request, zone):
    return __zone_render_core(request, zone, 'sackett/empty_bed_template_summary.html',
                              'sackett/occupied_bed_template_summary.html',
                              'sackett/waiting_list_item_template_summary.html', 'summary_template',
                              STATE_ICON_DEFAULT_SIZE - 1)


def __zone_render_core(request, zone, empty_bed_template, occupied_bed_template, waiting_list_item_template,
                       zone_template_property, icon_size_base):
    if not is_user_authorised_for_zone(zone.id):
        raise PermissionDenied

    beds = zone.bed_set.all()
    empty_bed_template = loader.get_template(empty_bed_template)
    occupied_bed_template = loader.get_template(occupied_bed_template)
    waiting_list_item_template = loader.get_template(waiting_list_item_template)

    # list of episodes in this zone indexed by bed id
    episodes = Episode.objects.filter(bed__zone_id=zone.id)\
        .filter(bed__template_index__gt=ZONE_WAITING_LIST_BED_INDEX)
    grouped_episodes = {g[0]: g[1] for g in multi_group_by(episodes, ['bed_id', 'id'], ['bed_id', 'id'])}

    waiting_list = sorted([e for e in Episode.objects.filter(bed__zone_id=zone.id)
                          .filter(bed__template_index=ZONE_WAITING_LIST_BED_INDEX)],
                          key=get_triage_category)

    # combine beds and episodes to produce a collection of beds, some of which empty, some of which having an episode
    zone_context = {
        'beds': {b.name: SafeString(
                ''.join([occupied_bed_template.render({'episode': single_episode,
                                                       'complaint': PickListDataProxy.lookup_code(
                                                               PickListTableTypes.EmCareChiefComplaint.value,
                                                               single_episode.em_care_chief_complaint),
                                                       'bed': b,
                                                       'drag_data_id': single_episode.id,
                                                       'drag_bed_id': b.template_index,
                                                       'state_icons': get_icon_set_for_bed_episode(single_episode,
                                                                                                   icon_size_base)},
                                                      request)
                         for single_episode in grouped_episodes[b.id]
                         ]))
                 if grouped_episodes.get(b.id) is not None and b.template_index > ZONE_WAITING_LIST_BED_INDEX
                 else empty_bed_template.render({'bed': b,
                                                 'drag_bed_id': b.template_index}, request)
                 for b in beds},
        'waiting_list': [waiting_list_item_template.render({'episode': w,
                                                            'complaint': PickListDataProxy.lookup_code(
                                                                    PickListTableTypes.EmCareChiefComplaint.value,
                                                                    w.em_care_chief_complaint),
                                                            'drag_data_id': str(w.id),
                                                            'drag_bed_id': ZONE_WAITING_LIST_BED_INDEX,
                                                            'state_icons': get_icon_set_for_waiting_episode(w)})
                         # TODO: leaking db ids - change?
                         for w in waiting_list] if waiting_list is not None else [],
        'waiting_list_bed_id': ZONE_WAITING_LIST_DRAG_DATA_ID,
    }

    # load zone template
    zone_template = loader.get_template('sackett/zone/' + getattr(zone, zone_template_property, ''))

    zone_content = zone_template.render(zone_context, request)

    return zone_content

# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-03-04 07:22
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('sackett', '0004_uniqueidentifier'),
    ]

    operations = [
        migrations.CreateModel(
            name='DiagnosisData',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('group1', models.CharField(max_length=64)),
                ('group2', models.CharField(max_length=64)),
                ('group3', models.CharField(max_length=64)),
                ('sort1', models.IntegerField()),
                ('sort2', models.IntegerField()),
                ('sort3', models.IntegerField()),
                ('diagnosis', models.CharField(max_length=64)),
                ('snomed_code', models.CharField(max_length=64)),
                ('snomed_term', models.CharField(max_length=64)),
                ('injury', models.BooleanField()),
                ('aec', models.BooleanField()),
                ('post_macro', models.CharField(max_length=128, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='DiagnosisDataSearchTerm',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('term', models.CharField(max_length=64)),
            ],
        ),
        migrations.AlterField(
            model_name='episode',
            name='action',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='episode',
            name='assigned_clinician',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='episode',
            name='bed',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='sackett.Bed'),
        ),
        migrations.AlterField(
            model_name='episode',
            name='em_care_admit_speciality',
            field=models.CharField(blank=True, db_column='EmCareSpeciality', max_length=18, null=True),
        ),
        migrations.AlterField(
            model_name='episode',
            name='em_care_amb_unique_id',
            field=models.CharField(blank=True, db_column='EmCareAmbUniqueId', max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='episode',
            name='em_care_arrive_date_time',
            field=models.DateTimeField(blank=True, db_column='EmCareArriveDateTime', null=True),
        ),
        migrations.AlterField(
            model_name='episode',
            name='em_care_arrive_transfer_source',
            field=models.CharField(blank=True, db_column='EmCareArriveTransferSource', max_length=9, null=True),
        ),
        migrations.AlterField(
            model_name='episode',
            name='em_care_arrive_transport_mode',
            field=models.CharField(blank=True, db_column='EmCareArriveTransportMode', max_length=2, null=True),
        ),
        migrations.AlterField(
            model_name='episode',
            name='em_care_assess_date_time',
            field=models.DateTimeField(blank=True, db_column='EmCareAssessDateTime', null=True),
        ),
        migrations.AlterField(
            model_name='episode',
            name='em_care_assessment',
            field=models.CharField(blank=True, db_column='EmCareAssessment', max_length=512, null=True),
        ),
        migrations.AlterField(
            model_name='episode',
            name='em_care_attendance_type',
            field=models.CharField(blank=True, db_column='EmCareAttendanceType', max_length=2, null=True),
        ),
        migrations.AlterField(
            model_name='episode',
            name='em_care_chief_complaint',
            field=models.CharField(blank=True, db_column='EmCareChiefComplaint', max_length=18, null=True),
        ),
        migrations.AlterField(
            model_name='episode',
            name='em_care_clinical_narrative',
            field=models.CharField(blank=True, db_column='EmCareClinicalNarrative', max_length=4096, null=True),
        ),
        migrations.AlterField(
            model_name='episode',
            name='em_care_clinicians',
            field=models.CharField(blank=True, db_column='EmCareClinicians', max_length=4096, null=True),
        ),
        migrations.AlterField(
            model_name='episode',
            name='em_care_complete_date_time',
            field=models.DateTimeField(blank=True, db_column='EmCareCompleteDateTime', null=True),
        ),
        migrations.AlterField(
            model_name='episode',
            name='em_care_depart_date_time',
            field=models.DateTimeField(blank=True, db_column='EmCareDepartDateTime', null=True),
        ),
        migrations.AlterField(
            model_name='episode',
            name='em_care_diagnosis',
            field=models.CharField(blank=True, db_column='EmCareDiagnosis', max_length=4096, null=True),
        ),
        migrations.AlterField(
            model_name='episode',
            name='em_care_discharge_follow_up',
            field=models.CharField(blank=True, db_column='EmCareDischargeFollowUp', max_length=2, null=True),
        ),
        migrations.AlterField(
            model_name='episode',
            name='em_care_discharge_information_given',
            field=models.CharField(blank=True, db_column='EmCareDischargeInformationGiven', max_length=18, null=True),
        ),
        migrations.AlterField(
            model_name='episode',
            name='em_care_discharge_instructions',
            field=models.CharField(blank=True, db_column='EmCareDischargeInstructions', max_length=4096, null=True),
        ),
        migrations.AlterField(
            model_name='episode',
            name='em_care_discharge_medication',
            field=models.CharField(blank=True, db_column='EmCareDischargeMedication', max_length=4096, null=True),
        ),
        migrations.AlterField(
            model_name='episode',
            name='em_care_discharge_safeguarding',
            field=models.CharField(blank=True, db_column='EmCareDischargeSafeguarding', max_length=2, null=True),
        ),
        migrations.AlterField(
            model_name='episode',
            name='em_care_discharge_status',
            field=models.CharField(blank=True, db_column='EmCareDischargeStatus', max_length=2, null=True),
        ),
        migrations.AlterField(
            model_name='episode',
            name='em_care_dta_date_time',
            field=models.DateTimeField(blank=True, db_column='EmCareDtaDateTime', null=True),
        ),
        migrations.AlterField(
            model_name='episode',
            name='em_care_inj_activity_detail',
            field=models.CharField(blank=True, db_column='EmCareInjActivityDetail', max_length=18, null=True),
        ),
        migrations.AlterField(
            model_name='episode',
            name='em_care_inj_activity_type',
            field=models.CharField(blank=True, db_column='EmCareInjActivityType', max_length=18, null=True),
        ),
        migrations.AlterField(
            model_name='episode',
            name='em_care_inj_date_time',
            field=models.DateTimeField(blank=True, db_column='EmCareInjDateTime', null=True),
        ),
        migrations.AlterField(
            model_name='episode',
            name='em_care_inj_drug_alcohol',
            field=models.CharField(blank=True, db_column='EmCareInjDrugAlcohol', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='episode',
            name='em_care_inj_intent',
            field=models.CharField(blank=True, db_column='EmCareInjIntent', max_length=18, null=True),
        ),
        migrations.AlterField(
            model_name='episode',
            name='em_care_inj_mechanism',
            field=models.CharField(blank=True, db_column='EmCareInjMechanism', max_length=18, null=True),
        ),
        migrations.AlterField(
            model_name='episode',
            name='em_care_inj_place_exact',
            field=models.CharField(blank=True, db_column='EmCareInjPlaceExact', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='episode',
            name='em_care_inj_place_lat_long',
            field=models.CharField(blank=True, db_column='EmCareInjPlaceLatLong', max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='episode',
            name='em_care_inj_place_type',
            field=models.CharField(blank=True, db_column='EmCareInjPlaceType', max_length=2, null=True),
        ),
        migrations.AlterField(
            model_name='episode',
            name='em_care_investigations',
            field=models.CharField(blank=True, db_column='EmCareInvestigations', max_length=4096, null=True),
        ),
        migrations.AlterField(
            model_name='episode',
            name='em_care_provider_org_code',
            field=models.CharField(blank=True, db_column='EmCareProviderOrgCode', max_length=9, null=True),
        ),
        migrations.AlterField(
            model_name='episode',
            name='em_care_provider_site_code',
            field=models.CharField(blank=True, db_column='EmCareProviderSiteCode', max_length=9, null=True),
        ),
        migrations.AlterField(
            model_name='episode',
            name='em_care_provider_site_type',
            field=models.CharField(blank=True, db_column='EmCareProviderSiteType', max_length=1, null=True),
        ),
        migrations.AlterField(
            model_name='episode',
            name='em_care_referral_source',
            field=models.CharField(blank=True, db_column='EmCareReferralSource', max_length=2, null=True),
        ),
        migrations.AlterField(
            model_name='episode',
            name='em_care_referred_service',
            field=models.CharField(blank=True, db_column='EmCareReferredService', max_length=4096, null=True),
        ),
        migrations.AlterField(
            model_name='episode',
            name='em_care_research',
            field=models.CharField(blank=True, db_column='EmCareResearch', max_length=4096, null=True),
        ),
        migrations.AlterField(
            model_name='episode',
            name='em_care_transfer_destination',
            field=models.CharField(blank=True, db_column='EmCareTransferDestination', max_length=9, null=True),
        ),
        migrations.AlterField(
            model_name='episode',
            name='em_care_treatments',
            field=models.CharField(blank=True, db_column='EmCareTreatments', max_length=4096, null=True),
        ),
        migrations.AlterField(
            model_name='episode',
            name='em_care_unique_id',
            field=models.BigIntegerField(blank=True, db_column='EmCareUniqueId'),
        ),
        migrations.AlterField(
            model_name='episode',
            name='person_additional_information',
            field=models.CharField(blank=True, db_column='PersonAdditionalInformation', max_length=4096, null=True),
        ),
        migrations.AlterField(
            model_name='episode',
            name='person_age_at_attendance',
            field=models.IntegerField(blank=True, db_column='PersonAgeAtAttendance', null=True),
        ),
        migrations.AlterField(
            model_name='episode',
            name='person_allergies_adverse_reaction',
            field=models.CharField(blank=True, db_column='PersonAllergiesAdverseReaction', max_length=4096, null=True),
        ),
        migrations.AlterField(
            model_name='episode',
            name='person_birth_date',
            field=models.IntegerField(blank=True, db_column='PersonBirthDate', null=True),
        ),
        migrations.AlterField(
            model_name='episode',
            name='person_comm_lang',
            field=models.CharField(blank=True, db_column='PersonCommLang', max_length=18, null=True),
        ),
        migrations.AlterField(
            model_name='episode',
            name='person_comorbidities',
            field=models.CharField(blank=True, db_column='PersonComorbidities', max_length=4096, null=True),
        ),
        migrations.AlterField(
            model_name='episode',
            name='person_companion',
            field=models.CharField(blank=True, db_column='PersonCompanion', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='episode',
            name='person_current_meds',
            field=models.CharField(blank=True, db_column='PersonCurrentMeds', max_length=4096, null=True),
        ),
        migrations.AlterField(
            model_name='episode',
            name='person_ethnic_category',
            field=models.CharField(blank=True, db_column='PersonEthnicCategory', max_length=2, null=True),
        ),
        migrations.AlterField(
            model_name='episode',
            name='person_family_name',
            field=models.CharField(blank=True, db_column='PersonFamilyName', max_length=35, null=True),
        ),
        migrations.AlterField(
            model_name='episode',
            name='person_given_name',
            field=models.CharField(blank=True, db_column='PersonGivenName', max_length=35, null=True),
        ),
        migrations.AlterField(
            model_name='episode',
            name='person_global_number',
            field=models.CharField(blank=True, db_column='PersonGlobalNumber', max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='episode',
            name='person_global_number_status_indicator',
            field=models.CharField(blank=True, db_column='PersonGlobalNumberStatusIndicator', max_length=2, null=True),
        ),
        migrations.AlterField(
            model_name='episode',
            name='person_gp_practice_code',
            field=models.CharField(blank=True, db_column='PersonGpPracticeCode', max_length=6, null=True),
        ),
        migrations.AlterField(
            model_name='episode',
            name='person_identity_withheld_reason',
            field=models.CharField(blank=True, db_column='PersonIdentityWithheldReason', max_length=2, null=True),
        ),
        migrations.AlterField(
            model_name='episode',
            name='person_interpreter_lang',
            field=models.CharField(blank=True, db_column='PersonInterpreterLang', max_length=18, null=True),
        ),
        migrations.AlterField(
            model_name='episode',
            name='person_interpreter_rqd',
            field=models.CharField(blank=True, db_column='PersonInterpreterRqd', max_length=18, null=True),
        ),
        migrations.AlterField(
            model_name='episode',
            name='person_local_number',
            field=models.CharField(blank=True, db_column='PersonLocalNumber', max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='episode',
            name='person_preferred_contact',
            field=models.CharField(blank=True, db_column='PersonPreferredContact', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='episode',
            name='person_residence_lsoa',
            field=models.CharField(blank=True, db_column='PersonResidenceLsoa', max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='episode',
            name='person_residence_org_code',
            field=models.CharField(blank=True, db_column='PersonResidenceOrgCode', max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='episode',
            name='person_school',
            field=models.CharField(blank=True, db_column='PersonSchool', max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='episode',
            name='person_special_patient_note_local',
            field=models.CharField(blank=True, db_column='PersonSpecialPatientNoteLocal', max_length=4096, null=True),
        ),
        migrations.AlterField(
            model_name='episode',
            name='person_special_patient_note_local_review_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='episode',
            name='person_special_patient_note_local_review_due_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='episode',
            name='person_stated_gender',
            field=models.CharField(blank=True, db_column='PersonStatedGender', max_length=1, null=True),
        ),
        migrations.AlterField(
            model_name='episode',
            name='person_usual_address_1',
            field=models.CharField(blank=True, db_column='PersonUsualAddress1', max_length=35, null=True),
        ),
        migrations.AlterField(
            model_name='episode',
            name='person_usual_address_2',
            field=models.CharField(blank=True, db_column='PersonUsualAddress2', max_length=35, null=True),
        ),
        migrations.AlterField(
            model_name='episode',
            name='person_usual_address_postcode',
            field=models.CharField(blank=True, db_column='PersonUsualAddressPostcode', max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='episode',
            name='person_usual_residence_type',
            field=models.CharField(blank=True, db_column='PersonUsualResidenceType', max_length=18, null=True),
        ),
        migrations.AlterField(
            model_name='expected',
            name='em_care_chief_complaint',
            field=models.CharField(blank=True, db_column='EmCareChiefComplaint', max_length=18, null=True),
        ),
        migrations.AlterField(
            model_name='expected',
            name='linked_episode',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='sackett.Episode'),
        ),
        migrations.AlterField(
            model_name='expected',
            name='person_age_at_attendance',
            field=models.IntegerField(blank=True, db_column='PersonAgeAtAttendance', null=True),
        ),
        migrations.AlterField(
            model_name='expected',
            name='person_family_name',
            field=models.CharField(blank=True, db_column='PersonFamilyName', max_length=35, null=True),
        ),
        migrations.AlterField(
            model_name='expected',
            name='person_given_name',
            field=models.CharField(blank=True, db_column='PersonGivenName', max_length=35, null=True),
        ),
        migrations.AlterField(
            model_name='expected',
            name='person_stated_gender',
            field=models.CharField(blank=True, db_column='PersonStatedGender', max_length=1, null=True),
        ),
        migrations.AddField(
            model_name='diagnosisdata',
            name='search_terms',
            field=models.ManyToManyField(to='sackett.DiagnosisDataSearchTerm'),
        ),
    ]

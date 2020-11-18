from django.conf import settings
from .fields import *


# TODO magic numbers
def em_care_discharge_information_given_from_db(x):
    return True if x == '787281000000102' else False


def em_care_discharge_information_given_to_db(x):
    return '787281000000102' if x in ('t', 'True', '1', True, 1) else ''


def person_interpreter_rqd_from_db(x):
    return True if x == '315594003' else False


def person_interpreter_rqd_to_db(x):
    return '315594003' if x in ('t', 'True', '1', True, 1) else '315595002'


# TODO add user id once logins are implemented - remember to make this optional though in the case that authentication
# is switched off
class RecordLock(models.Model):
    type = models.IntegerField(null=False)

    record_id = models.IntegerField(null=False)

    state = models.IntegerField(null=False)

    uuid = models.CharField(max_length=36, null=False)

    acquired_date_time = models.DateTimeField(null=False)

    last_refresh_date_time = models.DateTimeField(null=False)


# TODO review all blank=True fields across all models
class UniqueIdentifier(models.Model):
    series = models.CharField(max_length=16, null=False)

    identifier = models.IntegerField(null=False)


class PickListData(models.Model):
    # TableNumber, Code, Description, Group, Sort1, Sort2, Char1, Char2, Bool1
    table_number = models.IntegerField(null=False, db_index=True)

    code = models.CharField(max_length=64, null=False)

    description = models.CharField(max_length=256, null=False)

    group = models.CharField(max_length=64, null=True)

    sort1 = models.IntegerField(null=True)

    sort2 = models.IntegerField(null=True)

    # char1 = models.CharField(max_length=256, null=True)

    # char2 = models.CharField(max_length=256, null=True)

    bool1 = models.NullBooleanField()

    bool2 = models.NullBooleanField()

    bool3 = models.NullBooleanField()

    language_code = models.CharField(max_length=6, null=False)

    class Meta:
        index_together = [
            ["table_number", "code"],
            ["table_number", "description"],
        ]


class DiagnosisDataSearchTerm(models.Model):
    term = models.CharField(max_length=64, null=False)


class DiagnosisData(models.Model):
    group1 = models.CharField(max_length=96, null=False)

    group2 = models.CharField(max_length=96, null=False)

    group3 = models.CharField(max_length=96, null=False)

    sort1 = models.IntegerField(null=False)

    sort2 = models.IntegerField(null=False)

    sort3 = models.IntegerField(null=False)

    description = models.CharField(max_length=128, null=False)

    code = models.CharField(max_length=64, null=False)

    search_terms = models.ManyToManyField(DiagnosisDataSearchTerm)

    injury = models.BooleanField()

    aec = models.BooleanField()

    notifiable_disease = models.BooleanField()

    # TODO special case for 51178009 (SIDS) which forces value in EmCare_Discharge_Status; maybe others in future
    post_macro = models.CharField(max_length=128, null=True)

    language_code = models.CharField(max_length=6, null=False)


class Zone(models.Model):
    # `ZoneId` INT NOT NULL AUTO_INCREMENT, - implied

    # `Label` NVARCHAR(128) NOT NULL,
    label = models.CharField(max_length=128, null=False)

    # `Template` VARCHAR(1024) NOT NULL,
    template = models.CharField(max_length=1024, null=False)

    # 'SummaryTemplate' VARCHAR(1024) NOT NULL,
    summary_template = models.CharField(max_length=1024, null=False)

    # `Deleted` TINYINT(1) NOT NULL,
    deleted = models.BooleanField()

    # Many-many between Zone and User
    users = models.ManyToManyField(settings.AUTH_USER_MODEL)

    def __str__(self):
        return self.label


class Bed(models.Model):
    # `BedId` INT NOT NULL AUTO_INCREMENT, - implied

    # `ZoneId` INT NOT NULL,
    zone = models.ForeignKey(Zone, on_delete=models.CASCADE, null=False)

    # `TemplateIndex` INT NOT NULL,
    template_index = models.IntegerField(null=False)

    # `BedName` nchar(64) NOT NULL,
    name = models.CharField(max_length=64, null=False)

    # `BedLabel` nchar(128) NOT NULL,
    label = models.CharField(max_length=128, null=False)

    def __str__(self):
        return str(self.zone_id) + " (" + str(self.template_index) + ")"


class Episode(models.Model):
    # `EpisodeId` - implied

    # `PersonGivenName` NVARCHAR(35) NULL,
    person_given_name = models.CharField(db_column='PersonGivenName', max_length=35, null=True, blank=True)

    # `PersonFamilyName` NVARCHAR(35) NULL,
    person_family_name = models.CharField(db_column='PersonFamilyName', max_length=35, null=True, blank=True)

    # `PersonStatedGender` CHAR(1) NULL,
    person_stated_gender = models.CharField(db_column='PersonStatedGender', max_length=18, null=True, blank=True)

    # `PersonBirthDate` INT NULL,
    person_birth_date = models.DateField(db_column='PersonBirthDate', null=True, blank=True)

    # `PersonAgeAtAttendance` DECIMAL(9,2) NULL,
    person_age_at_attendance = models.DecimalField(db_column='PersonAgeAtAttendance', decimal_places=2, max_digits=9,
                                                   null=True, blank=True)

    # TODO PersonNhsNumber in the database? discuss possible spec change
    # `PersonGlobalNumber` NVARCHAR(10) NULL,
    person_global_number = models.CharField(db_column='PersonGlobalNumber', max_length=10, null=True, blank=True)

    # TODO as above
    # `PersonGlobalNumberStatusIndicator` CHAR(2) NULL,
    person_global_number_status_indicator = models.CharField(db_column='PersonGlobalNumberStatusIndicator',
                                                             max_length=2, null=True, blank=True)

    # `PersonIdentityWithheldReason` CHAR(2) NULL,
    person_identity_withheld_reason = models.CharField(db_column='PersonIdentityWithheldReason', max_length=2,
                                                       null=True, blank=True)

    # `PersonLocalNumber` NVARCHAR(20) NULL,
    person_local_number = models.CharField(db_column='PersonLocalNumber', max_length=20, null=True, blank=True)

    # `PersonUsualAddress1` NVARCHAR(35) NULL,
    person_usual_address_1 = models.CharField(db_column='PersonUsualAddress1', max_length=35, null=True, blank=True)

    # `PersonUsualAddress2` NVARCHAR(35) NULL,
    person_usual_address_2 = models.CharField(db_column='PersonUsualAddress2', max_length=35, null=True, blank=True)

    # `PersonUsualAddressPostcode` NVARCHAR(10) NULL,
    person_usual_address_postcode = models.CharField(db_column='PersonUsualAddressPostcode', max_length=10, null=True,
                                                     blank=True)

    # `PersonResidenceOrgCode` NVARCHAR(10) NULL,
    person_residence_org_code = models.CharField(db_column='PersonResidenceOrgCode', max_length=10, null=True,
                                                 blank=True)

    # `PersonUsualResidenceType` NVARCHAR(18) NULL,
    person_usual_residence_type = models.CharField(db_column='PersonUsualResidenceType', max_length=18, null=True,
                                                   blank=True)

    # `PersonResidenceLsoa` NVARCHAR(10) NULL,
    person_residence_lsoa = models.CharField(db_column='PersonResidenceLsoa', max_length=10, null=True, blank=True)

    # `PersonPreferredContact` NVARCHAR(255) NULL,
    person_preferred_contact = XmlCharField(xml_tags=('CONTACT',
                                                      {'mobile': 'MOBILE', 'home': 'HOME', 'email': 'EMAIL'}),
                                            populate_fully=True, db_column='PersonPreferredContact',
                                            max_length=255, null=True, blank=True)

    # `PersonGpPracticeCode` NVARCHAR(6) NULL,
    person_gp_practice_code = models.CharField(db_column='PersonGpPracticeCode', max_length=6, null=True, blank=True)

    # `PersonCommLang` NVARCHAR(18) NULL,
    person_comm_lang = models.CharField(db_column='PersonCommLang', max_length=18, null=True, blank=True)

    # `PersonInterpreterRqd` NVARCHAR(18) NULL,
    person_interpreter_rqd = ValueConverterCharField(from_db=person_interpreter_rqd_from_db,
                                                     to_db=person_interpreter_rqd_to_db,
                                                     # coerce_ui_value=person_interpreter_coerce,
                                                     db_column='PersonInterpreterRqd', max_length=18, null=True,
                                                     blank=True)

    # `PersonInterpreterLang` NVARCHAR(18) NULL,
    person_interpreter_lang = models.CharField(db_column='PersonInterpreterLang', max_length=18, null=True, blank=True)

    # `PersonEthnicCategory` NVARCHAR(2) NULL,
    person_ethnic_category = models.CharField(db_column='PersonEthnicCategory', max_length=2, null=True, blank=True)

    # `PersonSchool` NVARCHAR(10) NULL,
    person_school = models.CharField(db_column='PersonSchool', max_length=10, null=True, blank=True)

    # `PersonCompanion` NVARCHAR(255) NULL,
    person_companion = models.CharField(db_column='PersonCompanion', max_length=255, null=True, blank=True)

    # `PersonSpecialPatientNoteLocal` NVARCHAR(4096) NULL,
    person_special_patient_note_local = models.TextField(db_column='PersonSpecialPatientNoteLocal', null=True,
                                                         blank=True)

    # `PersonAdditionalInformation` NVARCHAR(4096) NULL,
    person_additional_information = models.TextField(db_column='PersonAdditionalInformation', null=True, blank=True)

    # `PersonAllergiesAdverseReaction` NVARCHAR(4096) NULL,
    person_allergies_adverse_reaction = models.TextField(db_column='PersonAllergiesAdverseReaction', null=True,
                                                         blank=True)

    # `PersonComorbidities` NVARCHAR(4096) NULL,
    person_comorbidities = models.TextField(db_column='PersonComorbidities', null=True, blank=True)

    # `PersonCurrentMeds` NVARCHAR(4096) NULL,
    person_current_meds = models.TextField(db_column='PersonCurrentMeds', null=True, blank=True)

    # `EmCareProviderOrgCode` NVARCHAR(9) NULL,
    em_care_provider_org_code = models.CharField(db_column='EmCareProviderOrgCode', max_length=9, null=True, blank=True)

    # `EmCareProviderSiteCode` NVARCHAR(9) NULL,
    em_care_provider_site_code = models.CharField(db_column='EmCareProviderSiteCode', max_length=9, null=True,
                                                  blank=True)

    # `EmCareProviderSiteType` CHAR(1) NULL,
    em_care_provider_site_type = models.CharField(db_column='EmCareProviderSiteType', max_length=1, null=True,
                                                  blank=True)

    # `EmCareUniqueId` CHAR(12) NULL, - LONG NOT NULL?
    em_care_unique_id = models.BigIntegerField(db_column='EmCareUniqueId', null=False, blank=True)

    # `EmCareArriveTransportMode` CHAR(2) NULL,
    em_care_arrive_transport_mode = models.CharField(db_column='EmCareArriveTransportMode', max_length=18, null=True,
                                                     blank=True)

    # `EmCareAmbUniqueId` NVARCHAR(20) NULL,
    em_care_amb_unique_id = models.CharField(db_column='EmCareAmbUniqueId', max_length=20, null=True, blank=True)

    # `EmCareArriveDateTime` CHAR(19) NULL, - DATETIME NULL?
    em_care_arrive_date_time = models.DateTimeField(db_column='EmCareArriveDateTime', null=True, blank=True)

    # `EmCareAttendanceType` CHAR(2) NULL,
    em_care_attendance_type = models.CharField(db_column='EmCareAttendanceType', max_length=18, null=True, blank=True)

    # `EmCareReferralSource` CHAR(2) NULL,
    em_care_referral_source = models.CharField(db_column='EmCareReferralSource', max_length=18, null=True, blank=True)

    # `EmCareArriveTransferSource` NVARCHAR(9) NULL,
    em_care_arrive_transfer_source = models.CharField(db_column='EmCareArriveTransferSource', max_length=9, null=True,
                                                      blank=True)

    # `EmCareAssessDateTime` CHAR(19) NULL, - DATETIME NULL?
    em_care_assess_date_time = models.DateTimeField(db_column='EmCareAssessDateTime', null=True, blank=True)

    # `EmCareClinicians` NVARCHAR(4096) NULL,
    em_care_clinicians = models.TextField(db_column='EmCareClinicians', null=True, blank=True)

    # `EmCareReferredService` NVARCHAR(4096) NULL,
    em_care_referred_service = models.TextField(db_column='EmCareReferredService', null=True, blank=True)

    # `EmCareDtaDateTime` CHAR(19) NULL, - DATETIME NULL?
    em_care_dta_date_time = models.DateTimeField(db_column='EmCareDtaDateTime', null=True, blank=True)

    # `EmCareCompleteDateTime` CHAR(19) NULL, - DATETIME NULL?
    em_care_complete_date_time = models.DateTimeField(db_column='EmCareCompleteDateTime', null=True, blank=True)

    # `EmCareDepartDateTime` CHAR(19) NULL, - DATETIME NULL?
    em_care_depart_date_time = models.DateTimeField(db_column='EmCareDepartDateTime', null=True, blank=True)

    # `EmCareAdmitSpeciality` NVARCHAR(18) NULL,
    em_care_admit_speciality = models.CharField(db_column='EmCareAdmitSpeciality', max_length=18, null=True, blank=True)

    # `EmCareAssessmentType` NVARCHAR(255) NULL,
    # em_care_assessment_type = models.CharField(db_column='EmCareAssessmentType', max_length=255, null=True)

    # `EmCareAssessmentScore` NVARCHAR(255) NULL,
    # em_care_assessment_score = models.CharField(db_column='EmCareAssessmentScore', max_length=255, null=True)

    # EmCareAssessmentType and EmCareAssessmentScore now combined into one (XML) field:
    em_care_assessment = models.CharField(db_column='EmCareAssessment', max_length=512, null=True, blank=True)

    # `EmCareChiefComplaint` NVARCHAR(18) NULL,
    em_care_chief_complaint = models.CharField(db_column='EmCareChiefComplaint', max_length=18, null=True, blank=True)

    # `EmCareClinicalNarrative` NVARCHAR(4096) NULL,
    em_care_clinical_narrative = models.TextField(db_column='EmCareClinicalNarrative', null=True, blank=True)

    # `EmCareDiagnosis` NVARCHAR(4096) NULL,
    em_care_diagnosis = XmlTextField(xml_tags=('DIAGS', ('DIAG', {'index': 'NUM', 'code': 'CODE', 'mod': 'MOD'})),
                                     db_column='EmCareDiagnosis', null=True, blank=True)

    # `EmCareInvestigations` NVARCHAR(4096) NULL,
    em_care_investigations = XmlTextField(xml_tags=('INVS', 'INV'), db_column='EmCareInvestigations',
                                          null=True, blank=True)

    # `EmCareTreatments` NVARCHAR(4096) NULL,
    em_care_treatments = XmlTextField(xml_tags=('TRMTS', 'TRMT'), db_column='EmCareTreatments',
                                      null=True, blank=True)

    # `EmCareResearch` NVARCHAR(4096) NULL,
    em_care_research = models.TextField(db_column='EmCareResearch', null=True, blank=True)

    # `EmCareInjDateTime` CHAR(19) NULL, - DATETIME NULL?
    em_care_inj_date_time = models.DateTimeField(db_column='EmCareInjDateTime', null=True, blank=True)

    # `EmCareInjPlaceLatLong` NVARCHAR(50) NULL,
    em_care_inj_place_lat_long = models.CharField(db_column='EmCareInjPlaceLatLong', max_length=50, null=True,
                                                  blank=True)

    # `EmCareInjPlaceExact` NVARCHAR(255) NULL,
    em_care_inj_place_exact = models.CharField(db_column='EmCareInjPlaceExact', max_length=255, null=True, blank=True)

    # `EmCareInjPlaceType` CHAR(2) NULL,
    em_care_inj_place_type = models.CharField(db_column='EmCareInjPlaceType', max_length=18, null=True, blank=True)

    # `EmCareInjActivity` NVARCHAR(18) NULL,
    # em_care_inj_activity = models.CharField(db_column='EmCareInjActivity', max_length=18, null=True)

    # EmCareInjActivity now split in two parts:
    em_care_inj_activity_type = models.CharField(db_column='EmCareInjActivityType', max_length=18, null=True,
                                                 blank=True)

    em_care_inj_activity_detail = models.CharField(db_column='EmCareInjActivityDetail', max_length=255, null=True,
                                                   blank=True)

    # `EmCareInjMechanism` NVARCHAR(18) NULL,
    em_care_inj_mechanism = models.CharField(db_column='EmCareInjMechanism', max_length=18, null=True, blank=True)

    # `EmCareInjDrugAlcohol` NVARCHAR(255) NULL,
    em_care_inj_drug_alcohol = XmlCharField(xml_tags=('INJ_DAS', 'INJ_DA'),
                                            db_column='EmCareInjDrugAlcohol', max_length=255, null=True, blank=True)

    # `EmCareInjIntent` NVARCHAR(18) NULL,
    em_care_inj_intent = models.CharField(db_column='EmCareInjIntent', max_length=18, null=True, blank=True)

    # `EmCareDischargeStatus` CHAR(2) NULL,
    em_care_discharge_status = models.CharField(db_column='EmCareDischargeStatus', max_length=18, null=True, blank=True)

    # `EmCareDischargeFollowUp` CHAR(2) NULL,
    em_care_discharge_follow_up = models.CharField(db_column='EmCareDischargeFollowUp', max_length=18, null=True,
                                                   blank=True)

    # `EmCareDischargeMedication` NVARCHAR(4096) NULL,
    em_care_discharge_medication = models.TextField(db_column='EmCareDischargeMedication', null=True, blank=True)

    # `EmCareDischargeInstructions` NVARCHAR(4096) NULL,
    em_care_discharge_instructions = models.TextField(db_column='EmCareDischargeInstructions', null=True, blank=True)

    # `EmCareDischargeInformationGiven` NVARCHAR(18) NULL,
    # em_care_discharge_information_given = models.CharField(db_column='EmCareDischargeInformationGiven', max_length=18,
    #                                                        null=True, blank=True)
    em_care_discharge_information_given = ValueConverterCharField(from_db=em_care_discharge_information_given_from_db,
                                                                  to_db=em_care_discharge_information_given_to_db,
                                                                  db_column='EmCareDischargeInformationGiven',
                                                                  max_length=18,
                                                                  null=True,
                                                                  blank=True)
    # `EmCareDischargeSafeguarding` CHAR(2) NULL,
    em_care_discharge_safeguarding = models.CharField(db_column='EmCareDischargeSafeguarding', max_length=18, null=True,
                                                      blank=True)

    # `EmCareTransferDestination` NVARCHAR(9) NULL,
    em_care_transfer_destination = models.CharField(db_column='EmCareTransferDestination', max_length=9, null=True,
                                                    blank=True)

    # `BedId` INT NULL,
    bed = models.ForeignKey(Bed, on_delete=models.SET_NULL, null=True, blank=True)

    # `AssignedClinicianId` INT NULL,
    assigned_clinician = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    # `Action` NVARCHAR(255) NULL,
    action = models.CharField(max_length=255, null=True, blank=True)

    # `BedRequested` TINYINT(1) NULL,
    bed_requested = models.NullBooleanField()

    # `PersonSpecialPatientNoteLocalReviewDueDate` DATETIME NULL,
    person_special_patient_note_local_review_due_date = models.DateTimeField(null=True, blank=True)

    # `PersonSpecialPatientNoteLocalReviewedDate` DATETIME NULL,
    person_special_patient_note_local_review_date = models.DateTimeField(null=True, blank=True)

    early_discharge = models.NullBooleanField()

    def __str__(self):
        return self.person_family_name + " " + self.person_given_name + " (" + str(self.em_care_unique_id) + ")"


class Expected(models.Model):
    # ExpectedId - implied

    # PersonGivenName
    person_given_name = models.CharField(db_column='PersonGivenName', max_length=35, null=True, blank=True)

    # PersonFamilyName
    person_family_name = models.CharField(db_column='PersonFamilyName', max_length=35, null=True, blank=True)

    # EmCareChiefComplaint
    em_care_chief_complaint = models.CharField(db_column='EmCareChiefComplaint', max_length=18, null=True, blank=True)

    # PersonStatedGender
    person_stated_gender = models.CharField(db_column='PersonStatedGender', max_length=18, null=True, blank=True)

    # PersonAgeAtAttendance
    person_age_at_attendance = models.IntegerField(db_column='PersonAgeAtAttendance', null=True, blank=True)

    # LinkedEpisodeId
    linked_episode = models.ForeignKey(Episode, on_delete=models.SET_NULL, null=True, blank=True)

    # Removed
    removed = models.BooleanField(db_column='Removed')

    def __str__(self):
        return self.person_family_name + " " + self.person_given_name


class Breach(models.Model):
    # `BreachId` INT NOT NULL AUTO_INCREMENT, - implied

    # `EpisodeId` INT NOT NULL,
    episode = models.ForeignKey(Episode, on_delete=models.CASCADE, null=False)

    # `Narrative` NVARCHAR(4096) NOT NULL,
    narrative = models.CharField(max_length=4096, null=False)

    # `LoggedInUserId` INT NULL, - TODO: remove this unless there is a good reason to keep it
    logged_in_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    # 'AddedDateTime' DATETIME NOT NULL
    added_date_time = models.DateTimeField(auto_now=True, null=False)

    def __str__(self):
        return self.added_date_time


# per https://stackoverflow.com/a/37988537 - proxy model purely for supporting custom permissions
class UserPermissionSupport(models.Model):

    class Meta:

        managed = False  # No database table creation or deletion operations will be performed for this model.

        permissions = (
            ('can_undischarge', 'Can undo patient discharge'),
            ('can_administer_users', 'Can administer users'),
            ('can_consult', 'Can be an assigned doctor'),
            ('can_clear_consultant', 'Can clear assigned doctor for an episode'),
            ('can_modify_org', 'Can change organisation details'),  # name, logo
            ('can_administer_zones', 'Can administer hospital zones'),
            ('can_export_data', 'Can export data'),
            ('can_review_breaches', 'Can review breach reports'),
            ('can_view_dashboard', 'Can view dashboard'),
            ('is_consultant', 'Is a doctor, for the purpose of assignment to episodes'),
        )

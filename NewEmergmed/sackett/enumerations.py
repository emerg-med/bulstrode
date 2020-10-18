from enum import Enum


class LockAcquireResult(Enum):
    Success = 1
    Failure = 2


class LockRefreshResult(Enum):
    Success = 1
    Failure = 2
    Error = 3


class LockStates(Enum):
    Pending = 1
    Acquired = 2


class LockTypes(Enum):
    Episode = 1
    PatientDetails = 2


class PickListTableTypes(Enum):
    # appendices
    PersonCommLang = 1
    PersonInterpreterLang = 2
    PersonEthnicCategory = 3
    PersonComorbidities = 4
    EmCareReferredService = 5
    EmCareAdmitSpecialty = 6
    EmCareChiefComplaint = 7
    EmCareTreatments = 8
    EmCareInjActivity = 9
    # other tables
    PersonStatedGender = 100
    PersonNHSNumberStatusIndicator = 101
    PersonIdentityWithheldReason = 102
    PersonUsualResidenceType = 103
    PersonInterpreterReqd = 104
    EmCareProviderSiteType = 105
    EmCareArriveTransportMode = 106
    EmCareAttendanceType = 107
    EmCareReferralSource = 108
    # TODO these three fields are separate in the v3 spec
    ClinicianType = 109             # used in EmCareClinicians, part of a compound field
    ClinicianTier = 110             # used in EmCareClinicians, part of a compound field
    ClinicianDischarge = 111        # used in EmCareClinicians, part of a compound field
    EmCareAssessmentType = 112      # TODO possibly unused at present
    DiagnosisModerator = 113        # used in EmCareDiagnosis, part of a compound field
    EmCareInvestigations = 114
    EmCareInjPlaceType = 115
    EmCareInjMechanism = 116
    EmCareInjDrugAlcohol = 117
    EmCareInjIntent = 118
    EmCareDischargeStatus = 119
    EmCareDischargeFollowUp = 120
    EmCareDischargeInformationGiven = 121
    EmCareDischargeSafeguarding = 122
    # coded locations - e.g. hospitals
    HealthCareFacility = 900                # http://systems.hscic.gov.uk/data/ods/datadownloads/data-files/etr.zip
    School = 901                            # http://systems.hscic.gov.uk/data/ods/datadownloads/data-files/eschools.zip
    GeneralPractice = 902                   # http://systems.hscic.gov.uk/data/ods/datadownloads/data-files/epraccur.zip

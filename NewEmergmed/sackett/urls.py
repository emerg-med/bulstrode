from django.urls import re_path
from . import views

app_name = 'sackett'

urlpatterns = [
    re_path(r'debug/import_datatables$', views.debug_import_tables, name='debug_import_tables'),
    re_path(r'debug/import_diagnoses$', views.debug_import_diagnoses, name='debug_import_diagnoses'),
    re_path(r'admin/area/add$', views.add_zone, name='add_zone'),
    re_path(r'admin/area/zoneimg/(?P<image_path>.+\.(jpe?g|gif|png))$', views.zone_image, name='zone_image'),
    re_path(r'arrivals/expected$', views.expected_arrival, name='expected_arrival'),
    re_path(r'arrivals/triage$', views.triage_arrival, name='triage_arrival'),
    # re_path(r'config/language$', views.config_choose_language, name='config_choose_language'),
    re_path(r'episode/(?P<episode_id>[0-9]+)$', views.episode, name='episode'),
    re_path(r'episode/(?P<episode_id>[0-9]+)/patient$', views.patient_details, name='patient_details'),
    re_path(r'episode/(?P<episode_id>[0-9]+)/update$', views.episode_update, name='episode_update'),
    re_path(r'episode/breach/(?P<episode_id>[0-9]+)$', views.episode_breach, name='submit_breach'),
    re_path(r'lock/acquire$', views.lock_acquire, name='lock_acquire'),
    re_path(r'lock/refresh$', views.lock_refresh, name='lock_refresh'),
    re_path(r'lock/release$', views.lock_release, name='lock_release'),
    re_path(r'registration$', views.patient_details_overview, name='patient_details_overview'),
    re_path(r'search/diagnosis/(?P<search>.*)$', views.diagnosis_search, name='diagnosis_search'),
    re_path(r'search/gp/(?P<search>.*)$', views.gp_search, name='gp_search'),
    re_path(r'search/school/(?P<search>.*)$', views.school_search, name='school_search'),
    re_path(r'search/hcfacility/(?P<search>.*)$', views.healthcare_facility_search, name='healthcare_facility_search'),
    re_path(r'user/add/(?P<is_doctor>[0-1])$', views.user_management_add, name='user_management_add'),
    re_path(r'user/delete/(?P<user_id>[0-9]+)$', views.user_management_delete_doctor, name='user_management_delete_doctor'),
    re_path(r'user/disable/(?P<user_id>[0-9]+)$', views.user_management_disable_doctor,
        name='user_management_disable_doctor'),
    re_path(r'user/edit/(?P<user_id>[0-9]+)$', views.user_management_edit_user, name='user_management_edit'),
    re_path(r'user/enable/(?P<user_id>[0-9]+)$', views.user_management_enable_doctor, name='user_management_enable_doctor'),
    re_path(r'user/login$', views.user_management_login, name='login'),
    re_path(r'user/logout$', views.user_management_logout, name='logout'),
    re_path(r'user/manage(/?P<show_inactive>[0-1])?$', views.user_management_all, name='user_management_all'),
    re_path(r'user/profile$', views.user_management_personal, name='user_management_personal'),
    re_path(r'area$', views.zone_summary, name='zone_summary'),
    re_path(r'area/content$', views.zone_summary_content_only, name='zone_summary_content_only'),
    re_path(r'area/(?P<zone_id>[0-9]+)$', views.zone_overview, name='zone_overview'),
    re_path(r'area/(?P<zone_id>[0-9]+)/content$', views.zone_overview_content_only, name='zone_overview_content_only'),
    re_path(r'$', views.zone_summary, name='default'),
    re_path(r'index\.html$', views.zone_summary, name='default_index'),

# still TODO
    re_path(r'admin/discharged$', views.zone_summary, name='view_discharged'),
    re_path(r'admin/export$', views.zone_summary, name='export_data'),
    re_path(r'admin/quality$', views.zone_summary, name='review_breaches'),
    re_path(r'admin/dashboard$', views.zone_summary, name='dashboard'),
    re_path(r'admin/settings$', views.zone_summary, name='modify_org'),
]

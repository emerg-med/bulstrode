from django.conf.urls import url
from . import views

app_name = 'sackett'

urlpatterns = [
    url(r'debug/import_datatables$', views.debug_import_tables, name='debug_import_tables'),
    url(r'debug/import_diagnoses$', views.debug_import_diagnoses, name='debug_import_diagnoses'),
    url(r'admin/area/add$', views.add_zone, name='add_zone'),
    url(r'admin/area/zoneimg/(?P<image_path>.+\.(jpe?g|gif|png))$', views.zone_image, name='zone_image'),
    url(r'arrivals/expected$', views.expected_arrival, name='expected_arrival'),
    url(r'arrivals/triage$', views.triage_arrival, name='triage_arrival'),
    # url(r'config/language$', views.config_choose_language, name='config_choose_language'),
    url(r'episode/(?P<episode_id>[0-9]+)$', views.episode, name='episode'),
    url(r'episode/(?P<episode_id>[0-9]+)/patient$', views.patient_details, name='patient_details'),
    url(r'episode/(?P<episode_id>[0-9]+)/update$', views.episode_update, name='episode_update'),
    url(r'episode/breach/(?P<episode_id>[0-9]+)$', views.episode_breach, name='submit_breach'),
    url(r'lock/acquire$', views.lock_acquire, name='lock_acquire'),
    url(r'lock/refresh$', views.lock_refresh, name='lock_refresh'),
    url(r'lock/release$', views.lock_release, name='lock_release'),
    url(r'registration$', views.patient_details_overview, name='patient_details_overview'),
    url(r'search/diagnosis/(?P<search>.*)$', views.diagnosis_search, name='diagnosis_search'),
    url(r'search/gp/(?P<search>.*)$', views.gp_search, name='gp_search'),
    url(r'search/school/(?P<search>.*)$', views.school_search, name='school_search'),
    url(r'search/hcfacility/(?P<search>.*)$', views.healthcare_facility_search, name='healthcare_facility_search'),
    url(r'user/add/(?P<is_doctor>[0-1])$', views.user_management_add, name='user_management_add'),
    url(r'user/delete/(?P<user_id>[0-9]+)$', views.user_management_delete_doctor, name='user_management_delete_doctor'),
    url(r'user/disable/(?P<user_id>[0-9]+)$', views.user_management_disable_doctor,
        name='user_management_disable_doctor'),
    url(r'user/edit/(?P<user_id>[0-9]+)$', views.user_management_edit_user, name='user_management_edit'),
    url(r'user/enable/(?P<user_id>[0-9]+)$', views.user_management_enable_doctor, name='user_management_enable_doctor'),
    url(r'user/login$', views.user_management_login, name='login'),
    url(r'user/logout$', views.user_management_logout, name='logout'),
    url(r'user/manage(/?P<show_inactive>[0-1])?$', views.user_management_all, name='user_management_all'),
    url(r'user/profile$', views.user_management_personal, name='user_management_personal'),
    url(r'area$', views.zone_summary, name='zone_summary'),
    url(r'area/content$', views.zone_summary_content_only, name='zone_summary_content_only'),
    url(r'area/(?P<zone_id>[0-9]+)$', views.zone_overview, name='zone_overview'),
    url(r'area/(?P<zone_id>[0-9]+)/content$', views.zone_overview_content_only, name='zone_overview_content_only'),
    url(r'$', views.zone_summary, name='default'),
    url(r'index\.html$', views.zone_summary, name='default_index'),

# still TODO
    url(r'admin/discharged$', views.zone_summary, name='view_discharged'),
    url(r'admin/export$', views.zone_summary, name='export_data'),
    url(r'admin/quality$', views.zone_summary, name='review_breaches'),
    url(r'admin/dashboard$', views.zone_summary, name='dashboard'),
    url(r'admin/settings$', views.zone_summary, name='modify_org'),
]

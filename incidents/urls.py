from django.urls import re_path
from . import views

urlpatterns = [
    re_path(r'^incidents$', views.incidents_root, name='incident-list-create'),
    re_path(r'^incidents/(?P<incident_id>[0-9a-fA-F-]{36})$', views.get_incident, name='incident-detail'),
    re_path(r'^incidents/(?P<incident_id>[0-9a-fA-F-]{36})/status$', views.update_incident_status, name='incident-status'),
]
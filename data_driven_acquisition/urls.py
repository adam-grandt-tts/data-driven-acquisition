# -*- coding: utf-8 -*-
from django.urls import path, include, re_path
from django.contrib import admin
from adminplus.sites import AdminSitePlus

from data_driven_acquisition.views import (
    HomePageView,
    Package,
    NewPackage,
    FileEditor,
    RawFile,
)


admin.site = AdminSitePlus()
admin.sites.site = admin.site
admin.autodiscover()

admin.site.site_header = "Collaborative Acquisition Tool Admin"
admin.site.site_title = "Collaborative Acquisition Tool Admin"
admin.site.index_title = "Welcome the the CAT Admin"

app_name = 'data_driven_acquisition'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', HomePageView.as_view(), name='home'),

    path('package/<int:package_id>/', Package.as_view(), name='package'),
    path('new/', NewPackage.as_view(), name='new'),
    path('file/<int:file_id>/', FileEditor.as_view(), name='file'),
    path('rawfile/<int:file_id>/', RawFile.as_view(), name='rawfile'),


]

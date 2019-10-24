# -*- coding: utf-8 -*-
from django.conf.urls import url
from django.urls import path
from django.contrib import admin
from adminplus.sites import AdminSitePlus

admin.site = AdminSitePlus()
admin.sites.site = admin.site
admin.autodiscover()

app_name = 'data_driven_acquisition'
urlpatterns = [
	    path('admin/', admin.site.urls),
	]

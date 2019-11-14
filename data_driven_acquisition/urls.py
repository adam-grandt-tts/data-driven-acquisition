# -*- coding: utf-8 -*-
from django.urls import path, include
from django.contrib import admin
from adminplus.sites import AdminSitePlus

from data_driven_acquisition.views import (
    HomePageView,
    Package,
)


admin.site = AdminSitePlus()
admin.sites.site = admin.site
admin.autodiscover()

app_name = 'data_driven_acquisition'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', HomePageView.as_view(), name='home'),

    # JSON Views
    path('package/<int:package_id>/', Package.as_view(), name='package')

    # path('data/packages/', Package.as_view(), name='home'),

]

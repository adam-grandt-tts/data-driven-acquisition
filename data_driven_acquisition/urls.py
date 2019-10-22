# -*- coding: utf-8 -*-
from django.conf.urls import url
from django.views.generic import TemplateView

from . import views


app_name = 'data_driven_acquisition'
urlpatterns = [
    url(
        regex="^django-json-widget/~create/$",
        view=views.django-json-widgetCreateView.as_view(),
        name='django-json-widget_create',
    ),
    url(
        regex="^django-json-widget/(?P<pk>\d+)/~delete/$",
        view=views.django-json-widgetDeleteView.as_view(),
        name='django-json-widget_delete',
    ),
    url(
        regex="^django-json-widget/(?P<pk>\d+)/$",
        view=views.django-json-widgetDetailView.as_view(),
        name='django-json-widget_detail',
    ),
    url(
        regex="^django-json-widget/(?P<pk>\d+)/~update/$",
        view=views.django-json-widgetUpdateView.as_view(),
        name='django-json-widget_update',
    ),
    url(
        regex="^django-json-widget/$",
        view=views.django-json-widgetListView.as_view(),
        name='django-json-widget_list',
    ),
	]

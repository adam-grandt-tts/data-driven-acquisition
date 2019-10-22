# -*- coding: utf-8 -*-
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    UpdateView,
    ListView
)

from .models import (
	django-json-widget,
)


class django-json-widgetCreateView(CreateView):

    model = django-json-widget


class django-json-widgetDeleteView(DeleteView):

    model = django-json-widget


class django-json-widgetDetailView(DetailView):

    model = django-json-widget


class django-json-widgetUpdateView(UpdateView):

    model = django-json-widget


class django-json-widgetListView(ListView):

    model = django-json-widget


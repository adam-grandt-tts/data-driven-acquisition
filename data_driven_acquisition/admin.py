
from django.contrib import admin
from django import forms

from django_admin_hstore_widget.forms import HStoreFormField

from .models import (
    Folder,
    File, 
    PackageTemplate)


class FolderAdminForm(forms.ModelForm):
    properties = HStoreFormField()

    class Meta:
        model = Folder
        exclude = ()

@admin.register(Folder)
class FolderAdmin(admin.ModelAdmin):
    form = FolderAdminForm


admin.site.register(File)
admin.site.register(PackageTemplate)

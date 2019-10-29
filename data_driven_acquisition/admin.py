
from django.contrib import admin
from django import forms

from django_admin_hstore_widget.forms import HStoreFormField
from guardian.admin import GuardedModelAdmin
from reversion.admin import VersionAdmin

from .models import (
    Folder,
    File,
    PackageTemplate)


class FolderAdminForm(forms.ModelForm):
    properties = HStoreFormField()

    class Meta:
        model = Folder
        exclude = ()


class PackageTemplateAdminForm(forms.ModelForm):
    properties = HStoreFormField()

    class Meta:
        model = PackageTemplate
        exclude = ()


@admin.register(Folder)
class FolderAdmin(GuardedModelAdmin):
    form = FolderAdminForm
    list_filter = ('parent', )


@admin.register(File)
class FileAdmin(GuardedModelAdmin, VersionAdmin):
    pass


@admin.register(PackageTemplate)
class PackageTemplateAdmin(GuardedModelAdmin):
    form = FolderAdminForm


from django.contrib import admin
from django import forms

from django_admin_hstore_widget.forms import HStoreFormField

from .models import (
    Folder,
    File,
    PackageTemplate,
    ACL)


class PackageFolderFilter(admin.SimpleListFilter):
    """ A filter on the is package attribute the Folder Module"""
    title = 'package'
    default_value = 'all'

    def lookups(self, request, model_admin):
        return [
            ('all', 'All Folders'),
            ('true','Packages'),
            ('false', 'Subfolders')
        ]

    def queryset(self, request, queryset):
        if self.value() == 'true':
            return queryset.filter(is_package=True)
        elif self.value() == 'false':
            return queryset.filter(is_package=True)
        else:
            return queryset.filter
    parameter_name = 'Is Package'


class FolderAdminForm(forms.ModelForm):
    properties = HStoreFormField()

    class Meta:
        model = Folder
        exclude = ()

@admin.register(Folder)
class FolderAdmin(admin.ModelAdmin):
    form = FolderAdminForm
    list_filter = ('parent', )


admin.site.register(File)
admin.site.register(PackageTemplate)
admin.site.register(ACL)


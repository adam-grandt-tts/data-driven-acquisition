
from django.contrib import admin
from django.urls import reverse
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe


from guardian.admin import GuardedModelAdmin
from reversion.admin import VersionAdmin

from .models import (
    Folder,
    File,
    PackageTemplate,
    PackageProperty,
    PropertyValue)


class IsPackageFilter(admin.SimpleListFilter):
    title = 'Is package'
    parameter_name = 'parent'

    def lookups(self, request, model_admin):
        return [
            ('package', 'Package'),
            ('folder', 'Folder')
        ]

    def queryset(self, request, queryset):
        if self.value() == 'folder':
            return queryset.distinct().filter(parent__isnull=False)
        if self.value() == 'package':
            return queryset.distinct().filter(parent__isnull=True)
        if self.value():
            return queryset.distinct().filter(pages__isnull=True)


class SubfolderInline(admin.TabularInline):
    model = Folder
    extra = 0
    verbose_name = "Subfolder"
    verbose_name_plural = "Subfolders"
    fields = ["get_edit_link", "name"]
    readonly_fields = ["get_edit_link", "name"]

    def get_edit_link(self, obj=None):
        if obj.pk:  # if object has already been saved and has a primary key, show link to it
            url = reverse('admin:%s_%s_change' % (obj._meta.app_label, obj._meta.model_name), args=[force_text(obj.pk)])
            return mark_safe("""<a href="{url}">{text}</a>""".format(
                url=url,
                text="Edit folder",
            ))
        return ""
    get_edit_link.short_description = "Edit link"
    get_edit_link.allow_tags = True


class PropertyValueInline(admin.TabularInline):
    model = PropertyValue
    extra = 0
    verbose_name = "Property"
    verbose_name_plural = "Properties"
    fields = ["prop", "get_type", "value"]
    readonly_fields = ["get_type"]

    def get_type(self, obj=None):
        if obj.pk:
            return obj.property_type
        else:
            return ""
    get_type.short_description = "Type"
    get_type.allow_tags = True


class FileInline(admin.TabularInline):
    model = File
    extra = 0
    verbose_name = "File"
    verbose_name_plural = "Files"
    fields = ["get_edit_link", "name"]
    readonly_fields = ["get_edit_link", "name"]

    def get_edit_link(self, obj=None):
        if obj.pk:  # if object has already been saved and has a primary key, show link to it
            url = reverse('admin:%s_%s_change' % (obj._meta.app_label, obj._meta.model_name), args=[force_text(obj.pk)])
            return mark_safe("""<a href="{url}">{text}</a>""".format(
                url=url,
                text="Edit file",
            ))
        return ""
    get_edit_link.short_description = "Edit link"
    get_edit_link.allow_tags = True


@admin.register(Folder)
class FolderAdmin(GuardedModelAdmin, VersionAdmin):
    list_filter = (IsPackageFilter, )
    inlines = [SubfolderInline, FileInline, PropertyValueInline]
    search_fields = ['name']



@admin.register(File)
class FileAdmin(GuardedModelAdmin, VersionAdmin):
    pass


@admin.register(PackageTemplate)
class PackageTemplateAdmin(GuardedModelAdmin):
    filter_horizontal = ('properties',)

    pass


@admin.register(PackageProperty)
class PackagePropertyAdmin(GuardedModelAdmin):
    list_display = ('name', 'property_type', 'max_length', 'tab')
    list_filter = ('tab', 'property_type')
    search_fields = ['name']


@admin.register(PropertyValue)
class PropertyAdmin(GuardedModelAdmin, VersionAdmin):
    search_fields = ['name']
    list_display = ('package', 'name', 'property_type', 'max_length', 'value')


from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils.decorators import method_decorator
from django.urls import reverse
from django.utils.text import slugify
from django.views.generic.base import TemplateView
from django.views import View
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render, redirect
from django.core.exceptions import ValidationError
from django.conf import settings
from django.core.paginator import Paginator

from data_driven_acquisition.models import Folder, File, PackageTemplate, PackageProperty
from data_driven_acquisition.utils import (
    user_permitted_tree,
    package_prop_by_tab,
    highlight_properties,
    lowlight_properties,
    trello_card_get_or_create,
    trello_list_get_or_create,
    trello_card_desc,
    apply_properties,
    get_package_tree)

from guardian.shortcuts import (
    get_objects_for_user,
    get_perms,
    get_perms_for_model,
    assign_perm)

import reversion
from reversion.views import RevisionMixin

import copy
import logging
logger = logging.getLogger('data_driven_acquisition')


def genreal_context(request):
    tree = user_permitted_tree(request.user)

    return {
        'packages': tree,
        'templates': get_objects_for_user(
            request.user,
            'data_driven_acquisition.can_deploy').all()
    }


@method_decorator(login_required, name='dispatch')
class HomePageView(TemplateView):

    template_name = "home.html"

    page_size = 5

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(genreal_context(self.request))
        context['statuses'] = [x[0] for x in Folder.STATUS]
        context['users'] = User.objects.filter(is_staff = False)
        context['status'] = self.request.GET.get('status')
        context['partner'] = self.request.GET.get('partner')
        context['owner'] = self.request.GET.get('owner')
        context['office'] = self.request.GET.get('office')
        context['current_user'] = self.request.user

        # Filtering 
        
        raw_packages = copy.deepcopy(context['packages'])

        for package in context['packages']:
            if context['owner']:
                if not package.owner:
                    del(raw_packages[package])
                    continue
                if package.owner.username != context['owner']:
                    del(raw_packages[package])
                    continue

        context['packages'] = raw_packages

        paginator = Paginator(list(context['packages']), self.page_size)
        page = paginator.get_page(self.request.GET.get('page'))
        context['page'] = page

        try:
            context['offices'] = PackageProperty.objects.get(name='Office').options
        except PackageProperty.DoesNotExist:
            context['offices'] = ''
        try:
            context['partners'] = PackageProperty.objects.get(name='Agency-Partner').options
        except PackageProperty.DoesNotExist:
            context['partners'] = ''

        return context


@method_decorator(login_required, name='dispatch')
class Package(View):
    """ Manage Package and its attributes"""

    def get(self, request, package_id):
        """Return package data"""
        try:
            package = get_object_or_404(Folder, pk=int(package_id))
        except ValueError:
            return HttpResponseForbidden('Not a valid Package ID')

        if not package.is_package:
            return HttpResponseForbidden('Not a valid Package ID')

        if not request.user.has_perm('view_folder', package):
            return HttpResponseForbidden('Not allowed')

        trello_url = "False"
        if settings.USE_TRELLO:
            # Update the Trello card
            card = trello_card_get_or_create(package)
            trello_url = card.short_url

        # Get and clean package tree
        tree = user_permitted_tree(request.user)
        package_tree = get_package_tree(tree, package)

        # Get tabs for template
        tabs_set = set(x.tab for x in package.properties.all())
        tabs = {slugify(x) :x for x in tabs_set}
        # print(tabs, sorted(tabs))

        context = genreal_context(self.request)
        context['package'] = package
        context['package_tree'] = package_tree
        context['updated'] = False
        context['form_errors'] = ''
        context['can_edit'] = request.user.has_perm('can_set_properties', package),
        context['can_push'] = request.user.has_perm('can_propagate_properties', package)
        context['tabs'] = tabs #{slugify(x[0]): x[0] for x in PackageProperty.TABS}
        context['tab_dict'] = package_prop_by_tab(package, PackageProperty.TABS)
        context['package_status'] = [x[0] for x in Folder.STATUS]
        context['trello_url'] = trello_url



        return render(
            request,
            'package.html',
            context)

    def post(self, request, package_id):
        """Update package"""

        try:
            package = get_object_or_404(Folder, pk=int(package_id))
        except ValueError:
            return HttpResponseForbidden('Not a valid Package ID')

        if not package.is_package:
            return HttpResponseForbidden('Not a valid Package ID')

        form_errors = []
        if not request.user.has_perm('can_set_properties', package):
            form_errors.append('Not allowed to edit')
        else:
            try:
                with reversion.create_revision():
                    # Update the name and status
                    package.name = request.POST.get('name', package.name)
                    package.status = request.POST.get('status', package.status)
                    package.save()
                    reversion.set_user(request.user)
                    reversion.set_comment("Package updated via UI")
            except (ValueError, ValidationError) as e:
                form_errors.append(str(e))

            # update the properties:
            for prop_id, val in request.POST.items():
                if not prop_id.startswith('prop_'):
                    continue
                try:
                    with reversion.create_revision():
                        prop_id = int(prop_id.strip('prop_id'))
                        prop = package.properties.get(id=prop_id)
                        prop.value = val
                        # TODO: input verification goes here
                        prop.save()
                        reversion.set_user(request.user)
                        reversion.set_comment("Property updated via UI")
                except Exception as e:
                    form_errors.append(f"Could not save {prop.name} {e}")
                    continue

            trello_url = "False"
            if settings.USE_TRELLO:
                # Update the Trello card
                card = trello_card_get_or_create(package)

                # Set the list based on status
                new_list = trello_list_get_or_create(package.status)
                if card.get_list().id != new_list.id:
                    card.change_list(new_list.id)

                # Update description
                card.set_description(
                    trello_card_desc(
                        package,
                        PackageProperty.TABS
                    )
                )
                logger.info(f'Updated trello card for package {package.id} - {package.name}')

                trello_url = card.short_url

        logger.info(f'Updated package {package.id} - {package.name}')

        if not package.update_children(update_user=request.user):
            form_errors.append('The package was updated, but those changes could not be applied to the underlying documents. Try saving again.')

        tree = user_permitted_tree(request.user)
        package_tree = get_package_tree(tree, package)

        # Get tabs for template
        tabs_set = set(x.tab for x in package.properties.all())
        tabs = {slugify(x) :x for x in tabs_set}

        context = genreal_context(self.request)
        context['trello_url'] = trello_url
        context['updated'] = True
        context['package'] = package
        context['package_tree'] = package_tree
        context['form_errors'] = form_errors
        context['can_edit'] = request.user.has_perm('can_set_properties', package)
        context['can_push'] = request.user.has_perm('can_propagate_properties', package)
        context['tabs'] = tabs #{slugify(x[0]): x[0] for x in PackageProperty.TABS}
        context['tab_dict'] = package_prop_by_tab(package, PackageProperty.TABS)
        context['package_status'] = [x[0] for x in Folder.STATUS]

        return render(
            request,
            'package.html',
            context)

@method_decorator(login_required, name='dispatch')
class NewPackage(View):
    """ Manage Package and its attributes"""

    def get(self, request):
        """Return package data"""
        try:
            template = get_object_or_404(PackageTemplate, pk=int(request.GET['template_id']))
        except ValueError:
            return HttpResponseForbidden('Not a valid Template ID')

        if not request.user.has_perm('can_deploy', template):
            return HttpResponseForbidden('Not allowed')

        # Get tabs for template
        tabs_set = set(x.tab for x in template.properties.all()) 
        tabs = {slugify(x) :x for x in tabs_set}

        context = genreal_context(self.request)
        context['template'] = template
        context['can_edit'] = True
        context['can_deploy'] = request.user.has_perm('can_deploy', template)
        context['tabs'] = tabs #{slugi\fy(x[0]): x[0] for x in PackageProperty.TABS}
        context['tab_dict'] = package_prop_by_tab(template, PackageProperty.TABS, True)

        return render(
            request,
            'new.html',
            context)

    def post(self, request):
        """ Create package"""

        try:
            template = get_object_or_404(PackageTemplate, pk=int(request.GET['template_id']))
        except ValueError:
            return HttpResponseForbidden('Not a valid Template ID')

        if not request.user.has_perm('can_deploy', template):
            return HttpResponseForbidden('Not allowed')
        else:
            try:
                package = template.deploy(
                    request.POST.get('name'),
                    request.POST,
                )
                if package:
                    # Set owner
                    package.owner = request.user
                    package.save()

                    # Set permissions
                    folder_perms = get_perms_for_model(
                        'data_driven_acquisition.Folder').values_list(
                            'codename', flat=True)
                    for p in folder_perms:
                        assign_perm(p, request.user, package)

                    return redirect('package', package_id=package.id)
                else:
                    raise ValueError('Could not create package')
            except Exception as e:
                context = genreal_context(self.request)
                context['template'] = template
                context['can_deploy'] = request.user.has_perm('can_deploy', template)
                import traceback
                var = traceback.format_exc()
                print(var)
                context['form_errors'] = [e, ]
                context['tabs'] = {slugify(x[0]):x[0] for x in PackageProperty.TABS}
                context['tab_dict'] = package_prop_by_tab(template, PackageProperty.TABS, True)

                return render(
                    request,
                    'new.html',
                    context)


@method_decorator(login_required, name='dispatch')
class RawFile(View):
    """ Return raw file content."""

    def get(self, request, file_id):
        """Return package data"""
        try:
            the_file = get_object_or_404(File, pk=int(file_id))
        except ValueError:
            return HttpResponseForbidden('Not a valid File ID')

        # Figure out perms
        can_read = False

        perm_set = set(get_perms(request.user, the_file))
        p = the_file.parent
        while p is not None:
            perm_set.update(get_perms(request.user, p))
            p = p.parent

        if perm_set:
            can_read = True

        if not can_read:
            return HttpResponseForbidden('Not permitted to access this file.')

        highlighted = highlight_properties(the_file.content, the_file.package.properties.all())
        return HttpResponse(highlighted)

    def post(self, request, file_id):
        """ Update file content"""

        try:
            the_file = get_object_or_404(File, pk=int(file_id))
        except ValueError:
            return HttpResponseForbidden('Not a valid File ID')

        # Figure out perms
        can_edit = False
        can_read = False
        edit_perms = set(['can_edit_content', 'can_edit_child_content'])

        perm_set = set(get_perms(request.user, the_file))
        p = the_file.parent
        while p is not None:
            perm_set.update(get_perms(request.user, p))
            p = p.parent

        if perm_set:
            can_read = True

        if perm_set.intersection(edit_perms):
            can_edit = True

        if not (can_read or can_edit):
            return HttpResponseForbidden('Not permitted to access this file.')

        if can_edit:
            with reversion.create_revision():
                raw_data = request.POST.get('rawdata')
                the_file.content = raw_data
                the_file.save()

                reversion.set_comment('Edited raw file content directly.')
                reversion.set_user(request.user)

            return JsonResponse({'success': True})


@method_decorator(login_required, name='dispatch')
class FileEditor(RevisionMixin, View):
    """ Manage Package and its attributes"""

    def get(self, request, file_id):
        """Return package data"""
        try:
            the_file = get_object_or_404(File, pk=int(file_id))
        except ValueError:
            return HttpResponseForbidden('Not a valid File ID')

        # Figure out perms
        can_edit = False
        can_read = False
        edit_perms = set(['can_edit_content', 'can_edit_child_content'])

        perm_set = set(get_perms(request.user, the_file))
        p = the_file.parent
        while p is not None:
            perm_set.update(get_perms(request.user, p))
            p = p.parent

        if perm_set:
            can_read = True

        if perm_set.intersection(edit_perms):
            can_edit = True

        if not (can_read or can_edit):
            return HttpResponseForbidden('Not permitted to access this file.')

        tree = user_permitted_tree(request.user)
        for key, value in tree.items():
            if key.id == the_file.package.id:
                package_tree = value
                break

        context = genreal_context(self.request)
        context['file'] = the_file
        context['package'] = the_file.package
        context['package_tree'] = package_tree
        context['can_read'] = can_read
        context['can_edit'] = can_edit
        context['perm_set'] = perm_set
        context['raw_url'] = reverse('rawfile', kwargs={'file_id': file_id})

        if the_file.file_type == 'Document':
            template = "file_document.html"
        elif the_file.file_type == 'Sheet':
            template = "file_sheet.html"
        else:
            template = "file_other.html"

        return render(
            request,
            template,
            context)

    def post(self, request, file_id):
        """ Update file content"""

        try:
            the_file = get_object_or_404(File, pk=int(file_id))
        except ValueError:
            return HttpResponseForbidden('Not a valid File ID')

        # Figure out perms
        can_edit = False
        can_read = False
        edit_perms = set(['can_edit_content', 'can_edit_child_content'])

        perm_set = set(get_perms(request.user, the_file))
        p = the_file.parent
        while p is not None:
            perm_set.update(get_perms(request.user, p))
            p = p.parent

        if perm_set:
            can_read = True

        if perm_set.intersection(edit_perms):
            can_edit = True

        if not (can_read or can_edit):
            return HttpResponseForbidden('Not permitted to access this file.')

        if can_edit:

            doc_body = request.POST.get('editor')
            # removing highlight
            doc_body = lowlight_properties(
                doc_body, the_file.package.properties.all())

            # The editor will only return the page  body so we have keep the
            # current head
            old_content = the_file.content.split('<body')
            new_content = ''.join([
                old_content[0],
                '<body>',
                doc_body,
                '</body></html>'
            ])

            the_file.content = new_content
            the_file.save()

            reversion.set_comment('Edited file content directly.')

        tree = user_permitted_tree(request.user)
        for key, value in tree.items():
            if key.id == the_file.package.id:
                package_tree = value
                break

        context = genreal_context(self.request)
        context['file'] = the_file
        context['package'] = the_file.package
        context['package_tree'] = package_tree
        context['can_read'] = can_read
        context['can_edit'] = can_edit
        context['perm_set'] = perm_set
        context['raw_url'] = reverse('rawfile', kwargs={'file_id': file_id})

        if the_file.file_type == 'Document':
            template = "file_document.html"
        elif the_file.file_type == 'Sheet':
            template = "file_sheet.html"
        else:
            template = "file_other.html"

        return render(
            request,
            template,
            context)

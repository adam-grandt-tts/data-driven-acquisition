from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.urls import reverse
from django.views.generic.base import TemplateView
from django.views import View
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render
from django.core.exceptions import ValidationError


from data_driven_acquisition.models import Folder, File, PackageTemplate
from data_driven_acquisition.utils import user_permitted_tree

from guardian.shortcuts import get_objects_for_user

tree_ul = ''


def genreal_context(request):
    global tree_ul

    # Get user tree
    tree = user_permitted_tree(request.user)

    def tree_to_ul(d, indent=0):
        global tree_ul
        for key, value in d.items():
            actions = ''
            if key == 'files':
                for item in value:
                    tree_ul += ''.join([
                        '  ' * (indent + 1),
                        '<li><a href = "#"> ' + '&nbsp;&nbsp;' * (indent + 1),
                        '<i class="icon-file-text-alt"></i>&nbsp;&nbsp;',
                        ''.join(item.name.split('.')[:-1]),
                        '</a></li>\n'])
                continue
            tree_ul += ''.join([
                '  ' * indent,
                '<li>' ,
                f'<a href="#folder_{key.id}_sub" data-toggle="collapse" ',
                'aria-expanded="false" class="dropdown-toggle">' + '&nbsp;&nbsp;' * (indent + 1)
            ])
            if key.is_package:
                tree_ul += ''.join([
                    '<i class="icon-briefcase"></i>',
                ])
                edit_href = reverse('package', kwargs={'package_id': key.id})
                actions += f'<a href="{edit_href}" class="sublink">Edit</a>&nbsp;'
            else:
                tree_ul += ''.join([
                    '<i class="icon-folder-close"></i>',
                ])
            tree_ul += ''.join([
                '&nbsp;&nbsp;',
                f'{key.name}</a> ',
                '\n' + '  ' * (indent + 1),
                f'<ul class="collapse list-unstyled" id="folder_{key.id}_sub">\n',
                actions])
            if isinstance(value, dict):
                tree_to_ul(value, indent + 1)
                tree_ul += '  ' * (indent + 1) + '</ul>\n'
            else:
                tree_ul += '  ' * (indent + 1) + '<li>' + value.name + '</li>\n'
            tree_ul += '  ' * indent + '</li>\n'
    
    tree_ul = ''
    tree_to_ul(tree)

    return {
        'tree_ul': tree_ul,
        'templates': get_objects_for_user(
            request.user,
            'data_driven_acquisition.can_deploy').all()
    }


@method_decorator(login_required, name='dispatch')
class HomePageView(TemplateView):

    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(genreal_context(self.request))
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

        context = genreal_context(self.request)
        context['package'] = package
        context['can_edit'] = request.user.has_perm('can_set_properties', package),
        context['can_push'] = request.user.has_perm('can_propagate_properties', package),

        return render(
            request, 
            'package.html',
            context)

    def post(self, request, package_id):
        """ Update package"""

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
            # Update the name
            package.name = request.POST.get('name', package.name)
            try:
                package.save()
            except (ValueError, ValidationError) as e:
                form_errors.append(str(e))

            # update the properties:
            for prop_id, val in request.POST.items():
                if not prop_id.startswith('prop_'):
                    continue
                try:
                    prop_id = int(prop_id.strip('prop_id'))
                    prop = package.properties.get(id=prop_id)
                    prop.value = val
                    # TODO: input verification goes here
                    prop.save()
                except Exception as e:
                    form_errors.append(f"Could not save {prop.name} {e}")
                    continue

        context = genreal_context(self.request)
        context['updated'] = True
        context['package'] = package
        context['form_errors'] = form_errors
        context['can_edit'] = request.user.has_perm('can_set_properties', package),
        context['can_push'] = request.user.has_perm('can_propagate_properties', package),

        return render(
            request, 
            'package.html',
            context)
        
    def put(self, request, package_id):
        """Ajax trigger for updating the content of a package"""
        if not request.is_ajax():
            return HttpResponseForbidden('Unexpected request')

        try:
            package = get_object_or_404(Folder, pk=int(package_id))
        except ValueError:
            return HttpResponseForbidden('Not a valid Package ID')

        if not package.is_package:
            return HttpResponseForbidden('Not a valid Package ID')

        form_errors = []
        if not request.user.has_perm('can_set_properties', package):
            return HttpResponseForbidden('Not allowed to update.')

        if package.update_children():
            return JsonResponse({'status': 'success'})
        else:
            return JsonResponse({'status': 'error'})


@method_decorator(login_required, name='dispatch')
class NewPackage(View):
    """ Manage Package and its attributes"""

    def get(self, request, template_id):
        """Return package data"""
        try:
            template = get_object_or_404(PackageTemplate, pk=int(template_id))
        except ValueError:
            return HttpResponseForbidden('Not a valid Template ID')

        if not request.user.has_perm('can_deploy', template):
            return HttpResponseForbidden('Not allowed')

        context = genreal_context(self.request)
        context['template'] = template
        context['can_deploy'] = request.user.has_perm('can_deploy', template),

        return render(
            request, 
            'new.html',
            context)

    def post(self, request, package_id):
        """ Update package"""

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
            # Update the name
            package.name = request.POST.get('name', package.name)
            try:
                package.save()
            except (ValueError, ValidationError) as e:
                form_errors.append(str(e))

            # update the properties:
            for prop_id, val in request.POST.items():
                if not prop_id.startswith('prop_'):
                    continue
                try:
                    prop_id = int(prop_id.strip('prop_id'))
                    prop = package.properties.get(id=prop_id)
                    prop.value = val
                    # TODO: input verification goes here
                    prop.save()
                except Exception as e:
                    form_errors.append(f"Could not save {prop.name} {e}")
                    continue

        context = genreal_context(self.request)
        context['updated'] = True
        context['package'] = package
        context['form_errors'] = form_errors
        context['can_edit'] = request.user.has_perm('can_set_properties', package),
        context['can_push'] = request.user.has_perm('can_propagate_properties', package),

        return render(
            request, 
            'package.html',
            context)
        
    def put(self, request, package_id):
        """Ajax trigger for updating the content of a package"""
        if not request.is_ajax():
            return HttpResponseForbidden('Unexpected request')

        try:
            package = get_object_or_404(Folder, pk=int(package_id))
        except ValueError:
            return HttpResponseForbidden('Not a valid Package ID')

        if not package.is_package:
            return HttpResponseForbidden('Not a valid Package ID')

        form_errors = []
        if not request.user.has_perm('can_set_properties', package):
            return HttpResponseForbidden('Not allowed to update.')

        if package.update_children():
            return JsonResponse({'status': 'success'})
        else:
            return JsonResponse({'status': 'error'})











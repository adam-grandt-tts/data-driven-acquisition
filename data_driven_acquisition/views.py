from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic.base import TemplateView
from django.views import View
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404

from data_driven_acquisition.models import Folder, File
from data_driven_acquisition.utils import user_permitted_tree

from guardian.shortcuts import get_perms


@method_decorator(login_required, name='dispatch')
class HomePageView(TemplateView):

    template_name = "home.html"
    tree_ul = ''

    def tree_to_ul(self, d, indent=0):
        for key, value in d.items():
            if key == 'files':
                for item in value:
                    self.tree_ul += ''.join([
                        '  ' * (indent + 1),
                        '<li><a href = "#"> ' + '&nbsp;&nbsp;' * (indent + 1),
                        '<i class="icon-file-text-alt"></i>&nbsp;&nbsp;',
                        ''.join(item.name.split('.')[:-1]),
                        '</a></li>\n'])
                continue
            self.tree_ul += ''.join([
                '  ' * indent,
                '<li>' ,
                f'<a href="#folder_{key.id}_sub" data-toggle="collapse" ',
                'aria-expanded="false" class="dropdown-toggle">' + '&nbsp;&nbsp;' * (indent + 1)
            ])
            if key.is_package:
                self.tree_ul += ''.join([
                    '<i class="icon-briefcase"></i>',
                ])
            else:
                self.tree_ul += ''.join([
                    '<i class="icon-folder-close"></i>',

                ])
            self.tree_ul += ''.join([
                '&nbsp;&nbsp;',
                f'{key.name}</a>',
                '\n' + '  ' * (indent + 1),
                f'<ul class="collapse list-unstyled" id="folder_{key.id}_sub">\n'])
            if isinstance(value, dict):
                self.tree_to_ul(value, indent + 1)
                self.tree_ul += '  ' * (indent + 1) + '</ul>\n'
            else:
                self.tree_ul += '  ' * (indent + 1) + '<li>' + value.name + '</li>\n'
            self.tree_ul += '  ' * indent + '</li>\n'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.tree = user_permitted_tree(self.request.user)
        self.tree_to_ul(self.tree)
        context['tree'] = self.tree
        context['tree_ul'] = self.tree_ul
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

        if 'view_folder' not in get_perms(request.user, package):
            return HttpResponseForbidden('Not allowed')

        package_data = {
            'id': package.id,
            'name': package.name,
        }
        package_data.update(package.properties)

        return JsonResponse(package_data)

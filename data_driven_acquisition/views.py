from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic.base import TemplateView
from django.views import View
from django.http import JsonResponse, HttpResponse
from guardian.shortcuts import get_objects_for_user

from data_driven_acquisition.models import Folder

@method_decorator(login_required, name='dispatch')
class HomePageView(TemplateView):

    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # context['latest_articles'] = Article.objects.all()[:5]
        return context


@method_decorator(login_required, name='dispatch')
class Package(View):

    def get(self, request):
        allowed_packages = ()
        view_files = get_objects_for_user(request.user,
            'data_driven_acquisition.view_file').all()


        projects = get_objects_for_user(request.user, 'folder.can_view_folder')

        packages = Folder.objects.filter(parent=None).values()
        packages = list(packages)
        return JsonResponse(packages, safe=False)

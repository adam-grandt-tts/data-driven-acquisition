from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic.base import TemplateView
from django.views import View
from django.http import JsonResponse, HttpResponse
from guardian.shortcuts import (
    get_objects_for_user,
    get_perms_for_model)

from data_driven_acquisition.models import Folder, File

@method_decorator(login_required, name='dispatch')
class HomePageView(TemplateView):

    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # context['latest_articles'] = Article.objects.all()[:5]
        return context


@method_decorator(login_required, name='dispatch')
class Tree(View):

    file_perm_list = [
        f'data_driven_acquisition.{perm}' for perm in
            get_perms_for_model(File).values_list('codename', flat=True)]

    folder_perm_list = [
        f'data_driven_acquisition.{perm}' for perm in
            get_perms_for_model(Folder).values_list('codename', flat=True)]


    def get(self, request):
        tree = {}

        allowed_folders = get_objects_for_user(
            request.user,
            self.folder_perm_list,
            any_perm=True).all()

        for folder in allowed_folders:
            tree = self.add_folder(tree, folder)

        allowed_files = get_objects_for_user(
            request.user,
            self.files_perm_list,
            any_perm=True).all()




        return JsonResponse(packages, safe=False)

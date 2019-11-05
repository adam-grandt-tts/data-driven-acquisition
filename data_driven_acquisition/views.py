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



# def get_folder(folder):
#     # Get folder content
#     folder_tree = {}
#     files = File.objects.filter(parent=folder)
#     subs = Folder.objects.filter(parent=folder)
    
#     folder_tree['files'] = [f.name for f in files]
#     for sub in subs:
#         folder_tree[sub.name] = get_folder(sub)
#     return(folder_tree)


# def stick_folder_in_tree(mt, folder, tree):
#     if folder.parent.name in list(mt):
#         mt[folder.parent.name][folder.name] = tree
#         return mt
#     else:
#         for key in list(mt):
#             if type(mt[key]) == dict:
#                 mt = stick_in_tree(mt[key], folder, tree)
#                 return mt
#     return False

# def climb_to_packge(mt, folder):
#     while folder.parent is not None:
#         mt[folder.parent.name] = {}
#         mt[folder.parent.name][folder.name] = mt[folder.name]
#         del(mt[folder.name])
#         folder = folder.parent
#     return mt
        


# master_tree = {}
# fs = [Folder.objects.get(id=50),Folder.objects.get(id=57),Folder.objects.get(id=64)]

# fi = [File.objects.get(id= 40),]


# for f in fs:
#     print('--------------------------------------')
#     print (f'=={f.name}===tree=======')
#     # Get the folder dontent as tree
#     tree = get_folder(f)
#     print(json.dumps(tree))
    
#     # Stick in place in the tree 
#     if not stick_in_tree(master_tree, f, tree):
#         # Cold not find a place to stick 
#         # Settingf at root level and clmbing up to the Package
#         master_tree[f.name] = tree
#         master_tree = climb_to_packge(master_tree, f)

    
#     print (f'=={f.name}===master posyt place=======')
#     print(json.dumps(master_tree))
    
# for f in fi:
#     # First add the parent folder to the tree 
#     if not stick_in_tree(master_tree, f, tree):
#         # Cold not find a place to stick 
#         # Settingf at root level and clmbing up to the Package
#         master_tree[f.parent.name] = tree
#         master_tree = climb_to_packge(master_tree, f)

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

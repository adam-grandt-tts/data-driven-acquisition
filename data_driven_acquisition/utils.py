import re

from guardian.shortcuts import (
    get_objects_for_user,
    get_perms_for_model)


def apply_properties(data, properties):
    """
        Apply the provided properties to a data string following one of these
        formats:

        1. "{{ Property Name }}" : The entire string will be replaces with the value. 
        2. <!--PROPERTY:property_name-->VALUE<!--/PROPERTY:property_name--> The
            value will replace the string between the comments. Leaving the comments
            in place for later update.
    """
    # Github returns bytes and we need a string so:
    if type(data) == bytes:
        data = str(data, encoding='utf-8')
    
    for prop in properties.keys():

        # {{ Var }} format
        data = data.replace(f"{{{{{prop}}}}}", properties[prop])

        # <!--PROPERTY:var-->VALUE<!--/PROPERTY:var--> format
        re_str = re.compile(f"<!--PROPERTY:{prop}-->.+?<!--/PROPERTY:{prop}-->")

        if re.search(re_str, data):
            new_str = f"<!--PROPERTY:{prop}-->{properties[prop]}<!--/PROPERTY:{prop}-->"
            data = re.sub(re_str, new_str, data)

    return data


def get_folder_tree(folder_obj):
    """Return a dictionary represanting the content tree of a folder."""
    folder_tree = {}

    files = folder_obj.files.all()
    subs = folder_obj.subfolders.all()

    folder_tree['files'] = [f for f in files]
    for sub in subs:
        folder_tree[sub] = get_folder(sub)
    return(folder_tree)


def place_folder_in_tree(master_tree, folder, tree):
    """Place the forder tree in a provided master tree  under the folders
        parent or return False if the parent is not in the tree.
    """
    if folder.parent in list(master_tree):
        # Parent is found place the tree where it belongs.
        master_tree[folder.parent][folder] = tree
        return master_tree
    else:
        # No parent found, lets dig into all subfolders.
        for key in list(master_tree):
            if type(master_tree[key]) == dict:
                master_tree = stick_folder_in_tree(
                    master_tree[key],
                    folder,
                    tree)
                return master_tree
    return False


def user_permitted_tree(user:
    """Generate a dictionary of the representing a folder tree composed of
    the elements the user is allowed to acccess.
    """
    user_tree= {}

    file_perm_list = [
        f'data_driven_acquisition.{perm}' for perm in
        get_perms_for_model('data_driven_acquisition.File').values_list(
            'codename', flat=True)
        ]

    folder_perm_list = [
        f'data_driven_acquisition.{perm}' for perm in
        get_perms_for_model('data_driven_acquisition.Folder').values_list(
            'codename', flat=True)
        ]

    permitted_folders = get_objects_for_user(
        user,
        folder_perm_list,
        any_perm=True).all()

    permitted_files = get_objects_for_user(
        user,
        files_perm_list,
        any_perm=True).all()

    for folder_obj in permitted_folders:
        # Get the folder dontent as tree
        tree = get_folder_tree(folder_obj)
        
        # Try to place the tree in the user tree
        if not stick_folder_in_tree(user_tree, f, tree):
            # The parent is not ins the tr
            # Settingf at root level and clmbing up to the Package
            master_tree[f] = tree
            master_tree = climb_to_packge(master_tree, f)

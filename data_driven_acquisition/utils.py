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
        folder_tree[sub] = get_folder_tree(sub)
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
                master_tree = place_folder_in_tree(
                    master_tree[key],
                    folder,
                    tree)
                return master_tree
    return False


def climb_to_package(master_tree, folder):
    """Add the parent of folder to the master tree above folder until we reach
        the package level. Checking on each iteration to see if the current
        parent is already in the tree and placing the current tree in place if
        it is.
    """
    # Since the folder is already at root, we are good to skip if its a Package
    while folder.parent is not None:
        # if the parent exits in the tree copy to proper lobation
        if place_folder_in_tree(master_tree, folder, master_tree[folder]):
            # Then delete the original place holder
            del(master_tree[folder])
            return master_tree
        else:
            # Add the parent folder to the placeholder and try again
            master_tree[folder.parent] = {}
            master_tree[folder.parent]['files'] = []
            master_tree[folder.parent][folder] = master_tree[folder]
            del(master_tree[folder])
            folder = folder.parent
    return master_tree


def place_file_in_tree(master_tree, file_obj):
    """Add the file to its proper location in the master tree.
        Return False if the parent folder is not in the master tree
    """
    if file_obj.parent in list(master_tree):
        if "files" not in master_tree[file_obj.parent].keys():
            master_tree[file_obj.parent]["files"] = []
        master_tree[file_obj.parent]["files"].append(file_obj)
        return master_tree
    else:
        for key in list(master_tree):
            if type(master_tree[key]) == dict:
                master_tree = place_file_in_tree(master_tree[key], file_obj)
                return master_tree
    return False


def user_permitted_tree(user):
    """Generate a dictionary of the representing a folder tree composed of
    the elements the user is allowed to acccess.
    """

    # Init
    user_tree = {}

    # Dynamically collect permission to avoid hardcoding
    # Note: Any permission to an element is the same as read permission so
    # they are all included.

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

    # Collect all permistted elements
    permitted_folders = get_objects_for_user(
        user,
        folder_perm_list,
        any_perm=True).all()

    permitted_files = get_objects_for_user(
        user,
        file_perm_list,
        any_perm=True).all()

    # Add all permitted folders to the user tree with their content and parents.
    for folder_obj in permitted_folders:
        # Get the folder content as tree
        tree = get_folder_tree(folder_obj)

        # Try to place the tree in the user tree
        if not place_folder_in_tree(user_tree, folder_obj, tree):
            # The parent is not in the user tree.
            # Cresting the parent folder at root level and then completing the
            # climb to the package level, mergin as needed.
            user_tree[folder_obj] = tree
            user_tree = climb_to_package(user_tree, folder_obj)

    # Add all permitted files to the user tree with theirs parents.
    for file_obj in permitted_files:
        # Add to user tree iof the parent folder is already there.
        if not place_file_in_tree(user_tree, file_obj):
            # Cold not find the parent folder in the tree.
            # Creating a base tree with the parent folder
            # the  file at root level and the climbing up to the Package
            # Merging when required
            tree = {
                "files": [file_obj, ]
            }
            user_tree[file_obj.parent] = tree
            user_tree = climb_to_package(user_tree, file_obj.parent)

    return user_tree

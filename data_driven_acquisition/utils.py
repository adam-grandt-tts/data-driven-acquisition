import re

from django.db.models.query import QuerySet
from django.utils.text import slugify
from django.conf import settings

from trello import TrelloClient, Card
from trello.exceptions import ResourceUnavailable


from guardian.shortcuts import (
    get_objects_for_user,
    get_perms_for_model)

from data_driven_acquisition.templates.trello_card import (
    template_card,
    checklists)


def apply_properties(data, properties):
    """
        Apply the provided properties to a data string following one of these
        formats:

        1. "{{ Property Name }}" : The entire string will be replaces with the value.
        2. <!--PROPERTY:property_name-->VALUE<!--/PROPERTY:property_name--> The
            value will replace the string between the comments. Leaving the comments
            in place for later update.
        3. "**Propert Name:**VALUE" The name will remain unaffected, the value will change.
    """
    # Github returns bytes and we need a string so:
    if type(data) == bytes:
        data = str(data, encoding='utf-8')

    # If we got a query set translate to dict
    # This allows us to send either query sets ior simple dict into this util
    if isinstance(properties, QuerySet):
        properties = {p.name: p.value for p in properties}

    for prop in properties.keys():

        # {{ Var }} format
        data = data.replace(f"{{{{{prop}}}}}", str(properties[prop]))

        # <!--PROPERTY:var-->VALUE<!--/PROPERTY:var--> format
        re_str = re.compile(f"<!--PROPERTY:{prop}-->.+?<!--/PROPERTY:{prop}-->")

        if re.search(re_str, data):
            new_str = f"<!--PROPERTY:{prop}-->{properties[prop]}<!--/PROPERTY:{prop}-->"
            data = re.sub(re_str, new_str, data)

        # "**Property Name:**VALUE" format
        re_str = f"\*\*{prop}:\*\*.*?\\n"

        if re.search(re_str, data, flags=re.IGNORECASE):

            new_str = f"**{prop}:** {properties[prop]}\n"
            data = re.sub(re_str, new_str, data, flags=re.IGNORECASE)

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


def get_package_tree(user_tree, package):
    """ Get a user tree and package nad return a sorted package tree"""
    package_tree = {}

    # Find package in user tree
    for key, value in user_tree.items():
        if key.id == package.id:
            package_tree = value
            break

    if not package_tree:
        return package_tree
    
    # Put files aside 
    if 'files' in package_tree.keys():
        files = package_tree.pop('files')
    else:
        files = []
    
    # Sort the folder names 
    sorted_top_folders  = sorted([x.name for x in package_tree.keys()])

    # Put it back together in teh right order

    out = {}
    for folder_name in sorted_top_folders:
        for f in package_tree.keys():
            if f.name == folder_name:
                out[f] = package_tree[f]
                break
    out['files'] = files

    return out


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


def package_prop_by_tab(package, tabs, template=False):
    """Return a dictionary of tabs and their property query set for a package"""
    out = {}
    for tab in tabs:
        if template:
            out[tab[0]] = package.properties.filter(tab=tab[0])
        else:
            out[tab[0]] = package.properties.filter(prop__tab=tab[0])
    return out


def highlight_properties(data, properties):
    """
        return data will properties highlighted
        <!--PROPERTY:property_name-->VALUE<!--/PROPERTY:property_name--> The
        value will replace the string between the comments. Leaving the comments
        in place for later update.
    """

    # Github returns bytes and we need a string so:
    if type(data) == bytes:
        data = str(data, encoding='utf-8')

    # If we got a query set translate to dict
    # This allows us to send either query sets ior simple dict into this util
    if isinstance(properties, QuerySet):
        properties = {p.name: p.value for p in properties}

    for prop in properties.keys():

        # <!--PROPERTY:var-->VALUE<!--/PROPERTY:var--> format
        re_str = f"<!--PROPERTY:{prop}-->.*<!--/PROPERTY:{prop}-->"

        if re.search(re_str, data):
            new_str = f'<!--PROPERTY:{prop}-->'

            if properties[prop]:
                new_str += f'<span style="background-color: yellow">'
                new_str += f'{properties[prop]}'
            else:
                new_str += f'<span style="background-color: gray">'
                new_str += f'[{prop}]'

            new_str += f'</span>'
            new_str += f'<!--/PROPERTY:{prop}-->'

            data = re.sub(re_str, new_str, data)

    return data


def lowlight_properties(data, properties):
    """
        return data without properties highlight
        <!--PROPERTY:property_name-->VALUE<!--/PROPERTY:property_name--> The
        value will replace the string between the comments. Leaving the comments
        in place for later update.
    """

    if not data:
        return ""

    # Github returns bytes and we need a string so:
    if type(data) == bytes:
        data = str(data, encoding='utf-8')

    # If we got a query set translate to dict
    # This allows us to send either query sets ior simple dict into this util
    if isinstance(properties, QuerySet):
        properties = {p.name: p.value for p in properties}

    for prop in properties.keys():

        # <!--PROPERTY:var-->VALUE<!--/PROPERTY:var--> format
        re_str = f"<!--PROPERTY:{prop}-->.*<!--/PROPERTY:{prop}-->"

        if re.search(re_str, data):
            new_str = f'<!--PROPERTY:{prop}-->'

            if properties[prop]:
                new_str += f'{properties[prop]}'

            new_str += f'<!--/PROPERTY:{prop}-->'

            data = re.sub(re_str, new_str, data)

    return data


def trello_board():
    """ A wrapper for trello API connections """
    client = TrelloClient(
        api_key=settings.TRELLO["APP_KEY"],
        api_secret=settings.TRELLO["APP_SECRET"],
        token=settings.TRELLO["TOKEN"]
    )

    return client.get_board(settings.TRELLO['BOARD_ID'])


def trello_list_get_or_create(list_name):
    """ Get or create a list by nam,e _list_name on trello board."""

    board = trello_board()

    for a_list in board.all_lists():
        if a_list.name == list_name:
            return a_list
    # No list found, make one.
    the_list = board.add_list(list_name, 'top')
    return the_list


def trello_card_desc(package, tabs):
    """Generate a trello card description from package attributes"""

    properties  = package_prop_by_tab(package, tabs)
    tab_names = sorted(properties)
    title = package.get_package_property_by_name('Title')

    desc = f'**Title:** {title}\n'
    desc += '=============\n'
    desc += '\n'

    for tab_name in tab_names:
        desc += f'{tab_name}\n'
        desc += '-----------\n'

        for prop in properties[tab_name]:
            # Skipping Title 
            if prop.name == 'Title':
                continue
            desc += f'- **{prop.name}:** {prop.value}\n'
        
        desc += '\n'
    return desc


def trello_card_get_or_create(package):
    """
        Get the card object for a package, if no card is available create one.
        NOTE: Packages with no status are assumes to be in "-- NO STATUS --".
    """

    if not package.is_package:
        raise ValueError('Must be a valid package')

    # Make sure the package has a status, if it dose not assing the default one.
    if not package.status:
        package.status = list(package.STATUS)[0][0]
        package.save()

    trello_list = trello_list_get_or_create(package.status)

    if not package.project_card_id:
        # No card listed, creating a new one.
        trello_card = trello_list.add_card(
            package.name,
            desc=trello_card_desc(
                package,
                package.properties.all()[0].prop.TABS 
            ),
            position='top'
        )

        for cl in checklists:
            trello_card.add_checklist(
                cl['name'],
                [x['name'] for x in cl['items']])

        package.project_card_id = trello_card.id
        package.save()
        return trello_card
    else:
        # Get the card and return it, if the card is not found raise ValueError
        try:
            card = Card(trello_board(), package.project_card_id)
            card.fetch()
        except ResourceUnavailable:
            raise ValueError('Probided card ID is invalid.')
        return card


        
        
        





# def trello_required(function):
#     """Decorator to check if we need a Trello token and have it in session.
#         IF we need and don't hav it in session go get it from trello.
#     """

#     def _dec(view_func):
#         def _view(request, *args, **kwargs):
#              # If Trello is disabled, do nothing
#             if not settings.USE_TRELLO:
#                 return view_func(request, *args, **kwargs)

#             current_token = request.session.get('trello_token')
#             if not current_token:
#                 trello_auth_url = ''.join([
#                     'https://trello.com/1/authorize?expiration=never',
#                     '&name=DataDrivenAcquisition&scope=read,write&response_type=token',
#                     '&return_url=' + request.build_absolute_uri('/trello/'),
#                     f'&key={settings.TRELLO["APP_KEY"]}'])
#                 print(trello_auth_url)
#                 # Need trello token but dnt have it, redirecting to
#                 # return HttpResponseRedirect(url)
#                 return view_func(request, *args, **kwargs)
#             else:
#                 return view_func(request, *args, **kwargs)
#         return _view
#     return _dec(function)

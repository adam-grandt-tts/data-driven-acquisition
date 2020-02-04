# -*- coding: utf-8 -*-

from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User

from model_utils.models import TimeStampedModel, StatusModel, SoftDeletableModel
from model_utils import Choices

from github import Github
from github.GithubException import GithubException

from .utils import apply_properties

import base64
import logging
import reversion


logger = logging.getLogger('data_driven_acquisition')


class PackageTemplate(TimeStampedModel, StatusModel, SoftDeletableModel):
    """A template of a an acquisition package.
    A package contains a group of folder and files templates and is stored in
    a github repository.
    """
    STATUS = Choices('Draft', 'Available', 'Deprecated')

    title = models.CharField(
        max_length=256,
        null=False,
        blank=False)

    package_root_path = models.CharField(
        max_length=1024,
        help_text="The path to the package locairton in the repository",
        blank=False,
        null=False)

    properties = models.ManyToManyField(
        'PackageProperty',
        related_name='packages',
    )

    class Meta:
        permissions = (
            ('can_deploy', 'Can deploy package from template'),
        )
        get_latest_by = 'created_at'
        verbose_name_plural = 'Packages Templates'

    def _create_content(self, parent, github, contents):
        """Create a Folder instance with the provided parent and all child docs.

        parent: Either a Folder object or None for packages.
        comtent: folder content list as generated by the github API
        """
        for content in contents:
            print("Processing %s" % content.path)

            if content.type == 'dir':
                # Creating folder
                folder = Folder(
                    name=apply_properties(
                        content.name, parent.package.properties.all()),
                    parent=parent
                )
                folder.save()
                logger.info(
                    'Create folder {folder.name} under {folder.parent.name} '
                    'in package {folder.package.name}.'
                )

                # Get folder content
                folder_contents = github["repo"].get_dir_contents(
                    content.path,
                    ref=github["branch"].commit.sha)
                logger.info('Got folder {content.path} content from github.')

                # Go diving
                self._create_content(folder, github, folder_contents)

            else:
                try:
                    path = content.path
                    file_content = github["repo"].get_contents(
                        path,
                        ref=github["branch"].commit.sha)
                    file_data = base64.b64decode(file_content.content)
                    file_ext = content.name.split('.')[-1]
                    if file_ext == 'html':
                        file_type = File.TYPES['Document']
                    elif file_ext == 'json':
                        file_type = File.TYPES['Sheet']
                    else:
                        file_type = File.TYPES['Other']

                    new_file = File(
                        parent=parent,
                        name=apply_properties(
                            content.name, parent.package.properties.all()),
                        file_type=file_type,
                        content=apply_properties(
                            file_data, parent.package.properties.all())
                    )

                    new_file.save()
                    logger.info(
                        'Got and created {file.name} under {file.parent.name} '
                        'in package {file.package.name}.'
                    )

                except (GithubException, IOError) as exc:
                    logger.error('Error processing %s: %s', content.path, exc)
                    return False

    def deploy(self, name, property_values):
        """ Deploy a new package from the template.
            Set the property values based on the provided properties dictionary.
        """

        try:
            # Get the github repo content
            github = {}
            github["gh"] = Github(settings.GITHUB["ACCESS_KEY"])
            github["repo"] = github["gh"].get_user().get_repo(
                settings.GITHUB["TEMPLATE_REPO"])
            github["branch"] = github["repo"].get_branch('master')
            contents = github["repo"].get_dir_contents(
                self.package_root_path,
                ref=github["branch"].commit.sha)
        
            logger.info('Got template {self.package_root_path} from github.')

        except (GithubException, IOError) as exc:
            logger.error('Error processing %s: %s', self.package_root_path, exc)
            return False
        
        from pprint import pprint
        pprint(property_values)

        # Create the Package folder
        package = Folder(
            name=apply_properties(name, property_values),
        )
        package.save()
        for prop in self.properties.all():
            new_val = PropertyValue(
                package=package,
                prop=prop,
                value=property_values.get(f'prop_{prop.id}', '')
            )
            new_val.save()
        
        logger.info('Create package {package.name}.')

        # Creating package content
        self._create_content(package, github, contents)
        return package
    
    def __str__(self):
        return self.title

    # TODO: Create the make package method, this will grab the var names from
    # all the files in the tempalate and populate the properties Hstore in the
    # package.


@reversion.register()
class Folder(TimeStampedModel, StatusModel, SoftDeletableModel):
    """Represents a folder containing multiple documents.
    Folders can have have other folders as parents.
    If folder dose not have a parent folder it will be considered a package.
    Packages are folders that wil have the following attribute enabled:
        The project URL of the trello board.
        The properties JSON array stored in an HSStore that will include all
        configured properties for this package.
    """
    STATUS = Choices(
        '00 - Unassigned',
        '01 - Requirement Development',
        '02 - Solicitation Development',
        '03 - Solicitation Issued',
        '04 - Evaluations',
        '05 - Awarded Contracts',
        '06 - Modifications',
        '07a - 120 days before renewal',
        '08b - 60 days before expiration',
        '07 - Pending Closeout',
        '08 - Closed Out',
        '08a - 60 days before renewal',
        '07b - 120 days before expiration',
        'A - P-card planning',
        'B - P-card active',
        'C - P-card closed'
    )

    name = models.CharField(
        max_length=256,
        null=False,
        blank=False)
    
    owner = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='acquisitions',
        null=True,
        blank=True    
    )

    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        related_name='subfolders',
        null=True,
        blank=True)

    project_card_id = models.CharField(
        blank=True,
        null=True,
        max_length=1024,
        help_text='Trello Card ID'
    )

    class Meta:
        permissions = (
            ('can_set_properties', 'Can set properties on folder'),
            ('can_propagate_properties', 'Can propagate properties to children.'),
            ('can_edit_child_content', 'Can edit content of children.'),
        )
        get_latest_by = 'created_at'
        verbose_name_plural = 'Folders & Packages'

    def __str__(self):
        if self.is_package:
            return f"Package {self.id}: {self.name}"
        else:
            return f"Folder {self.id}: {self.name}"

    def __repr__(self):
        return self.__str__()

    @property
    def is_package(self):
        """Is this folder a package?"""
        if self.parent is None:
            return True
        else:
            return False

    @property
    def package(self):
        """Return the root folder of the package"""
        p = self
        while p.parent is not None:
            p = p.parent
        return p

    @property
    def agency_partner(self):
        return self.get_package_property_by_name('Agency-Partner').value or ''

    @property
    def office_team(self):
        return self.get_package_property_by_name('Office Team').value or ''

    @property
    def office(self):
        return self.get_package_property_by_name('Office').value or ''


    def get_package_property_by_name(self, name):
        prop = self.properties.filter(prop__name=name)
        if len(prop) >= 1:
            return prop[0]
        else:
            return ''

            

    def update_children(self, update_user=None):
        """Update all child objects based on the package properties"""
        # Get new properties to apply
        props = self.package.properties.all()

        # Update all child files
        for child in self.files.all():
            with reversion.create_revision():
                child.content = apply_properties(child.content, props)
                child.save()

                if update_user:
                    reversion.set_user(update_user)
                reversion.set_comment("Updated as part of package updates")

        # Update subfolder names and dive
        for sub in self.subfolders.all():
            with reversion.create_revision():
                sub.name = apply_properties(sub.name, props)
                sub.save()

                if update_user:
                    reversion.set_user(update_user)
                reversion.set_comment("Updated as part of package updates")

            sub.update_children(update_user)
        return True

    def save(self, *args, **kwargs):

        # We cant have a folder be its own parent
        # This prob should be done by ID but new objects have no ID
        if self.parent and self.parent.name == self.name:
            raise ValidationError('You can\'t have a folder be its own parent.')

        # Folder name must be unique in its parent
        # if we are updating we exclude ourselves form the check or it will
        # allways be True
        allsubs = Folder.objects.filter(parent=self.parent)
        if self.id:
            allsubs = allsubs.exclude(id=self.id)

        if self.name in [f.name for f in allsubs]:
            raise ValidationError('Folder name must be unique in parent.')

        return super(Folder, self).save(*args, **kwargs)


@reversion.register()
class File(TimeStampedModel, SoftDeletableModel):
    """Represent a file in a package"""
    TYPES = Choices('Document', 'Sheet', 'Other')

    parent = models.ForeignKey(
        'Folder',
        on_delete=models.CASCADE,
        related_name='files',
        null=False,
        blank=False)

    name = models.CharField(
        max_length=256,
        null=False,
        blank=False)

    content = models.TextField()

    file_type = models.CharField(
        choices=TYPES,
        max_length=15,
        blank=False,
        null=False,
        default='Document')

    class Meta:
        permissions = (
            ('can_edit_content', 'Can edit file content'),
        )
        get_latest_by = 'created_at'

    def __str__(self):
        return f'File {self.id} {self.name}'
    
    def __repr__(self):
        return self.__str__()

    @property
    def package(self):
        """Return the root folder of the package"""
        p = self
        while p.parent is not None:
            p = p.parent
        return p

    @property
    def extname(self):
        """Return the file’s extension"""
        return self.name.split('.')[-1]

    @property
    def basename(self):
        """Return the file’s name without extension"""
        return ''.join(self.name.split('.')[:-1])


class PackageProperty(TimeStampedModel, SoftDeletableModel):
    """A property definition for an acquisition."""
    TYPES = Choices(
        'String',
        'Text',
        'Number',
        'Integer',
        'Boolean',
        'List',
        'Date')

    TABS = Choices(
        '1 General Information',
        '2 Acquisition Overview',
        '3 Requirements Document',
        '4 Market Research',
        '5 Solicitation/Evaluation',
        '6 Pre-Award',
        '7 Modification')

    name = models.CharField(
        max_length=256,
        null=False,
        blank=False)

    max_length = models.IntegerField(
        null=True,
        blank=True)

    property_type = models.CharField(
        choices=TYPES,
        max_length=50,
        blank=False,
        null=False,
        default='Document')

    tab = models.CharField(
        choices=TABS,
        max_length=50,
        blank=False,
        null=False,
        default='General')

    description = models.TextField(
        null=True,
        blank=True)

    options_list = models.TextField(
        null=True,
        blank=True,
        help_text='Enter each option in a line.')

    @property
    def options(self):
        if self.property_type == 'List':
            if self.options_list:
                return [x.strip for x in self.options_list.split('\n')]
            else:
                return []
        elif self.property_type == 'Boolean':
            return ['Yes', 'No']
        else:
            return None

    @property
    def widget(self):
        if self.property_type == 'Text':
            return 'textarea'
        elif self.property_type == 'Boolean':
            return 'radio'
        elif self.property_type == 'List':
            return 'dropdown'
        else:
            return 'input'

    class Meta:
        get_latest_by = 'created_at'
        verbose_name_plural = 'Packages Properties'

    def __str__(self):
        return f'Property {self.id} {self.name}'
    
    def __repr__(self):
        return self.__str__()


@reversion.register()
class PropertyValue(TimeStampedModel, SoftDeletableModel):
    """A property definition for an acquisition."""

    prop = models.ForeignKey(
        'PackageProperty',
        on_delete=models.PROTECT,
        related_name='values',
        null=False,
        blank=False)

    package = models.ForeignKey(
        'Folder',
        on_delete=models.CASCADE,
        related_name='properties',
        null=False,
        blank=False)

    @property
    def name(self):
        return self.prop.name

    @property
    def property_type(self):
        return self.prop.property_type

    @property
    def max_length(self):
        return self.prop.max_length

    @property
    def description(self):
        return self.prop.description

    @property
    def options(self):
        return self.prop.options

    @property
    def widget(self):
        return self.prop.widget

    @property
    def tab(self):
        return self.prop.tab

    # TODO: Add max length check to save method
    # TODO: Add is package check to save method

    value = models.TextField(
        null=True,
        blank=True)

    class Meta:
        get_latest_by = 'created_at'
        verbose_name_plural = 'Property Values'

    def __str__(self):
        return f'Property Value {self.id} {self.name}'

    def __repr__(self):
        return self.__str__()
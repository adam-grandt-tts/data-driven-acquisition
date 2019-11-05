# -*- coding: utf-8 -*-

from django.conf import settings
from django.db import models
from django.contrib.postgres.fields import HStoreField
from django.core.exceptions import ValidationError

from model_utils.models import TimeStampedModel, StatusModel, SoftDeletableModel
from model_utils import Choices

from github import Github
from github.GithubException import GithubException

from .utils import apply_properties

import base64
import logging

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

    properties = HStoreField(
        blank=True,
        null=True)

    class Meta:
        permissions = (
            ('can_deploy', 'Can deploy package from template'),
        )
        get_latest_by = 'created_at'

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
                        content.name, parent.package.properties),
                    properties=None,
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
                            content.name, parent.package.properties),
                        file_type=file_type,
                        content=apply_properties(
                            file_data, parent.package.properties)
                    )

                    new_file.save()
                    logger.info(
                        'Got and created {file.name} under {file.parent.name} '
                        'in package {file.package.name}.'
                    )

                except (GithubException, IOError) as exc:
                    logger.error('Error processing %s: %s', content.path, exc)
                    return False

    def deploy(self, name, properties):
        """Deploy a new package from the template."""

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
        
        # Create the Package folder
        package = Folder(
            name=apply_properties(name, properties),
            properties=properties,
        )
        package.save()
        logger.info('Create package {package.name}.')

        # Creating package content
        self._create_content(package, github, contents)
        
    def __str__(self):
        return self.title

    # TODO: Create the make package method, this will grab the var names from
    # all the files in the tempalate and populate the properties Hstore in the
    # package.


class Folder(TimeStampedModel, StatusModel, SoftDeletableModel):
    """Represents a folder containing multiple documents.
    Folders can have have other folders as parents.
    If folder dose not have a parent folder it will be considered a package.
    Packages are folders that wil have the following attribute enabled:
        The project URL of the trello board.
        The properties JSON array stored in an HSStore that will include all
        configured properties for this package.
    """
    STATUS = Choices('Draft', 'In Progress', 'Completed')

    name = models.CharField(
        max_length=256,
        null=False,
        blank=False)

    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        related_name='subfolders',
        null=True,
        blank=True)

    properties = HStoreField(
        blank=True,
        null=True)

    project_card_id = models.URLField(
        blank=True,
        null=True,
        help_text='Trello Card IDL'
    )

    class Meta:
        permissions = (
            ('can_set_properties', 'Can set properties on folder'),
            ('can_propagate_properties', 'Can propagate properties to children.'),
            ('can_edit_child_content', 'Can edit content of children.'),
        )
        get_latest_by = 'created_at'

    def __str__(self):
        if self.is_package:
            return f"Package {self.id}: {self.name}"
        else:
            return f"Folder {self.id}: {self.name}"

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

    def update_children(self):
        """Update all child objects based on the package properties"""
        # Get new properties to apply
        props = self.package.properties

        # Update al child files
        for child in self.files.all():
            child.content = apply_properties(child.content, props)
            child.save()

        # Update subfolder names and dive
        for sub in self.subfolders.all():
            sub.name = apply_properties(sub.name, props)
            sub.save()
            sub.update_children()

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

    @property
    def package(self):
        """Return the root folder of the package"""
        p = self
        while p.parent is not None:
            p = p.parent
        return p


# -*- coding: utf-8 -*-

from django.db import models
from django.contrib.postgres.fields import HStoreField
from django.core.exceptions import ValidationError

from model_utils.models import TimeStampedModel, StatusModel, SoftDeletableModel
from model_utils import Choices


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

    root_package_path = models.CharField(
        max_length=256,
        blank=False,
        null=False)
    
    properties = HStoreField(
        blank=True,
        null=True)

    class Meta:
        permissions = (
            ('can_deploy', 'Can deploy from template'),
        )
        get_latest_by = 'created_at'

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

    project_url = models.URLField(
        blank=True,
        null=True,
        help_text='Trello project URL'
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

    def is_package(self):
        """Is this folder a package?"""
        if self.parent is None:
            return True
        else:
            return False

    def package(self):
        """Return the root folder of the package"""
        p = self
        while p.parent is not None:
            p = p.parent
        return p

    def save(self, *args, **kwargs):

        # We cant have a folder be its own parent
        if self.parent and self.parent.name == self.name:
            raise ValidationError('You can\'t have a folder be its own parent.')

        # Folder name must be unique in its parent
        if self.parent and self.parent.name in [f.name for f in self.subfolders]:
            raise ValidationError('Folder name must be unique in parent.')

        return super(Folder, self).save(*args, **kwargs)


class File(TimeStampedModel, SoftDeletableModel):
    """Represent a file in a package"""
    TYPES = Choices('Document', 'Sheet', 'Other')

    parent = models.ForeignKey(
        'Folder',
        on_delete=models.CASCADE,
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
        return self.name


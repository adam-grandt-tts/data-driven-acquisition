# -*- coding: utf-8 -*-

from django.db import models
from django.contrib.postgres.fields import HStoreField

from model_utils.models import TimeStampedModel, StatusModel, SoftDeletableModel
from model_utils import Choices


class PackageTemplate(TimeStampedModel, StatusModel, SoftDeletableModel):
    """A template of a an acquisition package.
    A package contains a group of folder and files templates and is stored in
    a github repository.
    """
    STATUS = Choices('Draft', 'Available', 'Deprecated')
    root_package_path = models.CharField(
        max_length=256,
        blank=False,
        null=False)

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

    def is_package(self):
        if self.parent is None:
            return True
        else:
            return False

    # TODO Unique name in parent on save


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


class ACL(TimeStampedModel, SoftDeletableModel):
    """Access control List to Templates, Folders and Files"""
    ACCESS_LEVELS = Choices('Read', 'Write', 'Admin')
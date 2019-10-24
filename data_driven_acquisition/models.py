# -*- coding: utf-8 -*-

from django.db import models
from django.contrib.postgres.fields import HStoreField

from model_utils.models import TimeStampedModel, StatusModel, SoftDeletableModel
from model_utils import Choices

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

    properties = HStoreField(blank=True, null=True)

    #TODO Unique name in parent on save 
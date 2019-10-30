# -*- coding: utf-8 -*-

from django.conf import settings
from django.db import models
from django.contrib.postgres.fields import HStoreField
from django.core.exceptions import ValidationError

from model_utils.models import TimeStampedModel, StatusModel, SoftDeletableModel
from model_utils import Choices

from github import Github


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

    def deploy(self, properties):
        """Deploy a new package from the template."""

        # Get the gothub repo content
        gh = Github(settings.GITHUB["ACCESS_KEY"])
        repo = gh.get_user().get_repo(settings.GITHUB["TEMPLATE_REPO"])
        branch = repo.get_branch('master')
        contents = repo.get_dir_contents(
            self.package_root_path,
            ref=branch.commit.sha)

        for content in contents:
            print ("Processing %s" % content.path)
            if content.type == 'dir':
                download_directory(repository, sha, content.path)
            else:
                try:
                    path = content.path
                    file_content = repository.get_contents(path, ref=sha)
                    file_data = base64.b64decode(file_content.content)
                    file_out = open(content.name, "w")
                    file_out.write(file_data)
                    file_out.close()
                except (GithubException, IOError) as exc:
                    logging.error('Error processing %s: %s', content.path, exc)

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


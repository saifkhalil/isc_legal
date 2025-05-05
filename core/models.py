import json

from asgiref.sync import async_to_sync
from auditlog.models import LogEntry as OriginalLogEntry
from channels.layers import get_channel_layer
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import NON_FIELD_ERRORS, ValidationError
from django.core.validators import FileExtensionValidator
from django.db import connection, models, transaction
from django.utils.translation import gettext_lazy as _
from mptt.models import MPTTModel, TreeForeignKey

from accounts.models import User
from .classes import EventManagerMethodAfter
from .decorators import method_event
from .events import (
    event_path_deleted, event_path_document_added, event_path_document_removed
)
from .model_mixins import ExtraDataModelMixin, HooksModelMixin


class priorities(models.Model):
    id = models.AutoField(primary_key=True, )
    priority = models.CharField(
        max_length=250, blank=False, null=False, verbose_name=_('Priority'))

    def __str__(self):
        return self.priority

    def __unicode__(self):
        return self.priority

    class Meta:
        verbose_name = _('Priority')
        verbose_name_plural = _('Priorities')


class replies(models.Model):
    id = models.AutoField(primary_key=True, )
    reply = models.CharField(max_length=250, blank=False,
                             null=False, verbose_name=_('Reply'))
    comment_id = models.BigIntegerField(blank=True, null=True)
    is_deleted = models.BooleanField(
        default=False, verbose_name=_("Is Deleted"))
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True, editable=False)
    created_by = models.ForeignKey(
        User, related_name='%(class)s_createdby', on_delete=models.CASCADE, blank=True, null=True, editable=False)
    modified_by = models.ForeignKey(
        User, related_name='%(class)s_modifiedby', null=True, blank=True, on_delete=models.CASCADE, editable=False)

    def __str__(self):
        return self.reply

    def __unicode__(self):
        return self.reply

    class Meta:
        verbose_name = _('Reply')
        verbose_name_plural = _('Replies')
        ordering = ['-created_at']


class comments(models.Model):
    id = models.AutoField(primary_key=True, )
    comment = models.CharField(
        max_length=250, blank=False, null=False, verbose_name=_('Comment'))
    replies = models.ManyToManyField(
        replies, related_name='%(class)s_replies', blank=True, verbose_name=_('Reply'))
    case_id = models.BigIntegerField(blank=True, null=True)
    folder_id = models.BigIntegerField(blank=True, null=True)
    event_id = models.BigIntegerField(blank=True, null=True)
    task_id = models.BigIntegerField(blank=True, null=True)
    hearing_id = models.BigIntegerField(blank=True, null=True)
    notation_id = models.BigIntegerField(blank=True, null=True)
    contract_id = models.BigIntegerField(blank=True, null=True)
    is_deleted = models.BooleanField(
        default=False, verbose_name=_("Is Deleted"))
    created_at = models.DateTimeField(
        auto_now_add=True, blank=True, null=True, editable=False)
    modified_at = models.DateTimeField(
        auto_now=True, blank=True, null=True, editable=False)
    created_by = models.ForeignKey(
        User, related_name='%(class)s_createdby', on_delete=models.CASCADE, blank=True, null=True, editable=False)
    modified_by = models.ForeignKey(
        User, related_name='%(class)s_modifiedby', null=True, blank=True, on_delete=models.CASCADE, editable=False)

    def __str__(self):
        return str(self.id)

    def __unicode__(self):
        return str(self.id)

    class Meta:
        verbose_name = _('Comment')
        verbose_name_plural = _('Comments')
        ordering = ['-created_at']


class court(models.Model):
    id = models.AutoField(primary_key=True, )
    name = models.CharField(max_length=250, unique=True,
                            blank=False, null=False, verbose_name=_('Name'))

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = _('Court')
        verbose_name_plural = _('Courts')
        ordering = ["name"]


class contracts(models.Model):
    id = models.AutoField(primary_key=True, )
    name = models.CharField(max_length=250, blank=False,
                            null=False, verbose_name=_('Name'))
    attachment = models.FileField(upload_to='contracts/%Y/%m/%d/', verbose_name=_('Attachment'), validators=[
        FileExtensionValidator(['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png', 'git'])])
    is_deleted = models.BooleanField(
        default=False, verbose_name=_("Is Deleted"))
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True, editable=False)
    created_by = models.ForeignKey(
        User, related_name='%(class)s_createdby', on_delete=models.CASCADE, blank=True, null=True, editable=False)
    modified_by = models.ForeignKey(
        User, related_name='%(class)s_modifiedby', null=True, blank=True, on_delete=models.CASCADE, editable=False)


class documents(ExtraDataModelMixin, HooksModelMixin, models.Model):
    id = models.AutoField(primary_key=True, )
    name = models.CharField(max_length=250, blank=False,
                            null=False, verbose_name=_('Name'))
    attachment = models.FileField(upload_to='documents/%Y/%m/%d/', verbose_name=_('Attachment'), validators=[
        FileExtensionValidator(['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png', 'git'])])
    case_id = models.IntegerField(
        blank=True, null=True, verbose_name=_('Litigation Case'))
    path_id = models.IntegerField(
        blank=True, null=True, verbose_name=_('Path'))
    folder_id = models.IntegerField(
        blank=True, null=True, verbose_name=_('Folder'))
    task_id = models.IntegerField(
        blank=True, null=True, verbose_name=_('Task'))
    hearing_id = models.IntegerField(
        blank=True, null=True, verbose_name=_('Hearing'))
    is_deleted = models.BooleanField(
        default=False, verbose_name=_("Is Deleted"))
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True, editable=False)
    created_by = models.ForeignKey(
        User, related_name='%(class)s_createdby', on_delete=models.CASCADE, blank=True, null=True, editable=False)
    modified_by = models.ForeignKey(
        User, related_name='%(class)s_modifiedby', null=True, blank=True, on_delete=models.CASCADE, editable=False)


    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name

class Path(MPTTModel):
    name = models.CharField(max_length=100,)
    parent = TreeForeignKey('self', on_delete=models.CASCADE,
                            null=True, blank=True, related_name='children')
    documents = models.ManyToManyField(
        blank=True, related_name='paths', to=documents,
        verbose_name=_('Documents')
    )
    case_id = models.IntegerField(
        blank=True, null=True, verbose_name=_('Litigation Case'))
    folder_id = models.IntegerField(
        blank=True, null=True, verbose_name=_('Folder'))
    admin_id = models.IntegerField(
        blank=True, null=True, verbose_name=_('Administrative Investigation'))
    notation_id = models.IntegerField(blank=True, null=True, verbose_name=_('Notation'))
    contract_id = models.IntegerField(blank=True, null=True, verbose_name=_('Contract'))
    # is_deleted = models.BooleanField(default=False,verbose_name=_("Is Deleted"))
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True, editable=False)
    created_by = models.ForeignKey(
        User, related_name='%(class)s_createdby', on_delete=models.CASCADE, blank=True, null=True)
    modified_by = models.ForeignKey(
        User, related_name='%(class)s_modifiedby', null=True, blank=True, on_delete=models.CASCADE, editable=False)

    class MPTTMeta:
        level_attr = 'level'
        order_insertion_by = ['name']

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name

    class Meta:
        unique_together = ('parent', 'name')
        verbose_name = _('Path')
        verbose_name_plural = _('Paths')

    @property
    def active_path(self):
        return self.children

    @method_event(
        action_object='self',
        event=event_path_document_added,
        event_manager_class=EventManagerMethodAfter
    )
    def _document_add(self, document, user=None):
        self._event_actor = user
        self._event_target = document
        self.documents.add(document)

    @method_event(
        action_object='self',
        event=event_path_document_removed,
        event_manager_class=EventManagerMethodAfter
    )
    def _document_remove(self, document, user=None):
        self._event_actor = user
        self._event_target = document
        self.documents.remove(document)

    @method_event(
        action_object='parent',
        event=event_path_deleted,
        event_manager_class=EventManagerMethodAfter
    )
    def delete(self, *args, **kwargs):
        self._event_actor = getattr(self, '_event_actor', 'parent')

        result = super().delete(*args, **kwargs)

        if not self.parent:
            self._event_ignore = True

        return result

    def get_absolute_url(self):
        return reverse(
            viewname='path_view', kwargs={
                'path_id': self.pk
            }
        )

    def save(self, *args, **kwargs):
        return super().save(*args, **kwargs)

    def validate_unique(self, exclude=None):
        """
        Explicit validation of uniqueness of parent+name as the provided
        unique_together check in Meta is not working for all 100% cases
        when there is a FK in the unique_together tuple
        https://code.djangoproject.com/ticket/1751
        """
        with transaction.atomic():
            if connection.vendor == 'oracle':
                queryset = Path.objects.filter(
                    parent=self.parent, name=self.name
                )
            else:
                queryset = Path.objects.select_for_update().filter(
                    parent=self.parent, name=self.name
                )

            if queryset.exists():
                params = {
                    'model_name': _('Path'),
                    'field_names': _('Parent and Name')
                }
                raise ValidationError(
                    message={
                        NON_FIELD_ERRORS: [
                            ValidationError(
                                message=_(
                                    '%(model_name)s with this %(field_names)s already '
                                    'exists.'
                                ), code='unique_together', params=params
                            )
                        ]
                    }
                )



class Status(models.Model):
    theme_colors= (
        ("primary","primary"),
        ("secondary","secondary"),
        ("success","success"),
        ("info","info"),
        ("warning","warning"),
        ("danger","danger"),
        ("light","light"),
        ("dark","dark")
    )
    
    id = models.AutoField(primary_key=True, )
    status = models.CharField(
        max_length=250, blank=False, null=False, verbose_name=_('Status'))
    icon = models.CharField(default='bi bi-bootstrap',
        max_length=250, blank=False, null=False, verbose_name=_('Icon'))
    color = models.CharField(choices=theme_colors, default='primary',
        max_length=250, blank=False, null=False, verbose_name=_('Color'))
    is_deleted = models.BooleanField(
        default=False, verbose_name=_("Is Deleted"))
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True, editable=False)
    created_by = models.ForeignKey(
        User, related_name='%(class)s_createdby', on_delete=models.CASCADE, blank=True, null=True, editable=False)
    is_completed = models.BooleanField(default=False, verbose_name=_("Is Completed"))
    is_done = models.BooleanField(default=False, verbose_name=_("Is Done"))

    def __str__(self):
        return self.status

    def __unicode__(self):
        return self.status

    class Meta:
        verbose_name = _('Status')
        verbose_name_plural = _('Statuses')


class NotificationManager(models.Manager):
    def create_notification(self, action, content_type, object_id, object_name, user, action_by, role):
        Notification = self.create(action=action, content_type=content_type,
                                   object_id=object_id, object_name=object_name, user=user, action_by=action_by, role=role)
        # do something with the book
        return Notification



class Notification(models.Model):

    CREATE = 0
    UPDATE = 1
    DELETE = 2
    ACCESS = 3

    choices = (
        (CREATE, _("create")),
        (UPDATE, _("update")),
        (DELETE, _("delete")),
        (ACCESS, _("access")),
    )
    id = models.AutoField(primary_key=True, )
    action_at = models.DateTimeField(auto_now_add=True)
    action_by = models.ForeignKey(
        User, related_name='%(class)s_actionby', on_delete=models.CASCADE, blank=True, null=True)
    # model = models.CharField(verbose_name="Model Name", max_length=50)
    # obj = models.IntegerField(verbose_name=_("Object ID"))
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    object_name = models.CharField(verbose_name="Object Name",
                            max_length=200, blank=True, null=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    user = models.ForeignKey(
        User, related_name='%(class)s_user', on_delete=models.CASCADE, blank=True, null=True)
    role = models.CharField(verbose_name="Role",
                            max_length=20, blank=True, null=True)
    created_by = models.ForeignKey(
        User, related_name='%(class)s_createdby', on_delete=models.CASCADE, blank=True, null=True, editable=False)
    action = models.CharField(verbose_name="Action", max_length=20,choices=choices)
    is_deleted = models.BooleanField(
        default=False, verbose_name=_("Is Deleted"))
    is_read = models.BooleanField(verbose_name="Read Status", default=False)
    browser_read = models.BooleanField(verbose_name="Brwoser Read Status", default=False)

    objects = NotificationManager()

    def __str__(self):
        return f'{self.action_by.username if self.action_by else None} is {self.action} the {self.content_type.model} - {self.object_id} at {self.action_at}'

    def __unicode__(self):
        return self.status

    def mark_as_read(self):
        self.is_read = True
        self.save()

    class Meta:
        verbose_name = _('Notification')
        verbose_name_plural = _('Notifications')
        ordering = ['-action_at']

    def send_notification(self):
        """Send notification event to WebSocket consumers."""
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"notifications_{self.user.id}",  # Send notification to the user's WebSocket group
            {
                "type": "send_notification",
                "message": json.dumps({
                    "id": self.id,
                    "content_type": self.content_type.name,
                    "action": self.action,
                    "action_by": self.action_by.username if self.action_by else "System",
                    "object_name": self.object_name,
                    "timestamp": self.action_at.strftime("%Y-%m-%d %H:%M"),
                }),
            },
        )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.send_notification()  # Send WebSocket event after saving


#
# class LogEntry(OriginalLogEntry):
#     def get_changes(self):
#         changes = []
#         model = self.content_type.model_class()
#
#         if self.action == OriginalLogEntry.Action.CREATE:
#             # LogEntry was created, so all fields should be considered as changed
#             for field in flatten_fieldsets(model):
#                 change = {
#                     'field': field['name'],
#                     'old': None,
#                     'new': str(getattr(self.object_repr, field['name']))
#                 }
#                 changes.append(change)
#         else:
#             # LogEntry was updated or deleted
#             old_values = self.object_repr.get_edited_object()
#             new_values = self.object_repr.get_object()
#
#             for field in model._meta.fields:
#                 field_name = field.name
#
#                 if field.primary_key or field_name == 'logentry_ptr':
#                     continue
#
#                 old_value = getattr(old_values, field_name)
#                 new_value = getattr(new_values, field_name)
#
#                 if old_value != new_value:
#                     old_value = str(old_value) if old_value else None
#                     new_value = str(new_value) if new_value else None
#
#                     # Convert foreign key IDs to their string representations
#                     if isinstance(field, models.ForeignKey):
#                         old_value = repr(old_value)
#                         new_value = repr(new_value)
#
#                     change = {
#                         'field': field_name,
#                         'old': old_value,
#                         'new': new_value,
#                     }
#                     changes.append(change)
#
#         return changes
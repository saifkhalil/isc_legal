from tabnanny import verbose
from django.db import connection, models, transaction
import uuid
from django.utils.translation import gettext_lazy as _
from ckeditor.fields import RichTextField
from pytz import timezone
from accounts.models import User
from django.core.validators import FileExtensionValidator
import pghistory
from mptt.models import MPTTModel, TreeForeignKey
from .decorators import method_event
from .events import (
    event_path_created, event_path_deleted, event_path_edited,
    event_path_document_added, event_path_document_removed
)
from django.core.exceptions import ValidationError,NON_FIELD_ERRORS
from .model_mixins import ExtraDataModelMixin,HooksModelMixin
from .classes import EventManagerMethodAfter, EventManagerSave




@pghistory.track(pghistory.Snapshot())
class priorities(models.Model):
    id = models.AutoField(primary_key=True,)
    priority = models.CharField(max_length=250, blank=False, null=False,verbose_name=_('Priority'))

    def __str__(self):
        return self.priority

    def __unicode__(self):
        return self.priority

    class Meta:
        verbose_name = _('Priority')
        verbose_name_plural = _('Priorities')

@pghistory.track(pghistory.Snapshot())
class replies(models.Model):
    id = models.AutoField(primary_key=True,)
    reply = models.CharField(max_length=250, blank=False, null=False,verbose_name=_('Reply'))
    comment_id = models.BigIntegerField(blank=True, null=True)
    is_deleted = models.BooleanField(default=False,verbose_name=_("Is Deleted"))
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

    # def save(self, *args, **kwargs):
        
    #     if self.id is None:

    #         self.created_by = self.request.user
    #         self.created_at = timezone.now()
    #     else:
    #         self.modified_by = self.request.user
    #         self.modified_at = timezone.now()
    #     super(comments, self).save(*args, **kwargs)
    #     comments.objects.get(id=self.comment_id).replies.add(self.id)      
    #     return super(comments, self).save(*args, **kwargs)

@pghistory.track(pghistory.Snapshot())
class comments(models.Model):
    id = models.AutoField(primary_key=True,)
    comment = models.CharField(max_length=250, blank=False, null=False,verbose_name=_('Comment'))
    replies = models.ManyToManyField(replies, related_name='%(class)s_replies', blank=True,verbose_name=_('Reply'))
    case_id = models.BigIntegerField(blank=True, null=True)
    folder_id = models.BigIntegerField(blank=True, null=True)
    event_id = models.BigIntegerField(blank=True, null=True)
    task_id = models.BigIntegerField(blank=True, null=True)
    hearing_id = models.BigIntegerField(blank=True, null=True)
    is_deleted = models.BooleanField(default=False,verbose_name=_("Is Deleted"))
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True,blank=True, null=True, editable=False)
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

    # def save(self, *args, **kwargs):
    #     if self.id is None:
    #         self.created_by = self.request.user
    #         self.created_at = timezone.now()
    #     else:
    #         self.modified_by = self.request.user
    #         self.modified_at = timezone.now()            
    #     return super(comments, self).save(*args, **kwargs)
@pghistory.track(pghistory.Snapshot())
class court(models.Model):
    id = models.AutoField(primary_key=True,)
    name = models.CharField(max_length=250,unique=True, blank=False, null=False,verbose_name=_('Name'))

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = _('Court')
        verbose_name_plural = _('Courts')

@pghistory.track(pghistory.Snapshot())
class contracts(models.Model):
    id = models.AutoField(primary_key=True,)
    name = models.CharField(max_length=250, blank=False, null=False,verbose_name=_('Name'))
    attachment = models.FileField(upload_to='contracts/%Y/%m/%d/',verbose_name=_('Attachment'),validators=[FileExtensionValidator(['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png', 'git'])])
    is_deleted = models.BooleanField(default=False,verbose_name=_("Is Deleted"))
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True, editable=False)
    created_by = models.ForeignKey(
        User, related_name='%(class)s_createdby', on_delete=models.CASCADE, blank=True, null=True, editable=False)
    modified_by = models.ForeignKey(
        User, related_name='%(class)s_modifiedby', null=True, blank=True, on_delete=models.CASCADE, editable=False)


@pghistory.track(pghistory.Snapshot())
class documents(ExtraDataModelMixin,HooksModelMixin,models.Model):
    id = models.AutoField(primary_key=True,)
    name = models.CharField(max_length=250, blank=False, null=False,verbose_name=_('Name'))
    attachment = models.FileField(upload_to='documents/%Y/%m/%d/',verbose_name=_('Attachment'),validators=[FileExtensionValidator(['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png', 'git'])])
    case_id = models.IntegerField(blank=True,null=True, verbose_name=_('Litigation Case'))
    path_id = models.IntegerField(blank=True,null=True, verbose_name=_('Path'))
    folder_id = models.IntegerField(blank=True,null=True, verbose_name=_('Folder'))
    is_deleted = models.BooleanField(default=False,verbose_name=_("Is Deleted"))
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True, editable=False)
    created_by = models.ForeignKey(
        User, related_name='%(class)s_createdby', on_delete=models.CASCADE, blank=True, null=True, editable=False)
    modified_by = models.ForeignKey(
        User, related_name='%(class)s_modifiedby', null=True, blank=True, on_delete=models.CASCADE, editable=False)

# @pghistory.track(pghistory.Snapshot())
# class directory(models.Model):
#     id = models.AutoField(primary_key=True,)
#     name = models.CharField(max_length=250, blank=False, null=False,verbose_name=_('Name'))
#     document = models.ManyToManyField(documents, related_name='%(class)s_documents', blank=True,verbose_name=_('documents'))
#     sub_directory = models.ForeignKey('self',null=True, blank=True,on_delete=models.CASCADE,verbose_name=_('Sub directory'))
#     is_deleted = models.BooleanField(default=False,verbose_name=_("Is Deleted"))
#     created_at = models.DateTimeField(auto_now_add=True, editable=False)
#     modified_at = models.DateTimeField(auto_now=True, editable=False)
#     created_by = models.ForeignKey(
#         User, related_name='%(class)s_createdby', on_delete=models.CASCADE, blank=True, null=True, editable=False)
#     modified_by = models.ForeignKey(
#         User, related_name='%(class)s_modifiedby', null=True, blank=True, on_delete=models.CASCADE, editable=False)

@pghistory.track(pghistory.Snapshot())
class Path(MPTTModel):
    name = models.CharField(max_length=50, unique=True)
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    documents = models.ManyToManyField(
        blank=True, related_name='paths', to=documents,
        verbose_name=_('Documents')
    )

    class MPTTMeta:
        order_insertion_by = ['name']

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name

    class Meta:
        unique_together = ('parent', 'name')
        verbose_name = _('Path')
        verbose_name_plural = _('Paths')

    # def __str__(self):
    #     return self.get_full_path()

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

    # @method_event(
    #     event_manager_class=EventManagerSave,
    #     created={
    #         'action_object': 'parent',
    #         'event': event_path_created,
    #         'target': 'self'
    #     },
    #     edited={
    #         'event': event_path_edited,
    #         'target': 'self'
    #     }
    # )
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






@pghistory.track(pghistory.Snapshot())
class Status(models.Model):
    id = models.AutoField(primary_key=True,)
    status = models.CharField(max_length=250, blank=False, null=False,verbose_name=_('Status'))

    def __str__(self):
        return self.status

    def __unicode__(self):
        return self.status

    class Meta:
        verbose_name = _('Status')
        verbose_name_plural = _('Statuses')


from email.policy import default
from statistics import mode
from tabnanny import verbose
from django.db import models
import uuid
from django.utils.translation import gettext_lazy as _
from ckeditor.fields import RichTextField
from accounts.models import User
from core.models import priorities,comments,court,status
from django.core.validators import FileExtensionValidator
from django.utils import timezone
from django.dispatch import receiver
from django.db.models.signals import post_save
import pghistory
# Create your models here.

# class hearing_type(models.Model):
#     id = models.AutoField(primary_key=True,)
#     type = models.CharField(max_length=250, blank=False, null=False,verbose_name=_('Hearing Type'))

#     def __str__(self):
#         return self.type

#     def __unicode__(self):
#         return self.type

#     class Meta:
#         verbose_name = _('Hearing Type')
#         verbose_name_plural = _('Hearing Types')
@pghistory.track(pghistory.Snapshot())
class hearing(models.Model):
    id = models.AutoField(primary_key=True,)
    # hid = models.CharField(max_length=20, blank=False, null=False, verbose_name=_('Hearing ID'))
    name = models.CharField(max_length=250, blank=True, null=True,verbose_name=_('Name'))
    case_id = models.IntegerField(blank=True,null=True, verbose_name=_('Litigation Case'))
    hearing_date = models.DateTimeField(verbose_name=_('Hearing Date'))
    assignee = models.ForeignKey(User, on_delete=models.CASCADE, blank=True,null=True, verbose_name=_('Assignee'))
    # time_spent = models.TimeField(verbose_name=_('Time Spent'))
    comments = models.ManyToManyField(comments,verbose_name="Comments", blank=True)
    court = models.ForeignKey(court, on_delete=models.CASCADE, blank=True,null=True, verbose_name=_('Court name'))
    comments_by_lawyer = models.TextField(max_length=250, blank=True, null=True,verbose_name=_('Summary by lawyer'))
    is_deleted = models.BooleanField(default=False,verbose_name=_("Is Deleted"))
    hearing_status = models.ForeignKey(status, related_name='%(class)s_hearing_status', on_delete=models.CASCADE, null=True, blank=True,verbose_name=_('Hearing Status'),default=1)
    # attachment = models.FileField(upload_to='hearing/%Y/%m/%d/', verbose_name='Attachment', validators=[FileExtensionValidator(['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png', 'gif'])])
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

    class Meta:
        verbose_name = _('Hearing')
        verbose_name_plural = _('Hearings')



# class task_type(models.Model):
#     id = models.AutoField(primary_key=True,)
#     type = models.CharField(max_length=250, blank=False, null=False,verbose_name=_('Task Type'))

#     def __str__(self):
#         return self.type

#     def __unicode__(self):
#         return self.type

#     class Meta:
#         verbose_name = _('Task Type')
#         verbose_name_plural = _('Task Types')

@pghistory.track(pghistory.Snapshot())
class task(models.Model):
    id = models.AutoField(primary_key=True,)
    # tid = models.CharField(max_length=20, blank=False, null=False, verbose_name=_('Task ID'))
    title = models.CharField(max_length=250, blank=False, null=False,verbose_name=_('title'))
    # task_type = models.ForeignKey('task_type', on_delete=models.CASCADE, blank=False,null=False, verbose_name=_('Task Type'))
    description = models.CharField(max_length=250,default='', blank=False, null=False, verbose_name=_('Task Description'))
    assignee = models.ForeignKey(User, related_name='%(class)s_assigned_to', on_delete=models.CASCADE, null=False, blank=False,verbose_name=_('Assigned to'))
    # requested_by = models.ForeignKey(User, related_name='%(class)s_requested_by', on_delete=models.CASCADE, null=False, blank=False,verbose_name=_('Requested By'))
    # priority = models.ForeignKey(priorities,  on_delete=models.CASCADE, null=False, blank=False,verbose_name=_('Matter Priority'))
    task_status = models.ForeignKey(status, related_name='%(class)s_task_status', on_delete=models.CASCADE, null=True, blank=True,verbose_name=_('Task Status'),default=1)
    case_id = models.IntegerField(blank=True,null=True, verbose_name=_('Litigation Case'))
    due_date = models.DateField(verbose_name=_('Due date'))
    comments = models.ManyToManyField(comments,verbose_name="Comments", blank=True)
    is_deleted = models.BooleanField(default=False,verbose_name=_("Is Deleted"))
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True, editable=False)
    created_by = models.ForeignKey(
        User, related_name='%(class)s_createdby', on_delete=models.CASCADE, blank=True, null=True, editable=False)
    modified_by = models.ForeignKey(
        User, related_name='%(class)s_modifiedby', null=True, blank=True, on_delete=models.CASCADE, editable=False)    


    def __str__(self):
        return self.title

    def __unicode__(self):
        return self.title

    class Meta:
        verbose_name = _('Task')
        verbose_name_plural = _('Tasks')

# @receiver(post_save, sender=task)
# def create_task_comment(sender, instance=None, created=False,update_fields=None, **kwargs):
#     if created:
#         current_comment = comments.objects.create(comment="New Task Created by " + str(instance.created_by))
#         instance.comments.add(current_comment)
#     else:
#         if update_fields:
#             current_comment = comments.objects.create(comment="This Task modified by " + str(instance.created_by) + " with fields " + update_fields)
#             instance.comments.add(current_comment)
#         else:
#             current_comment = comments.objects.create(comment="This Task modified by " + str(instance.created_by) )
#             instance.comments.add(current_comment)
    

# class event_type(models.Model):
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     type = models.CharField(max_length=250, blank=False, null=False,verbose_name=_('Event Type'))

#     def __str__(self):
#         return self.type

#     def __unicode__(self):
#         return self.type

#     class Meta:
#         verbose_name = _('Event Type')
#         verbose_name_plural = _('Event Types')


# class event(models.Model):
#     id = models.AutoField(primary_key=True,)
#     eid = models.CharField(max_length=20, blank=True, null=True, verbose_name=_('Event ID'),editable=True)
#     event_type = models.ForeignKey('event_type', on_delete=models.CASCADE, blank=False,null=False, verbose_name=_('Event Type'))
#     created_by = models.ForeignKey(User, related_name='%(class)s_created_by', on_delete=models.CASCADE, null=False, blank=False,verbose_name=_('Created By'))
#     from_date = models.DateTimeField(verbose_name=_('From'),default=timezone.now)
#     to_date = models.DateTimeField(verbose_name=_('To'),default=timezone.now)
#     attendees = models.ManyToManyField(User, related_name='%(class)s_attendees', blank=False,verbose_name=_('Attendees'))
#     comments = models.ManyToManyField(comments,verbose_name="Comments", blank=True)

#     def __str__(self):
#         return str(self.id)

#     def __unicode__(self):
#         return str(self.id)

#     class Meta:
#         verbose_name = _('Event')
#         verbose_name_plural = _('Events')

from email.policy import default
from statistics import mode
from tabnanny import verbose
from django.db import models
import uuid
from django.utils.translation import gettext_lazy as _
from ckeditor.fields import RichTextField
from accounts.models import User
from core.models import priorities,comments
from django.core.validators import FileExtensionValidator
from django.utils import timezone

# Create your models here.

class hearing_type(models.Model):
    id = models.AutoField(primary_key=True,)
    type = models.CharField(max_length=250, blank=False, null=False,verbose_name=_('Hearing Type'))

    def __str__(self):
        return self.type

    def __unicode__(self):
        return self.type

    class Meta:
        verbose_name = _('Hearing Type')
        verbose_name_plural = _('Hearing Types')

class hearing(models.Model):
    id = models.AutoField(primary_key=True,)
    hid = models.CharField(max_length=20, blank=False, null=False, verbose_name=_('Hearing ID'))
    name = models.CharField(max_length=250, blank=False, null=False,verbose_name=_('Name'))
    hearing_type = models.ForeignKey('hearing_type', on_delete=models.CASCADE, blank=False,null=False, verbose_name=_('Hearing Type'))
    hearing_date = models.DateTimeField(verbose_name=_('Hearing Date'))
    assignee = models.ManyToManyField(User, blank=False, verbose_name=_('Assignee'))
    time_spent = models.TimeField(verbose_name=_('Time Spent'))
    comments = models.ManyToManyField(comments,verbose_name="Comments", blank=True)
    summary_by_lawyer = models.TextField(max_length=250, blank=False, null=False,verbose_name=_('Summary by lawyer'))
    attachment = models.FileField(upload_to='hearing/%Y/%m/%d/', verbose_name='Attachment', validators=[FileExtensionValidator(['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png', 'gif'])])

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = _('Hearing')
        verbose_name_plural = _('Hearings')

    def save(self, *args, **kwargs):
        if self.hid is None:
            self.hid = str('H-' + str(self.id))
        return super(event, self).save(*args, **kwargs)


class task_type(models.Model):
    id = models.AutoField(primary_key=True,)
    type = models.CharField(max_length=250, blank=False, null=False,verbose_name=_('Task Type'))

    def __str__(self):
        return self.type

    def __unicode__(self):
        return self.type

    class Meta:
        verbose_name = _('Task Type')
        verbose_name_plural = _('Task Types')


class task(models.Model):
    id = models.AutoField(primary_key=True,)
    tid = models.CharField(max_length=20, blank=False, null=False, verbose_name=_('Task ID'))
    name = models.CharField(max_length=250, blank=False, null=False,verbose_name=_('Name'))
    task_type = models.ForeignKey('task_type', on_delete=models.CASCADE, blank=False,null=False, verbose_name=_('Task Type'))
    description = RichTextField(default='', blank=False, null=False, verbose_name=_('Task Description'))
    assigned_to = models.ForeignKey(User, related_name='%(class)s_assigned_to', on_delete=models.CASCADE, null=False, blank=False,verbose_name=_('Assigned to'))
    requested_by = models.ForeignKey(User, related_name='%(class)s_requested_by', on_delete=models.CASCADE, null=False, blank=False,verbose_name=_('Requested By'))
    priority = models.ForeignKey(priorities,  on_delete=models.CASCADE, null=False, blank=False,verbose_name=_('Matter Priority'))
    due_date = models.DateField(verbose_name=_('Due date'))
    comments = models.ManyToManyField(comments,verbose_name="Comments", blank=True)
    
    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = _('Task')
        verbose_name_plural = _('Tasks')

    def save(self, *args, **kwargs):
        super(task, self).save(*args, **kwargs)
        if self.tid is None:
            self.tid = str('T-' + str(self.id))
        return super(task, self).save(*args, **kwargs)


class event_type(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type = models.CharField(max_length=250, blank=False, null=False,verbose_name=_('Event Type'))

    def __str__(self):
        return self.type

    def __unicode__(self):
        return self.type

    class Meta:
        verbose_name = _('Event Type')
        verbose_name_plural = _('Event Types')


class event(models.Model):
    id = models.AutoField(primary_key=True,)
    eid = models.CharField(max_length=20, blank=True, null=True, verbose_name=_('Event ID'),editable=True)
    event_type = models.ForeignKey('event_type', on_delete=models.CASCADE, blank=False,null=False, verbose_name=_('Event Type'))
    created_by = models.ForeignKey(User, related_name='%(class)s_created_by', on_delete=models.CASCADE, null=False, blank=False,verbose_name=_('Created By'))
    from_date = models.DateTimeField(verbose_name=_('From'),default=timezone.now)
    to_date = models.DateTimeField(verbose_name=_('To'),default=timezone.now)
    attendees = models.ManyToManyField(User, related_name='%(class)s_attendees', blank=False,verbose_name=_('Attendees'))
    comments = models.ManyToManyField(comments,verbose_name="Comments", blank=True)

    def __str__(self):
        return str(self.id)

    def __unicode__(self):
        return str(self.id)

    class Meta:
        verbose_name = _('Event')
        verbose_name_plural = _('Events')

    def save(self, *args, **kwargs):
        super(event, self).save(*args, **kwargs)
        if self.eid is None:
            self.eid = str('E-' + str(self.id))
        return super(event, self).save(*args, **kwargs)
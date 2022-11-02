from tabnanny import verbose
from django.db import models
import uuid
from django.utils.translation import gettext_lazy as _
from ckeditor.fields import RichTextField
from pytz import timezone
from accounts.models import User

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

class replies(models.Model):
    id = models.AutoField(primary_key=True,)
    reply = models.CharField(max_length=250, blank=False, null=False,verbose_name=_('Reply'))
    comment_id = models.BigIntegerField(blank=True, null=True)
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


class comments(models.Model):
    id = models.AutoField(primary_key=True,)
    comment = RichTextField( blank=False, null=False,verbose_name=_('Comment'))
    replies = models.ManyToManyField(replies, related_name='%(class)s_replies', blank=True,verbose_name=_('Reply'))
    case_id = models.BigIntegerField(blank=True, null=True)
    event_id = models.BigIntegerField(blank=True, null=True)
    task_id = models.BigIntegerField(blank=True, null=True)
    hearing_id = models.BigIntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True, editable=False)
    created_by = models.ForeignKey(
        User, related_name='%(class)s_createdby', on_delete=models.CASCADE, blank=True, null=True, editable=False)
    modified_by = models.ForeignKey(
        User, related_name='%(class)s_modifiedby', null=True, blank=True, on_delete=models.CASCADE, editable=False)


    def __str__(self):
        return self.comment

    def __unicode__(self):
        return self.comment

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
class court(models.Model):
    id = models.AutoField(primary_key=True,)
    name = models.CharField(max_length=250, blank=False, null=False,verbose_name=_('Name'))

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = _('Court')
        verbose_name_plural = _('Courts')

class contracts(models.Model):
    id = models.AutoField(primary_key=True,)
    name = models.CharField(max_length=250, blank=False, null=False,verbose_name=_('Name'))
    attachment = models.FileField(upload_to='contracts/%Y/%m/%d/',verbose_name=_('Attachment'))
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True, editable=False)
    created_by = models.ForeignKey(
        User, related_name='%(class)s_createdby', on_delete=models.CASCADE, blank=True, null=True, editable=False)
    modified_by = models.ForeignKey(
        User, related_name='%(class)s_modifiedby', null=True, blank=True, on_delete=models.CASCADE, editable=False)

class documents(models.Model):
    id = models.AutoField(primary_key=True,)
    name = models.CharField(max_length=250, blank=False, null=False,verbose_name=_('Name'))
    attachment = models.FileField(upload_to='documents/%Y/%m/%d/',verbose_name=_('Attachment'))
    case_id = models.IntegerField(blank=True,null=True, verbose_name=_('Litigation Case'))
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True, editable=False)
    created_by = models.ForeignKey(
        User, related_name='%(class)s_createdby', on_delete=models.CASCADE, blank=True, null=True, editable=False)
    modified_by = models.ForeignKey(
        User, related_name='%(class)s_modifiedby', null=True, blank=True, on_delete=models.CASCADE, editable=False)
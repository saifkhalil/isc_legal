import pghistory
from django.db import models
from django.utils.translation import gettext_lazy as _
from accounts.models import User
from core.models import comments, court, Status

@pghistory.track(pghistory.Snapshot())
class hearing(models.Model):
    id = models.AutoField(primary_key=True, )
    name = models.CharField(max_length=250, blank=True, null=True, verbose_name=_('Name'))
    case_id = models.IntegerField(blank=True, null=True, verbose_name=_('Litigation Case'))
    folder_id = models.IntegerField(blank=True, null=True, verbose_name=_('Folder'))
    hearing_date = models.DateTimeField(verbose_name=_('Hearing Date'))
    assignee = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, verbose_name=_('Assignee'))
    comments = models.ManyToManyField(comments, verbose_name="Comments", blank=True)
    court = models.ForeignKey(court, on_delete=models.CASCADE, blank=True, null=True, verbose_name=_('Court name'))
    comments_by_lawyer = models.TextField(max_length=250, blank=True, null=True, verbose_name=_('Summary by lawyer'))
    is_deleted = models.BooleanField(default=False, verbose_name=_("Is Deleted"))
    hearing_status = models.ForeignKey(Status, related_name='%(class)s_hearing_status', on_delete=models.CASCADE,
                                       null=True, blank=True, verbose_name=_('Hearing Status'))
    latest = models.BooleanField(verbose_name='Latest', default=True, null=False, blank=False)
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

@pghistory.track(pghistory.Snapshot())
class task(models.Model):
    id = models.AutoField(primary_key=True, )
    title = models.CharField(max_length=250, blank=False, null=False, verbose_name=_('title'))
    description = models.CharField(max_length=250, default='', blank=False, null=False,
                                   verbose_name=_('Task Description'))
    assignee = models.ForeignKey(User, related_name='%(class)s_assigned_to', on_delete=models.CASCADE, null=False,
                                 blank=False, verbose_name=_('Assigned to'))
    task_status = models.ForeignKey(Status, related_name='%(class)s_task_status', on_delete=models.CASCADE, null=True,
                                    blank=True, verbose_name=_('Task Status'))
    case_id = models.IntegerField(blank=True, null=True, verbose_name=_('Litigation Case'))
    folder_id = models.IntegerField(blank=True, null=True, verbose_name=_('Folder'))
    due_date = models.DateField(verbose_name=_('Due date'))
    comments = models.ManyToManyField(comments, verbose_name="Comments", blank=True)
    is_deleted = models.BooleanField(default=False, verbose_name=_("Is Deleted"))
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


from auditlog.registry import auditlog
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.urls import reverse

from accounts.models import User
from core.models import comments, court, Status, documents, priorities


class hearing(models.Model):
    id = models.AutoField(primary_key=True, )
    name = models.CharField(max_length=250, blank=True, null=True, verbose_name=_('Name'))
    case_id = models.IntegerField(blank=True, null=True, verbose_name=_('Litigation Case'))
    folder_id = models.IntegerField(blank=True, null=True, verbose_name=_('Folder'))
    hearing_date = models.DateTimeField(verbose_name=_('Hearing Date'))
    assignee = models.ManyToManyField(User, blank=True, verbose_name=_('Assignee'), related_name='hearing_assignees')
    comments = models.ManyToManyField(comments, verbose_name="Comments", blank=True)
    court = models.ForeignKey(court, on_delete=models.CASCADE, blank=True, null=True, verbose_name=_('Court name'))
    comments_by_lawyer = models.TextField(max_length=250, blank=True, null=True, verbose_name=_('Summary by lawyer'))
    is_deleted = models.BooleanField(default=False, verbose_name=_("Is Deleted"))
    priority = models.ForeignKey(priorities, on_delete=models.CASCADE, null=True, blank=True,
                                 verbose_name=_('Hearing Priority'))
    hearing_status = models.ForeignKey(Status, related_name='%(class)s_hearing_status', on_delete=models.CASCADE,
                                       null=True, blank=True, verbose_name=_('Hearing Status'))
    documents = models.ManyToManyField(
        blank=True, related_name='hearings', to=documents,
        verbose_name=_('Documents'))
    remind_me = models.BooleanField(default=False,verbose_name='Remind me', null=True, blank=True)
    remind_date = models.DateTimeField(verbose_name=_('Remind Date'), null=True, blank=True)
    latest = models.BooleanField(verbose_name='Latest', default=True, null=False, blank=False)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True, editable=False)
    created_by = models.ForeignKey(
        User, related_name='hearings_createdby', on_delete=models.CASCADE, blank=True, null=True, editable=False)
    modified_by = models.ForeignKey(
        User, related_name='%(class)s_modifiedby', null=True, blank=True, on_delete=models.CASCADE, editable=False)

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = _('Hearing')
        verbose_name_plural = _('Hearings')

    @property
    def get_html_url(self):
        url = reverse('hearing_view', args=(self.id,))
        return url

task_categories = (
    ("Public", _("Public")),
    ("Private", _("Private")),
)


class task(models.Model):
    id = models.AutoField(primary_key=True, )
    title = models.CharField(max_length=250, blank=False, null=False, verbose_name=_('title'))
    description = models.CharField(max_length=250, default='', blank=False, null=False,
                                   verbose_name=_('Task Description'))
    task_category = models.CharField(max_length=500, choices=task_categories, default='Public', blank=False, null=False,
                                     verbose_name=_('Task Category'))
    assignee = models.ManyToManyField(User, related_name='task_assignees', blank=False, verbose_name=_('Assigned to'))
    task_status = models.ForeignKey(Status, related_name='%(class)s_task_status', on_delete=models.CASCADE, null=True,
                                    blank=True, verbose_name=_('Task Status'))
    case_id = models.IntegerField(blank=True, null=True, verbose_name=_('Litigation Case'))
    folder_id = models.IntegerField(blank=True, null=True, verbose_name=_('Folder'))
    due_date = models.DateField(verbose_name=_('Due date'))
    assign_date = models.DateField(verbose_name=_('Assign date'), blank=True, null=True)
    documents = models.ManyToManyField(blank=True, related_name='tasks', to=documents, verbose_name=_('Documents'))
    comments = models.ManyToManyField(comments, verbose_name="Comments", blank=True)
    is_deleted = models.BooleanField(default=False, verbose_name=_("Is Deleted"))
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True, editable=False)
    created_by = models.ForeignKey(
        User, related_name='tasks_createdby', on_delete=models.CASCADE, blank=True, null=True)
    modified_by = models.ForeignKey(
        User, related_name='%(class)s_modifiedby', null=True, blank=True, on_delete=models.CASCADE)

    def __str__(self):
        return self.title

    def __unicode__(self):
        return self.title

    class Meta:
        verbose_name = _('Task')
        verbose_name_plural = _('Tasks')

    @property
    def get_html_url(self):
        url = reverse('task_view', args=(self.id,))
        return url

auditlog.register(
    task,
    m2m_fields={
        "documents",
        "comments",
        "assignee"

    },
    exclude_fields=['modified_by', 'created_by', 'modified_at']
)
auditlog.register(
    hearing,
    m2m_fields={
        "documents",
        "comments",
        "assignee"
    },
    exclude_fields=['modified_by', 'created_by', 'remind_me']
)
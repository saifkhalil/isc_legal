import pghistory
from auditlog.registry import auditlog
from django.db import models
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from accounts.models import User, Employees
from activities.models import task, hearing
from core.models import priorities, comments, documents, court, Status, Path
from core.threading import send_html_mail

class case_type(models.Model):
    id = models.AutoField(primary_key=True, )
    type = models.CharField(max_length=250, blank=False, null=False, verbose_name=_('Name'))
    stage = models.ManyToManyField('stages', related_name='case_types', blank=True)
    is_deleted = models.BooleanField(default=False, verbose_name=_("Is Deleted"))

    def __str__(self):
        return self.type

    def __unicode__(self):
        return self.type

    class Meta:
        verbose_name = _('Case Type')
        verbose_name_plural = _('Case Types')


class characteristic(models.Model):
    id = models.AutoField(primary_key=True, )
    name = models.CharField(max_length=250, blank=False, null=False, verbose_name=_('Name'))


    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = _('Case characteristic')
        verbose_name_plural = _('Case characteristics')


class stages(models.Model):
    id = models.AutoField(primary_key=True, )
    name = models.CharField(max_length=250, blank=False, null=False, verbose_name=_('Name'))
    is_deleted = models.BooleanField(default=False, verbose_name=_("Is Deleted"))

    # status = models.ForeignKey(
    #     Status, related_name='statuses', on_delete=models.CASCADE, blank=True, null=True,)

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = _('Stage')
        verbose_name_plural = _('Stage')


class client_position(models.Model):
    id = models.AutoField(primary_key=True, )
    name = models.CharField(max_length=250, blank=False, null=False, verbose_name=_('Name'))

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = _('Client Position')
        verbose_name_plural = _('Client Positions')


class ImportantDevelopment(models.Model):
    id = models.AutoField(primary_key=True, )
    title = models.CharField(max_length=1000, blank=False, null=False, verbose_name=_('Title'))
    is_deleted = models.BooleanField(default=False, verbose_name=_("Is Deleted"))
    case_id = models.BigIntegerField(blank=True, null=True)
    folder_id = models.BigIntegerField(blank=True, null=True)
    admin_id = models.BigIntegerField(blank=True, null=True)
    notation_id = models.BigIntegerField(blank=True, null=True)
    contract_id = models.BigIntegerField(blank=True, null=True)
    # event_id = models.BigIntegerField(blank=True, null=True)
    # task_id = models.BigIntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True, blank=True, null=True, editable=False)
    created_by = models.ForeignKey(
        User, related_name='%(class)s_createdby', on_delete=models.CASCADE, blank=True, null=True, editable=False)
    modified_by = models.ForeignKey(
        User, related_name='%(class)s_modifiedby', null=True, blank=True, on_delete=models.CASCADE, editable=False)

    def __str__(self):
        return self.title

    def __unicode__(self):
        return self.title

    class Meta:
        verbose_name = _('Important Development')
        verbose_name_plural = _('Important Developments')
        ordering = ["created_at"]


class opponent_position(models.Model):
    id = models.AutoField(primary_key=True, )
    position = models.CharField(max_length=250, blank=False, null=False, verbose_name=_('Position'))

    def __str__(self):
        return self.position

    def __unicode__(self):
        return self.position

    class Meta:
        verbose_name = _('Opponent Position')
        verbose_name_plural = _('Opponent Positions')


case_categories = (
    ("Public", _("Public")),
    ("Private", _("Private")),
)


case_close_status = (
    ("رابحة", _("رابحة")),
    ("خاسرة", _("خاسرة")),
)


class LitigationCases(models.Model):
    """
    This Model Handle the Litigation cases objects

    """
    id = models.AutoField(primary_key=True, help_text='Litigation cases Id')
    name = models.CharField(
        max_length=500,
        blank=False,
        null=False,
        verbose_name=_('Title'),
        help_text="Name of Litigation case"
    )
    description = models.CharField(max_length=500, blank=True, null=True, verbose_name=_('Subject'))
    case_category = models.CharField(max_length=500, choices=case_categories, default='Public', blank=False, null=False,
                                     verbose_name=_('Case Category'))
    judge = models.CharField(max_length=500, blank=True, null=True, verbose_name=_('Judge Name'))
    detective = models.CharField(max_length=500, blank=True, null=True, verbose_name=_('Detective'))
    case_type = models.ForeignKey('case_type', on_delete=models.CASCADE, blank=True, null=True,
                                  verbose_name=_('Case type'))
    characteristic = models.ForeignKey('characteristic', on_delete=models.CASCADE, blank=True, null=True,
                                  verbose_name=_('Case characteristic'))
    court = models.ForeignKey(court, on_delete=models.CASCADE, blank=True, null=True, verbose_name=_('Court name'))
    documents = models.ManyToManyField(documents, blank=True, verbose_name=_('Documents'))

    paths = models.ManyToManyField(Path, blank=True, verbose_name=_('Paths'))
    client_position = models.ForeignKey('client_position', on_delete=models.CASCADE, blank=True, null=True,
                                        verbose_name=_('Client Position'))
    opponent_position = models.ForeignKey('opponent_position', on_delete=models.CASCADE, blank=True, null=True,
                                          verbose_name=_('Opponent Position'))
    assignee = models.ForeignKey(User, related_name='%(class)s_assignee', on_delete=models.CASCADE, null=True,
                                 blank=True, verbose_name=_('Assignee'))
    shared_with = models.ManyToManyField(User, related_name='%(class)s_shared_with', blank=True,
                                         verbose_name=_('Shared With'))
    internal_ref_number = models.CharField(max_length=50, blank=True, null=True, verbose_name=_('Internal Ref Number'))
    priority = models.ForeignKey(priorities, on_delete=models.CASCADE, null=True, blank=True,
                                 verbose_name=_('Matter Priority'))
    Stage = models.ForeignKey('stages', on_delete=models.CASCADE, null=True, blank=True, verbose_name=_('Stage'))
    case_status = models.ForeignKey(Status, related_name='%(class)s_case_status', on_delete=models.CASCADE, null=True,
                                    blank=True, verbose_name=_('Case Status'))
    case_close_status = models.CharField(max_length=10, choices=case_close_status, default='', blank=True, null=True,
                                     verbose_name=_('Case Close Status'))
    case_close_comment = models.CharField(max_length=500, blank=True,
                                         null=True,
                                         verbose_name=_('Case Close Comment'))

    hearing = models.ManyToManyField(hearing, blank=True, verbose_name=_('Hearing'), related_name='cases')
    tasks = models.ManyToManyField(task, related_name='cases', blank=True, verbose_name=_('Task'), )
    ImportantDevelopment = models.ManyToManyField(ImportantDevelopment, related_name='%(class)s_ImportantDevelopment',
                                                  blank=True, verbose_name=_('Important Development'))
    comments = models.ManyToManyField(comments, verbose_name="Comments", blank=True)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False, verbose_name=_("Is Deleted"))
    created_at = models.DateTimeField(editable=False)
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
        verbose_name = _('Litigation Case')
        verbose_name_plural = _('Litigation Cases')
        indexes = [models.Index(
            fields=['id', 'name', 'Stage', 'case_type', 'case_category', 'assignee', 'court', 'description']), ]

    @property
    def get_html_url(self):
        url = reverse('cases:case_edit', args=(self.id,))
        return f'<a class="btn qi-primary-outline btn-sm" href="{url}" data-bs-toggle="tooltip" data-bs-placement="top" data-bs-html="true" title="<em>Tooltip</em> <u>with</u> <b>HTML</b>"> {self.name} </a>'



@receiver(post_save, sender=LitigationCases)
def LitigationCases_send_email(sender, instance, created, *args, **kwargs):
    # request = current_request()
    current_case = instance
    case = LitigationCases.objects.get(id=current_case.id)
    if created:
        if case.assignee and case.assignee.email_notification:
            message = 'text version of HTML message'
            email_subject = _('رقم الدعوى ') + str(case.id)
            email_body = render_to_string('cases/emailnew.html', {
                'user': case.assignee,
                'case': case,
                'msgtype': _('You have been assigned with you below case details')
            })
            send_html_mail(email_subject, email_body, [case.assignee.email])
        if case.shared_with.exists():
            for shuser in case.shared_with.all():
                if shuser.email_notification:
                    message = 'text version of HTML message'
                    email_subject = _('New Case #') + str(case.id)
                    email_body = render_to_string('cases/emailnew.html', {
                        'user': shuser,
                        'case': case,
                        'msgtype': _('You have been shared with you below case details')
                    })
                    send_html_mail(email_subject, email_body, [case.assignee.email])


@receiver(m2m_changed, sender=LitigationCases.shared_with.through)
def LitigationCases_sharedwith_send_email(sender, instance, action, reverse, pk_set, *args, **kwargs):
    # request = current_request()
    current_case = instance
    case = LitigationCases.objects.get(id=current_case.id)
    if action == 'post_add':
        for shuser in pk_set:
            cuser = User.objects.get(id=shuser)
            if cuser.email_notification:
                message = 'text version of HTML message'
                email_subject = _('New Case #') + str(case.id)
                email_body = render_to_string('cases/emailnew.html', {
                    'user': cuser,
                    'case': case,
                    'msgtype': _('You have been shared with you below case details')
                })
                send_html_mail(email_subject, email_body, [cuser.email])


class Folder(models.Model):
    record_types = (
        ("Folder", _("Folder")),
        ("Administrative_investigations", _("Administrative investigations")),
        ("Notation", _("Notation")),
    )
    id = models.AutoField(primary_key=True, )
    record_type = models.CharField(max_length=100, choices=record_types, default='Folder', blank=False, null=False,
                                   verbose_name=_('Record Type'))
    name = models.CharField(max_length=500, blank=False, null=False, verbose_name=_('Title'))
    description = models.CharField(max_length=500, blank=True, null=True, verbose_name=_('Subject'))
    folder_category = models.CharField(max_length=500, choices=case_categories, default='Public', blank=False,
                                       null=False, verbose_name=_('Folder Category'))
    folder_type = models.ForeignKey('case_type', on_delete=models.CASCADE, blank=True, null=True,
                                    verbose_name=_('Folder type'))
    court = models.ForeignKey(court, on_delete=models.CASCADE, blank=True, null=True, verbose_name=_('Court name'))
    documents = models.ManyToManyField(documents, blank=True, verbose_name=_('Documents'))
    paths = models.ManyToManyField(Path, blank=True, verbose_name=_('Paths'))
    assignee = models.ForeignKey(User, related_name='%(class)s_assignee', on_delete=models.CASCADE, null=True,
                                 blank=True, verbose_name=_('Assignee'))
    shared_with = models.ManyToManyField(User, related_name='%(class)s_shared_with', blank=True,
                                         verbose_name=_('Shared With'))
    internal_ref_number = models.CharField(max_length=50, blank=True, null=True, verbose_name=_('Internal Ref Number'))
    priority = models.ForeignKey(priorities, on_delete=models.CASCADE, null=True, blank=True,
                                 verbose_name=_('Folder Priority'))
    ImportantDevelopment = models.ManyToManyField(ImportantDevelopment, related_name='%(class)s_ImportantDevelopment',
                                                  blank=True, verbose_name=_('Important Development'))
    hearing = models.ManyToManyField(hearing, blank=True, verbose_name=_('Hearing'))
    tasks = models.ManyToManyField(task, related_name='%(class)s_task', blank=True, verbose_name=_('Task'))
    comments = models.ManyToManyField(comments, verbose_name="Comments", blank=True)
    folder_status = models.ForeignKey(Status, related_name='%(class)s_folder_status', on_delete=models.CASCADE,
                                      null=True, blank=True, verbose_name=_('Folder Status'))
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(default=timezone.now)
    is_deleted = models.BooleanField(default=False, verbose_name=_("Is Deleted"))
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
        verbose_name = _('Folder')
        verbose_name_plural = _('Folders')
        indexes = [
            models.Index(fields=['id', 'name', 'folder_type', 'folder_category', 'assignee', 'court', 'description']), ]

    @property
    def get_html_url(self):
        url = reverse('folders:folder_edit', args=(self.id,))
        return f'<a class="btn qi-primary-outline btn-sm" href="{url}" data-bs-toggle="tooltip" data-bs-placement="top" data-bs-html="true" title="<em>Tooltip</em> <u>with</u> <b>HTML</b>"> {self.name} </a>'


#
# @receiver(post_save, sender=LitigationCases)
# def LitigationCases_send_email(sender, instance, created, *args, **kwargs):
#     current_case = instance
#     case = LitigationCases.objects.get(id=current_case.id)
#     if created:
#         if case.assignee.email_notification:
#             message = 'text version of HTML message'
#             email_subject = _('رقم الدعوى ') + str(case.id)
#             email_body = render_to_string('cases/emailnew.html', {
#                 'user': case.assignee,
#                 'case': case,
#                 'msgtype': _('You have been assigned with you below case details')
#             })
#             send_html_mail(email_subject, email_body, [case.assignee.email])
#         print(instance.shared_with)
#         if case.shared_with.exists():
#             for shuser in case.shared_with.all():
#                 print(shuser)
#                 if shuser.email_notification:
#                     message = 'text version of HTML message'
#                     email_subject = _('New Case #') + str(case.id)
#                     email_body = render_to_string('cases/emailnew.html', {
#                         'user': shuser,
#                         'case': case,
#                         'msgtype': _('You have been shared with you below case details')
#                     })
#                     send_html_mail(email_subject, email_body, [case.assignee.email])
#
#
# @receiver(m2m_changed, sender=LitigationCases.shared_with.through)
# def LitigationCases_sharedwith_send_email(instance, action, pk_set, *args, **kwargs):
#     current_case = instance
#     case = LitigationCases.objects.get(id=current_case.id)
#     if action == 'post_add':
#         for shuser in pk_set:
#             cuser = User.objects.get(id=shuser)
#             if cuser.email_notification:
#                 message = 'text version of HTML message'
#                 email_subject = _('New Case #') + str(case.id)
#                 email_body = render_to_string('cases/emailnew.html', {
#                     'user': cuser,
#                     'case': case,
#                     'msgtype': _('You have been shared with you below case details')
#                 })
#                 send_html_mail(email_subject, email_body, [cuser.email])


class AdministrativeInvestigation(models.Model):
    id = models.AutoField(primary_key=True, )
    subject = models.CharField(max_length=500, blank=True, null=True, verbose_name=_('Subject'))
    admin_order_number = models.CharField(max_length=500, blank=True, null=True,
                                          verbose_name=_('Administrative order number'))
    paths = models.ManyToManyField(Path, blank=True, verbose_name=_('Paths'))
    chairman = models.ForeignKey(Employees, related_name='%(class)s_chairman', on_delete=models.CASCADE, null=True,
                                 blank=True, verbose_name=_('Chairman of the Committee'))
    members = models.ManyToManyField(Employees, related_name='%(class)s_members', blank=True,
                                     verbose_name=_('Committee members'))
    assignee = models.ForeignKey(User, related_name='%(class)s_assignee', on_delete=models.CASCADE, null=True,
                                 blank=True, verbose_name=_('Assignee'))
    shared_with = models.ManyToManyField(User, related_name='%(class)s_shared_with', blank=True,
                                         verbose_name=_('Shared With'))
    priority = models.ForeignKey(priorities, on_delete=models.CASCADE, null=True, blank=True,
                                 verbose_name=_('Priority'))
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    ImportantDevelopment = models.ManyToManyField('ImportantDevelopment', related_name='%(class)s_ImportantDevelopment',
                                                  blank=True, verbose_name=_('Important Development'))
    is_deleted = models.BooleanField(default=False, verbose_name=_("Is Deleted"))
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True, editable=False)
    created_by = models.ForeignKey(
        User, related_name='%(class)s_createdby', on_delete=models.CASCADE, blank=True, null=True, editable=False)
    modified_by = models.ForeignKey(
        User, related_name='%(class)s_modifiedby', null=True, blank=True, on_delete=models.CASCADE, editable=False)

    def __str__(self):
        return self.subject

    def __unicode__(self):
        return self.subject

    class Meta:
        verbose_name = _('Administrative Investigation')
        verbose_name_plural = _('Administrate IveInvestigations')
        indexes = [
            models.Index(fields=['id', 'subject', 'admin_order_number']),
        ]


class Notation(models.Model):
    id = models.AutoField(primary_key=True, )
    subject = models.CharField(max_length=500, blank=True, null=True, verbose_name=_('Subject'))
    description = models.CharField(max_length=2000, blank=True, null=True, verbose_name=_('Description'))
    reference_number = models.CharField(max_length=500, blank=True, null=True,
                                        verbose_name=_('Reference Number'))
    reference_date = models.DateField(null=True, blank=True)
    notation_date = models.DateField(null=True, blank=True)
    paths = models.ManyToManyField(Path, blank=True, verbose_name=_('Paths'))
    requester = models.CharField(max_length=500, blank=True, null=True, verbose_name=_('Requester'))
    court = models.ForeignKey(court, on_delete=models.CASCADE, blank=True, null=True, verbose_name=_('Court name'))
    judge = models.CharField(max_length=500, blank=True, null=True, verbose_name=_('Judge Name'))
    detective = models.CharField(max_length=500, blank=True, null=True, verbose_name=_('Detective'))
    authorized_number = models.CharField(max_length=500, blank=True, null=True, verbose_name=_('Authorized number'))
    ImportantDevelopment = models.ManyToManyField('ImportantDevelopment', related_name='%(class)s_ImportantDevelopment',
                                                  blank=True, verbose_name=_('Important Development'))
    comments = models.ManyToManyField(comments, verbose_name="Comments", blank=True)
    assignee = models.ForeignKey(User, related_name='%(class)s_assignee', on_delete=models.CASCADE, null=True,
                                 blank=True, verbose_name=_('Assignee'))
    shared_with = models.ManyToManyField(User, related_name='%(class)s_shared_with', blank=True,
                                         verbose_name=_('Shared With'))
    priority = models.ForeignKey(priorities, on_delete=models.CASCADE, null=True, blank=True,
                                 verbose_name=_('Priority'))
    start_time = models.DateField(null=True, blank=True)
    end_time = models.DateField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False, verbose_name=_("Is Deleted"))
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True, editable=False)
    created_by = models.ForeignKey(
        User, related_name='%(class)s_createdby', on_delete=models.CASCADE, blank=True, null=True, editable=False)
    modified_by = models.ForeignKey(
        User, related_name='%(class)s_modifiedby', null=True, blank=True, on_delete=models.CASCADE, editable=False)

    def __str__(self):
        return self.subject

    def __unicode__(self):
        return self.subject

    class Meta:
        verbose_name = _('Notation')
        verbose_name_plural = _('Notations')
        indexes = [
            models.Index(fields=['id', 'subject', 'description']),
        ]


auditlog.register(
    LitigationCases,
    m2m_fields={
        "paths", "documents", "shared_with", "hearing", "tasks", "ImportantDevelopment", "comments"
    },
    exclude_fields=['modified_by', 'created_by']
)
auditlog.register(
    Notation,
    m2m_fields={
        'paths', 'ImportantDevelopment', 'comments', 'shared_with'
    }
)
auditlog.register(
    AdministrativeInvestigation,
    m2m_fields={
        'paths', 'ImportantDevelopment', 'members', 'shared_with'
    },
    exclude_fields=['modified_by', 'created_by']
)
auditlog.register(
    Folder,
    m2m_fields={
        "paths", "documents", "shared_with", "hearing", "tasks", "ImportantDevelopment", "comments"
    },
    exclude_fields=['modified_by', 'created_by']
)



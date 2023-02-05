from email.headerregistry import Address
from email.policy import default
from http import client
from pyexpat import model
from sre_constants import CHCODES
from tabnanny import verbose
from turtle import position
from django.db import models
import uuid
from django.utils.translation import gettext_lazy as _
from accounts.models import User
from django.contrib.auth.models import Group
from activities.models import task, hearing
from core.models import priorities,comments,documents,court,Status,Path
from django_countries.fields import CountryField
from phonenumber_field.modelfields import PhoneNumberField
from django.urls import reverse
from django.utils import timezone
from django.core.mail import EmailMessage, send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.db.models.signals import pre_save,post_save,m2m_changed 
from django.db.models import Count
from django.dispatch import receiver
from core.current_user import current_request
from core.threading import send_html_mail
import pghistory


@pghistory.track(pghistory.Snapshot())
class case_type(models.Model):
    id = models.AutoField(primary_key=True,)
    type = models.CharField(max_length=250, blank=False, null=False,verbose_name=_('Name'))
    
    def __str__(self):
        return self.type

    def __unicode__(self):
        return self.type

    class Meta:
        verbose_name = _('Case Type')
        verbose_name_plural = _('Case Types')


@pghistory.track(pghistory.Snapshot())
class stages(models.Model):
    id = models.AutoField(primary_key=True,)
    name = models.CharField(max_length=250, blank=False, null=False,verbose_name=_('Name'))

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = _('Stage')
        verbose_name_plural = _('Stage')

@pghistory.track(pghistory.Snapshot())
class client_position(models.Model):
    id = models.AutoField(primary_key=True,)
    name = models.CharField(max_length=250, blank=False, null=False,verbose_name=_('Name'))

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = _('Client Position')
        verbose_name_plural = _('Client Positions')

@pghistory.track(pghistory.Snapshot())
class ImportantDevelopment(models.Model):
    id = models.AutoField(primary_key=True,)
    title = models.CharField(max_length=250, blank=False, null=False,verbose_name=_('Title'))
    is_deleted = models.BooleanField(default=False,verbose_name=_("Is Deleted"))
    case_id = models.BigIntegerField(blank=True, null=True)
    # event_id = models.BigIntegerField(blank=True, null=True)
    # task_id = models.BigIntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True,blank=True, null=True, editable=False)
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


# class client_type(models.Model):
#     id = models.AutoField(primary_key=True,)
#     type = models.CharField(max_length=250, blank=False, null=False,verbose_name=_('Client type'))

#     def __str__(self):
#         return self.type

#     def __unicode__(self):
#         return self.type

#     class Meta:
#         verbose_name = _('Client Type')
#         verbose_name_plural = _('Client Types')
@pghistory.track(pghistory.Snapshot())
class opponent_position(models.Model):
    id = models.AutoField(primary_key=True,)
    position = models.CharField(max_length=250, blank=False, null=False,verbose_name=_('Position'))

    def __str__(self):
        return self.position

    def __unicode__(self):
        return self.position

    class Meta:
        verbose_name = _('Opponent Position')
        verbose_name_plural = _('Opponent Positions')



# class companies_sub_category(models.Model):
#     id = models.AutoField(primary_key=True,)
#     sub_category = models.CharField(max_length=250, blank=False, null=False,verbose_name=_('Sub-category'))

#     def __str__(self):
#         return self.sub_category

#     def __unicode__(self):
#         return self.sub_category

#     class Meta:
#         verbose_name = _('Company sub-category')
#         verbose_name_plural = _('Company sub-categories')

# class companies_group(models.Model):
#     id = models.AutoField(primary_key=True,)
#     group = models.CharField(max_length=250, blank=False, null=False,verbose_name=_('Group'))

#     def __str__(self):
#         return self.group

#     def __unicode__(self):
#         return self.group

#     class Meta:
#         verbose_name = _('Company Group')
#         verbose_name_plural = _('Company Groups')

# class company_legal_type(models.Model):
#     id = models.AutoField(primary_key=True,)
#     legal_type = models.CharField(max_length=250, blank=False, null=False,verbose_name=_('Legal type'))

#     def __str__(self):
#         return self.legal_type

#     def __unicode__(self):
#         return self.legal_type

#     class Meta:
#         verbose_name = _('Company legal type')
#         verbose_name_plural = _('Company legal types')


# class company(models.Model):
#     id = models.AutoField(primary_key=True,)
#     full_name = models.CharField(max_length=250, blank=False, null=False,verbose_name=_('Full Name'))
#     name = models.CharField(max_length=250, blank=False, null=False,verbose_name=_('Name'))
#     foreign_name = models.CharField(max_length=250, blank=False, null=False,verbose_name=_('Foreign Name'))
#     category = models.ForeignKey('companies_category', on_delete=models.CASCADE, blank=False,null=False, verbose_name=_('Category'))
#     sub_category = models.ForeignKey('companies_sub_category', on_delete=models.CASCADE, blank=False,null=False, verbose_name=_('Sub-category'))
#     company_legal_type = models.ForeignKey('company_legal_type', on_delete=models.CASCADE, blank=False,null=False, verbose_name=_('Company Legal Type'))
#     company_group = models.ForeignKey('companies_group', on_delete=models.CASCADE, blank=False,null=False, verbose_name=_('Company Group'))
#     # client_type = models.ForeignKey('client_type', on_delete=models.CASCADE, blank=False,null=False, verbose_name=_('Client type'))
#     reference = models.CharField(max_length=100, blank=False, null=False,verbose_name=_('Reference'))

#     def __str__(self):
#         return self.name

#     def __unicode__(self):
#         return self.name

#     class Meta:
#         verbose_name = _('Company')
#         verbose_name_plural = _('Companies')

    # def save(self, *args, **kwargs):
    #     if self.client_type is None:
    #         self.client_type = case_status.objects.first().id
    #     return super(Companies, self).save(*args, **kwargs)    


# class companies_address(models.Model):
#     id = models.AutoField(primary_key=True,)
#     company = models.ForeignKey(company,blank=False, null=False, on_delete=models.CASCADE,verbose_name=_('Company'))
#     address = models.CharField(max_length=250, blank=False, null=False,verbose_name=_('Address'))
#     state = models.CharField(max_length=250, blank=True, null=True,verbose_name=_('State'))
#     zip = models.IntegerField( blank=True, null=True,verbose_name=_('Zip'))
#     street_name = models.CharField(max_length=250, blank=True, null=True,verbose_name=_('Street Name'))
#     building_number = models.CharField(max_length=250, blank=True, null=True,verbose_name=_('Building Number'))
#     district = models.CharField(max_length=250,blank=True, null=True,verbose_name=_('District/Neighborhood'))
#     mobile = PhoneNumberField(blank=True, null=True,verbose_name=_('Mobile'))
#     fax = models.CharField(max_length=250, blank=True, null=True,verbose_name=_('Fax'))
#     city = models.CharField(max_length=250, blank=True, null=True,verbose_name=_('City'))
#     website = models.URLField(blank=True, null=True, max_length=200, verbose_name=_('Website'))
#     additional_street_name = models.CharField(max_length=250, blank=True, null=True,verbose_name=_('Additional Street Name'))
#     address_additional_number = models.CharField(max_length=250, blank=True, null=True,verbose_name=_('Address Additional Number'))
#     phone = PhoneNumberField( blank=True, null=True, verbose_name=_('Phone'))
#     email = models.EmailField(verbose_name=_('Email'))
#     country = CountryField(blank=True, null=True, verbose_name=_('Country'),default='IQ')
#     def __str__(self):
#         return self.address

#     def __unicode__(self):
#         return self.address

#     class Meta:
#         verbose_name = _('Company Address')
#         verbose_name_plural = _('Company Address')

# class persons(models.Model):
#     id = models.AutoField(primary_key=True,)
#     name = models.CharField(max_length=250, blank=False, null=False,verbose_name=_('Name'))
#     # client_type = models.ForeignKey('client_type', on_delete=models.CASCADE, blank=False,null=False, verbose_name=_('Client type'))

#     def __str__(self):
#         return self.name

#     def __unicode__(self):
#         return self.name

#     class Meta:
#         verbose_name = _('Person')
#         verbose_name_plural = _('Persons')


case_categories = (
    ("Public", _("Public")),
    ("Private", _("Private")),
)
  
@pghistory.track(pghistory.Snapshot())
class LitigationCases(models.Model):
    id = models.AutoField(primary_key=True,)
    # cid = models.CharField(max_length=20, blank=True, null=True, verbose_name=_('Case ID'),editable=False)
    name = models.CharField(max_length=500, blank=False, null=False, verbose_name=_('Title'))
    description   = models.CharField(max_length=500, blank=True, null=True, verbose_name=_('Subject'))
    case_category = models.CharField(max_length=500,choices=case_categories,default='Public', blank=False, null=False, verbose_name=_('Case Category'))
    judge = models.CharField(max_length=500, blank=True, null=True, verbose_name=_('Judge Name'))
    detective = models.CharField(max_length=500, blank=True, null=True, verbose_name=_('Detective'))
    case_type = models.ForeignKey('case_type', on_delete=models.CASCADE, blank=True,null=True, verbose_name=_('Case type'))
    court = models.ForeignKey(court, on_delete=models.CASCADE, blank=True,null=True, verbose_name=_('Court name'))
    documents = models.ManyToManyField(documents, blank=True, verbose_name=_('Documents'))

    paths = models.ManyToManyField(Path,blank=True, verbose_name=_('Paths'))
    # arrival_date = models.DateTimeField(verbose_name=_('Entry Date'))
    # client_type = models.ForeignKey('client_type', on_delete=models.CASCADE, blank=False,null=False, verbose_name=_('Client type'))
    # company = models.ForeignKey('company', on_delete=models.CASCADE, blank=True,null=True, verbose_name=_('Company'))
    # person = models.ForeignKey('persons',related_name='%(class)s_person', on_delete=models.CASCADE, blank=True,null=True, verbose_name=_('Person'))
    client_position = models.ForeignKey('client_position', on_delete=models.CASCADE, blank=True,null=True, verbose_name=_('Client Position'))
    # opponent = models.ForeignKey('persons',related_name='%(class)s_opponent', on_delete=models.CASCADE, blank=True,null=True, verbose_name=_('Opponent'))
    opponent_position = models.ForeignKey('opponent_position', on_delete=models.CASCADE, blank=True,null=True, verbose_name=_('Opponent Position'))
    # assigned_team = models.ForeignKey(Group, on_delete=models.CASCADE, blank=True,null=True, verbose_name=_('Assigned Team'))
    assignee = models.ForeignKey(User, related_name='%(class)s_assignee', on_delete=models.CASCADE, null=True, blank=True,verbose_name=_('Assignee'))
    shared_with = models.ManyToManyField(User, related_name='%(class)s_shared_with', blank=True,verbose_name=_('Shared With'))
    # filed_on = models.DateField(verbose_name=_('Filed on'), null=True, blank=True)
    # due_date = models.DateField(verbose_name=_('Due date'), null=True, blank=True)
    internal_ref_number = models.CharField(max_length=50, blank=True,null=True, verbose_name=_('Internal Ref Number'))    
    priority = models.ForeignKey(priorities,  on_delete=models.CASCADE, null=True, blank=True,verbose_name=_('Matter Priority'))
    Stage = models.ForeignKey('stages',  on_delete=models.CASCADE, null=True, blank=True,verbose_name=_('Stage'))
    # requested_by = models.ForeignKey(User, related_name='%(class)s_requested_by', on_delete=models.CASCADE, null=True, blank=True,verbose_name=_('Requested By'))
    case_status = models.ForeignKey(Status, related_name='%(class)s_case_status', on_delete=models.CASCADE, null=True, blank=True,verbose_name=_('Case Status'))
    hearing = models.ManyToManyField(hearing, blank=True, verbose_name=_('Hearing'))
    tasks = models.ManyToManyField(task, related_name='%(class)s_task', blank=True,verbose_name=_('Task'))
    ImportantDevelopment = models.ManyToManyField(ImportantDevelopment, related_name='%(class)s_ImportantDevelopment', blank=True,verbose_name=_('Important Development'))
    # event = models.ManyToManyField(event, related_name='%(class)s_event', blank=True,verbose_name=_('Event'))
    comments = models.ManyToManyField(comments,verbose_name="Comments", blank=True)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False,verbose_name=_("Is Deleted"))
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
        verbose_name = _('Litigation Case')
        verbose_name_plural = _('Litigation Cases')
        indexes = [ models.Index(fields=['id','name','Stage','case_type','case_category','assignee','court','description']),]
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
        if case.assignee.email_notification:
            message = 'text version of HTML message'
            email_subject = _('رقم الدعوى ') + str(case.id)
            email_body = render_to_string('cases/emailnew.html', {
            'user': case.assignee,
            'case':case,
            'msgtype':_('You have been assigned with you below case details')
            })
            send_html_mail(email_subject, email_body,  [case.assignee.email])
        print(instance.shared_with)
        if case.shared_with.exists():
            for shuser in case.shared_with.all():
                print(shuser)
                if shuser.email_notification:
                    message = 'text version of HTML message'
                    email_subject = _('New Case #') + str(case.id)
                    email_body = render_to_string('cases/emailnew.html', {
                        'user': shuser,
                        'case':case,
                        'msgtype':_('You have been shared with you below case details')
                        })
                    send_html_mail(email_subject, email_body,  [case.assignee.email])

@receiver(m2m_changed, sender=LitigationCases.shared_with.through)
def LitigationCases_sharedwith_send_email(sender, instance, action,reverse,pk_set, *args, **kwargs):
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
                    'case':case,
                    'msgtype':_('You have been shared with you below case details')
                    })
                send_html_mail(email_subject, email_body,  [cuser.email])


@pghistory.track(pghistory.Snapshot())
class Folder(models.Model):
    id = models.AutoField(primary_key=True,)
    # cid = models.CharField(max_length=20, blank=True, null=True, verbose_name=_('Folder ID'),editable=False)
    name = models.CharField(max_length=500, blank=False, null=False, verbose_name=_('Title'))
    description   = models.CharField(max_length=500, blank=True, null=True, verbose_name=_('Subject'))
    folder_category = models.CharField(max_length=500,choices=case_categories,default='Public', blank=False, null=False, verbose_name=_('Folder Category'))
    judge = models.CharField(max_length=500, blank=True, null=True, verbose_name=_('Judge Name'))
    detective = models.CharField(max_length=500, blank=True, null=True, verbose_name=_('Detective'))
    folder_type = models.ForeignKey('case_type', on_delete=models.CASCADE, blank=True,null=True, verbose_name=_('Folder type'))
    court = models.ForeignKey(court, on_delete=models.CASCADE, blank=True,null=True, verbose_name=_('Court name'))
    documents = models.ManyToManyField(documents, blank=True, verbose_name=_('Documents'))
    paths = models.ManyToManyField(Path,blank=True, verbose_name=_('Paths'))
    # arrival_date = models.DateTimeField(verbose_name=_('Entry Date'))
    # client_type = models.ForeignKey('client_type', on_delete=models.CASCADE, blank=False,null=False, verbose_name=_('Client type'))
    # company = models.ForeignKey('company', on_delete=models.CASCADE, blank=True,null=True, verbose_name=_('Company'))
    # person = models.ForeignKey('persons',related_name='%(class)s_person', on_delete=models.CASCADE, blank=True,null=True, verbose_name=_('Person'))
    client_position = models.ForeignKey('client_position', on_delete=models.CASCADE, blank=True,null=True, verbose_name=_('Client Position'))
    # opponent = models.ForeignKey('persons',related_name='%(class)s_opponent', on_delete=models.CASCADE, blank=True,null=True, verbose_name=_('Opponent'))
    opponent_position = models.ForeignKey('opponent_position', on_delete=models.CASCADE, blank=True,null=True, verbose_name=_('Opponent Position'))
    # assigned_team = models.ForeignKey(Group, on_delete=models.CASCADE, blank=True,null=True, verbose_name=_('Assigned Team'))
    assignee = models.ForeignKey(User, related_name='%(class)s_assignee', on_delete=models.CASCADE, null=True, blank=True,verbose_name=_('Assignee'))
    shared_with = models.ManyToManyField(User, related_name='%(class)s_shared_with', blank=True,verbose_name=_('Shared With'))
    # filed_on = models.DateField(verbose_name=_('Filed on'), null=True, blank=True)
    # due_date = models.DateField(verbose_name=_('Due date'), null=True, blank=True)
    internal_ref_number = models.CharField(max_length=50, blank=True,null=True, verbose_name=_('Internal Ref Number'))    
    priority = models.ForeignKey(priorities,  on_delete=models.CASCADE, null=True, blank=True,verbose_name=_('Matter Priority'))
    Stage = models.ForeignKey('stages',  on_delete=models.CASCADE, null=True, blank=True,verbose_name=_('Stage'))
    ImportantDevelopment = models.ManyToManyField(ImportantDevelopment, related_name='%(class)s_ImportantDevelopment', blank=True,verbose_name=_('Important Development'))
    # requested_by = models.ForeignKey(User, related_name='%(class)s_requested_by', on_delete=models.CASCADE, null=True, blank=True,verbose_name=_('Requested By'))
    # case_status = models.ForeignKey('case_status', related_name='%(class)s_case_status', on_delete=models.CASCADE, null=False, blank=False,verbose_name=_('Case Status'),default=case_status.get_default)
    hearing = models.ManyToManyField(hearing, blank=True, verbose_name=_('Hearing'))
    tasks = models.ManyToManyField(task, related_name='%(class)s_task', blank=True,verbose_name=_('Task'))
    # event = models.ManyToManyField(event, related_name='%(class)s_event', blank=True,verbose_name=_('Event'))
    comments = models.ManyToManyField(comments,verbose_name="Comments", blank=True)
    folder_status = models.ForeignKey(Status, related_name='%(class)s_folder_status', on_delete=models.CASCADE, null=True, blank=True,verbose_name=_('Folder Status'))
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(default=timezone.now)
    is_deleted = models.BooleanField(default=False,verbose_name=_("Is Deleted"))
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
        indexes = [ models.Index(fields=['id','name','Stage','folder_type','folder_category','assignee','court','description']),]
    @property
    def get_html_url(self):
        url = reverse('folders:folder_edit', args=(self.id,))
        return f'<a class="btn qi-primary-outline btn-sm" href="{url}" data-bs-toggle="tooltip" data-bs-placement="top" data-bs-html="true" title="<em>Tooltip</em> <u>with</u> <b>HTML</b>"> {self.name} </a>'


@receiver(post_save, sender=LitigationCases)
def LitigationCases_send_email(sender, instance, created, *args, **kwargs):
    # request = current_request()
    current_case = instance
    case = LitigationCases.objects.get(id=current_case.id)
    if created:
        if case.assignee.email_notification:
            message = 'text version of HTML message'
            email_subject = _('رقم الدعوى ') + str(case.id)
            email_body = render_to_string('cases/emailnew.html', {
            'user': case.assignee,
            'case':case,
            'msgtype':_('You have been assigned with you below case details')
            })
            send_html_mail(email_subject, email_body,  [case.assignee.email])
        print(instance.shared_with)
        if case.shared_with.exists():
            for shuser in case.shared_with.all():
                print(shuser)
                if shuser.email_notification:
                    message = 'text version of HTML message'
                    email_subject = _('New Case #') + str(case.id)
                    email_body = render_to_string('cases/emailnew.html', {
                        'user': shuser,
                        'case':case,
                        'msgtype':_('You have been shared with you below case details')
                        })
                    send_html_mail(email_subject, email_body,  [case.assignee.email])

@receiver(m2m_changed, sender=LitigationCases.shared_with.through)
def LitigationCases_sharedwith_send_email(sender, instance, action,reverse,pk_set, *args, **kwargs):
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
                    'case':case,
                    'msgtype':_('You have been shared with you below case details')
                    })
                send_html_mail(email_subject, email_body,  [cuser.email])



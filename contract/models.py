import pghistory
from django.db import models
from django.utils.translation import gettext_lazy as _
from core.models import priorities, comments, Path
from accounts.models import User
from cases.models import ImportantDevelopment
from django.urls import reverse
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
from auditlog.registry import auditlog


class Contract(models.Model):
    id = models.AutoField(primary_key=True, help_text='Contract Id')
    name = models.CharField(
        max_length=500,
        blank=False,
        null=False,
        verbose_name=_('Title'),
        help_text="Name of Contract"
    )
    description = models.CharField(max_length=500, blank=True, null=True, verbose_name=_('Subject'))
    type = models.ForeignKey('Type', on_delete=models.CASCADE, blank=True, null=True, verbose_name=_('type'))
    company = models.CharField(max_length=500, blank=True, null=True, verbose_name=_('Company Name'))
    out_side_iraq = models.BooleanField(default=False, verbose_name=_("Out Side Iraq"))
    total_amount = models.PositiveBigIntegerField(default=False, blank=False, null=False, verbose_name=_("Total amount"))
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    first_party = models.CharField(max_length=500, blank=True, null=True, verbose_name=_('First Party'))
    second_party = models.CharField(max_length=500, blank=True, null=True, verbose_name=_('Second Party'))
    third_party = models.CharField(max_length=500, blank=True, null=True, verbose_name=_('Third Party'))
    auto_renewal = models.BooleanField(default=False, verbose_name=_("Auto Renewal"))
    penal_clause = models.CharField(max_length=500, blank=True, null=True, verbose_name=_('Penal clause'))
    paths = models.ManyToManyField(Path, blank=True, verbose_name=_('Paths'))
    assignee = models.ForeignKey(User, related_name='%(class)s_assignee', on_delete=models.CASCADE, null=True, blank=True, verbose_name=_('Assignee'))
    shared_with = models.ManyToManyField(User, related_name='%(class)s_shared_with', blank=True, verbose_name=_('Shared With'))
    ImportantDevelopment = models.ManyToManyField(ImportantDevelopment, related_name='%(class)s_ImportantDevelopment', blank=True, verbose_name=_('Important Development'))
    comments = models.ManyToManyField(comments, verbose_name="Comments", blank=True)
    is_deleted = models.BooleanField(default=False, verbose_name=_("Is Deleted"))
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True, editable=False)
    created_by = models.ForeignKey(User, related_name='%(class)s_createdby', on_delete=models.CASCADE, blank=True, null=True, editable=False)
    modified_by = models.ForeignKey(User, related_name='%(class)s_modifiedby', null=True, blank=True, on_delete=models.CASCADE, editable=False)

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = _('Contract')
        verbose_name_plural = _('Contracts')
        indexes = [models.Index(
            fields=['id', 'name', 'type']), ]

    def get_total_amount(self):
        Payment.objects.filter()

    @property
    def get_html_url(self):
        url = reverse('cases:contract_edit', args=(self.id,))
        return f'<a class="btn qi-primary-outline btn-sm" href="{url}" data-bs-toggle="tooltip" data-bs-placement="top" data-bs-html="true" title="<em>Tooltip</em> <u>with</u> <b>HTML</b>"> {self.name} </a>'



class Payment(models.Model):
    id = models.AutoField(primary_key=True)
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='payments', verbose_name=_('Contract'))
    amount = models.PositiveBigIntegerField(blank=False, null=False, verbose_name=_('Amount'))
    date = models.DateTimeField(blank=False, null=False)
    duration = models.ForeignKey('Duration', related_name='%(class)s_duration', on_delete=models.CASCADE, blank=False, null=False)
    is_deleted = models.BooleanField(default=False, verbose_name=_("Is Deleted"))
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True, editable=False)
    created_by = models.ForeignKey(User, related_name='%(class)s_createdby', on_delete=models.CASCADE, blank=True, null=True, editable=False)
    modified_by = models.ForeignKey(User, related_name='%(class)s_modifiedby', null=True, blank=True, on_delete=models.CASCADE, editable=False)

    def __str__(self):
        return str(self.amount)

    def __unicode__(self):
        return str(self.amount)

    class Meta:
        verbose_name = _('Payment')
        verbose_name_plural = _('Payments')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        reminder_days = self.duration.no_of_days - self.duration.reminder_days
        reminder_date = self.date + timedelta(days=reminder_days)
        Reminder.objects.update_or_create(payment=self, defaults={'reminder_date': reminder_date, 'created_by': self.created_by})



class Duration(models.Model):
    id = models.AutoField(primary_key=True, )
    type = models.CharField(max_length=250, blank=False,
                            null=False, verbose_name=_('Type'))
    no_of_days = models.PositiveIntegerField(blank=False, null=False, verbose_name=_("No of days"))
    reminder_days = models.PositiveIntegerField(blank=False, null=False, verbose_name=_("Reminder days"))
    is_recurring = models.BooleanField(default=False, verbose_name=_("Is recurring"))
    is_deleted = models.BooleanField(default=False, verbose_name=_("Is Deleted"))
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True, editable=False)
    created_by = models.ForeignKey(
        User, related_name='%(class)s_createdby', on_delete=models.CASCADE, blank=True, null=True, editable=False)
    modified_by = models.ForeignKey(
        User, related_name='%(class)s_modifiedby', null=True, blank=True, on_delete=models.CASCADE, editable=False)

    def __str__(self):
        return self.type

    def __unicode__(self):
        return self.type

    class Meta:
        verbose_name = _('Duration')
        verbose_name_plural = _('Durations')


class Type(models.Model):
    id = models.AutoField(primary_key=True, )
    name = models.CharField(max_length=200, blank=False, null=False, verbose_name=_('Name'))
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
        verbose_name = _('Type')
        verbose_name_plural = _('Types')


class Reminder(models.Model):
    id = models.AutoField(primary_key=True)
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name='reminder')
    reminder_date = models.DateTimeField(null=False, blank=False, verbose_name=_('Reminder Date'))
    is_sent = models.BooleanField(default=False, verbose_name=_('Is Sent'))
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    created_by = models.ForeignKey(User, related_name='reminders_created_by', on_delete=models.CASCADE, null=True, blank=True, editable=False)
    modified_by = models.ForeignKey(
        User, related_name='%(class)s_modifiedby', null=True, blank=True, on_delete=models.CASCADE, editable=False)
    modified_at = models.DateTimeField(auto_now=True, editable=False)

    def __str__(self):
        return f"Reminder for {self.payment} on {self.reminder_date}"

    class Meta:
        verbose_name = _('Reminder')
        verbose_name_plural = _('Reminders')

# @receiver(post_save, sender=Payment)
# def create_payment_reminder(sender, instance, created, **kwargs):
#     if created:
#         reminder_days = instance.duration.no_of_days - instance.duration.reminder_days
#         reminder_date = instance.date + timedelta(days=reminder_days)
#         Reminder.objects.create(payment=instance, reminder_date=reminder_date, created_by=instance.created_by)


auditlog.register(
    Contract,
    m2m_fields={
        "paths", "shared_with", "ImportantDevelopment", "comments"
    },
    exclude_fields=['modified_by', 'created_by']
)

auditlog.register(
    Payment,
    exclude_fields=['modified_by', 'created_by']
)

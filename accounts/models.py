import os.path
from io import BytesIO

from PIL import Image
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.files.base import ContentFile
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import strip_tags
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField
from rest_framework.authtoken.models import Token

from core.threading import send_html_mail
from .auth import generate_password


class UserManager(BaseUserManager):
    def create_user(self, email, username, password=None):
        if not email:
            raise ValueError(_('Users must have an email address'))
        if not username:
            raise ValueError(_('Users must have a username'))
        user = self.model(
            email=self.normalize_email(email),
            username=username,
        )
        if password is None:
            password = generate_password()
        user.set_password(password)
        user.save(using=self._db)
        email_subject = _('حساب جديد')
        email_body = render_to_string('cases/newuser.html', {
                'username': username,
                'password':password,
                'email':email,
                'msgtype': _('تم انشاء الحساب الخاص بك على النظام القانوني')
            })
        send_html_mail(email_subject, email_body, [user.email])
        return user

    def create_superuser(self, email, username, password):
        user = self.create_user(
            email=self.normalize_email(email),
            password=password,
            username=username,

        )
        user.is_verified = True
        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        email_subject = _('حساب جديد')
        email_body = render_to_string('cases/newuser.html', {
                'username': username,
                'password':password,
                'email':email,
                'msgtype': _('تم انشاء الحساب الخاص بك على النظام القانوني')
            })
        send_html_mail(email_subject, email_body, [user.email])
        return user


class Department(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=250, blank=False, null=False,verbose_name=_('Name'))
    Description = models.CharField(max_length=250, blank=False, null=False,verbose_name=_('Description'))

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = _('Department')
        verbose_name_plural = _('Departments')

class User(AbstractBaseUser, PermissionsMixin):
    LANGUAGE_CHOICES = [
        ('en', _('English')),
        ('ar', _('Arabic')),
    ]

    id = models.AutoField(primary_key=True,)
    phone = PhoneNumberField()
    first_name = models.CharField(verbose_name=_("first name"), max_length=30)
    last_name = models.CharField(verbose_name=_("last name"), max_length=30)
    email = models.EmailField(verbose_name=_("email"), max_length=60, unique=True)
    photo = models.ImageField(verbose_name=_("Photo"),
                              upload_to='photos', default='photos/default.jpg', blank=True, null=True)
    thumbnail = models.ImageField(verbose_name=_("Thumbnail image"),
                                  upload_to='thumbnail', editable=False, blank=True, null=True)
    username = models.CharField(max_length=30, unique=True,verbose_name=_('Username'))
    Manager = models.ForeignKey('User', on_delete=models.CASCADE, blank=True, null=True,verbose_name=_('Manager'))
    language = models.CharField(
        max_length=5, choices=LANGUAGE_CHOICES, default='ar', verbose_name=_('Language')
    )
    date_joined = models.DateTimeField(verbose_name=_('last login'), default=timezone.now)
    last_login = models.DateTimeField(verbose_name=_('last login'), default=timezone.now)
    is_admin = models.BooleanField(default=False,verbose_name=_('Is admin'))
    is_manager = models.BooleanField(default=False,verbose_name=_('Is Manager'))
    is_cases_public_manager = models.BooleanField(default=False,verbose_name=_('Is Cases Public Manager'))
    is_cases_private_manager = models.BooleanField(default=False,verbose_name=_('Is Cases Private Manager'))
    is_tasks_public_manager = models.BooleanField(default=False,verbose_name=_('Is Tasks Public Manager'))
    is_tasks_private_manager = models.BooleanField(default=False,verbose_name=_('Is Tasks Private Manager'))
    is_contract_manager = models.BooleanField(default=False,verbose_name=_('Is Contract Manager'))
    is_sub_manager = models.BooleanField(default=False,verbose_name=_('Is Sub Manager'))
    is_active = models.BooleanField(default=True,verbose_name=_('Is active'))
    is_staff = models.BooleanField(default=False,verbose_name=_('Is staff'))
    is_superuser = models.BooleanField(default=False,verbose_name=_('Is superuser'))
    is_verified = models.BooleanField(default=False,verbose_name=_('Is verified'))
    is_blocked = models.BooleanField(default=False,verbose_name=_('Is blocked'))
    enable_transision = models.BooleanField(default=True, verbose_name=_('Enable transision'))
    email_notification = models.BooleanField(default=True,verbose_name=_('Email Notification'))
    i_agree = models.BooleanField(
        verbose_name=_("Please confirm that you read and agree to our terms & conditions"), default=False, blank=False, null=False)
    created_at = models.DateTimeField(auto_now_add=True,editable=False,verbose_name=_('Created at'))
    modified_at = models.DateTimeField(auto_now=True,editable=False,verbose_name=_('Modified at'))
    created_by = models.ForeignKey(
        'User', related_name='%(class)s_createdby', on_delete=models.CASCADE, blank=True, null=True,editable=False,verbose_name=_('Created by'))
    modified_by = models.ForeignKey(
        'User', related_name='%(class)s_modifiedby', null=True, blank=True, on_delete=models.CASCADE,editable=False,verbose_name=_('Modified by'))

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    objects = UserManager()

    def save(self, *args, **kwargs):
        if not self.make_thumbnail():
            raise Exception(
                _('Could not create thumbnail - is the file type valid?'))
        
        super(User, self).save(*args, **kwargs)

    def make_thumbnail(self):
        image = Image.open(self.photo)
        image.thumbnail((100, 100), Image.Resampling.LANCZOS)

        thumb_name, thumb_extension = os.path.splitext(self.photo.name)
        thumb_extension = thumb_extension.lower()

        thumb_filename = thumb_name + '_thumb' + thumb_extension

        if thumb_extension in ['.jpg', '.jpeg']:
            FTYPE = 'JPEG'
        elif thumb_extension == '.gif':
            FTYPE = 'GIF'
        elif thumb_extension == '.png':
            FTYPE = 'PNG'
        else:
            return False    # Unrecognized file type

    # Save thumbnail to in-memory file as StringIO
        temp_thumb = BytesIO()
        image.save(temp_thumb, FTYPE)
        temp_thumb.seek(0)

    # set save=False, otherwise it will run in an infinite loop
        self.thumbnail.save(thumb_filename, ContentFile(
            temp_thumb.read()), save=False)
        temp_thumb.close()

        return True

    def __str__(self):
        return str(self.username)

    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    # For checking permissions. to keep it simple all admin have ALL permissons

    # Does this user have permission to view this app? (ALWAYS YES FOR SIMPLICITY)

    def has_module_perms(self, app_label):
        return True

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        password = generate_password()
        instance.set_password(password)
        instance.save()
        email_subject = _('Legal Application UAT user')
        email_body = render_to_string('cases/newuser.html', {
                'username': instance.username,
                'password':password,
                'email':instance.email,
                'msgtype': _('تم انشاء الحساب الخاص بك على النظام القانوني')
            })
        plain_message = strip_tags(email_body)

        send_html_mail(email_subject, email_body, [instance.email])
        # send_mail(email_subject, plain_message, settings.EMAIL_HOST_USER, [instance.email], html_message=email_body)
        Token.objects.create(user=instance)


class Employees(models.Model):
    id = models.AutoField(primary_key=True, )
    full_name = models.CharField(verbose_name=_("full name"), max_length=100)
    email = models.EmailField(verbose_name=_("email"), max_length=60, unique=True)
    full_info = models.JSONField("Employee Full Info", null=True, blank=True)
    def __str__(self):
        return self.full_name

    def __unicode__(self):
        return self.full_name

    class Meta:
        verbose_name = _('Employee')
        verbose_name_plural = _('Employees')
        indexes = [
            models.Index(fields=['full_name']),
        ]



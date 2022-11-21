from tabnanny import verbose
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from phonenumber_field.modelfields import PhoneNumberField
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token
import os.path
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile
import uuid
from django.utils.translation import gettext_lazy as _
import pghistory


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
        user.set_password(password)
        user.save(using=self._db)
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

@pghistory.track(pghistory.Snapshot())
class User(AbstractBaseUser, PermissionsMixin):
    id = models.AutoField(primary_key=True,)    
    phone = PhoneNumberField()
    firstname = models.CharField(verbose_name=_("first name"), max_length=30)
    lastname = models.CharField(verbose_name=_("last name"), max_length=30)
    email = models.EmailField(verbose_name=_("email"), max_length=60, unique=True)
    photo = models.ImageField(verbose_name=_("Photo"),
                              upload_to='photos', default='photos/default.jpg', blank=True, null=True)
    thumbnail = models.ImageField(verbose_name=_("Thumbnail image"),
                                  upload_to='thumbnail', editable=False, blank=True, null=True)
    username = models.CharField(max_length=30, unique=True,verbose_name=_('Username'))
    Manager = models.ForeignKey('User', on_delete=models.CASCADE, blank=True, null=True,verbose_name=_('Manager'))
    date_joined = models.DateTimeField(verbose_name=_('date joined'), auto_now_add=True)
    last_login = models.DateTimeField(verbose_name=_('last login'), auto_now=True)
    is_admin = models.BooleanField(default=False,verbose_name=_('Is admin'))
    is_manager = models.BooleanField(default=False,verbose_name=_('Is Manager'))
    is_active = models.BooleanField(default=True,verbose_name=_('Is active'))
    is_staff = models.BooleanField(default=False,verbose_name=_('Is staff'))
    is_superuser = models.BooleanField(default=False,verbose_name=_('Is superuser'))
    is_verified = models.BooleanField(default=False,verbose_name=_('Is verified'))
    is_blocked = models.BooleanField(default=False,verbose_name=_('Is blocked'))
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
        image.thumbnail((100, 100), Image.ANTIALIAS)

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
        Token.objects.create(user=instance)

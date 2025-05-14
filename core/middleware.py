import os.path
import threading

from auditlog.context import set_actor
from auditlog.middleware import AuditlogMiddleware as _AuditlogMiddleware
from django.utils import timezone
from django.utils.functional import SimpleLazyObject

_thread_local = threading.local()
from django.apps import apps
from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from django.utils.deprecation import MiddlewareMixin
from core.models import Notification
from django.shortcuts import redirect
from django.utils.translation import get_language
from django.urls import translate_url
from urllib import parse

class LanguageMiddleware(MiddlewareMixin):

    def process_request(self, request):
        if request.user.is_authenticated:
            user_language = request.user.language
            cur_language = get_language()
            path = request.get_full_path()
            fist_segment = parse.urlparse(path).path.split('/')[1]
            if cur_language != user_language and fist_segment not in ['', 'media','static','lang','load-more-notifications']:
                url = translate_url(path,user_language)
                return redirect(url)


class NotificationMiddleware(MiddlewareMixin):
    """Middleware to add unread notifications to request context"""

    def process_request(self, request):
        if request.user.is_authenticated:  # Only fetch for logged-in users
            all_notifications = Notification.objects.filter(user=request.user, is_deleted=False).order_by("-action_at")
            request.notifications = all_notifications[:10]  # Get latest 10 unread notifications
            request.not_read_notifications_count = len(all_notifications.filter(is_read=False))
            request.not_deleted_notifications_count = len(all_notifications.filter(is_deleted=False))
        else:
            request.notifications = []  # Empty for non-authenticated users
            request.not_read_notifications_count = 0
            request.not_deleted_notifications_count = 0

class AuditlogMiddleware(_AuditlogMiddleware):
    def __call__(self, request):
        remote_addr = self._get_remote_addr(request)
        user = SimpleLazyObject(lambda: getattr(request, "user", None))
        context = set_actor(actor=user, remote_addr=remote_addr)
        with context:
            return self.get_response(request)

_thread_local = threading.local()

class CurrentUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    def __call__(self, request):
        _thread_local.user = request.user
        response = self.get_response(request)
        return response

def get_current_user():
    return getattr(_thread_local, 'user', None)

@receiver(m2m_changed)
def update_m2m_modified_fields(sender, instance, action, model, pk_set, **kwargs):
    user = get_current_user()

    if user and user.is_authenticated:
        if action in ('post_add', 'post_remove'):
            if hasattr(instance, 'modified_by') and hasattr(instance, 'modified_at'):
                for obj in instance.related_models.through.objects.filter(your_model=instance, related_model__in=pk_set):
                    obj.modified_by = user
                    obj.modified_at = timezone.now()
                    obj.save()

class AutoUpdateFieldsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        user = get_current_user()
        if user and user.is_authenticated:
            for model in apps.get_models():
                if hasattr(model, 'modified_by') and hasattr(model, 'modified_at'):
                    for obj in model.objects.filter(modified_by=None):
                        obj.modified_by = user
                        obj.modified_at = timezone.now()
                        obj.save()

        return response
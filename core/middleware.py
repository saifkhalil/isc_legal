from auditlog.context import set_actor
from auditlog.middleware import AuditlogMiddleware as _AuditlogMiddleware
from django.utils.functional import SimpleLazyObject
import threading
from django.utils import timezone
_thread_local = threading.local()
from django.apps import apps
from django.db.models.signals import m2m_changed
from django.dispatch import receiver


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
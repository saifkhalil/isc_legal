from accounts.models import Employees
from django.db import models
from haystack import signals
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from auditlog.models import LogEntry
from django.utils.timezone import now
from django.contrib.contenttypes.models import ContentType


# def get_client_ip(request):
#     x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
#     if x_forwarded_for:
#         ip = x_forwarded_for.split(',')[0]
#     else:
#         ip = request.META.get('REMOTE_ADDR')
#     return ip


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    # client_ip = get_client_ip(request)
    LogEntry.objects.create(
        actor=user,
        content_type=ContentType.objects.get_for_model(user),
        object_id=user.id,
        action=LogEntry.Action.ACCESS,
        changes={"username": {
            "type": "m2m",
            "objects": [
                user.username
            ],
            "operation": "login"
        },
            # "IP address": {
            #     "type": "m2m",
            #     "objects": [
            #         client_ip
            #     ],
            #     "operation": "-"
            # },

        }
    )


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    # client_ip = get_client_ip(request)
    LogEntry.objects.create(
        actor=user,
        content_type=ContentType.objects.get_for_model(user),
        object_id=user.id,
        action=LogEntry.Action.ACCESS,
        changes={"username": {
            "type": "m2m",
            "objects": [
                user.username
            ],
            "operation": "logout"
        },
            # "IP address": {
            #     "type": "m2m",
            #     "objects": [
            #         client_ip
            #     ],
            #     "operation": "-"
            # },

        }
    )


class EmployeesSignalProcessor(signals.BaseSignalProcessor):
    def setup(self):
        # Listen only to the ``Employees`` model.
        models.signals.post_save.connect(self.handle_save, sender=Employees)
        models.signals.post_delete.connect(self.handle_delete, sender=Employees)

    def teardown(self):
        # Disconnect only for the ``Employees`` model.
        models.signals.post_save.disconnect(self.handle_save, sender=Employees)
        models.signals.post_delete.disconnect(self.handle_delete, sender=Employees)

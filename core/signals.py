# signals.py
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.core.exceptions import FieldDoesNotExist
from django.db.models.signals import m2m_changed
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin

from accounts.models import User
from .models import Notification

ALLOWED_APPS = {"activities", "cases", "contract", "core"}


def get_users_to_notify(instance, action_by):
    users_to_notify = set()
    if hasattr(instance, "assignee") and instance.assignee:
        if type(instance.assignee) == User:
            users_to_notify.add(instance.assignee)
        else:
            for user in instance.assignee.all():
                users_to_notify.add(user)
    if hasattr(instance, "shared_with_users"):
        for user in instance.shared_with_users.all():
            users_to_notify.add(user)
    manager_users = User.objects.filter(Manager=True)  # Fixed Manager field
    users_to_notify.update(manager_users)
    if action_by and action_by in users_to_notify:
        users_to_notify.remove(action_by)
    return users_to_notify


@receiver(post_save)
def create_update_notification(sender, instance, created, **kwargs):
    """
    Handles notifications for object creation and updates.
    """
    if sender == Notification:  # Prevent recursive notifications
        return

    content_type = ContentType.objects.get_for_model(sender)

    if content_type.app_label not in ALLOWED_APPS:
        return

    action = "created" if created else "updated"

    action_by = getattr(instance, "modified_by", None) or getattr(instance, "created_by", None)
    users_to_notify = get_users_to_notify(instance, action_by)
    print(f'{users_to_notify=}')
    for user in users_to_notify:
        print(f'{user=}')
        Notification.objects.create_notification(
            action=action,
            content_type=content_type,
            object_id=instance.id,
            object_name=str(instance),
            user=user,  # User receiving the notification
            action_by=action_by,  # User who triggered the change
            role="admin" if user.Manager else "user"  # Fixed Manager field
        )


@receiver(pre_delete)
def delete_notification(sender, instance, **kwargs):
    """
    Handles notifications for object deletion.
    """
    if sender == Notification:  # Prevent recursive notifications
        return

    content_type = ContentType.objects.get_for_model(sender)

    if content_type.app_label not in ALLOWED_APPS:
        return

    action_by = getattr(instance, "modified_by", None) or getattr(instance, "created_by", None)

    users_to_notify = get_users_to_notify(instance, action_by)
    for user in users_to_notify:
        Notification.objects.create_notification(
            action="deleted",
            content_type=content_type,
            object_id=instance.id,
            object_name=str(instance),
            user=user,
            action_by=action_by,
            role="admin" if user.Manager else "user"  # Fixed Manager field
        )


# Connect signals to all models
post_save.connect(create_update_notification)
pre_delete.connect(delete_notification)

@receiver(m2m_changed)
def update_child_modified_fields(sender, instance, action, model, pk_set, **kwargs):
    if action in ['post_add', 'post_remove']:
        modified_at = timezone.now()
        if action == 'post_add':
            for child_id in pk_set:
                try:
                    child = model.objects.get(pk=child_id)
                    try:
                        instance._meta.get_field('modified_by')
                        instance.modified_by = child.created_by if child._meta.model.__name__ != 'Employees' else None
                        instance.modified_at = modified_at
                        instance.save()
                    except FieldDoesNotExist:
                        pass
                except model.DoesNotExist:
                    pass

        if action == 'post_remove':
            model.objects.filter(pk__in=pk_set).update(modified_by=None, modified_at=modified_at)


class CacheClearMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        """
        Clears cache when specific API endpoints are called (e.g., POST, PUT, DELETE).
        """
        if request.method in ["POST", "PUT", "DELETE"]:
            # Extract model name from URL if applicable (Modify as per your URL structure)
            path_parts = request.path.split("/")
            model_name = path_parts[2] if len(path_parts) > 2 else None

            if model_name:
                cache.delete(f"{model_name.lower()}_all")  # Clear model cache
                cache.delete_pattern(f"{model_name.lower()}_*")  # Clear individual objects

        return response
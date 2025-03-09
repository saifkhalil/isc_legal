# signals.py
from django.core.exceptions import FieldDoesNotExist
from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from django.utils import timezone
from django.core.cache import cache
from django.utils.deprecation import MiddlewareMixin


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
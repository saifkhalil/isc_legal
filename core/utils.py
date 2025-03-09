# from django.utils.encoding import force_text
# from django.utils.hashcompat import md5_constructor
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from django.db.models import Model

# def cache_key_func(view_instance, view_method, request, args, kwargs):
#     path = request.build_absolute_uri()
#     query_params = request.query_params.dict()
#     key = ':'.join([view_instance.__class__.__name__, view_method.__name__, path, force_text(sorted(query_params.items()))])
#     return md5_constructor(key).hexdigest()

class LegalCache:
    def __init__(self, model, obj_id=None):
        """
        Initialize LegalCache with a model and optional object ID.
        :param model: The Django model class.
        :param obj_id: The ID of the specific object (optional).
        """
        if not issubclass(model, Model):
            raise ValueError("Invalid model class provided.")
        self.model = model
        self.obj_id = obj_id

    def get_object(self):
        """
        Retrieve a single object from the cache or database.
        :return: The object instance.
        """
        if not self.obj_id:
            raise ValueError("Object ID is required for get_object().")

        cache_key = f"{self.model.__name__.lower()}_{self.obj_id}"
        data = cache.get(cache_key)

        if data is None:
            data = get_object_or_404(self.model, id=self.obj_id)
            cache.set(cache_key, data, timeout=60 * 60)  # Cache for 1 hour

        return data

    def get_objects(self):
        """
        Retrieve a queryset of all non-deleted objects from the cache or database.
        :return: Queryset of objects.
        """
        cache_key = f"{self.model.__name__.lower()}_all"
        data = cache.get(cache_key)

        if data is None:
            data = self.model.objects.filter(is_deleted=False).order_by("-created_at")
            cache.set(cache_key, data, timeout=60 * 60)  # Cache for 1 hour

        return data

    def clear_object_cache(self):
        """
        Clear cache for a specific object.
        """
        if not self.obj_id:
            raise ValueError("Object ID is required for clear_object_cache().")

        cache_key = f"{self.model.__name__.lower()}_{self.obj_id}"
        cache.delete(cache_key)

    def clear_objects_cache(self):
        """
        Clear cache for all objects of the model.
        """
        cache_key = f"{self.model.__name__.lower()}_all"
        cache.delete(cache_key)

    def clear_all_caches(self):
        """
        Clears both object-specific and model-wide cache.
        """
        self.clear_objects_cache()
        if self.obj_id:
            self.clear_object_cache()
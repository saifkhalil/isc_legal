# from django.utils.encoding import force_text
# from django.utils.hashcompat import md5_constructor
from django.core.cache import cache
from django.db.models import Model
from django.shortcuts import get_object_or_404
import os
import subprocess
from pdf2image import convert_from_path
from PIL import Image
import pytesseract

import cv2
import numpy as np

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
            cache.set(cache_key, data, timeout=None)  # Cache for 1 hour

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
            cache.set(cache_key, data, timeout=None)  # Cache for 1 hour

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

def convert_office_to_pdf(input_path, output_dir):
    subprocess.run([
        'libreoffice', '--headless', '--convert-to', 'pdf',
        input_path, '--outdir', output_dir
    ])
    base = os.path.splitext(os.path.basename(input_path))[0]
    return os.path.join(output_dir, f'{base}.pdf')

def extract_images_from_pdf(pdf_path):
    return convert_from_path(pdf_path)

def preprocess_image_for_ocr(pil_image):
    # Convert PIL image to OpenCV format
    img_array = np.array(pil_image.convert('L'))  # Grayscale
    _, thresh = cv2.threshold(img_array, 150, 255, cv2.THRESH_BINARY)
    return Image.fromarray(thresh)

def extract_text_from_image(image):
    image = preprocess_image_for_ocr(image)
    return pytesseract.image_to_string(image, lang='ara+eng')


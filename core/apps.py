from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _
from django.db.models import ManyToManyField
from django.db.models.signals import m2m_changed

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = _('Core')

    def ready(self):
        import core.signals

        # Dynamically connect the signal handler to all Many-to-Many relationships
        models = self.get_models()
        for model in models:
            for field in model._meta.get_fields():
                if isinstance(field, ManyToManyField):
                    # Get the through model using the through attribute of the field's remote field
                    through_model = field.remote_field.through
                    m2m_changed.connect(
                        core.signals.update_child_modified_fields,
                        sender=through_model,
                        weak=False,
                        dispatch_uid=f'update_child_modified_{model.__name__}_{field.name}'
                    )
import logging

from django.apps import apps
from django.contrib.auth import get_user_model
from rest_framework.pagination import LimitOffsetPagination

from .class_mixins import AppsModuleLoaderMixin
from .literals import (
    EVENT_MANAGER_ORDER_AFTER
)

logger = logging.getLogger(name=__name__)

DEFAULT_ACTION_EXPORTER_FIELD_NAMES = (
    'timestamp', 'id', 'actor_content_type', 'actor_object_id', 'actor',
    'target_content_type', 'target_object_id', 'target', 'verb',
    'action_object_content_type', 'action_object_object_id', 'action_object'
)


class EventManager:
    """
    keep_attributes - List of event related object attributes that should
    not be removed after the event is committed.
    """
    EVENT_ATTRIBUTES = ('ignore', 'keep_attributes', 'type')
    EVENT_ARGUMENTS = ('actor', 'action_object', 'target')

    def __init__(self, instance, **kwargs):
        self.instance = instance
        self.instance_event_attributes = {}
        self.kwargs = kwargs

    def commit(self):
        if not self.instance_event_attributes['ignore']:
            self._commit()
        else:
            # If the event is ignored, restore the event related attributes
            # that were removed via .pop().
            for key, value in self.instance_event_attributes.items():
                if key not in ('ignore', 'type'):
                    setattr(
                        self.instance, '_event_{}'.format(key), value
                    )

    def get_event_arguments(self, argument_map):
        result = {}

        for argument in self.EVENT_ARGUMENTS:
            # Grab the static argument value from the argument map.
            # If the argument is not in the map, it is dynamic and must be
            # obtained from the instance attributes.
            value = argument_map.get(
                argument, self.instance_event_attributes[argument]
            )

            if value == 'self':
                result[argument] = self.instance
            elif isinstance(value, str):
                result[argument] = return_attrib(
                    attrib=value, obj=self.instance
                )
            else:
                result[argument] = value

        return result

    def pop_event_attributes(self):
        for attribute in self.EVENT_ATTRIBUTES:
            # If the attribute is not set or is set but is None.
            if not self.instance_event_attributes.get(attribute, None):
                full_name = '_event_{}'.format(attribute)
                value = self.instance.__dict__.pop(full_name, None)
                self.instance_event_attributes[attribute] = value

        keep_attributes = self.instance_event_attributes['keep_attributes'] or ()

        # Allow passing a runtime defined event.
        if self.instance_event_attributes['type']:
            self.kwargs['event'] = self.instance_event_attributes['type']

        for attribute in self.EVENT_ARGUMENTS:
            # If the attribute is not set or is set but is None.
            if not self.instance_event_attributes.get(attribute, None):
                full_name = '_event_{}'.format(attribute)
                if full_name in keep_attributes:
                    value = self.instance.__dict__.get(full_name, None)
                else:
                    value = self.instance.__dict__.pop(full_name, None)

                self.instance_event_attributes[attribute] = value

    def prepare(self):
        """Optional method to gather information before the actual commit."""


class EventManagerMethodAfter(EventManager):
    order = EVENT_MANAGER_ORDER_AFTER

    def _commit(self):
        self.kwargs['event'].commit(
            **self.get_event_arguments(argument_map=self.kwargs)
        )


class EventManagerSave(EventManager):
    order = EVENT_MANAGER_ORDER_AFTER

    def _commit(self):
        if self.created:
            if 'created' in self.kwargs:
                self.kwargs['created']['event'].commit(
                    **self.get_event_arguments(
                        argument_map=self.kwargs['created']
                    )
                )
        else:
            if 'edited' in self.kwargs:
                self.kwargs['edited']['event'].commit(
                    **self.get_event_arguments(
                        argument_map=self.kwargs['edited']
                    )
                )

    def prepare(self):
        self.created = not self.instance.pk


class EventTypeNamespace(AppsModuleLoaderMixin):
    _registry = {}
    _loader_module_name = 'events'

    @classmethod
    def all(cls):
        return sorted(cls._registry.values())

    @classmethod
    def get(cls, name):
        return cls._registry[name]

    def __init__(self, name, label):
        self.name = name
        self.label = label
        self.event_types = []
        self.__class__._registry[name] = self

    def __lt__(self, other):
        return self.label < other.label

    def __str__(self):
        return str(self.label)

    def add_event_type(self, name, label):
        event_type = EventType(namespace=self, name=name, label=label)
        self.event_types.append(event_type)
        return event_type

    def get_event(self, name):
        return EventType.get(
            id='{}.{}'.format(self.name, name)
        )

    def get_event_types(self):
        return EventType.sort(event_type_list=self.event_types)


class EventType:
    _registry = {}

    @staticmethod
    def sort(event_type_list):
        return sorted(
            event_type_list, key=lambda event_type: (
                event_type.namespace.label, event_type.label
            )
        )

    @classmethod
    def all(cls):
        # Return sorted permisions by namespace.name.
        return EventType.sort(
            event_type_list=cls._registry.values()
        )

    @classmethod
    def get(cls, id):
        return cls._registry[id]

    @classmethod
    def refresh(cls):
        for event_type in cls.all():
            # Invalidate cache and recreate store events while repopulating
            # cache.
            event_type.stored_event_type = None
            event_type.get_stored_event_type()

    def __init__(self, namespace, name, label):
        self.namespace = namespace
        self.name = name
        self.label = label
        self.stored_event_type = None
        self.__class__._registry[self.id] = self

    def __str__(self):
        return '{}: {}'.format(self.namespace.label, self.label)

    def commit(self, actor=None, action_object=None, target=None):
        EventSubscription = apps.get_model(
            app_label='events', model_name='EventSubscription'
        )
        Notification = apps.get_model(
            app_label='events', model_name='Notification'
        )
        ObjectEventSubscription = apps.get_model(
            app_label='events', model_name='ObjectEventSubscription'
        )
        User = get_user_model()

        if actor is None and target is None:
            # If the actor and the target are None there is no way to
            # create a new event.
            logger.warning(
                'Attempting to commit event "%s" without an actor or a '
                'target. This is not supported.', self
            )
            return

        result = action.send(
            actor or target, actor=actor, verb=self.id,
            action_object=action_object, target=target
        )[0][1]
        # The [0][1] means: get the first and only action from the list
        # and ignore the handler.

        # Create notifications for the actions created by the event committed.

        # Gather the users subscribed globally to the event.
        user_queryset = User.objects.filter(
            id__in=EventSubscription.objects.filter(
                stored_event_type__name=result.verb
            ).values('user')
        )

        # Gather the users subscribed to the target object event.
        if result.target:
            user_queryset = user_queryset | User.objects.filter(
                id__in=ObjectEventSubscription.objects.filter(
                    content_type=result.target_content_type,
                    object_id=result.target.pk,
                    stored_event_type__name=result.verb
                ).values('user')
            )

        # Gather the users subscribed to the action object event.
        if result.action_object:
            user_queryset = user_queryset | User.objects.filter(
                id__in=ObjectEventSubscription.objects.filter(
                    content_type=result.action_object_content_type,
                    object_id=result.action_object.pk,
                    stored_event_type__name=result.verb
                ).values('user')
            )

        for user in user_queryset:
            if result.action_object:
                Notification.objects.create(action=result, user=user)
                # Don't check or add any other notification for the
                # same user-event-object.
                continue

            if result.target:
                Notification.objects.create(action=result, user=user)
                # Don't check or add any other notification for the
                # same user-event-object.
                continue

        return result

    def get_stored_event_type(self):
        if not self.stored_event_type:
            StoredEventType = apps.get_model(
                app_label='events', model_name='StoredEventType'
            )

            self.stored_event_type, created = StoredEventType.objects.get_or_create(
                name=self.id
            )

        return self.stored_event_type

    @property
    def id(self):
        return '{}.{}'.format(self.namespace.name, self.name)


class ModelEventType:
    """
    Class to allow matching a model to a specific set of events.
    """
    _inheritances = {}
    _registry = {}

    @classmethod
    def get_for_class(cls, klass):
        result = cls._registry.get(
            klass, ()
        )
        return EventType.sort(event_type_list=result)

    @classmethod
    def get_for_instance(cls, instance):
        StoredEventType = apps.get_model(
            app_label='events', model_name='StoredEventType'
        )

        events = []

        class_events = cls._registry.get(type(instance))

        if class_events:
            events.extend(class_events)

        pks = [
            event.id for event in set(events)
        ]

        return EventType.sort(
            event_type_list=StoredEventType.objects.filter(name__in=pks)
        )

    @classmethod
    def get_inheritance(cls, model):
        return cls._inheritances[model]

    @classmethod
    def register(cls, model, event_types):
        cls._registry.setdefault(
            model, []
        )
        for event_type in event_types:
            cls._registry[model].append(event_type)

    @classmethod
    def register_inheritance(cls, model, related):
        cls._inheritances[model] = related


class StandardResultsSetPagination(LimitOffsetPagination):
    default_limit = 10
    limit_query_param = 'limit'
    max_limit = 100

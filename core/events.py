from django.utils.translation import gettext_lazy as _

from .classes import EventTypeNamespace

namespace = EventTypeNamespace(
    label=_('Paths'), name='paths'
)

event_path_created = namespace.add_event_type(
    label=_('Path created'), name='path_created'
)
event_path_deleted = namespace.add_event_type(
    label=_('Path deleted'), name='path_deleted'
)
event_path_edited = namespace.add_event_type(
    label=_('Path edited'), name='path_edited'
)
event_path_document_added = namespace.add_event_type(
    label=_('Document added to path'), name='add_document'
)
event_path_document_removed = namespace.add_event_type(
    label=_('Document removed from path'), name='remove_document'
)

from djangochannelsrestframework.generics import GenericAsyncAPIConsumer
from djangochannelsrestframework.mixins import ListModelMixin
from djangochannelsrestframework.observer import model_observer

from .models import Notification
from .serializers import NotificationSerializer


# class NotificationConsumer(ListModelMixin,GenericAsyncAPIConsumer):
#
#     queryset = Notification.objects.all().filter(is_deleted=False)
#     serializer_class = NotificationSerializer
#     # permission_classes = (permissions.AllowAny)
#
#
#     async def connect(self,**kwargs):
#         await self.Notification_change.subscribe()
#         await super().connect()
#
#     @model_observer(Notification)
#     async def Notification_change(self,message,observer=None, **kwargs):
#         await self.send_json(message)
#
#     @Notification_change.serializer
#     def model_serialize(self,instance,action,**kwargs):
#         return dict(data=NotificationSerializer(instance=instance).data,action=action.value)

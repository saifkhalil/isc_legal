from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.cache import cache
import json

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """Handle new WebSocket connection."""
        if self.scope["user"].is_authenticated:
            self.user = self.scope["user"]
            await self.set_user_online(self.user.id)
            await self.channel_layer.group_add("online_users", self.channel_name)
            # await self.channel_layer.group_send("online_users", {
            #     "type": "user.status",
            #     "user_id": self.user.id,
            #     "username":self.user.username,
            #     "status": "online"
            # })

            self.group_name = f"notifications_{self.scope['user'].id}"
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()
        else:
            await self.close()

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        if self.scope["user"].is_authenticated:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

            await self.set_user_offline(self.user.id)
            await self.channel_layer.group_discard("online_users", self.channel_name)

            # await self.channel_layer.group_send("online_users", {
            #     "type": "user.status",
            #     "user_id": self.user.id,
            #     "username":self.user.username,
            #     "status": "offline"
            # })

    async def send_notification(self, event):
        """Send notification to WebSocket frontend."""
        await self.send(text_data=event["message"])

    # async def user_status(self, event):
    #     await self.send(text_data=json.dumps({
    #         "type": "user.status",
    #         "user_id": event["user_id"],
    #         "username":event["username"],
    #         "status": event["status"]
    #     }))

    @database_sync_to_async
    def set_user_online(self, user_id):
        check_cache = cache.get(f"user_online_{user_id}")
        if not check_cache:
            cache.set(f"user_online_{user_id}", True,timeout=None)

    @database_sync_to_async
    def set_user_offline(self, user_id):
        cache.delete(f"user_online_{user_id}")
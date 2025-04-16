import json
from channels.generic.websocket import AsyncWebsocketConsumer

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """Handle new WebSocket connection."""
        if self.scope["user"].is_authenticated:
            self.group_name = f"notifications_{self.scope['user'].id}"
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()
        else:
            await self.close()

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        if self.scope["user"].is_authenticated:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def send_notification(self, event):
        """Send notification to WebSocket frontend."""
        await self.send(text_data=event["message"])

from channels.consumer import AsyncConsumer


class QueueConsumer(AsyncConsumer):

    async def websocket_connect(self, event):
        await self.send({"type": "websocket.accept"})

    async def websocket_receive(self, text_data):
        await self.send({
            "type": "websocket.send",
            "text": "queue_updated"
        })

    async def websocket_disconnect(self, event):
        pass
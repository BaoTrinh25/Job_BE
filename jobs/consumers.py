import json
from django.db.models import Q
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import User, Room, Message

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'
        print("self.room_name", self.room_name)
        print("self.room_group_name", self.room_group_name)
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        print("text_data_json", text_data_json)
        message = text_data_json.get('message', [])
        print("self.room_group_name", self.room_group_name)
        job_id = text_data_json.get('jobId', [])
        sender_id = text_data_json.get('sender',[])
        receiver_id = text_data_json.get('receiver',[])

        # Kiểm tra hoặc tạo ChatRoom
        room = await self.get_or_create_chatroom(sender_id, receiver_id)
        # Lưu tin nhắn vào database
        await self.save_message(room, sender_id, message)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'jobId': job_id,
                'sender': sender_id,
                'receiver': receiver_id,
            }
        )


    async def chat_message(self, event):
        message = event['message']
        job_id = event['jobId']
        sender = event['sender']
        receiver = event['receiver']

        await self.send(text_data=json.dumps({
            'message': message,
            'jobId': job_id,
            'sender': sender,
            'receiver': receiver
        }))



    @database_sync_to_async
    def get_or_create_chatroom(self, sender_id, receiver_id):
        sender = User.objects.get(id=sender_id)
        receiver = User.objects.get(id=receiver_id)

        # Tìm phòng chat không phân biệt thứ tự giữa sender và receiver
        room = Room.objects.filter(
            (Q(sender=sender) & Q(receiver=receiver)) | (Q(sender=receiver) & Q(sender=sender))
        ).first()

        # Nếu không có phòng chat, tạo mới
        if not room:
            room = Room.objects.create(sender=sender, receiver=receiver)

        return room

    @database_sync_to_async
    def save_message(self, room, sender_id, message):
        sender = User.objects.get(id=sender_id)
        Message.objects.create(room=room, sender=sender, message=message)

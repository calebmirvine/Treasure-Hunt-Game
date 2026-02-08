import json
from channels.generic.websocket import AsyncWebsocketConsumer

class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.game_id = self.scope['url_route']['kwargs']['game_id']
        self.room_group_name = f'game_{self.game_id}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json.get('message', '')
        message_type = text_data_json.get('type', 'game_message')
        
        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': message_type,
                'message': message,
                # You can add more fields here if needed, like player_id, etc.
            }
        )

    # Receive message from room group
    async def game_message(self, event):
        message = event['message']
        
        # Get player name from cookie
        cookies = self.scope.get('cookies', {})
        player_name = cookies.get('player_name')
        
        # We need to run sync DB operations to get context
        from game.views.views_gameplay import build_game_context
        from asgiref.sync import sync_to_async
        from django.template.loader import render_to_string
        
        context = await sync_to_async(build_game_context)(player_name)
        
        # Add constants since context processor doesn't run hereby default? 
        # Actually render_to_string might not use context processors unless request is passed.
        # But we can import constants if needed or pass request if we had one. 
        # Better: use a mock request or ensure constants are in context if used in template.
        # The partial uses constants like PICKED_TILE.
        # We should adding them to context manually or passing request.
        # Creating a basic WS request wrapper is complex. 
        # Let's import constants and add to context.
        from game.constants.constants import PICKED_TILE, FOUND_TREASURE, DEFAULT_TILE
        
        csrf_token = cookies.get('csrftoken')

        context.update({
            'PICKED_TILE': PICKED_TILE,
            'FOUND_TREASURE': FOUND_TREASURE,
            'DEFAULT_TILE': DEFAULT_TILE,
            'game_message': message,
            'csrf_token': csrf_token
        })

        html = await sync_to_async(render_to_string)('game/partials/board.html', context)

        # Send message to WebSocket
        # We send the HTML content to swap.
        # HTMX ws extension replaces the innerHTML of the target by default or swaps out of band.
        # Since we want to replace #game-container, and our data is #game-container, we can use OOB swap.
        
        # Inject hx-swap-oob into the top div
        html = html.replace('<div id="game-container">', '<div id="game-container" hx-swap-oob="true">', 1)

        await self.send(text_data=html)

    async def lobby_update(self, event):
        from game.models import Player
        from asgiref.sync import sync_to_async
        from django.template.loader import render_to_string
        
        players = await sync_to_async(list)(Player.objects.all())
        p1_exists = any(p.player_number == 1 for p in players)
        p2_exists = any(p.player_number == 2 for p in players)
        
        context = {
            'players': players,
            'p1_exists': p1_exists,
            'p2_exists': p2_exists
        }

        html = await sync_to_async(render_to_string)('game/partials/player_slots.html', context)
        
        # OOB swap for lobby
        html = html.replace('<div id="player-slots"', '<div id="player-slots" hx-swap-oob="true"', 1)
        
        await self.send(text_data=html)

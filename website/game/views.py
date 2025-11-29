from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import HttpResponse, HttpRequest, HttpResponseBadRequest
from django.shortcuts import render, redirect
from rest_framework import viewsets
from .serializers import PlayerSerializer, TileSerializer
from .models import Player, Tile, validate_col_range, validate_row_range
from .models import Player, Tile, validate_col_range, validate_row_range
from game.constants.constants import (
    PICKED_TILE,
    DEFAULT_TILE,
    DEFAULT_BOARD_SIZE,
    DEFAULT_TREASURE_COUNT,
    MIN_PLAYERS,
    PLAYER_1,
    PLAYER_2,
)
from game.constants.messages import ErrorMessages
import random

# Create your views here.
"""
The viewsets base class provides the implementation for CRUD operations by default. 
This code specifies the serializer_class and the queryset.
"""
class TileView(viewsets.ModelViewSet):
    serializer_class = TileSerializer
    queryset = Tile.objects.all()

class PlayerView(viewsets.ModelViewSet):
    serializer_class = PlayerSerializer
    queryset = Player.objects.all()

def index(request: HttpRequest) -> HttpResponse:
    if request.method == 'POST':
        player_number = int(request.POST.get('player_number'))
        if player_number == 1:
            name = PLAYER_1
            color = 'green'
        else:
            name = PLAYER_2
            color = 'red'
        
        Player.objects.create(name=name, player_number=player_number, color=color)
        return redirect('lobby')
    
    players = Player.objects.all()
    p1_exists = players.filter(player_number=1).exists()
    p2_exists = players.filter(player_number=2).exists()

    return render(request, 'game/index.html', {
        'players': players,
        'MIN_PLAYERS': MIN_PLAYERS,
        'p1_exists': p1_exists,
        'p2_exists': p2_exists
    })

@transaction.atomic
def reset_game(request: HttpRequest) -> HttpResponse:
    """
    Resets the game by deleting all tiles and players.
    Redirects to the lobby.
    """
    Tile.objects.all().delete()
    Player.objects.all().delete()
    return redirect('index')

@transaction.atomic
def start_game(request: HttpRequest, size: int = DEFAULT_BOARD_SIZE, treasure : int = DEFAULT_TREASURE_COUNT) -> HttpResponse:
    """
    Starts the game with existing players.
    Creates a new board and places treasure.
    """
    Tile.objects.all().delete()
    Player.objects.all().delete() 

    tiles = [Tile(row=i, col=j, value=DEFAULT_TILE) for i in range(size) for j in range(size)]
    Tile.objects.bulk_create(tiles)
    
    # players = [Player(name=PLAYER_1), Player(name=PLAYER_2)]
    # Player.objects.bulk_create(players)
    
    t_count = treasure

    directions = {'up': (-1, 0), 'down': (1, 0), 'left': (0, -1), 'right': (0, 1)}
    while t_count > 0:
        placed = False
        while not placed:
            row = random.randint(0, size - 1)
            col = random.randint(0, size - 1)
            direction = random.choice(list(directions.values()))

            temp_row, temp_col = row, col

            positions = []
            for _ in range(t_count):
                temp_row = temp_row % size
                temp_col = temp_col % size

                # locked until committed
                tile = Tile.objects.select_for_update().get(row=temp_row, col=temp_col)
                if tile.value != DEFAULT_TILE:
                    break
                positions.append((temp_row, temp_col))
                temp_row += direction[0]
                temp_col += direction[1]

            if len(positions) == t_count:
                for pos_row, pos_col in positions:

                    #locked until committed
                    tile = Tile.objects.select_for_update().get(row=pos_row, col=pos_col)
                    tile.value = str(t_count)
                    tile.save()
                placed = True
                t_count -= 1
    
    return redirect('game')


def game(request: HttpRequest) -> HttpResponse | None:
    """
    This function displays the game page.
    It first checks if the game has been created, if not it redirects to create.
    Then it gets all the players and tiles, and creates a board.
    :param request: HttpRequest
    :return: HttpResponse
    """

    #if the game hasn't been created yet, redirect to lobby to wait for players
    if not Tile.objects.exists():
        if Player.objects.count() >= MIN_PLAYERS:
            return start_game(request)
        return redirect('lobby')

    players = Player.objects.all()
    tiles = Tile.objects.all().order_by('row', 'col')
    board = []
    for row in range(DEFAULT_BOARD_SIZE):
        row_tiles = [tiles.get(row=row, col=col) for col in range(DEFAULT_BOARD_SIZE)]
        board.append(row_tiles)

    context = {
        'player_list': players,
        'board': board,
        'DEFAULT_TILE': DEFAULT_TILE,
        'PICKED_TILE': PICKED_TILE,
        'game_message': 'Pick a tile to start the game'
    }
    return render(request, 'game/game.html', context)

def pick(request: HttpRequest, name: str, row: int, col: int) -> HttpResponse:
    """
    This function handles the pick action.
    It first checks if the player exists, if not it returns a 404 error.
    Then it checks if the row and column are valid, if not it returns a 400 error.
    Then it gets the tile and checks if it is a default tile or a picked tile, if not it returns a 400 error.
    :param request: HttpRequest
    :param name: str
    :param row: int
    :param col: int
    :return: HttpResponse
    """
    message = ""
    try:
        player = Player.objects.get(name=name)
    except Player.DoesNotExist:
        message = ErrorMessages.PLAYER_404
        player = None 

    if player:
        try:
            validate_row_range(row)
        except ValidationError:
            message = ErrorMessages.ROW_OUT_OF_RANGE
        try:
            validate_col_range(col)
        except ValidationError:
            message = ErrorMessages.COL_OUT_OF_RANGE

        if not message: # Only proceed if no errors so far
            tile = Tile.objects.get(row=row, col=col)
            value = tile.value
            if value == DEFAULT_TILE or value == PICKED_TILE:
                message = f'Player {player.name} picked tile ({row}, {col}). No treasure'
            else:
                player.score += int(value)
                player.save()
                message = f'Player {player.name} found {value} points! Total: {player.score}'
                tile.value = PICKED_TILE
                tile.save()

    players = Player.objects.all()
    tiles = Tile.objects.all().order_by('row', 'col')
    board = []
    for r in range(DEFAULT_BOARD_SIZE):
        row_tiles = [tiles.get(row=r, col=c) for c in range(DEFAULT_BOARD_SIZE)]
        board.append(row_tiles)

    return render(request, 'game/game.html', {
        'player_list': players,
        'board': board,
        'PICKED_TILE': PICKED_TILE,
        'game_message': message
    })

def reload_board(request: HttpRequest) -> HttpResponse:
    players = Player.objects.all()
    tiles = Tile.objects.all().order_by('row', 'col')
    message = 'Pick a tile to start the game'
    board = []
    row_tiles = [tiles.get(row=r, col=c) for c in range(DEFAULT_BOARD_SIZE) for r in range(DEFAULT_BOARD_SIZE)]
    board.append(row_tiles)

    return render(request, 'game/game.html', {
        'player_list': players,
        'board': board,
        'PICKED_TILE': PICKED_TILE,
        'game_message': message
    })


def custom_404(request: HttpRequest, exception: Exception) -> HttpResponse:
    """
    This function handles the 404 error.It returns a custom 404 page.
    :param request: HttpRequest
    :param exception: Exception
    :return: HttpResponse
    """
    return render(request, '404.html', {'message': ErrorMessages.PAGE_404}, status=404)

from django.http import HttpResponse, HttpRequest
from django.shortcuts import render, redirect
from game.models import Player
from game.forms import PlayerForm
from game.constants.constants import MIN_PLAYERS, PLAYER_1, PLAYER_2

def index(request: HttpRequest) -> HttpResponse:
    if request.method == 'POST':
        form = PlayerForm(request.POST)
        if form.is_valid():
            player_number = int(request.POST.get('player_number'))
            name = (PLAYER_1 if player_number == 1 else PLAYER_2)
            #Security check after validation
            color = form.cleaned_data['color']

            try:
                Player.objects.create(name=name, player_number=player_number, color=color)
                
                response = redirect('game')
                #Cookie to remember player 
                response.set_cookie('player_name', name)
                return response
            except Exception:
                # If player already exists (race condition), just redirect to lobby
                # The page will reload and show the button as disabled/joined
                return redirect('lobby')
    else:
        # Check if player cookie exists
        player_name = request.COOKIES.get('player_name')
        if player_name:
            # Verify player actually exists in DB
            if Player.objects.filter(name=player_name).exists():
                return redirect('game')
        
        form = PlayerForm()
    
    players = Player.objects.all()
    p1_exists = players.filter(player_number=1).exists()
    p2_exists = players.filter(player_number=2).exists()

    return render(request, 'game/index.html', {
        'form': form,
        'players': players,
        'p1_exists': p1_exists,
        'p2_exists': p2_exists
    })

from aiogram.fsm.context import FSMContext

async def get_players(state: FSMContext) -> list[dict]:
    return await state.get_value("players", [])

async def set_players(state: FSMContext, players: list[dict]):
    data = await state.get_data()
    data["players"] = players
    await state.set_data(data)

id = 0

async def add_player(state: FSMContext, player_name: str):
    players = await get_players(state)
    global id
    id += 1
    players.append({
            "id": id,
            "name": player_name,
            "is_playing": True,
            "lhand": None,
            "rhand": None,
            "lfoot": None,
            "rfoot": None
        })
    await set_players(state, players)

async def get_player(state: FSMContext, id: int):
    players = await get_players(state)
    
    for player in players:
        if player["id"] == id:
            return player
    return None

async def set_player(state: FSMContext, id: int, values: dict):
    players = await get_players(state)
    
    for player in players:
        if player["id"] == id:
            for key, value in values.items():
                player[key] = value
    
    await set_players(state, players)

async def remove_player(state: FSMContext, id: int):
    players = await get_players(state)
    for i in range(len(players)):
        if players[i]["id"] == id:
            del players[i]
            break
    await set_players(state, players)

async def kick_player(state: FSMContext, id: int):
    await set_player(state, id, {"is_playing": False})

async def start_game(state: FSMContext, lead_id: int):
    players = await get_players(state)
    for player in players:
        player["is_playing"] = player["id"] != lead_id
        player["lhand"] = player['rhand'] = player['lfoot'] = player['rfoot'] = None
    await set_players(state, players)

async def get_winner(state: FSMContext):
    players = await get_players(state)
    for player in players:
        if player['is_playing']:
            return player
    return None

async def next_player_id(state: FSMContext, current_id: int | None = None):
    players = await get_players(state)

    for player in players:
        if player["is_playing"]:
            break
    else:
        return None

    for i in range(len(players)):
        if players[i]["id"] == current_id or current_id is None:
            break
    else:
        return None

    while True:
        i = (i + 1) % len(players)
        if players[i]['is_playing']:
            return players[i]["id"]

from random import randint

EMOJIES = '🐶🐱🐰🦊🐷'

def get_random_emoji():
    return EMOJIES[randint(0, len(EMOJIES) - 1)]

def format_name(name:str, length: int):
    emoji = get_random_emoji()
    prefix_len = (length - len(name)) // 2
    if prefix_len <= 0:
        return name
    return emoji * prefix_len + name + emoji * (length // 2 - prefix_len)

LIMBS = ["lhand", 'rhand', 'lfoot', 'rfoot']
COLORS = ['blue', 'red', 'green', 'yellow']

def gen_action():
    return LIMBS[randint(0, 3)], COLORS[randint(0, 3)]

async def count_players(state):
    count = 0
    players = await get_players(state)
    for player in players:
        if player["is_playing"]:
            count+=1
    return count
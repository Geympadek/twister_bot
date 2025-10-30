from aiogram import types
import utils
import config

get_keyboard = lambda keyboard: types.InlineKeyboardMarkup(inline_keyboard=keyboard)

START_GAME_BTN = types.InlineKeyboardButton(
        text="🎮Начать игру",
        callback_data="start_game"
    )

REGENERATE_BTN = types.InlineKeyboardButton(
        text="🔄",
        callback_data="regenerate"
    )

NEXT_BTN = types.InlineKeyboardButton(
        text="➡️", 
        callback_data="next"
    )

KICK_PLAYER_BTN = types.InlineKeyboardButton(
        text="🖕Выгнать",
        callback_data="kick_player"
    )

STOP_GAME_BTN = types.InlineKeyboardButton(
        text="👾Завершить",
        callback_data="stop_game"
    )

ADD_PLAYER_BTN = types.InlineKeyboardButton(
        text="➕Добавить игрока",
        callback_data="add_player"
    )

ACTION_KB = get_keyboard([
        [KICK_PLAYER_BTN, REGENERATE_BTN],
        [STOP_GAME_BTN, NEXT_BTN]
    ])

BACK_BTN = types.InlineKeyboardButton(text="⬅️", callback_data="list")
BACK_KB = get_keyboard([[BACK_BTN]])

def get_player_btn(player_name: str, player_id: int):
    return types.InlineKeyboardButton(
        text=player_name,
        callback_data=f"get_player:{player_id}"
    )

def player_list(players: list[dict]):
    result = []
    for player in players:
        result.append([get_player_btn(player["name"], player["id"])])
    return result

def get_player_kb(player_id: int):
    return get_keyboard([[
            BACK_BTN,
            types.InlineKeyboardButton(text="❌Выгнать", callback_data=f"remove_player:{player_id}")
        ]])
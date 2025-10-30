import loader
from loader import dp, bot

from aiogram import types
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command, StateFilter
from aiogram import F

import config
import utils

import menu

@dp.message(Command("start"))
async def on_start(msg: types.Message, state: FSMContext):
    await msg.answer(text="<b>Добро пожаловать!</b>👋")
    await msg.answer(text="Список игроков пока что пуст, начните играть, добавив игроков и нажав кнопку <code>Начать игру</code>.")
    await on_list_command(msg, state)

@dp.message(Command("list"))
async def on_list_command(msg: types.Message, state: FSMContext):
    bot_msg = await msg.answer("Список игроков:")
    await list_players(bot_msg, state)

@dp.callback_query(F.data.startswith("list"))
async def on_list_query(query: CallbackQuery, state: FSMContext):
    await list_players(query.message, state)

async def list_players(sender_msg: types.Message, state: FSMContext):
    players = await utils.get_players(state)

    if len(players) == 0:
        result_msg = await sender_msg.edit_text("✨Список игроков пока что пуст.")
        kb = menu.get_keyboard([[menu.ADD_PLAYER_BTN]])
        await result_msg.edit_reply_markup(reply_markup=kb)
        return

    kb = menu.player_list(players)

    if len(players) < config.MAX_PLAYERS:
        kb.append([menu.ADD_PLAYER_BTN])
    if len(players) >= 3:
        kb.append([menu.START_GAME_BTN])
    await sender_msg.edit_text(text=f"✨Игроков {len(players)}/{config.MAX_PLAYERS} ✨", reply_markup=menu.get_keyboard(kb))

@dp.callback_query(F.data.startswith("add_player"))
async def on_add_player(query: CallbackQuery, state: FSMContext):
    await query.message.edit_text("<b>Введите имя игрока</b>")
    await state.set_state("player_name")

@dp.callback_query(StateFilter(None), F.data.startswith("get_player"))
async def on_get_player(query: CallbackQuery, state: FSMContext):
    player_id = int(query.data.split(':', 1)[1])
    player = await utils.get_player(state, player_id)
    await query.message.edit_text(f"Игрок <b>{player['name']}</b>", reply_markup=menu.get_player_kb(player_id))

@dp.callback_query(F.data.startswith("remove_player"))
async def on_remove_player(query: CallbackQuery, state: FSMContext):
    player_id = int(query.data.split(':', 1)[1])
    await utils.remove_player(state, player_id)
    await list_players(query.message, state)

@dp.message(StateFilter("player_name"))
async def on_player_name(msg: types.Message, state: FSMContext):
    if msg.text is None:
        return
    await utils.add_player(state, msg.text)
    await on_list_command(msg, state)
    await state.set_state(None)

@dp.callback_query(F.data.startswith("start_game"))
async def on_start_game(query: CallbackQuery, state: FSMContext):
    await state.set_state("lead_select")
    await query.message.edit_text(
        text="👤<b>Выберите ведущего игрока</b>",
        reply_markup=menu.get_keyboard(menu.player_list(await utils.get_players(state)))
    )

@dp.callback_query(StateFilter("lead_select"), F.data.startswith("get_player"))
async def on_lead_selected(query: CallbackQuery, state: FSMContext):
    player_id = int(query.data.split(':', 1)[1])
    await utils.start_game(state, player_id)

    data = await state.get_data()
    data["player_id"] = await utils.next_player_id(state)
    await state.set_data(data)

    await state.set_state("game")
    await gen_next_action(state)
    await display_action(query.message, state)

async def gen_next_action(state: FSMContext):
    data = await state.get_data()
    player = await utils.get_player(state, data["player_id"])
    
    while True:
        limb, color = utils.gen_action()
        if player[limb] != color:
            break
    data["action"] = f"{limb}:{color}"
    await state.set_data(data)

async def display_action(sender_msg: Message, state: FSMContext):
    data = await state.get_data()
    player = await utils.get_player(state, data["player_id"])

    limb, color = data["action"].split(":", 1)

    action_txt = "<b>"
    if limb.startswith('r'):
        action_txt += "Правая"
    else:
        action_txt += "Левая"
    if "hand" in limb:
        action_txt += " рука ✋"
    else:
        action_txt += " нога 🦶"
    
    action_txt += "</b> на <b>"

    if color == "red":
        action_txt += "красный 🔴"
    elif color == "green":
        action_txt += "зелёный 🟢"
    elif color == "yellow":
        action_txt += "жёлтый 🟡"
    else:
        action_txt += 'синий 🔵'

    action_txt += "</b>"

    await sender_msg.edit_text(
        f"👤 <i>{player['name']}</i>\n{action_txt}",
        reply_markup=menu.ACTION_KB
        )

@dp.callback_query(StateFilter("game"), F.data.startswith("regenerate"))
async def on_regenerate(query: CallbackQuery, state: FSMContext):
    action = await state.get_value('action')
    while True:
        await gen_next_action(state)
        if action != await state.get_value('action'):
            break
    await display_action(query.message, state)

@dp.callback_query(StateFilter("game"), F.data.startswith("kick_player"))
async def on_kick_player(query: CallbackQuery, state: FSMContext):
    player_id = await state.get_value("player_id")
    await utils.kick_player(state, player_id)

    winner = await utils.get_winner(state)

    if await utils.count_players(state) < 2:
        await query.message.edit_text(
            f"🎉Игра окончена, победа <b>{winner['name']}</b>!✨"
        )
        await state.set_state(None)
        await on_list_command(query.message, state)
        return

    await on_next(query, state)

@dp.callback_query(StateFilter("game"), F.data.startswith("stop_game"))
async def on_stop_game(query: CallbackQuery, state: FSMContext):
    await state.set_state(None)
    await list_players(query.message, state)

@dp.callback_query(StateFilter("game"), F.data.startswith("next"))
async def on_next(query: CallbackQuery, state: FSMContext):
    player_id = await state.get_value("player_id")
    data = await state.get_data()
    limb, color = data["action"].split(":", 1)
    await utils.set_player(state, player_id, {limb: color})

    data["player_id"] = await utils.next_player_id(state, player_id)
    await state.set_data(data)
    await gen_next_action(state)
    await display_action(query.message, state)

async def main():
    await loader.launch()

import asyncio

if __name__ == "__main__":
    asyncio.run(main())
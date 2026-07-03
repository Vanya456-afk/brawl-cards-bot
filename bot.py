import os
import asyncio
import random
from aiogram import Bot, Dispatcher, html, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import CommandStart
from aiohttp import web
import database

TOKEN = "8978194297:AAHp1oqolPRqtCZ48KRndAGFXrd-in30OTw"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Словарь со всеми новыми эмодзи редкостей
EMOJIS = {
    "Common": "🟢", "Rare": "🔵", "Epic": "🟣", "Mythic": "🟡", "Legendary": "🟠",
    "Стартовая": "🌱", "Закаленная": "🛡️", "Тайная": "🔮", "Мифическая": "🌟",
    "Легендарная": "👑", "Эфирная": "🌌", "Божественная": "🔱", "Лимитированная": "🚨",
    "Ржавая": "🔧", "Заряженная": "⚡", "Токсичная": "☣️", "Хайповая": "🕶️",
    "Трендовая": "🔥", "🧪 Экспериментальная": "🧪", "Пустотная": "🌑", "Алмазная": "💎"
}

def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎰 Испытать удачу"), KeyboardButton(text="👤 Профиль")],
            [KeyboardButton(text="🛒 Магазин"), KeyboardButton(text="⚔️ Искать Бой")],
            [KeyboardButton(text="👥 Друзья"), KeyboardButton(text="🛡 Кланы")]
        ],
        resize_keyboard=True
    )

@dp.message(CommandStart())
async def command_start_handler(message: Message):
    await database.register_user(message.from_user.id, message.from_user.username or f"id_{message.from_user.id}")
    await message.answer(
        f"Привет, {html.bold(message.from_user.full_name)}! Твой бот полностью готов и обновлен!\n\n"
        f"Жми на кнопки внизу, чтобы проверить новые фандомы, бои, систему друзей и кланов.",
        reply_markup=get_main_keyboard()
    )

@dp.message(F.text == "👤 Профиль")
async def profile_handler(message: Message):
    profile = await database.get_user_profile(message.from_user.id)
    if profile:
        coins, power, clan = profile
        clan_text = clan if clan else "Нет клана"
        await message.answer(
            f"👤 {html.bold('Игровой Профиль:')}\n\n"
            f"🪙 Баланс: {coins} монет\n"
            f"💪 Сила аккаунта: {power}\n"
            f"🛡 Твой клан: {clan_text}\n\n"
            f"🆔 Твой ID для друзей: `{message.from_user.id}`"
        )

@dp.message(F.text == "🎰 Испытать удачу")
async def drop_card_handler(message: Message):
    card = await database.get_random_card()
    if card:
        card_id, name, fandom, rarity = card
        await database.add_to_inventory(message.from_user.id, card_id)
        
        rarity_emoji = EMOJIS.get(rarity, "🃏")
        
        await message.answer(
            f"🎉 Дроп получен!\n\n"
            f"🎬 Фэндом: {html.bold(fandom)}\n"
            f"👤 Карточка: {name}\n"
            f"{rarity_emoji} Редкость: {rarity}\n\n"
            f"💪 Твоя общая сила выросла!"
        )

@dp.message(F.text == "🛒 Магазин")
async def shop_handler(message: Message):
    items = await database.get_shop_items()
    if not items:
        return await message.answer("Магазин пуст.")
    
    text = "🏪 {html.bold('Ассортимент магазина:')}\n\n"
    keyboard = []
    for item in items:
        card_id, name, fandom, rarity, price = item
        rarity_emoji = EMOJIS.get(rarity, "🃏")
        text += f"🔹 {rarity_emoji} {name} [{fandom}] — 🪙 {price} монет\n"
        keyboard.append([InlineKeyboardButton(text=f"Купить {name} за 🪙{price}", callback_data=f"buy_{card_id}")])
        
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    await message.answer(text, reply_markup=reply_markup)

@dp.callback_query(F.data.startswith("buy_"))
async def buy_callback(callback: CallbackQuery):
    card_id = int(callback.data.split("_")[1])
    success = await database.buy_card(callback.from_user.id, card_id)
    if success:
        await callback.answer("🎉 Карточка успешно куплена!")
    else:
        await callback.answer("❌ Недостаточно монет для покупки!")

@dp.message(F.text == "⚔️ Искать Бой")
async def battle_handler(message: Message):
    user_id = message.from_user.id
    user_profile = await database.get_user_profile(user_id)
    enemy = await database.get_enemy(user_id)
    
    if not enemy or not user_profile:
        return await message.answer("🤖 Противников пока нет. Ты первый игрок в базе!")
        
    _, u_power, _ = user_profile
    enemy_id, enemy_name, enemy_power = enemy
    
    await message.answer(f"⚔️ Ищем соперника... Найдено: Игрок @{enemy_name} (Сила: {enemy_power})!")
    await asyncio.sleep(1)
    
    user_roll = u_power + random.randint(1, 25)
    enemy_roll = enemy_power + random.randint(1, 25)
    
    if user_roll >= enemy_roll:
        reward = random.randint(50, 120)
        await database.update_coins(user_id, reward)
        await message.answer(f"🏆 Ты выиграл дуэль! Твоя атака: {user_roll}, защита соперника: {enemy_roll}.\nНаграда: 🪙 +{reward} монет!")
    else:
        loss = random.randint(15, 40)
        await database.update_coins(user_id, -loss)
        await message.answer(f"💀 Поражение. Твоя атака: {user_roll}, защита соперника: {enemy_roll}.\nПотеряно: 🪙 -{loss} монет.")

@dp.message(F.text == "👥 Друзья")
async def friends_menu(message: Message):
    friends = await database.get_friends(message.from_user.id)
    text = "👥 {html.bold('Список твоих друзей:')}\n\n"
    if friends:
        for f_id, f_name in friends:
            text += f"• @{f_name} (ID: {f_id})\n"
    else:
        text += "У тебя пока нет друзей.\n"
    text += "\nЧтобы добавить друга, введи команду:\n`/add_friend ID`"
    await message.answer(text, parse_mode="Markdown")

@dp.message(F.text.startswith("/add_friend"))
async def add_friend_command(message: Message):
    try:
        friend_id = int(message.text.split(" ")[1])
        if friend_id == message.from_user.id:
            return await message.answer("Нельзя добавить самого себя! 🙃")
        success = await database.add_friend(message.from_user.id, friend_id)
        if success:
            await message.answer("✅ Игрок добавлен в друзья!")
        else:
            await message.answer("❌ Ошибка добавления.")
    except:
        await message.answer("Пример команды: `/add_friend 12345678`")

@dp.message(F.text == "🛡 Кланы")
async def clan_menu(message: Message):
    await message.answer(
        "🛡 {html.bold('Клановое Убежище')}\n\n"
        "Создай свой собственный топ-клан командой:\n"
        "`/create_clan НАЗВАНИЕ`"
    )

@dp.message(F.text.startswith("/create_clan"))
async def create_clan_command(message: Message):
    parts = message.text.split(" ", 1)
    if len(parts) < 2:
        return await message.answer("Пример: `/create_clan BRAWL_STARS`")
    clan_name = parts[1]
    success = await database.create_clan(clan_name, message.from_user.id)
    if success:
        await message.answer(f"🎉 Клан '{clan_name}' успешно создан! Вы глава клана.")
    else:
        await message.answer("❌ Имя клана уже занято.")

async def handle_ping(request):
    return web.Response(text="OK")

async def main():
    await database.init_db()
    print("Бот успешно запущен!")
    asyncio.create_task(dp.start_polling(bot))
    
    app = web.Application()
    app.router.add_get('/', handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 80)
    await site.start()
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())

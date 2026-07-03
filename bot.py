import os
import asyncio
import random
import aiosqlite
from aiogram import Bot, Dispatcher, html, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import CommandStart
from aiohttp import web
import database

TOKEN = "8978194297:AAHp1oqolPRqtCZ48KRndAGFXrd-in30OTw"
ADMIN_ID = 7844240869  # Твой ID владельца

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Состояния для админ-рассылки
admin_states = {}

EMOJIS = {
    "Common": "🟢", "Rare": "🔵", "Epic": "🟣", "Mythic": "🟡", "Legendary": "🟠",
    "Стартовая": "🌱", "Закаленная": "🛡️", "Тайная": "🔮", "Мифическая": "🌟",
    "Легендарная": "👑", "Эфирная": "🌌", "Божественная": "🔱", "Лимитированная": "🚨",
    "Ржавая": "🔧", "Заряженная": "⚡", "Токсичная": "☣️", "Хайповая": "🕶️",
    "Трендовая": "🔥", "🧪 Экспериментальная": "🧪", "Пустотная": "🌑", "Алмазная": "💎"
}

def get_main_keyboard(user_id: int):
    buttons = [
        [KeyboardButton(text="🎰 Испытать удачу"), KeyboardButton(text="👤 Профиль")],
        [KeyboardButton(text="🛒 Магазин"), KeyboardButton(text="🎒 Мой Инвентарь")],
        [KeyboardButton(text="⚔️ Искать Бой"), KeyboardButton(text="👥 Друзья")],
        [KeyboardButton(text="🛡 Кланы")]
    ]
    # Если это ты, добавляем кнопку админки в самый низ
    if user_id == ADMIN_ID:
        buttons.append([KeyboardButton(text="👑 Админ-Панель")])
        
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

@dp.message(CommandStart())
async def command_start_handler(message: Message):
    await database.register_user(message.from_user.id, message.from_user.username or f"id_{message.from_user.id}")
    await message.answer(
        f"🤖 Добро пожаловать! Все системы активны.\n\n"
        f"Собирай карточки, торгуй на рынке, вступай в кланы и сражайся!",
        reply_markup=get_main_keyboard(message.from_user.id)
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
            f"💪 Карта добавлена в инвентарь! Сила выросла."
        )

@dp.message(F.text == "🎒 Мой Инвентарь")
async def inventory_handler(message: Message):
    inv = await database.get_user_inventory(message.from_user.id)
    if not inv:
        return await message.answer("🎒 Твой инвентарь пока пуст. Крути дропы!")
    
    await message.answer("🎒 Твоя коллекция карт. Нажми на карту ниже, чтобы продать её за монеты:")
    
    for item in inv:
        inv_id, name, fandom, rarity, price = item
        rarity_emoji = EMOJIS.get(rarity, "🃏")
        sell_price = int(price * 0.7)
        
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"💰 Продать за 🪙 {sell_price}", callback_data=f"sell_{inv_id}")]
        ])
        
        await message.answer(
            f"{rarity_emoji} {html.bold(name)}\n🎬 Фандом: {fandom}\n⭐ Редкость: {rarity}",
            reply_markup=kb
        )

@dp.callback_query(F.data.startswith("sell_"))
async def sell_callback(callback: CallbackQuery):
    inv_id = int(callback.data.split("_")[1])
    earned = await database.sell_card_back(callback.from_user.id, inv_id)
    
    if earned:
        await callback.message.edit_text("✅ Карточка успешно продана на рынке!")
        await callback.answer(f"Получено 🪙 +{earned} монет!")
    else:
        await callback.answer("❌ Ошибка продажи! Возможно, карта уже продана.")

@dp.message(F.text == "🛒 Магазин")
async def shop_handler(message: Message):
    items = await database.get_shop_items()
    if not items:
        return await message.answer("Магазин пуст.")
    
    text = f"🏪 {html.bold('Ассортимент магазина:')}\n\n"
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
        await message.answer(f"🏆 Ты выиграл дуэль! Твоя общая атака: {user_roll}, защита соперника: {enemy_roll}.\nНаграда: 🪙 +{reward} монет!")
    else:
        loss = random.randint(15, 40)
        await database.update_coins(user_id, -loss)
        await message.answer(f"💀 Поражение. Твоя общая атака: {user_roll}, защита соперника: {enemy_roll}.\nПотеряно: 🪙 -{loss} монет.")

@dp.message(F.text == "👥 Друзья")
async def friends_menu(message: Message):
    friends = await database.get_friends(message.from_user.id)
    text = "👥 **Список твоих друзей:**\n\n"
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
        "🛡 **Клановое Убежище**\n\n"
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

# ==================== АДМИН ПАНЕЛЬ (ТОЛЬКО ДЛЯ ТЕБЯ) ====================

@dp.message(F.text == "👑 Админ-Панель")
async def admin_panel_handler(message: Message):
    if message.from_user.id != ADMIN_ID:
        return await message.answer("🔒 Доступ ограничен. Вы не создатель бота.")
        
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Статистика", callback_data="adm_stats")],
        [InlineKeyboardButton(text="📢 Сделать рассылку", callback_data="adm_broadcast")]
    ])
    await message.answer("👑 Панель управления Создателя. Выберите действие:", reply_markup=kb)

@dp.callback_query(F.data.startswith("adm_"))
async def admin_callbacks(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return await callback.answer("Отказано в доступе!", show_alert=True)
        
    if callback.data == "adm_stats":
        async with aiosqlite.connect(database.DB_NAME) as db:
            async with db.execute("SELECT COUNT(*) FROM users") as res:
                total_users = (await res.fetchone())[0]
            async with db.execute("SELECT COUNT(*) FROM inventory") as res:
                total_cards = (await res.fetchone())[0]
                
        await callback.message.edit_text(
            f"📊 {html.bold('Статистика бота:')}\n\n"
            f"👥 Всего игроков зарегистрировано: {total_users}\n"
            f"🃏 Всего выбито карт в инвентарях: {total_cards}"
        )
        await callback.answer()
        
    elif callback.data == "adm_broadcast":
        admin_states[callback.from_user.id] = "waiting_text"
        await callback.message.edit_text("📢 Отправь следующим сообщением текст, который получат ВСЕ игроки бота:")
        await callback.answer()

# Перехват текста рассылки
@dp.message(lambda msg: admin_states.get(msg.from_user.id) == "waiting_text")
async def process_broadcast_text(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
        
    broadcast_text = message.text
    admin_states[message.from_user.id] = None # Сброс состояния
    
    await message.answer("🚀 Начинаю глобальную рассылку...")
    
    async with aiosqlite.connect(database.DB_NAME) as db:
        async with db.execute("SELECT tg_id FROM users") as cursor:
            users = await cursor.fetchall()
            
    success = 0
    for u in users:
        try:
            await bot.send_message(chat_id=u[0], text=broadcast_text)
            success += 1
            await asyncio.sleep(0.05) # Защита от спам-фильтра Telegram
        except:
            continue
            
    await message.answer(f"📢 Рассылка завершена!\nУспешно отправлено: {success} игрокам.")

# =========================================================================

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

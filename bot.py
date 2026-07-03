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

# Состояния для админ-действий
admin_states = {}

EMOJIS = {
    "Common": "🟢", "Rare": "🔵", "Epic": "🟣", "Mythic": "🟡", "Legendary": "🟠",
    "Brawl Stars": "🌟", "Roblox": "🧱", "Geometry Dash": "🔺"
}

# Стоимость ящиков по фэндомам
BOX_PRICES = {
    "Brawl Stars": 150,
    "Roblox": 100,
    "Geometry Dash": 80
}

def get_main_keyboard(user_id: int):
    # УДАЛЕНА кнопка Мой Инвентарь по твоему запросу
    buttons = [
        [KeyboardButton(text="🎰 Испытать удачу"), KeyboardButton(text="👤 Профиль")],
        [KeyboardButton(text="🛒 Магазин"), KeyboardButton(text="⚔️ Искать Бой")],
        [KeyboardButton(text="👥 Друзья"), KeyboardButton(text="🛡 Кланы")]
    ]
    if user_id == ADMIN_ID:
        buttons.append([KeyboardButton(text="👑 Админ-Панель")])
        
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

@dp.message(CommandStart())
async def command_start_handler(message: Message):
    admin_states[message.from_user.id] = None
    await database.register_user(message.from_user.id, message.from_user.username or f"id_{message.from_user.id}")
    await message.answer(
        f"🤖 Добро пожаловать в обновленную версию бота!\n\n"
        f"Покупай кейсы фэндомов, продавай карты прямо в магазине и побеждай!",
        reply_markup=get_main_keyboard(message.from_user.id)
    )

@dp.message(F.text == "👤 Профиль")
async def profile_handler(message: Message):
    admin_states[message.from_user.id] = None
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
    admin_states[message.from_user.id] = None
    card = await database.get_random_card()
    if card:
        card_id, name, fandom, rarity = card
        
        # УДАЛЕНИЕ МЕЛСТРОЯ: Фильтруем на лету, если карта осталась в базе
        if "мелстрой" in name.lower() or "mellstroy" in name.lower() or "мем" in name.lower():
            return await message.answer("🎰 Карточка выпала... Но она оказалась удаленной цензурой! Крути еще раз.")
            
        await database.add_to_inventory(message.from_user.id, card_id)
        rarity_emoji = EMOJIS.get(rarity, "🃏")
        fandom_emoji = EMOJIS.get(fandom, "🎬")
        await message.answer(
            f"🎉 Дроп получен!\n\n"
            f"{fandom_emoji} Фэндом: {html.bold(fandom)}\n"
            f"👤 Карточка: {name}\n"
            f"{rarity_emoji} Редкость: {rarity}\n\n"
            f"💪 Карта добавлена в инвентарь!"
        )

# === ОБНОВЛЕННЫЙ МАГАЗИН: ПОКУПКА, ПРОДАЖА КАРТ И ЯЩИКИ ===
@dp.message(F.text == "🛒 Магазин")
async def shop_handler(message: Message):
    admin_states[message.from_user.id] = None
    
    text = f"🏪 {html.bold('Добро пожаловать в Магазин!')}\n\n"
    text += f"📦 {html.bold('Ящики фэндомов:')}\n"
    for fandom, b_price in BOX_PRICES.items():
        text += f"• Ящик {fandom} — 🪙 {b_price} монет\n"
        
    keyboard = [
        [InlineKeyboardButton(text="⭐ Ящик Brawl Stars", callback_data="open_box_Brawl Stars")],
        [InlineKeyboardButton(text="🧱 Ящик Roblox", callback_data="open_box_Roblox")],
        [InlineKeyboardButton(text="🔺 Ящик Geometry Dash", callback_data="open_box_Geometry Dash")],
        [InlineKeyboardButton(text="💰 Продать мои карточки", callback_data="shop_sell_menu")]
    ]
    
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    await message.answer(text, reply_markup=reply_markup)

# Меню продажи внутри магазина
@dp.callback_query(F.data == "shop_sell_menu")
async def shop_sell_menu_callback(callback: CallbackQuery):
    inv = await database.get_user_inventory(callback.from_user.id)
    if not inv:
        return await callback.answer("🎒 Твой инвентарь пуст, продавать нечего!", show_alert=True)
        
    text = f"💰 {html.bold('Окно продажи твоих карт:')}\nВыбери карту, которую хочешь продать:\n\n"
    keyboard = []
    
    for num, item in enumerate(inv, 1):
        inv_id, name, fandom, rarity, price = item
        # Пропускаем Мелстроя, если он завалялся в инвентаре
        if "мелстрой" in name.lower() or "mellstroy" in name.lower():
            continue
        sell_price = int(price * 0.7)
        rarity_emoji = EMOJIS.get(rarity, "🃏")
        
        text += f"{num}. {rarity_emoji} {name} ({fandom}) — 🪙 {sell_price}\n"
        keyboard.append([InlineKeyboardButton(text=f"Продать №{num} (+🪙{sell_price})", callback_data=f"ssell_{inv_id}")])
        
    keyboard.append([InlineKeyboardButton(text="🔙 Назад в магазин", callback_data="back_to_shop")])
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))

@dp.callback_query(F.data.startswith("ssell_"))
async def shop_sell_execute(callback: CallbackQuery):
    inv_id = int(callback.data.split("_")[1])
    earned = await database.sell_card_back(callback.from_user.id, inv_id)
    if earned:
        await callback.answer(f"✅ Продано! Получено 🪙 +{earned} монет!", show_alert=True)
        await shop_sell_menu_callback(callback) # Перерисовываем меню
    else:
        await callback.answer("❌ Ошибка продажи.")

# Покупка тематических ящиков
@dp.callback_query(F.data.startswith("open_box_"))
async def open_box_callback(callback: CallbackQuery):
    fandom = callback.data.replace("open_box_", "")
    price = BOX_PRICES.get(fandom, 100)
    
    profile = await database.get_user_profile(callback.from_user.id)
    if not profile or profile[0] < price:
        return await callback.answer("❌ Недостаточно монет для покупки этого ящика!", show_alert=True)
        
    # Снимаем монеты
    await database.update_coins(callback.from_user.id, -price)
    
    # Ищем карты конкретного фэндома (без Мелстроя)
    async with aiosqlite.connect(database.DB_NAME) as db:
        async with db.execute(
            "SELECT id, name, fandom, rarity FROM cards WHERE fandom = ? AND name NOT LIKE '%Мелстрой%' AND name NOT LIKE '%Mellstroy%'", 
            (fandom,)
        ) as cursor:
            cards = await cursor.fetchall()
            
    if not cards:
        await database.update_coins(callback.from_user.id, price) # Возврат
        return await callback.answer("🤖 В этом ящике временно кончились карты!", show_alert=True)
        
    card_id, name, fandom, rarity = random.choice(cards)
    await database.add_to_inventory(callback.from_user.id, card_id)
    
    rarity_emoji = EMOJIS.get(rarity, "🃏")
    await callback.message.answer(
        f"📦 Вы открыли **Ящик {fandom}** за 🪙 {price} монет!\n\n"
        f"👤 Выпала карта: {html.bold(name)}\n"
        f"{rarity_emoji} Редкость: {rarity}"
    )
    await callback.answer("Успешное открытие!")

@dp.callback_query(F.data == "back_to_shop")
async def back_to_shop_callback(callback: CallbackQuery):
    await callback.message.delete()
    # Имитируем нажатие на Магазин
    await shop_handler(callback.message)

# === ОСТАЛЬНЫЕ ИГРОВЫЕ ФУНКЦИИ ===
@dp.message(F.text == "⚔️ Искать Бой")
async def battle_handler(message: Message):
    admin_states[message.from_user.id] = None
    user_id = message.from_user.id
    user_profile = await database.get_user_profile(user_id)
    enemy = await database.get_enemy(user_id)
    
    if not enemy or not user_profile:
        return await message.answer("🤖 Противников пока нет.")
        
    _, u_power, _ = user_profile
    enemy_id, enemy_name, enemy_power = enemy
    
    await message.answer(f"⚔️ Ищем соперника... Найдено: Игрок @{enemy_name} (Сила: {enemy_power})!")
    await asyncio.sleep(1)
    
    user_roll = u_power + random.randint(1, 25)
    enemy_roll = enemy_power + random.randint(1, 25)
    
    if user_roll >= enemy_roll:
        reward = random.randint(50, 120)
        await database.update_coins(user_id, reward)
        await message.answer(f"🏆 Ты выиграл! Награда: 🪙 +{reward} монет!")
    else:
        loss = random.randint(15, 40)
        await database.update_coins(user_id, -loss)
        await message.answer(f"💀 Поражение. Потеряно: 🪙 -{loss} монет.")

@dp.message(F.text == "👥 Друзья")
async def friends_menu(message: Message):
    admin_states[message.from_user.id] = None
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
        success = await database.add_friend(message.from_user.id, friend_id)
        if success: await message.answer("✅ Добавлен!")
        else: await message.answer("❌ Ошибка.")
    except:
        await message.answer("Пример: `/add_friend 12345678`")

@dp.message(F.text == "🛡 Кланы")
async def clan_menu(message: Message):
    admin_states[message.from_user.id] = None
    await message.answer("🛡 **Клановое Убежище**\n\nСоздай клан:\n`/create_clan НАЗВАНИЕ`")

@dp.message(F.text.startswith("/create_clan"))
async def create_clan_command(message: Message):
    parts = message.text.split(" ", 1)
    if len(parts) < 2: return await message.answer("Пример: `/create_clan BRAWL`")
    success = await database.create_clan(parts[1], message.from_user.id)
    if success: await message.answer(f"🎉 Клан '{parts[1]}' успешно создан!")
    else: await message.answer("❌ Ошибка создания.")


# ==================== МОЩНАЯ АДМИН ПАНЕЛЬ (10 КОМАНД) ====================

@dp.message(F.text == "👑 Админ-Панель")
async def admin_panel_handler(message: Message):
    if message.from_user.id != ADMIN_ID:
        return await message.answer("🔒 Отказано в доступе.")
        
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 1. Статистика", callback_data="a_1"), InlineKeyboardButton(text="📢 2. Рассылка", callback_data="a_2")],
        [InlineKeyboardButton(text="🪙 3. Выдать монет", callback_data="a_3"), InlineKeyboardButton(text="⛔ 4. Забрать монет", callback_data="a_4")],
        [InlineKeyboardButton(text="🃏 5. Добавить Карту", callback_data="a_5"), InlineKeyboardButton(text="🗑️ 6. Удалить Мемы", callback_data="a_6")],
        [InlineKeyboardButton(text="🧙‍♂️ 7. Дать Силу", callback_data="a_7"), InlineKeyboardButton(text="❌ 8. Обнулить Топа", callback_data="a_8")],
        [InlineKeyboardButton(text="🛡️ 9. Список Кланов", callback_data="a_9"), InlineKeyboardButton(text="💥 10. Очистить Инвентарь", callback_data="a_10")]
    ])
    await message.answer("👑 **Панель Создателя (10 встроенных команд):**", reply_markup=kb)

@dp.callback_query(F.data.startswith("a_"))
async def admin_actions(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID: return
    cmd = callback.data.split("_")[1]
    
    if cmd == "1":  # 1. СТАТИСТИКА
        async with aiosqlite.connect(database.DB_NAME) as db:
            users = (await (await db.execute("SELECT COUNT(*) FROM users")).fetchone())[0]
            cards = (await (await db.execute("SELECT COUNT(*) FROM inventory")).fetchone())[0]
        await callback.message.answer(f"📊 Игроков: {users}\n🃏 Всего карт на руках: {cards}")
        
    elif cmd == "2":  # 2. РАССЫЛКА
        admin_states[callback.from_user.id] = "w_broadcast"
        await callback.message.answer("📢 Введи текст рассылки:")
        
    elif cmd == "3":  # 3. ВЫДАТЬ МОНЕТЫ
        admin_states[callback.from_user.id] = "w_give_coins"
        await callback.message.answer("🪙 Введи в формате: `ID КОЛИЧЕСТВО` (например, `7844240869 5000`)")
        
    elif cmd == "4":  # 4. ЗАБРАТЬ МОНЕТЫ
        admin_states[callback.from_user.id] = "w_take_coins"
        await callback.message.answer("⛔ Введи в формате: `ID КОЛИЧЕСТВО` (например, `123456 500`)")
        
    elif cmd == "5":  # 5. ДОБАВИТЬ НОВУЮ КАРТУ В БАЗУ
        admin_states[callback.from_user.id] = "w_add_card"
        await callback.message.answer("🃏 Введи: `Имя | Фэндом | Редкость | Цена` (Редкости: Common, Rare, Epic, Mythic, Legendary)")
        
    elif cmd == "6":  # 6. БЫСТРОЕ УДАЛЕНИЕ МЕЛСТРОЯ
        async with aiosqlite.connect(database.DB_NAME) as db:
            await db.execute("DELETE FROM cards WHERE name LIKE '%Мелстрой%' OR name LIKE '%Mellstroy%'")
            await db.execute("DELETE FROM inventory WHERE card_id NOT IN (SELECT id FROM cards)")
            await db.commit()
        await callback.message.answer("🗑️ Мелстрой и все связанные с ним мемы успешно и навсегда стерты из базы данных!")
        
    elif cmd == "7":  # 7. ВЫДАТЬ СИЛУ АККАУНТУ
        admin_states[callback.from_user.id] = "w_give_power"
        await callback.message.answer("💪 Введи: `ID СИЛА` (например, `7844240869 1000`)")
        
    elif cmd == "8":  # 8. ОБНУЛИТЬ ИГРОКА
        admin_states[callback.from_user.id] = "w_reset_user"
        await callback.message.answer("❌ Введи Telegram ID игрока, чтобы полностью сбросить его прогресс:")
        
    elif cmd == "9":  # 9. ПОСМОТРЕТЬ ВСЕ КЛАНЫ
        async with aiosqlite.connect(database.DB_NAME) as db:
            async with db.execute("SELECT name FROM clans") as c:
                clans = await c.fetchall()
        txt = "🛡️ **Список существующих кланов:**\n\n"
        for cl in clans: txt += f"• {cl[0]}\n"
        await callback.message.answer(txt if clans else "Кланов еще нет.")
        
    elif cmd == "10":  # 10. ОЧИСТИТЬ ЧЕЙ-ТО ИНВЕНТАРЬ
        admin_states[callback.from_user.id] = "w_clear_inv"
        await callback.message.answer("💥 Введи Telegram ID, чей инвентарь полностью очистить:")
        
    await callback.answer()

# Приемщик ответов админа
@dp.message(lambda msg: msg.from_user.id == ADMIN_ID and admin_states.get(msg.from_user.id) is not None)
async def process_admin_inputs(message: Message):
    state = admin_states[message.from_user.id]
    admin_states[message.from_user.id] = None # Сброс состояния
    
    try:
        if state == "w_broadcast":
            async with aiosqlite.connect(database.DB_NAME) as db:
                users = await (await db.execute("SELECT tg_id FROM users")).fetchall()
            for u in users:
                try: await bot.send_message(u[0], message.text)
                except: continue
            await message.answer("✅ Рассылка завершена успешно!")
            
        elif state == "w_give_coins":
            uid, amt = map(int, message.text.split())
            await database.update_coins(uid, amt)
            await message.answer(f"✅ Баланс игрока {uid} увеличен на 🪙 {amt}!")
            
        elif state == "w_take_coins":
            uid, amt = map(int, message.text.split())
            await database.update_coins(uid, -amt)
            await message.answer(f"✅ У игрока {uid} изъято 🪙 {amt} монет!")
            
        elif state == "w_add_card":
            name, fandom, rarity, price = map(str.strip, message.text.split("|"))
            async with aiosqlite.connect(database.DB_NAME) as db:
                await db.execute("INSERT INTO cards (name, fandom, rarity, base_price) VALUES (?,?,?,?)", (name, fandom, rarity, int(price)))
                await db.commit()
            await message.answer(f"✅ Карта '{name}' [{fandom}] добавлена в игру!")
            
        elif state == "w_give_power":
            uid, pwr = map(int, message.text.split())
            async with aiosqlite.connect(database.DB_NAME) as db:
                await db.execute("UPDATE users SET power = power + ? WHERE tg_id = ?", (pwr, uid))
                await db.commit()
            await message.answer(f"✅ Сила игрока {uid} увеличена на 💪 {pwr}!")
            
        elif state == "w_reset_user":
            uid = int(message.text)
            async with aiosqlite.connect(database.DB_NAME) as db:
                await db.execute("UPDATE users SET coins = 100, power = 0, clan = NULL WHERE tg_id = ?", (uid,))
                await db.execute("DELETE FROM inventory WHERE user_id = ?", (uid,))
                await db.commit()
            await message.answer(f"💥 Прогресс игрока {uid} полностью сброшен до нуля!")
            
        elif state == "w_clear_inv":
            uid = int(message.text)
            async with aiosqlite.connect(database.DB_NAME) as db:
                await db.execute("DELETE FROM inventory WHERE user_id = ?", (uid,))
                await db.commit()
            await message.answer(f"💥 Инвентарь игрока {uid} полностью очищен!")
    except Exception as e:
        await message.answer(f"❌ Ошибка ввода параметров: {e}. Попробуй еще раз через админ-панель.")

# =========================================================================

async def handle_ping(request): return web.Response(text="OK")

async def main():
    await database.init_db()
    print("Бот успешно запущен!")
    asyncio.create_task(dp.start_polling(bot))
    app = web.Application()
    app.router.add_get('/', handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', 80).start()
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())

import os
import asyncio
from aiogram import Bot, Dispatcher, html, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart
from aiohttp import web
import database

TOKEN = os.getenv(8978194297:AAHp1oqolPRqtCZ48KRndAGFXrd-in30OTw)

bot = Bot(token=TOKEN)
dp = Dispatcher()

def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎰 Испытать удачу"), KeyboardButton(text="👤 Профиль")]
        ],
        resize_keyboard=True
    )

@dp.message(CommandStart())
async def command_start_handler(message: Message):
    await database.register_user(message.from_user.id, message.from_user.username)
    await message.answer(
        f"Привет, {html.bold(message.from_user.full_name)}! Добро пожаловать в мультифэндомную ККИ!\n"
        f"Здесь ты можешь собирать карточки по Brawl Stars, Geometry Dash и Roblox.",
        reply_markup=get_main_keyboard()
    )

@dp.message(F.text == "👤 Профиль")
async def profile_handler(message: Message):
    profile = await database.get_user_profile(message.from_user.id)
    if profile:
        coins = profile[0]
        await message.answer(f"📝 Твой профиль:\n🪙 Баланс: {coins} монет")
    else:
        await message.answer("Сначала пропиши /start для регистрации!")

@dp.message(F.text == "🎰 Испытать удачу")
async def drop_card_handler(message: Message):
    card = await database.get_random_card()
    if card:
        card_id, name, fandom, rarity = card
        await database.add_to_inventory(message.from_user.id, card_id)
        
        rarity_emoji = "✨" if rarity == "Legendary" else "📦"
        
        await message.answer(
            f"🎉 Тебе выпала карточка!\n\n"
            f"🎬 Фэндом: {html.bold(fandom)}\n"
            f"👤 Имя: {name}\n"
            f"{rarity_emoji} Редкость: {rarity}"
        )
    else:
        await message.answer("Произошла ошибка, карточки не найдены в базе.")

# Хэндлер для Render, чтобы он видел, что бот работает
async def handle_ping(request):
    return web.Response(text="Бот работает!")

async def main():
    await database.init_db()
    print("Бот успешно запущен!")
    
    # Запускаем фоновую задачу для опроса Телеграма
    asyncio.create_task(dp.start_polling(bot))
    
    # Запускаем мини веб-сервер для Render на порту 80
    app = web.Application()
    app.router.add_get('/', handle_ping)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 80)
    await site.start()
    
    # Держим сервер запущенным бесконечно
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())

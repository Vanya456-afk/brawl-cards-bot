import os
import asyncio
from aiogram import Bot, Dispatcher, html, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart
import database

TOKEN = os.getenv("8978194297:AAHp1oqolPRqtCZ48KRndAGFXrd-in30OTw")

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

async def main():
    await database.init_db()
    print("Бот успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

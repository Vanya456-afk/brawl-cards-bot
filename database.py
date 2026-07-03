import aiosqlite
from datetime import datetime

DB_NAME = "cards_game.db"

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                tg_id INTEGER PRIMARY KEY,
                username TEXT,
                coins INTEGER DEFAULT 100,
                last_drop TEXT
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS cards (
                card_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                fandom TEXT NOT NULL,
                rarity TEXT NOT NULL
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tg_id INTEGER,
                card_id INTEGER,
                FOREIGN KEY (tg_id) REFERENCES users(tg_id),
                FOREIGN KEY (card_id) REFERENCES cards(card_id)
            )
        ''')
        await db.commit()
        await populate_test_cards()

async def populate_test_cards():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM cards")
        count = await cursor.fetchone()
        if count[0] == 0:
            test_cards = [
                ('Leon', 'Brawl Stars', 'Legendary'),
                ('Shelly', 'Brawl Stars', 'Common'),
                ('Bloodbath (Demon)', 'Geometry Dash', 'Legendary'),
                ('Classic Cube', 'Geometry Dash', 'Common'),
                ('Builderman', 'Roblox', 'Legendary'),
                ('Noob', 'Roblox', 'Common')
            ]
            await db.executemany("INSERT INTO cards (name, fandom, rarity) VALUES (?, ?, ?)", test_cards)
            await db.commit()

async def register_user(tg_id: int, username: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (tg_id, username) VALUES (?, ?)",
            (tg_id, username)
        )
        await db.commit()

async def get_user_profile(tg_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT coins FROM users WHERE tg_id = ?", (tg_id,)) as cursor:
            return await cursor.fetchone()

async def get_random_card():
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT card_id, name, fandom, rarity FROM cards ORDER BY RANDOM() LIMIT 1") as cursor:
            return await cursor.fetchone()

async def add_to_inventory(tg_id: int, card_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT INTO inventory (tg_id, card_id) VALUES (?, ?)", (tg_id, card_id))
        await db.commit()

import aiosqlite

DB_NAME = "cards_game.db"

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        # Таблица пользователей
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                tg_id INTEGER PRIMARY KEY,
                username TEXT,
                coins INTEGER DEFAULT 100,
                clan_id INTEGER DEFAULT NULL,
                power INTEGER DEFAULT 10,
                last_drop TEXT
            )
        ''')
        
        # Таблица всех доступных карточек
        await db.execute('''
            CREATE TABLE IF NOT EXISTS cards (
                card_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                fandom TEXT NOT NULL,
                rarity TEXT NOT NULL,
                price INTEGER DEFAULT 50
            )
        ''')
        
        # Таблица инвентаря
        await db.execute('''
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tg_id INTEGER,
                card_id INTEGER,
                FOREIGN KEY (tg_id) REFERENCES users(tg_id),
                FOREIGN KEY (card_id) REFERENCES cards(card_id)
            )
        ''')

        # Таблица КЛАНОВ
        await db.execute('''
            CREATE TABLE IF NOT EXISTS clans (
                clan_id INTEGER PRIMARY KEY AUTOINCREMENT,
                clan_name TEXT NOT NULL UNIQUE,
                owner_id INTEGER
            )
        ''')

        # Таблица ДРУЗЕЙ
        await db.execute('''
            CREATE TABLE IF NOT EXISTS friends (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                friend_id INTEGER,
                status TEXT DEFAULT 'accepted',
                UNIQUE(user_id, friend_id)
            )
        ''')
        await db.commit()
        await populate_test_cards()

async def populate_test_cards():
    async with aiosqlite.connect(DB_NAME) as db:
        # Полная очистка и перезалив карт без удаления структуры таблиц
        await db.execute("DELETE FROM cards")
        
        test_cards = [
            # === BRAWL STARS ===
            ('Shelly', 'Brawl Stars', 'Common', 50),
            ('Stu', 'Brawl Stars', 'Epic', 200),
            ('Mortis', 'Brawl Stars', 'Mythic', 350),
            ('Leon', 'Brawl Stars', 'Legendary', 500),
            
            # === GEOMETRY DASH ===
            ('Classic Cube', 'Geometry Dash', 'Common', 40),
            ('Spider Icon', 'Geometry Dash', 'Rare', 100),
            ('Bloodbath (Demon)', 'Geometry Dash', 'Epic', 250),
            ('Tidal Wave (Demon)', 'Geometry Dash', 'Mythic', 450),
            ('Acheron (Demon)', 'Geometry Dash', 'Legendary', 600),
            
            # === ROBLOX ===
            ('Noob', 'Roblox', 'Common', 30),
            ('Bacon Hair', 'Roblox', 'Rare', 90),
            ('Builderman', 'Roblox', 'Epic', 220),
            ('Seek (Doors)', 'Roblox', 'Mythic', 380),
            ('Adopt Me Dragon', 'Roblox', 'Legendary', 550),
            
            # === АНИМЕ ===
            ('Tanjiro', 'Аниме', 'Rare', 110),
            ('Zoro', 'Аниме', 'Epic', 260),
            ('Gojo Satoru', 'Аниме', 'Mythic', 420),
            ('Naruto Uzumaki', 'Аниме', 'Legendary', 520),
            
            # === МЕМЫ ===
            ('Sad Cat', 'Мемы', 'Common', 30),
            ('Doge', 'Мемы', 'Rare', 120),
            ('Pop Cat', 'Мемы', 'Epic', 200),
            ('Gigachad', 'Мемы', 'Хайповая', 500),
            ('Хомяк из Хамстер Комбат', 'Мемы', 'Ржавая', 15),
            ('Чипи Чипи Чапа Чапа Кошак', 'Мемы', 'Трендовая', 100),
            
            # === MINECRAFT ===
            ('Стив', 'Minecraft', 'Стартовая', 40),
            ('Эндермен', 'Minecraft', 'Тайная', 200),
            ('Варден (Босс)', 'Minecraft', 'Легендарная', 550),
            ('Алмазный Блок', 'Minecraft', 'Эфирная', 800),
            
            # === CLASH UNIVERSE ===
            ('Всадник на кабане (Хог)', 'Clash Universe', 'Закаленная', 110),
            ('П.Е.К.К.А', 'Clash Universe', 'Мифическая', 400),
            ('Мегарыцарь', 'Clash Universe', 'Легендарная', 600),
            
            # === ХОРРОРЫ ===
            ('Аниматроник Фредди', 'Хорроры', 'Тайная', 250),
            ('Сиреноголовый', 'Хорроры', 'Мифическая', 450),
            
            # === СУПЕРГЕРОИ ===
            ('Человек-Паук', 'Супергерои', 'Закаленная', 150),
            ('Дэдпул', 'Супергерои', 'Мифическая', 430),
            ('Бэтмен', 'Супергерои', 'Легендарная', 650),
            ('Танос с Перчаткой', 'Супергерои', 'Божественная', 1500),
            
            # === МУЛЬТФИЛЬМЫ ===
            ('Губка Боб', 'Мультфильмы', 'Стартовая', 50),
            ('Билл Шифр (Гравити Фолз)', 'Мультфильмы', 'Божественная', 1300),
            ('Рик Санчез', 'Мультфильмы', 'Легендарная', 700),
            
            # === РАЗРАБОТЧИКИ ===
            ('РобТоп (Создатель GD)', 'Разработчики', 'Божественная', 2000),
            ('Создатель Бота 😎', 'Разработчики', 'Лимитированная', 5000),
            
            # === UNDERTALE ===
            ('Санс (Глаз горит 💀)', 'Undertale', 'Заряженная', 300),
            ('Папирус', 'Undertale', 'Ржавая', 50),
            ('Флауи', 'Undertale', 'Токсичная', 150),
            
            # === БЛОГЕРЫ ===
            ('Влад А4', 'Блогеры', 'Хайповая', 250),
            ('MrBeast (Дает 10000$)', 'Блогеры', 'Алмазная', 999),
            ('Стример Бустер', 'Блогеры', 'Трендовая', 200),
            
            # === КРИПИПАСТА & SCP ===
            ('SCP-173 (Статуя)', 'Крипипаста', '🧪 Экспериментальная', 180),
            ('Монстр из Закулисья', 'Крипипаста', 'Пустотная', 400),
            ('Слендермен', 'Крипипаста', 'Пустотная', 600),
            
            # === ВЫЖИВАЛКИ ===
            ('Слизень из Terraria', 'Выживалки', 'Ржавая', 30),
            ('Жнец-Левиафан (Subnautica)', 'Выживалки', 'Алмазная', 750),
            
            # === ШУТЕРЫ & GTA ===
            ('Тревор Филиппс (GTA 5)', 'Шутеры', 'Токсичная', 350),
            ('Спецназовец из CS 2', 'Шутеры', 'Заряженная', 120)
        ]
        await db.executemany("INSERT INTO cards (name, fandom, rarity, price) VALUES (?, ?, ?, ?)", test_cards)
        await db.commit()

async def register_user(tg_id: int, username: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT OR IGNORE INTO users (tg_id, username) VALUES (?, ?)", (tg_id, username))
        await db.commit()

async def get_user_profile(tg_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('''
            SELECT u.coins, u.power, c.clan_name 
            FROM users u LEFT JOIN clans c ON u.clan_id = c.clan_id 
            WHERE u.tg_id = ?
        ''', (tg_id,)) as cursor:
            return await cursor.fetchone()

async def get_random_card():
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT card_id, name, fandom, rarity FROM cards ORDER BY RANDOM() LIMIT 1") as cursor:
            return await cursor.fetchone()

async def add_to_inventory(tg_id: int, card_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT INTO inventory (tg_id, card_id) VALUES (?, ?)", (tg_id, card_id))
        await db.execute("UPDATE users SET power = power + 5 WHERE tg_id = ?", (tg_id,))
        await db.commit()

async def get_shop_items():
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT card_id, name, fandom, rarity, price FROM cards ORDER BY RANDOM() LIMIT 4") as cursor:
            return await cursor.fetchall()

async def buy_card(tg_id: int, card_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT price FROM cards WHERE card_id = ?", (card_id,)) as c:
            card = await c.fetchone()
        async with db.execute("SELECT coins FROM users WHERE tg_id = ?", (tg_id,)) as u:
            user = await u.fetchone()
            
        if card and user and user[0] >= card[0]:
            await db.execute("UPDATE users SET coins = coins - ? WHERE tg_id = ?", (card[0], tg_id))
            await db.execute("INSERT INTO inventory (tg_id, card_id) VALUES (?, ?)", (tg_id, card_id))
            await db.execute("UPDATE users SET power = power + 10 WHERE tg_id = ?", (tg_id,))
            await db.commit()
            return True
        return False

async def create_clan(clan_name: str, owner_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        try:
            cursor = await db.execute("INSERT INTO clans (clan_name, owner_id) VALUES (?, ?)", (clan_name, owner_id))
            clan_id = cursor.lastrowid
            await db.execute("UPDATE users SET clan_id = ? WHERE tg_id = ?", (clan_id, owner_id))
            await db.commit()
            return True
        except:
            return False

async def add_friend(user_id: int, friend_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        try:
            await db.execute("INSERT INTO friends (user_id, friend_id) VALUES (?, ?)", (user_id, friend_id))
            await db.execute("INSERT INTO friends (user_id, friend_id) VALUES (?, ?)", (friend_id, user_id))
            await db.commit()
            return True
        except:
            return False

async def get_friends(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('''
            SELECT f.friend_id, u.username FROM friends f 
            JOIN users u ON f.friend_id = u.tg_id 
            WHERE f.user_id = ?
        ''', (user_id,)) as cursor:
            return await cursor.fetchall()

async def get_enemy(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT tg_id, username, power FROM users WHERE tg_id != ? ORDER BY RANDOM() LIMIT 1", (user_id,)) as cursor:
            return await cursor.fetchone()

async def update_coins(tg_id: int, amount: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE users SET coins = coins + ? WHERE tg_id = ?", (amount, tg_id))
        await db.commit()

import aiosqlite

DB_NAME = "game.db"

async def create_tables(app):
    async with aiosqlite.connect(DB_NAME) as db:
        # 🔒 Aktifkan foreign key (penting!)
        await db.execute("PRAGMA foreign_keys = ON;")

        # Tabel players
        await db.execute("""
            CREATE TABLE IF NOT EXISTS players (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                class_name TEXT DEFAULT 'Novice',
                level INTEGER DEFAULT 1,
                exp INTEGER DEFAULT 0,
                gold INTEGER DEFAULT 1000,
                max_exp INTEGER DEFAULT 100
            )
        """)

        # 🌍 Tambahan kolom dunia & lokasi awal
        await db.execute("""
            ALTER TABLE players ADD COLUMN current_kingdom TEXT DEFAULT 'Arvendale';
        """)
        await db.execute("""
            ALTER TABLE players ADD COLUMN location TEXT DEFAULT 'Solmare';
        """)
        await db.execute("""
            ALTER TABLE players ADD COLUMN story_progress INTEGER DEFAULT 0;
        """)



        # 🧱 Tambahkan tabel inventory
        await db.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                item_name TEXT,
                rarity TEXT,
                FOREIGN KEY (user_id) REFERENCES players (user_id) ON DELETE CASCADE
            )
        """)

         # 🏪 Tabel shop (toko)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS shop_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_name TEXT,
                rarity TEXT,
                price INTEGER
            )
        """)

        await db.commit()

        # 🏦 Market antar pemain
        await db.execute("""
            CREATE TABLE IF NOT EXISTS market (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                seller_id INTEGER,
                item_name TEXT,
                rarity TEXT,
                qty INTEGER DEFAULT 1,
                price INTEGER,
                FOREIGN KEY (seller_id) REFERENCES players (user_id) ON DELETE CASCADE
            )
        """)
        await db.commit()

        # --- Tambahkan tabel area_progress ---
        await db.execute("""
        CREATE TABLE IF NOT EXISTS area_progress (
            user_id INTEGER,
            area_name TEXT,
            monster_name TEXT,
            kills INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, area_name, monster_name)
        )
        """)

        await db.commit()









# +++++++++++ FUNGSI DATABASE ++++++++++ #
# ADD & GET PLAYER
async def add_player(user_id, username, first_name, class_name="Novice"):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT user_id FROM players WHERE user_id = ?", (user_id,)) as cursor:
            existing = await cursor.fetchone()
            if not existing:
                await db.execute(
                    "INSERT INTO players (user_id, username, first_name, class_name) VALUES (?, ?, ?, ?)",
                    (user_id, username, first_name, class_name)
                )
                await db.commit()


async def get_player(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT * FROM players WHERE user_id = ?", (user_id,)) as cursor:
            return await cursor.fetchone()
        
# HELPER UNTUK INVENTORY
async def add_item(user_id, item_name, rarity):
    async with aiosqlite.connect(DB_NAME) as db:
        # Pastikan foreign key aktif di tiap koneksi
        await db.execute("PRAGMA foreign_keys = ON;")

        # Cek apakah pemain ada
        async with db.execute("SELECT user_id FROM players WHERE user_id = ?", (user_id,)) as cursor:
            exists = await cursor.fetchone()

        if not exists:
            # Jangan simpan item jika pemain belum terdaftar
            return False

        
        await db.execute(
            "INSERT INTO inventory (user_id, item_name, rarity) VALUES (?, ?, ?)",
            (user_id, item_name, rarity)
        )
        await db.commit()


async def get_inventory(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        # Mengembalikan item_name, rarity, dan jumlah (qty)
        async with db.execute(
            "SELECT item_name, rarity, COUNT(*) AS qty "
            "FROM inventory WHERE user_id = ? "
            "GROUP BY item_name, rarity "
            "ORDER BY item_name ASC",
            (user_id,)
        ) as cursor:
            return await cursor.fetchall()

# HELPER UNTUK SHOP
async def get_shop_items():
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT id, item_name, rarity, price FROM shop_items") as cursor:
            return await cursor.fetchall()

async def get_shop_item(item_id):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT id, item_name, rarity, price FROM shop_items WHERE id = ?", (item_id,)) as cursor:
            return await cursor.fetchone()

async def seed_shop_items():
    async with aiosqlite.connect(DB_NAME) as db:
        # Buat tabel kalau belum ada
        await db.execute("""
            CREATE TABLE IF NOT EXISTS shop_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_name TEXT,
                rarity TEXT,
                price INTEGER
            )
        """)

        # Hapus semua data lama (agar tidak duplikat)
        await db.execute("DELETE FROM shop_items")

        # Tambahkan item baru
        items = [
            ("Potion", "Common", 50),
            ("Iron Sword", "Uncommon", 150),
            ("Steel Armor", "Rare", 300),
            ("Golden Dagger", "Epic", 600),
            ("Dragon Scale", "Legendary", 1000)
        ]

        await db.executemany(
            "INSERT INTO shop_items (item_name, rarity, price) VALUES (?, ?, ?)",
            items
        )
        await db.commit()
        print("✅ Shop berhasil diisi ulang dengan item baru.")


"""Database helpers for the Eldrathia Telegram RPG bot.

The original project shipped with a database module that attempted to
mutate the schema on every start which made the bot crash once the
migration had been applied.  The helpers below provide a small, well
structured API around the SQLite database and can safely be imported in
unit tests.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

import aiosqlite

DB_NAME = "game.db"


@dataclass
class Player:
    """Lightweight representation of a player record."""

    user_id: int
    username: Optional[str]
    first_name: Optional[str]
    class_name: str
    level: int
    exp: int
    gold: int
    max_exp: int
    current_kingdom: str
    location: str
    story_progress: int

    @classmethod
    def from_row(cls, row: Sequence) -> "Player":
        return cls(
            user_id=row[0],
            username=row[1],
            first_name=row[2],
            class_name=row[3],
            level=row[4],
            exp=row[5],
            gold=row[6],
            max_exp=row[7],
            current_kingdom=row[8],
            location=row[9],
            story_progress=row[10],
        )


async def _ensure_columns(db: aiosqlite.Connection) -> None:
    """Make sure optional columns are present.

    The project historically attempted to add columns via ``ALTER TABLE``
    every time the app booted which crashes once the columns exist.  We
    inspect ``PRAGMA table_info`` instead and only append columns that
    are missing.
    """

    async with db.execute("PRAGMA table_info(players)") as cursor:
        existing = {row[1] async for row in cursor}

    additions = [
        ("current_kingdom", "TEXT DEFAULT 'Arvendale'"),
        ("location", "TEXT DEFAULT 'Solmare'"),
        ("story_progress", "INTEGER DEFAULT 0"),
    ]

    for column, ddl in additions:
        if column not in existing:
            await db.execute(f"ALTER TABLE players ADD COLUMN {column} {ddl}")


async def create_tables() -> None:
    """Create all tables used by the bot.

    The function is idempotent and can safely be executed multiple times.
    """

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("PRAGMA foreign_keys = ON")

        await db.execute(
            """
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
            """
        )

        await _ensure_columns(db)

        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                item_name TEXT NOT NULL,
                rarity TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES players(user_id) ON DELETE CASCADE
            )
            """
        )

        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS shop_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_name TEXT NOT NULL,
                rarity TEXT NOT NULL,
                price INTEGER NOT NULL
            )
            """
        )

        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS market (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                seller_id INTEGER NOT NULL,
                item_name TEXT NOT NULL,
                rarity TEXT NOT NULL,
                qty INTEGER NOT NULL DEFAULT 1,
                price INTEGER NOT NULL,
                FOREIGN KEY (seller_id) REFERENCES players(user_id) ON DELETE CASCADE
            )
            """
        )

        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS area_progress (
                user_id INTEGER NOT NULL,
                area_name TEXT NOT NULL,
                monster_name TEXT NOT NULL,
                kills INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (user_id, area_name, monster_name),
                FOREIGN KEY (user_id) REFERENCES players(user_id) ON DELETE CASCADE
            )
            """
        )

        await db.commit()


async def add_player(
    user_id: int,
    username: Optional[str],
    first_name: Optional[str],
    class_name: str,
) -> None:
    """Insert a player if they do not yet exist."""

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """
            INSERT OR IGNORE INTO players (user_id, username, first_name, class_name)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, username, first_name, class_name),
        )
        await db.commit()


async def get_player(user_id: int) -> Optional[Player]:
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            "SELECT * FROM players WHERE user_id = ?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return Player.from_row(row) if row else None


async def update_player(
    user_id: int,
    *,
    level: Optional[int] = None,
    exp: Optional[int] = None,
    gold: Optional[int] = None,
    max_exp: Optional[int] = None,
    story_progress: Optional[int] = None,
) -> None:
    """Update one or more columns for a player.

    Parameters that are ``None`` are ignored.  A ``ValueError`` is raised
    if no field is supplied so that callers do not silently execute an
    empty UPDATE statement.
    """

    assignments = []
    values: List[int] = []

    for column, value in (
        ("level", level),
        ("exp", exp),
        ("gold", gold),
        ("max_exp", max_exp),
        ("story_progress", story_progress),
    ):
        if value is not None:
            assignments.append(f"{column} = ?")
            values.append(value)

    if not assignments:
        raise ValueError("At least one field must be provided")

    values.append(user_id)

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            f"UPDATE players SET {', '.join(assignments)} WHERE user_id = ?",
            values,
        )
        await db.commit()


async def delete_player(user_id: int) -> None:
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        await db.execute("DELETE FROM players WHERE user_id = ?", (user_id,))
        await db.commit()


async def add_item(user_id: int, item_name: str, rarity: str) -> None:
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """
            INSERT INTO inventory (user_id, item_name, rarity) VALUES (?, ?, ?)
            """,
            (user_id, item_name, rarity),
        )
        await db.commit()


async def get_inventory(user_id: int) -> List[Tuple[str, str, int]]:
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            """
            SELECT item_name, rarity, COUNT(*) as qty
            FROM inventory
            WHERE user_id = ?
            GROUP BY item_name, rarity
            ORDER BY item_name
            """,
            (user_id,),
        ) as cursor:
            return await cursor.fetchall()


async def get_shop_items() -> List[Tuple[int, str, str, int]]:
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            "SELECT id, item_name, rarity, price FROM shop_items ORDER BY id"
        ) as cursor:
            return await cursor.fetchall()


async def seed_shop_items() -> None:
    items = [
        ("Potion", "Common", 50),
        ("Iron Sword", "Uncommon", 150),
        ("Steel Armor", "Rare", 300),
        ("Golden Dagger", "Epic", 600),
        ("Dragon Scale", "Legendary", 1000),
    ]

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM shop_items")
        await db.executemany(
            "INSERT INTO shop_items (item_name, rarity, price) VALUES (?, ?, ?)",
            items,
        )
        await db.commit()


async def purchase_item(
    user_id: int,
    *,
    item_name: str,
    rarity: str,
    price: int,
    quantity: int,
) -> bool:
    """Attempt to purchase an item from the shop.

    Returns ``True`` if the purchase succeeded.  The function ensures that
    the player possesses enough gold and stores the newly acquired items
    atomically.
    """

    if quantity <= 0:
        raise ValueError("quantity must be positive")

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        async with db.execute(
            "SELECT gold FROM players WHERE user_id = ?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                return False
            gold = row[0]

        total_cost = price * quantity
        if gold < total_cost:
            return False

        await db.execute(
            "UPDATE players SET gold = gold - ? WHERE user_id = ?",
            (total_cost, user_id),
        )

        await db.executemany(
            "INSERT INTO inventory (user_id, item_name, rarity) VALUES (?, ?, ?)",
            [(user_id, item_name, rarity)] * quantity,
        )

        await db.commit()
        return True

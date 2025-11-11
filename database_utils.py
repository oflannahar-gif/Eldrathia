# =====================================================
# ⚙️ DATABASE UTILITIES UNTUK GAME ELDRAHTHIA
# =====================================================
import aiosqlite
import json
from functools import wraps
import aiosqlite
from telegram import Update

# Struktur tabel area_progress (buat dulu lewat SQLite)
# CREATE TABLE IF NOT EXISTS area_progress (
#   user_id INTEGER,
#   area_name TEXT,
#   progress_json TEXT
# );

# =====================================================
# 🔹 Ambil progress area (berapa kali player mengalahkan monster)
# =====================================================
async def get_area_progress(user_id: int, area_name: str):
    async with aiosqlite.connect("game.db") as db:
        async with db.execute(
            "SELECT progress_json FROM area_progress WHERE user_id = ? AND area_name = ?",
            (user_id, area_name),
        ) as cursor:
            row = await cursor.fetchone()
            if row and row[0]:
                return json.loads(row[0])
    return {}

# =====================================================
# 🔹 Update jumlah kill monster di area
# =====================================================
async def update_kill_count(user_id: int, area_name: str, monster_name: str):
    progress = await get_area_progress(user_id, area_name)
    progress[monster_name] = progress.get(monster_name, 0) + 1

    async with aiosqlite.connect("game.db") as db:
        await db.execute(
            """
            INSERT INTO area_progress (user_id, area_name, progress_json)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, area_name) DO UPDATE SET
            progress_json = excluded.progress_json
            """,
            (user_id, area_name, json.dumps(progress)),
        )
        await db.commit()

# =====================================================
# 💾 Simpan progress area (sesuai tabel area_name + monster_name)
# =====================================================
async def save_area_progress(user_id: int, area_name: str, progress: dict):
    async with aiosqlite.connect("game.db") as db:
        for monster_name, kills in progress.items():
            await db.execute("""
                INSERT INTO area_progress (user_id, area_name, monster_name, kills)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id, area_name, monster_name)
                DO UPDATE SET kills = excluded.kills
            """, (user_id, area_name, monster_name, kills))
        await db.commit()






# =====================================================
# 🧙‍♂️ DECORATOR: require_player
# =====================================================

# utils/decorators.py
import aiosqlite
from functools import wraps
from telegram import Update

# =====================================================
# ✅ 1. Cek kalau user SUDAH PUNYA karakter → cegah akses
# =====================================================
def prevent_if_has_character(func):
    """Decorator untuk mencegah user yang sudah punya karakter menjalankan handler tertentu."""
    @wraps(func)
    async def wrapper(update: Update, context, *args, **kwargs):
        query = getattr(update, "callback_query", None)
        user = update.effective_user or (query.from_user if query else None)

        if not user:
            return

        async with aiosqlite.connect("game.db") as db:
            async with db.execute("SELECT 1 FROM players WHERE user_id = ?", (user.id,)) as cursor:
                exists = await cursor.fetchone()

        if exists:
            # Jika dia punya karakter, munculkan peringatan dan hentikan handler
            if query:
                await query.answer("⚠️ Kamu sudah memiliki karakter.", show_alert=True)
            elif update.message:
                await update.message.reply_text(
                    "⚠️ Kamu sudah memiliki karakter. Gunakan /resetme untuk memulai ulang."
                )
            return

        # Lanjutkan handler jika belum punya karakter
        return await func(update, context, *args, **kwargs)
    return wrapper


# =====================================================
# ✅ 2. Cek kalau user BELUM PUNYA karakter → cegah akses
# =====================================================
def require_player(func):
    """Decorator untuk memastikan user sudah punya karakter sebelum lanjut."""
    @wraps(func)
    async def wrapper(update: Update, context, *args, **kwargs):
        query = getattr(update, "callback_query", None)
        user = update.effective_user or (query.from_user if query else None)

        if not user:
            return

        async with aiosqlite.connect("game.db") as db:
            async with db.execute("SELECT 1 FROM players WHERE user_id = ?", (user.id,)) as cursor:
                exists = await cursor.fetchone()

        if not exists:
            if query:
                await query.answer(
                    "⚠️ Kamu belum membuat karakter! Gunakan /start untuk memulai.",
                    show_alert=True,
                )
            elif update.message:
                await update.message.reply_text(
                    "⚠️ Kamu belum membuat karakter! Gunakan /start untuk memulai."
                )
            return

        return await func(update, context, *args, **kwargs)
    return wrapper


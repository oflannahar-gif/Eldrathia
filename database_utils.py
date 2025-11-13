"""Utility helpers that sit on top of :mod:`database`.

The module previously mixed different storage approaches for area
progress and duplicated imports.  The helpers below provide a consistent
API that is reused by the bot handlers.
"""

from __future__ import annotations

from functools import wraps
from typing import Any, Awaitable, Callable, Dict

import aiosqlite
from telegram import Update

DB_NAME = "game.db"


async def get_area_progress(user_id: int, area_name: str) -> Dict[str, int]:
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            """
            SELECT monster_name, kills
            FROM area_progress
            WHERE user_id = ? AND area_name = ?
            """,
            (user_id, area_name),
        ) as cursor:
            return {name: kills for name, kills in await cursor.fetchall()}


async def increment_kill(user_id: int, area_name: str, monster_name: str) -> None:
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """
            INSERT INTO area_progress (user_id, area_name, monster_name, kills)
            VALUES (?, ?, ?, 1)
            ON CONFLICT(user_id, area_name, monster_name)
            DO UPDATE SET kills = kills + 1
            """,
            (user_id, area_name, monster_name),
        )
        await db.commit()


async def save_area_progress(
    user_id: int, area_name: str, progress: Dict[str, int]
) -> None:
    async with aiosqlite.connect(DB_NAME) as db:
        await db.executemany(
            """
            INSERT INTO area_progress (user_id, area_name, monster_name, kills)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, area_name, monster_name)
            DO UPDATE SET kills = excluded.kills
            """,
            [
                (user_id, area_name, monster, kills)
                for monster, kills in progress.items()
            ],
        )
        await db.commit()


Handler = Callable[[Update, Any], Awaitable[Any]]


def _get_user(update: Update):
    if update.effective_user:
        return update.effective_user
    if update.callback_query:
        return update.callback_query.from_user
    return None


def prevent_if_has_character(func: Handler) -> Handler:
    """Block access if the player already created a character."""

    @wraps(func)
    async def wrapper(update: Update, context, *args, **kwargs):
        user = _get_user(update)
        if not user:
            return

        async with aiosqlite.connect(DB_NAME) as db:
            async with db.execute(
                "SELECT 1 FROM players WHERE user_id = ?", (user.id,)
            ) as cursor:
                exists = await cursor.fetchone()

        if exists:
            query = getattr(update, "callback_query", None)
            if query:
                await query.answer(
                    "Kamu sudah memiliki karakter. Gunakan /resetme jika ingin mengulang.",
                    show_alert=True,
                )
            elif update.message:
                await update.message.reply_text(
                    "⚠️ Kamu sudah memiliki karakter. Gunakan /resetme untuk memulai ulang."
                )
            return

        return await func(update, context, *args, **kwargs)

    return wrapper  # type: ignore[return-value]


def require_player(func: Handler) -> Handler:
    """Ensure that the handler is only called for registered players."""

    @wraps(func)
    async def wrapper(update: Update, context, *args, **kwargs):
        user = _get_user(update)
        if not user:
            return

        async with aiosqlite.connect(DB_NAME) as db:
            async with db.execute(
                "SELECT 1 FROM players WHERE user_id = ?", (user.id,)
            ) as cursor:
                exists = await cursor.fetchone()

        if not exists:
            query = getattr(update, "callback_query", None)
            if query:
                await query.answer(
                    "Kamu belum membuat karakter! Gunakan /start terlebih dahulu.",
                    show_alert=True,
                )
            elif update.message:
                await update.message.reply_text(
                    "⚠️ Kamu belum membuat karakter! Gunakan /start untuk memulai."
                )
            return

        return await func(update, context, *args, **kwargs)

    return wrapper  # type: ignore[return-value]

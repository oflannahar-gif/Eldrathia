"""A small, text based battle helper used by a couple of story beats."""

from __future__ import annotations

import asyncio
import random
from typing import Dict

from data.monsters.monsters_rank_F import monsters_rank_F
from database import Player, update_player


def get_monster_by_name(name: str) -> Dict | None:
    for monster in monsters_rank_F:
        if monster["name"].lower() == name.lower():
            return monster
    return None


async def start_battle(update, context, player: Player, monster_name: str):
    monster = get_monster_by_name(monster_name)
    if not monster:
        await update.message.reply_text("❌ Monster tidak ditemukan di database!")
        return

    base_stats = {
        "Fighter": {"hp": 120, "atk": 18, "def": 10},
        "Mage": {"hp": 90, "atk": 22, "def": 7},
        "Paladin": {"hp": 140, "atk": 15, "def": 14},
        "Tank": {"hp": 180, "atk": 12, "def": 20},
        "Assassin": {"hp": 100, "atk": 24, "def": 8},
        "Archer": {"hp": 110, "atk": 21, "def": 9},
    }

    stats = base_stats.get(player.class_name, {"hp": 100, "atk": 15, "def": 8})

    player_hp = stats["hp"] + player.level * 10
    player_atk = stats["atk"] + player.level * 2
    player_def = stats["def"] + player.level

    monster_hp = monster["hp"]
    monster_atk = monster["atk"]
    monster_def = monster["def"]

    await update.message.reply_text(
        "\n".join(
            [
                "🔥 *Pertarungan Dimulai!*",
                f"Kau melawan *{monster['name']}* (HP: {monster_hp})!",
                "",
            ]
        ),
        parse_mode="Markdown",
    )
    await asyncio.sleep(1)

    while monster_hp > 0 and player_hp > 0:
        damage_to_monster = max(
            1, random.randint(player_atk - 3, player_atk + 3) - monster_def // 8
        )
        monster_hp -= damage_to_monster
        await update.message.reply_text(
            f"🗡️ Kamu menyerang {monster['name']} dan memberikan *{damage_to_monster} dmg!*",
            parse_mode="Markdown",
        )

        if monster_hp <= 0:
            break

        await asyncio.sleep(1)

        damage_to_player = max(
            1, random.randint(monster_atk - 3, monster_atk + 3) - player_def // 8
        )
        player_hp -= damage_to_player
        await update.message.reply_text(
            f"👾 {monster['name']} menyerang balik dan memberikan *{damage_to_player} dmg!*",
            parse_mode="Markdown",
        )

        await asyncio.sleep(1)

    if player_hp > 0:
        exp_gain = monster["exp"]
        gold_gain = monster["gold_drop"]

        await update.message.reply_text(
            f"🏆 *Kemenangan!*\n✨ +{exp_gain} EXP  💰 +{gold_gain} Gold",
            parse_mode="Markdown",
        )

        await update_player(
            player.user_id,
            exp=player.exp + exp_gain,
            gold=player.gold + gold_gain,
        )
    else:
        await update.message.reply_text(
            "💀 Kamu dikalahkan oleh monster... Cobalah lagi setelah memulihkan diri."
        )
